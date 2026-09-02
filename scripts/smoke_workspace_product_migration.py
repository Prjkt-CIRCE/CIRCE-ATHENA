"""UX-03A real Alembic migration smoke against disposable databases."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path


TARGET_TABLES = {
    "workspace_products",
    "workspace_product_sections",
    "workspace_product_section_blocks",
}
PREVIOUS_HEAD = "0009_at06b_curated_intake_storage"
CURRENT_HEAD = "0010_ux03a_product_sections"


def _alembic(data_dir: Path, *args: str) -> None:
    env = os.environ.copy()
    env["DATA_DIR"] = str(data_dir)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=Path(__file__).resolve().parents[1], env=env,
        text=True, capture_output=True,
    )
    if result.returncode:
        raise AssertionError(f"Alembic failed ({' '.join(args)}):\n{result.stdout}\n{result.stderr}")


def _tables(db_path: Path) -> set[str]:
    with closing(sqlite3.connect(db_path)) as db:
        return {item[0] for item in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="circe-ux03a-migration-") as tmp:
        root = Path(tmp)

        fresh_dir = root / "fresh"
        fresh_dir.mkdir()
        _alembic(fresh_dir, "upgrade", "head")
        fresh_db = fresh_dir / "athena.db"
        assert TARGET_TABLES.issubset(_tables(fresh_db))
        with closing(sqlite3.connect(fresh_db)) as db:
            assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == CURRENT_HEAD
        _alembic(fresh_dir, "upgrade", "head")
        assert TARGET_TABLES.issubset(_tables(fresh_db))

        fixture_dir = root / "previous-head"
        fixture_dir.mkdir()
        _alembic(fixture_dir, "upgrade", PREVIOUS_HEAD)
        fixture_db = fixture_dir / "athena.db"
        with closing(sqlite3.connect(fixture_db)) as db:
            db.execute(
                "INSERT INTO shared_cases (id, case_ref, title, status, published_by, published_at, published_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (41, "MIG-SYNTH", "Caso sintético", "aberto", "smoke", "2026-09-02 12:00:00", 3),
            )
            db.execute(
                "INSERT INTO shared_documents (id, shared_case_id, document_ref, filename, file_type, sha256, description, imported_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (42, 41, "DOC-MIG", "metadata.txt", "txt", "b" * 64, "metadata-only", "2026-09-02"),
            )
            db.execute(
                "INSERT INTO investigative_workspaces (id, shared_case_id, created_by_operator_id, created_by_username, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (43, 41, 7, "smoke", "2026-09-02 12:00:00", "2026-09-02 12:00:00"),
            )
            db.execute(
                "INSERT INTO investigative_blocks (id, workspace_id, title, summary, status, created_by_operator_id, created_by_username, authorship_mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (44, 43, "Bloco anterior", "Preservar", "working", 7, "smoke", "literal", "2026-09-02 12:00:00", "2026-09-02 12:00:00"),
            )
            db.execute(
                "INSERT INTO investigative_block_sources (id, block_id, source_type, source_key, source_label_snapshot, source_snapshot, relation, position, added_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (45, 44, "document", "ref:DOC-MIG", "metadata.txt", "{\"synthetic\": true}", "context", 0, "2026-09-02 12:00:00"),
            )
            db.commit()
            before = {
                "case": db.execute("SELECT * FROM shared_cases WHERE id=41").fetchone(),
                "document": db.execute("SELECT * FROM shared_documents WHERE id=42").fetchone(),
                "workspace": db.execute("SELECT * FROM investigative_workspaces WHERE id=43").fetchone(),
                "block": db.execute("SELECT * FROM investigative_blocks WHERE id=44").fetchone(),
                "source": db.execute("SELECT * FROM investigative_block_sources WHERE id=45").fetchone(),
            }

        _alembic(fixture_dir, "upgrade", "head")
        assert TARGET_TABLES.issubset(_tables(fixture_db))
        with closing(sqlite3.connect(fixture_db)) as db:
            after = {
                "case": db.execute("SELECT * FROM shared_cases WHERE id=41").fetchone(),
                "document": db.execute("SELECT * FROM shared_documents WHERE id=42").fetchone(),
                "workspace": db.execute("SELECT * FROM investigative_workspaces WHERE id=43").fetchone(),
                "block": db.execute("SELECT * FROM investigative_blocks WHERE id=44").fetchone(),
                "source": db.execute("SELECT * FROM investigative_block_sources WHERE id=45").fetchone(),
            }
            assert after == before
            assert db.execute("SELECT storage_relpath FROM shared_documents WHERE id=42").fetchone()[0] is None
            assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == CURRENT_HEAD

        _alembic(fixture_dir, "downgrade", PREVIOUS_HEAD)
        assert not TARGET_TABLES.intersection(_tables(fixture_db))
        _alembic(fixture_dir, "upgrade", "head")
        assert TARGET_TABLES.issubset(_tables(fixture_db))

    print("UX-03A PRODUCT MIGRATION SMOKE: OK")
    print("fresh-chain=ok; repeated-head=ok; previous-head-fixture=preserved")
    print("downgrade-upgrade=disposable-only; operational-database=untouched")


if __name__ == "__main__":
    main()
