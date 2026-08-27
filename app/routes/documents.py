from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.database import SessionLocal
from app.models.platea import SharedDocument
from app.services.audit_service import log_action
from app.services.document_intake_service import (
    CaseNotFound,
    DocumentIntakeError,
    InvalidDocumentContent,
    InvalidOriginalFilename,
    UnsupportedDocumentType,
    incorporate_document,
)
from app.services.storage_service import (
    EmptyStoredFile,
    InvalidStorageReference,
    LocalCaseStorage,
    StorageError,
    StorageIntegrityError,
    StoredFileTooLarge,
)


router = APIRouter()


def _case_storage() -> LocalCaseStorage:
    return LocalCaseStorage(
        Path(settings.data_dir) / settings.case_storage_dir
    )


def _safe_log_filename(value: str | None) -> str:
    return (
        (value or "sem_nome")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()[:256]
    )


def _audit_failure(
    db,
    *,
    action: str,
    description: str,
    operator: dict,
    ip_address: str | None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> None:
    """
    Best-effort audit for a rejected operation.

    Known intake/retrieval failures should leave an audit record whenever the
    database itself remains available.
    """
    db.rollback()

    try:
        log_action(
            db,
            action=action,
            description=description,
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            manage_transaction=False,
        )
        db.commit()
    except Exception:
        db.rollback()


def _document_payload(document: SharedDocument) -> dict:
    return {
        "id": document.id,
        "case_id": document.shared_case_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "sha256": document.sha256,
        "storage_state": document.storage_state,
        "physical_available": document.physical_available,
    }


@router.post("/api/cases/{case_ref}/documents/intake")
async def document_intake(
    request: Request,
    case_ref: str,
    file: UploadFile = File(...),
):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    filename = _safe_log_filename(file.filename)

    db = SessionLocal()
    try:
        try:
            result = incorporate_document(
                db,
                storage=_case_storage(),
                case_ref=case_ref,
                source=file.file,
                original_filename=file.filename or "",
                max_bytes=settings.document_intake_max_bytes,
                operator_id=operator.get("id"),
                operator_username=operator.get("username"),
                ip_address=ip,
                storage_origin="case_intake",
            )

        except CaseNotFound as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado: caso não encontrado. "
                    f"case_ref={case_ref}; arquivo={filename}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": str(exc)},
                status_code=404,
            )

        except UnsupportedDocumentType as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado por formato não permitido. "
                    f"caso={case_ref}; arquivo={filename}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": str(exc)},
                status_code=415,
            )

        except InvalidOriginalFilename as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado por nome de arquivo inválido. "
                    f"caso={case_ref}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": str(exc)},
                status_code=400,
            )

        except InvalidDocumentContent as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado por incompatibilidade de conteúdo. "
                    f"caso={case_ref}; arquivo={filename}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": str(exc)},
                status_code=422,
            )

        except EmptyStoredFile as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado por arquivo vazio. "
                    f"caso={case_ref}; arquivo={filename}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": str(exc)},
                status_code=422,
            )

        except StoredFileTooLarge as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado por exceder o limite configurado. "
                    f"caso={case_ref}; arquivo={filename}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": str(exc)},
                status_code=413,
            )

        except (DocumentIntakeError, StorageError) as exc:
            _audit_failure(
                db,
                action="document_intake_failed",
                description=(
                    f"Intake rejeitado por erro controlado. "
                    f"caso={case_ref}; arquivo={filename}; "
                    f"tipo={type(exc).__name__}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_case",
                entity_id=case_ref,
            )
            return JSONResponse(
                {"error": "Não foi possível incorporar o material."},
                status_code=500,
            )

        status_code = 201 if result.status == "created" else 200

        return JSONResponse(
            {
                "status": result.status,
                "duplicate": result.duplicate,
                "document": _document_payload(result.document),
            },
            status_code=status_code,
        )

    finally:
        await file.close()
        db.close()


@router.get("/api/documents/{document_id}/original")
async def document_original(
    request: Request,
    document_id: int,
):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None

    db = SessionLocal()
    try:
        document = (
            db.query(SharedDocument)
            .filter(SharedDocument.id == document_id)
            .first()
        )

        if not document:
            return JSONResponse(
                {"error": "Documento não encontrado."},
                status_code=404,
            )

        if not document.storage_relpath:
            _audit_failure(
                db,
                action="document_original_retrieval_failed",
                description=(
                    f"Recuperação recusada: documento {document.id} "
                    f"não possui original físico incorporado."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_document",
                entity_id=str(document.id),
            )
            return JSONResponse(
                {
                    "error": (
                        "Documento existe apenas como metadado; "
                        "original físico indisponível."
                    )
                },
                status_code=409,
            )

        storage = _case_storage()

        try:
            original_path = storage.resolve(
                document.storage_relpath
            )

        except StorageIntegrityError:
            _audit_failure(
                db,
                action="document_original_retrieval_failed",
                description=(
                    f"Original físico ausente para documento {document.id}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_document",
                entity_id=str(document.id),
            )
            return JSONResponse(
                {"error": "Original físico não está disponível no storage."},
                status_code=410,
            )

        except InvalidStorageReference:
            _audit_failure(
                db,
                action="document_original_retrieval_failed",
                description=(
                    f"Referência física inválida detectada no documento "
                    f"{document.id}."
                ),
                operator=operator,
                ip_address=ip,
                entity_type="shared_document",
                entity_id=str(document.id),
            )
            return JSONResponse(
                {"error": "Referência interna de storage inválida."},
                status_code=500,
            )

        # Recuperação governada: se não for possível registrar a leitura,
        # o arquivo não é servido silenciosamente.
        log_action(
            db,
            action="document_original_retrieved",
            description=(
                f"Original físico recuperado para documento {document.id}; "
                f"arquivo={document.filename}; sha256={document.sha256}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="shared_document",
            entity_id=str(document.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()

        return FileResponse(
            path=str(original_path),
            media_type=document.mime_type or "application/octet-stream",
            filename=document.filename,
            content_disposition_type="attachment",
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
