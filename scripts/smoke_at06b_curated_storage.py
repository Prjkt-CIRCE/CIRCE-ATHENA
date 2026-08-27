"""AT-06B-CURATED-01 G1 smoke: canonical physical storage contract."""

from __future__ import annotations

import hashlib
import io
import tempfile
from pathlib import Path

from app.services.storage_service import (
    EmptyStoredFile,
    InvalidStorageReference,
    LocalCaseStorage,
    StorageIntegrityError,
    StoredFileTooLarge,
)


def expect_error(error_type, action) -> None:
    try:
        action()
    except error_type:
        return
    raise AssertionError(f"Era esperado {error_type.__name__}.")


def main() -> None:
    payload = b"%PDF-1.7\nCIRCE ATHENA STORAGE SMOKE\n%%EOF\n"
    expected_sha = hashlib.sha256(payload).hexdigest()

    with tempfile.TemporaryDirectory(prefix="circe-storage-smoke-") as tmp:
        root = Path(tmp) / "storage"
        storage = LocalCaseStorage(root)

        # 1. escrita temporária + hash sobre os bytes persistidos
        staged = storage.stage(
            io.BytesIO(payload),
            max_bytes=1024 * 1024,
        )

        assert staged.temp_path.is_file()
        assert staged.temp_path.read_bytes() == payload
        assert staged.size_bytes == len(payload)
        assert staged.sha256 == expected_sha

        # 2. destino canônico controlado pela aplicação
        stored = storage.finalize(
            staged,
            case_internal_id=42,
        )

        assert not staged.temp_path.exists()
        assert stored.absolute_path.is_file()
        assert stored.absolute_path.read_bytes() == payload
        assert stored.sha256 == expected_sha
        assert stored.size_bytes == len(payload)

        assert stored.storage_relpath.startswith(
            "cases/42/documents/"
        )
        assert not Path(stored.storage_relpath).is_absolute()

        # nome físico deve ser opaco: não reutiliza nome original
        assert "relatorio" not in stored.storage_relpath.lower()
        assert ".pdf" not in stored.storage_relpath.lower()

        # 3. resolução posterior reproduz o mesmo original
        resolved = storage.resolve(stored.storage_relpath)
        assert resolved == stored.absolute_path
        assert resolved.read_bytes() == payload
        assert hashlib.sha256(resolved.read_bytes()).hexdigest() == expected_sha

        # 4. arquivo vazio
        expect_error(
            EmptyStoredFile,
            lambda: storage.stage(
                io.BytesIO(b""),
                max_bytes=1024,
            ),
        )

        # 5. limite de tamanho
        expect_error(
            StoredFileTooLarge,
            lambda: storage.stage(
                io.BytesIO(b"123456"),
                max_bytes=5,
            ),
        )

        # 6. path absoluto não pode ser resolvido
        expect_error(
            InvalidStorageReference,
            lambda: storage.resolve(str(resolved)),
        )

        # 7. traversal deve ser bloqueado
        expect_error(
            InvalidStorageReference,
            lambda: storage.resolve("../fora-do-root"),
        )

        expect_error(
            InvalidStorageReference,
            lambda: storage.resolve(
                "cases/42/documents/../../../../fora-do-root"
            ),
        )

        # 8. referência válida porém arquivo ausente
        expect_error(
            StorageIntegrityError,
            lambda: storage.resolve(
                "cases/42/documents/arquivo-inexistente"
            ),
        )

        # 9. compensação física
        storage.delete(stored.storage_relpath)
        assert not stored.absolute_path.exists()

        # 10. nenhum temporário residual
        temp_files = (
            list(storage.temp_root.iterdir())
            if storage.temp_root.exists()
            else []
        )
        assert temp_files == []

    print("AT-06B-CURATED-01 STORAGE SMOKE: OK")
    print("original-bytes=preserved")
    print("sha256=persisted-bytes")
    print("storage-reference=relative")
    print("physical-name=opaque")
    print("path-traversal=blocked")
    print("absolute-reference=blocked")
    print("missing-file=explicit-error")
    print("empty-file=rejected")
    print("size-limit=enforced")
    print("compensation-delete=ok")


if __name__ == "__main__":
    main()
