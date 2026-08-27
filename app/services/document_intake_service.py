from __future__ import annotations

import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.models.platea import SharedCase, SharedDocument
from app.services.audit_service import log_action
from app.services.storage_service import LocalCaseStorage, StoredFile


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".csv",
    ".docx",
    ".xlsx",
}


class DocumentIntakeError(Exception):
    """Base error for canonical case document intake."""


class CaseNotFound(DocumentIntakeError):
    pass


class InvalidOriginalFilename(DocumentIntakeError):
    pass


class UnsupportedDocumentType(DocumentIntakeError):
    pass


class InvalidDocumentContent(DocumentIntakeError):
    pass


@dataclass(frozen=True)
class IntakeResult:
    status: str
    document: SharedDocument
    duplicate: bool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_original_filename(value: str) -> str:
    raw = (value or "").replace("\\", "/")
    name = raw.rsplit("/", 1)[-1].strip()

    if not name or name in {".", ".."}:
        raise InvalidOriginalFilename("Nome original do arquivo é inválido.")

    if "\x00" in name:
        raise InvalidOriginalFilename("Nome original contém caractere inválido.")

    if len(name) > 256:
        raise InvalidOriginalFilename(
            "Nome original excede o limite de 256 caracteres."
        )

    return name


def _extension_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedDocumentType(
            f"Formato não permitido para intake: {suffix or 'sem extensão'}."
        )

    return suffix


def _validate_text_file(path: Path) -> None:
    with path.open("rb") as handle:
        sample = handle.read(64 * 1024)

    if b"\x00" in sample:
        raise InvalidDocumentContent(
            "Conteúdo binário incompatível com arquivo textual."
        )

    try:
        sample.decode("utf-8-sig")
        return
    except UnicodeDecodeError:
        pass

    try:
        sample.decode("cp1252")
        return
    except UnicodeDecodeError as exc:
        raise InvalidDocumentContent(
            "Arquivo textual não possui codificação reconhecida."
        ) from exc


