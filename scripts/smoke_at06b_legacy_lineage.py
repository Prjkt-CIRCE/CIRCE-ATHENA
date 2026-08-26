"""AT-06B-CURATED-01 legacy-lineage compatibility smoke."""

from __future__ import annotations

import argparse
import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.platea import SharedCase, SharedDocument
from app.services.document_intake_service import incorporate_document
from app.services.storage_service import LocalCaseStorage


LEGACY_REVISION = "0013_at06b63_facts_topic_composition"
TARGET_REVISION = "0009_at06b_curated_intake_storage"

PDF = b"%PDF-1.7\nAT06B LEGACY LINEAGE SMOKE\n%%EOF\n"


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def read_state(path: Path) -> dict:
    con = sqlite3.connect(
        f"file:{path.as_posix()}?mode=ro",
        uri=True,
    )

    tables = {
        row[0]
        for row in con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
            """
        )
    }

    version = con.execute(
        "SELECT version_num FROM alembic_version"
    ).fetchone()[0]

    counts = {}

    for table in tables:
        if table == "alembic_version":
            continue

        counts[table] = con.execute(
            f"SELECT COUNT(*) FROM {quote_ident(table)}"
        ).fetchone()[0]

    doc_columns = {
        row[1]
        for row in con.execute(
            'PRAGMA table_info("shared_documents")'
        )
    }

    core_fields = [
        "id",
        "shared_case_id",
        "document_ref",
        "filename",
        "file_type",
        "sha256",
        "description",
        "imported_at",
    ]

    if "mime_type" in doc_columns:
        core_fields.append("mime_type")

    documents = con.execute(
        "SELECT "
        + ", ".join(quote_ident(item) for item in core_fields)
        + ' FROM "shared_documents" ORDER BY id'
    ).fetchall()

    con.close()

    return {
        "tables": tables,
        "version": version,
        "counts": counts,
        "documents": documents,
        "doc_columns": doc_columns,
    }


def run_alembic(project_root: Path, data_dir: Path) -> None:
    env = os.environ.copy()
    env["DATA_DIR"] = str(data_dir)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
        ],
        cwd=project_root,
        env=env,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_db")
    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    source = Path(args.source_db).resolve()

    if not source.is_file():
        raise SystemExit(
            f"Banco fonte não encontrado: {source}"
        )

    before = read_state(source)

    assert before["version"] == LEGACY_REVISION, (
        f"Esperado {LEGACY_REVISION}; "
        f"encontrado {before['version']}"
    )

    with tempfile.TemporaryDirectory(
        prefix="circe-at06b-lineage-"
    ) as tmp:
        tmp_path = Path(tmp)
        copied_db = tmp_path / "athena.db"

        shutil.copy2(source, copied_db)

        # Primeira migração da cópia real antiga.
        run_alembic(project_root, tmp_path)

        after = read_state(copied_db)

        assert after["version"] == TARGET_REVISION

        # Nenhuma tabela histórica pode desaparecer.
        assert before["tables"].issubset(after["tables"])

        # Nenhuma contagem antiga pode mudar pela migration.
        for table, count in before["counts"].items():
            assert after["counts"][table] == count, (
                table,
                count,
                after["counts"][table],
            )

        # Metadados documentais antigos devem ser byte/logicamente preservados.
        assert after["documents"] == before["documents"]

        expected_columns = {
            "storage_relpath",
            "mime_type",
            "size_bytes",
            "storage_origin",
            "stored_at",
        }

        assert expected_columns.issubset(
            after["doc_columns"]
        )

        con = sqlite3.connect(copied_db)

        fabricated = con.execute(
            """
            SELECT COUNT(*)
            FROM shared_documents
            WHERE storage_relpath IS NOT NULL
               OR size_bytes IS NOT NULL
               OR storage_origin IS NOT NULL
               OR stored_at IS NOT NULL
            """
        ).fetchone()[0]

        assert fabricated == 0

        indexes = {
            row[1]
            for row in con.execute(
                'PRAGMA index_list("shared_documents")'
            )
        }

        assert "ix_shared_documents_case_sha256" in indexes
        assert "ux_shared_documents_storage_relpath" in indexes

        con.close()

        # Segundo upgrade: estabilidade/idempotência.
        run_alembic(project_root, tmp_path)

        second = read_state(copied_db)
        assert second["version"] == TARGET_REVISION

        # Agora fazemos uma operação funcional REAL somente na cópia.
        engine = create_engine(
            f"sqlite:///{copied_db}",
            connect_args={"check_same_thread": False},
        )

        Session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )

        db = Session()

        case = (
            db.query(SharedCase)
            .order_by(SharedCase.id.asc())
            .first()
        )

        assert case is not None

        before_documents = db.query(SharedDocument).count()

        storage = LocalCaseStorage(
            tmp_path / "case_storage"
        )

        result = incorporate_document(
            db,
            storage=storage,
            case_ref=case.case_ref,
            source=io.BytesIO(PDF),
            original_filename="legacy_lineage_smoke.pdf",
            max_bytes=1024 * 1024,
            operator_username="legacy-lineage-smoke",
            storage_origin="compatibility_smoke",
        )

        assert result.status == "created"
        assert result.document.physical_available is True
        assert db.query(SharedDocument).count() == before_documents + 1

        recovered = storage.resolve(
            result.document.storage_relpath
        )

        assert recovered.read_bytes() == PDF

        duplicate = incorporate_document(
            db,
            storage=storage,
            case_ref=case.case_ref,
            source=io.BytesIO(PDF),
            original_filename="duplicate.pdf",
            max_bytes=1024 * 1024,
            operator_username="legacy-lineage-smoke",
        )

        assert duplicate.status == "duplicate"
        assert duplicate.document.id == result.document.id

        db.close()
        engine.dispose()

    print("AT-06B LEGACY LINEAGE SMOKE: OK")
    print("legacy-revision=recognized")
    print("legacy-tables=preserved")
    print("legacy-row-counts=preserved")
    print("legacy-document-metadata=preserved")
    print("preexisting-mime-type=preserved")
    print("missing-at06b-columns=added")
    print("fabricated-storage-metadata=no")
    print("second-upgrade=stable")
    print("real-copy-intake=created")
    print("real-copy-retrieval=byte-identical")
    print("real-copy-duplicate=blocked")


if __name__ == "__main__":
    main()
