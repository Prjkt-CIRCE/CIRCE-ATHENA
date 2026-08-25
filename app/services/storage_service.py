from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


class StorageError(Exception):
    """Base error for canonical case storage."""


class InvalidStorageReference(StorageError):
    """Raised when a persisted storage reference is unsafe."""


class StorageIntegrityError(StorageError):
    """Raised when a valid reference points to missing/non-file content."""


class EmptyStoredFile(StorageError):
    """Raised when an intake stream contains no bytes."""


class StoredFileTooLarge(StorageError):
    """Raised when an intake stream exceeds the configured byte limit."""


@dataclass(frozen=True)
class StagedFile:
    temp_path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class StoredFile:
    storage_relpath: str
    absolute_path: Path
    sha256: str
    size_bytes: int


class LocalCaseStorage:
    """
    Canonical local storage for original case materials.

    The database persists only storage_relpath.
    Absolute paths never form part of the domain contract.
    """

    CHUNK_SIZE = 1024 * 1024

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.temp_root = self.root / ".tmp"

    def _ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def _contained_path(self, relpath: str) -> Path:
        if not relpath or not isinstance(relpath, str):
            raise InvalidStorageReference("Referência de storage vazia ou inválida.")

        candidate_ref = Path(relpath)

        if candidate_ref.is_absolute():
            raise InvalidStorageReference(
                "Referência absoluta de storage não é permitida."
            )

        candidate = (self.root / candidate_ref).resolve()

        try:
            common = os.path.commonpath([str(self.root), str(candidate)])
        except ValueError as exc:
            raise InvalidStorageReference(
                "Referência de storage fora da raiz configurada."
            ) from exc

        if Path(common) != self.root:
            raise InvalidStorageReference(
                "Referência de storage escapa da raiz configurada."
            )

        return candidate

    def stage(
        self,
        source: BinaryIO,
        *,
        max_bytes: int,
    ) -> StagedFile:
        """
        Persist the received stream into a controlled temporary area while
        calculating SHA-256 over the bytes actually written.
        """
        if max_bytes <= 0:
            raise ValueError("max_bytes deve ser maior que zero.")

        self._ensure_root()

        temp_path = self.temp_root / f"{uuid.uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0

        try:
            with temp_path.open("xb") as target:
                while True:
                    chunk = source.read(self.CHUNK_SIZE)
                    if not chunk:
                        break

                    size += len(chunk)
                    if size > max_bytes:
                        raise StoredFileTooLarge(
                            f"Arquivo excede o limite de {max_bytes} bytes."
                        )

                    target.write(chunk)
                    digest.update(chunk)

                target.flush()
                os.fsync(target.fileno())

            if size == 0:
                raise EmptyStoredFile("Arquivo vazio não pode ser incorporado.")

            return StagedFile(
                temp_path=temp_path,
                sha256=digest.hexdigest(),
                size_bytes=size,
            )

        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    def finalize(
        self,
        staged: StagedFile,
        *,
        case_internal_id: int,
    ) -> StoredFile:
        """
        Atomically move a staged original into its canonical case location.

        The physical filename is opaque and unrelated to the user-supplied
        filename.
        """
        if case_internal_id <= 0:
            raise ValueError("case_internal_id deve ser maior que zero.")

        if not staged.temp_path.is_file():
            raise StorageIntegrityError(
                "Arquivo temporário de intake não está disponível."
            )

        destination_dir = (
            self.root
            / "cases"
            / str(case_internal_id)
            / "documents"
        )
        destination_dir.mkdir(parents=True, exist_ok=True)

        opaque_name = uuid.uuid4().hex
        destination = destination_dir / opaque_name

        os.replace(staged.temp_path, destination)

        relpath = destination.relative_to(self.root).as_posix()

        return StoredFile(
            storage_relpath=relpath,
            absolute_path=destination,
            sha256=staged.sha256,
            size_bytes=staged.size_bytes,
        )

    def resolve(self, storage_relpath: str) -> Path:
        """
        Resolve a persisted reference under the configured storage root.

        Arbitrary absolute paths and traversal are rejected.
        """
        candidate = self._contained_path(storage_relpath)

        if not candidate.exists() or not candidate.is_file():
            raise StorageIntegrityError(
                "Arquivo físico não encontrado para a referência informada."
            )

        return candidate

    def discard_stage(self, staged: StagedFile) -> None:
        staged.temp_path.unlink(missing_ok=True)

    def delete(self, storage_relpath: str) -> None:
        """
        Compensation helper for database failure after final storage write.

        This is not a user-facing permanent-delete feature.
        """
        candidate = self._contained_path(storage_relpath)

        if candidate.exists():
            if not candidate.is_file():
                raise StorageIntegrityError(
                    "Referência de storage não aponta para um arquivo."
                )
            candidate.unlink()

        parent = candidate.parent
        documents_dir = parent

        if documents_dir.name == "documents":
            try:
                documents_dir.rmdir()
                documents_dir.parent.rmdir()
            except OSError:
                pass

    def purge_temp(self) -> None:
        """
        Test/maintenance helper. Not part of the user-facing intake contract.
        """
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root)