def _validate_office_package(path: Path, extension: str) -> str:
    if not zipfile.is_zipfile(path):
        raise InvalidDocumentContent(
            "Conteúdo não corresponde a um pacote Office válido."
        )

    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise InvalidDocumentContent(
            "Pacote Office está corrompido ou inválido."
        ) from exc

    if "[Content_Types].xml" not in names:
        raise InvalidDocumentContent(
            "Pacote Office não possui Content Types."
        )

    if extension == ".docx":
        if "word/document.xml" not in names:
            raise InvalidDocumentContent(
                "Conteúdo não corresponde a DOCX válido."
            )
        return (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    if "xl/workbook.xml" not in names:
        raise InvalidDocumentContent(
            "Conteúdo não corresponde a XLSX válido."
        )

    return (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )


def _detect_and_validate_content(path: Path, extension: str) -> str:
    with path.open("rb") as handle:
        header = handle.read(16)

    if extension == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise InvalidDocumentContent(
                "Conteúdo não corresponde a um PDF."
            )
        return "application/pdf"

    if extension == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise InvalidDocumentContent(
                "Conteúdo não corresponde a PNG."
            )
        return "image/png"

    if extension in {".jpg", ".jpeg"}:
        if not header.startswith(b"\xff\xd8\xff"):
            raise InvalidDocumentContent(
                "Conteúdo não corresponde a JPEG."
            )
        return "image/jpeg"

    if extension == ".txt":
        _validate_text_file(path)
        return "text/plain"

    if extension == ".csv":
        _validate_text_file(path)
        return "text/csv"

    if extension in {".docx", ".xlsx"}:
        return _validate_office_package(path, extension)

    raise UnsupportedDocumentType(
        f"Formato não suportado: {extension}."
    )


def _file_type_from_extension(extension: str) -> str:
    return extension.lstrip(".").lower()


def incorporate_document(
    db: Session,
    *,
    storage: LocalCaseStorage,
    case_ref: str,
    source: BinaryIO,
    original_filename: str,
    max_bytes: int,
    operator_id: int | None = None,
    operator_username: str | None = None,
    ip_address: str | None = None,
    storage_origin: str = "case_intake",
) -> IntakeResult:
    """
    Incorporate one original file into the canonical material set of a Case.

    The operation owns its database transaction because physical storage and
    database state must either converge or be compensated.
    """
    case = (
        db.query(SharedCase)
        .filter(SharedCase.case_ref == case_ref)
        .first()
    )
    if not case:
        raise CaseNotFound(f"Caso não encontrado: {case_ref}.")

    filename = _normalize_original_filename(original_filename)
    extension = _extension_for(filename)

    staged = storage.stage(source, max_bytes=max_bytes)

    try:
        mime_type = _detect_and_validate_content(
            staged.temp_path,
            extension,
        )
    except Exception:
        storage.discard_stage(staged)
        raise

    existing = (
        db.query(SharedDocument)
        .filter(
            SharedDocument.shared_case_id == case.id,
            SharedDocument.sha256 == staged.sha256,
        )
        .order_by(SharedDocument.id.asc())
        .first()
    )

    # SHA already exists and the physical original is already present:
    # this is a true duplicate inside the same Case.
    if existing and existing.storage_relpath:
        storage.discard_stage(staged)

        try:
            log_action(
                db,
                action="document_intake_duplicate_detected",
                description=(
                    f"Material duplicado detectado no caso {case.case_ref}. "
                    f"arquivo={filename}; sha256={staged.sha256}; "
                    f"document_id={existing.id}; origem={storage_origin}."
                ),
                operator_id=operator_id,
                operator_username=operator_username,
                entity_type="shared_document",
                entity_id=str(existing.id),
                ip_address=ip_address,
                manage_transaction=False,
            )
            db.commit()
            db.refresh(existing)
        except Exception:
            db.rollback()
            raise

        return IntakeResult(
            status="duplicate",
            document=existing,
            duplicate=True,
        )

    stored: StoredFile | None = None
    now = _utcnow()

    try:
        stored = storage.finalize(
            staged,
            case_internal_id=case.id,
        )

        # A metadata-only record with the same SHA is completed rather than
        # duplicated.
        if existing:
            document = existing
            document.storage_relpath = stored.storage_relpath
            document.mime_type = mime_type
            document.size_bytes = stored.size_bytes
            document.storage_origin = storage_origin
            document.stored_at = now
            result_status = "hydrated"

            audit_action = "document_physical_original_attached"
            audit_description = (
                f"Original físico incorporado ao documento metadata-only "
                f"{document.id} do caso {case.case_ref}. "
                f"arquivo_recebido={filename}; sha256={stored.sha256}; "
                f"size_bytes={stored.size_bytes}; origem={storage_origin}."
            )

        else:
            document = SharedDocument(
                shared_case_id=case.id,
                document_ref=None,
                filename=filename,
                file_type=_file_type_from_extension(extension),
                sha256=stored.sha256,
                description=None,
                imported_at=now.isoformat(),
                storage_relpath=stored.storage_relpath,
                mime_type=mime_type,
                size_bytes=stored.size_bytes,
                storage_origin=storage_origin,
                stored_at=now,
            )
            db.add(document)
            db.flush()

            result_status = "created"

            audit_action = "document_intake_completed"
            audit_description = (
                f"Material incorporado ao caso {case.case_ref}. "
                f"arquivo={filename}; sha256={stored.sha256}; "
                f"size_bytes={stored.size_bytes}; "
                f"document_id={document.id}; origem={storage_origin}."
            )

        log_action(
            db,
            action=audit_action,
            description=audit_description,
            operator_id=operator_id,
            operator_username=operator_username,
            entity_type="shared_document",
            entity_id=str(document.id),
            ip_address=ip_address,
            manage_transaction=False,
        )

        db.commit()
        db.refresh(document)

        return IntakeResult(
            status=result_status,
            document=document,
            duplicate=False,
        )

    except Exception:
        db.rollback()

        # Physical write happened before the DB commit. Compensate it.
        if stored is not None:
            try:
                storage.delete(stored.storage_relpath)
            except Exception:
                # Preserve the original exception. Orphan cleanup can later
                # reconcile a physical artifact not referenced by the DB.
                pass
        else:
            storage.discard_stage(staged)

        raise
