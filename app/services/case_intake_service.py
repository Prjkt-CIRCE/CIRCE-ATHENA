from __future__ import annotations

import hashlib
import os
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.config import settings
from app.models.platea import SharedCase, SharedDocument

MAX_FILES_PER_BATCH = 50
MAX_FILE_BYTES = 250 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class CaseIntakeError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utcnow() -> datetime:
    return _utcnow().replace(tzinfo=None)


def _data_root() -> Path:
    root = Path(settings.data_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    return root.resolve()


def _safe_filename(value: str) -> str:
    name = Path(value or "arquivo").name.strip() or "arquivo"
    name = re.sub(r"[^A-Za-z0-9._()\- À-ÿ]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180] or "arquivo"


IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tif", "tiff", "heic", "heif"}
AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "aac", "ogg", "opus", "flac", "wma"}
VIDEO_EXTENSIONS = {"mp4", "mov", "mkv", "avi", "webm", "m4v", "3gp", "wmv"}


def classify_material_bin(filename: str, mime_type: str | None = None) -> str:
    """Classificação determinística mínima do intake.

    Não tenta inferir semântica (ex.: ficha de pessoa). Isso virá com OCR/indexação.
    """
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    mime = (mime_type or "").lower()
    if mime.startswith("image/") or suffix in IMAGE_EXTENSIONS:
        return "images"
    if mime.startswith("audio/") or suffix in AUDIO_EXTENSIONS:
        return "audio"
    if mime.startswith("video/") or suffix in VIDEO_EXTENSIONS:
        return "video"
    return "documents"


def generate_native_case_ref(db: Session, now: datetime | None = None) -> str:
    now = now or _utcnow()
    for _ in range(40):
        candidate = f"ATH-{now:%Y%m%d}-{secrets.token_hex(3).upper()}"
        if not db.query(SharedCase.id).filter(SharedCase.case_ref == candidate).first():
            return candidate
    raise CaseIntakeError("Não foi possível gerar um identificador interno único para o caso.")


def create_native_case(
    db: Session,
    *,
    title: str,
    classification: str | None,
    notes: str | None,
    source_unit: str | None,
    operator_id: int | None,
    operator_username: str | None,
) -> SharedCase:
    clean_title = (title or "").strip()
    if len(clean_title) < 3:
        raise CaseIntakeError("Informe um título provisório para o caso.")

    now = _utcnow()
    case = SharedCase(
        case_ref=generate_native_case_ref(db, now),
        case_uuid=str(uuid.uuid4()),
        origin_type="native",
        created_by_operator_id=operator_id,
        created_by_username=operator_username or "operador",
        title=clean_title[:256],
        status="aberto",
        classification=(classification or "").strip()[:64] or None,
        notes=(notes or "").strip() or None,
        source_unit=(source_unit or "").strip()[:128] or None,
        published_by=operator_username or "operador",
        published_at=now.replace(tzinfo=None),
        published_version=1,
        last_updated_at=now.replace(tzinfo=None),
    )
    db.add(case)
    db.flush()
    return case


async def ingest_case_uploads(
    db: Session,
    *,
    case: SharedCase,
    uploads: Iterable,
    operator_username: str | None,
    intake_bin: str | None = None,
) -> tuple[list[SharedDocument], list[str], int]:
    uploads = [item for item in uploads if getattr(item, "filename", None)]
    if len(uploads) > MAX_FILES_PER_BATCH:
        raise CaseIntakeError(f"Envie no máximo {MAX_FILES_PER_BATCH} arquivos por vez.")
    if not uploads:
        return [], [], 0
    if not case.case_uuid:
        raise CaseIntakeError("O caso não possui identidade nativa para armazenamento de arquivos.")

    root = _data_root()
    originals = root / "cases" / case.case_uuid / "originals"
    originals.mkdir(parents=True, exist_ok=True)

    created_docs: list[SharedDocument] = []
    created_paths: list[str] = []
    duplicates = 0

    try:
        for upload in uploads:
            safe_name = _safe_filename(str(upload.filename))
            temp_name = f".upload-{uuid.uuid4().hex}.part"
            temp_path = originals / temp_name
            hasher = hashlib.sha256()
            total = 0

            try:
                await upload.seek(0)
            except Exception:
                pass

            try:
                with temp_path.open("wb") as handle:
                    while True:
                        chunk = await upload.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_FILE_BYTES:
                            raise CaseIntakeError(
                                f"O arquivo {safe_name} excede o limite de {MAX_FILE_BYTES // (1024 * 1024)} MB desta etapa."
                            )
                        hasher.update(chunk)
                        handle.write(chunk)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise

            digest = hasher.hexdigest()
            existing = (
                db.query(SharedDocument)
                .filter(
                    SharedDocument.shared_case_id == case.id,
                    SharedDocument.sha256 == digest,
                )
                .first()
            )
            if existing:
                duplicates += 1
                temp_path.unlink(missing_ok=True)
                continue

            stored_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
            final_path = originals / stored_name
            os.replace(temp_path, final_path)
            relative = final_path.relative_to(root).as_posix()
            created_paths.append(relative)

            suffix = Path(safe_name).suffix.lower().lstrip(".") or "binary"
            upload_mime = (getattr(upload, "content_type", None) or "application/octet-stream")[:128]
            material_bin = (intake_bin or classify_material_bin(safe_name, upload_mime))[:64]
            doc = SharedDocument(
                shared_case_id=case.id,
                document_ref=f"NATIVE-DOC-{uuid.uuid4().hex[:12].upper()}",
                filename=safe_name,
                file_type=suffix[:32],
                sha256=digest,
                description="Material recebido no Pool do caso; classificação semântica e extração ainda pendentes.",
                imported_at=_utcnow().isoformat(),
                storage_path=relative,
                mime_type=upload_mime,
                file_size=total,
                intake_bin=material_bin,
                origin="native_intake",
                uploaded_by_username=operator_username or "operador",
                uploaded_at=_utcnow(),
            )
            db.add(doc)
            created_docs.append(doc)

        case.last_updated_at = _naive_utcnow()
        db.flush()
        return created_docs, created_paths, duplicates
    except Exception:
        cleanup_stored_paths(created_paths)
        raise


def cleanup_stored_paths(relative_paths: Iterable[str]) -> None:
    root = _data_root()
    for value in relative_paths:
        try:
            candidate = (root / value).resolve()
            if candidate == root or root not in candidate.parents:
                continue
            candidate.unlink(missing_ok=True)
        except Exception:
            continue

# AT06B52_DOCUMENT_PREVIEW_V1
def resolve_document_storage_path(document: SharedDocument) -> Path | None:
    """Resolve o original local sem permitir path traversal."""
    value = (document.storage_path or "").strip()
    if not value:
        return None

    root = _data_root()
    try:
        candidate = (root / value).resolve()
    except Exception:
        return None

    if candidate == root or root not in candidate.parents:
        return None
    if not candidate.is_file():
        return None
    return candidate

