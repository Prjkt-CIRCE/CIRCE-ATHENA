"""CURATED-00 smoke: clean install + non-destructive legacy compatibility."""

from __future__ import annotations

from contextlib import closing
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "operators",
    "audit_logs",
    "assistant_execution_preferences",
    "sync_queue",
    "photos",
    "shared_cases",
    "shared_persons",
    "shared_documents",
    "shared_links",
    "shared_case_annotations",
    "platea_access_log",
    "investigative_workspaces",
    "investigative_blocks",
    "investigative_block_sources",
}


def run(*args: str, data_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATA_DIR"] = str(data_dir)
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(args)}")
    return result


def table_names(db_path: Path) -> set[str]:
    with closing(sqlite3.connect(db_path)) as con:
        return {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }


def seed_legacy_schema(data_dir: Path) -> None:
    code = """
from app.database import Base, engine
import app.models.operator
import app.models.photo
import app.models.platea
import app.models.workspace
Base.metadata.create_all(bind=engine)
"""
    run("-c", code, data_dir=data_dir)

    db_path = data_dir / "athena.db"
    with closing(sqlite3.connect(db_path)) as con:
        con.execute(
            """
            INSERT INTO operators
                (username, full_name, password_hash, role, is_active,
                 failed_attempts, locked_until, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-audit",
                "Legacy Audit",
                "hash-preservado",
                "admin",
                1,
                0,
                None,
                "2026-08-25 10:00:00",
                None,
            ),
        )
        con.execute(
            """
            INSERT INTO audit_logs
                (timestamp, operator_id, operator_username, action,
                 entity_type, entity_id, description, ip_address,
                 previous_hash, current_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-08-25 10:00:00",
                1,
                "legacy-audit",
                "legacy_marker",
                "audit",
                "1",
                "preservar",
                "127.0.0.1",
                "0" * 64,
                "1" * 64,
            ),
        )
        con.execute(
            """
            INSERT INTO sync_queue
                (source_system, payload_type, payload, status,
                 created_at, processed_at, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy",
                "marker",
                '{"preservar": true}',
                "pending",
                "2026-08-25 10:00:00",
                None,
                None,
            ),
        )
        con.commit()


def verify_legacy_rows(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as con:
        operator = con.execute(
            "SELECT username, password_hash FROM operators WHERE username='legacy-audit'"
        ).fetchone()
        audit = con.execute(
            "SELECT action, description FROM audit_logs WHERE action='legacy_marker'"
        ).fetchone()
        queue = con.execute(
            "SELECT source_system, payload_type, status FROM sync_queue WHERE source_system='legacy'"
        ).fetchone()

    assert operator == ("legacy-audit", "hash-preservado")
    assert audit == ("legacy_marker", "preservar")
    assert queue == ("legacy", "marker", "pending")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="athena-curated-fresh-") as temp:
        fresh_dir = Path(temp)
        run("-m", "alembic", "upgrade", "head", data_dir=fresh_dir)
        fresh_db = fresh_dir / "athena.db"
        actual = table_names(fresh_db)
        missing = sorted(EXPECTED_TABLES - actual)
        assert not missing, f"Fresh schema missing: {missing}"

        run("-m", "alembic", "upgrade", "head", data_dir=fresh_dir)

    with tempfile.TemporaryDirectory(prefix="athena-curated-legacy-") as temp:
        legacy_dir = Path(temp)
        seed_legacy_schema(legacy_dir)
        legacy_db = legacy_dir / "athena.db"

        before = table_names(legacy_db)
        assert {"operators", "audit_logs", "sync_queue"} <= before

        run(
            "-m",
            "alembic",
            "stamp",
            "0007_at06a_workspace_core",
            data_dir=legacy_dir,
        )
        run("-m", "alembic", "upgrade", "head", data_dir=legacy_dir)

        after = table_names(legacy_db)
        assert EXPECTED_TABLES <= after
        verify_legacy_rows(legacy_db)

    print("CURATED-00 FOUNDATION SMOKE: OK")
    print("fresh-schema=complete")
    print("second-upgrade=idempotent")
    print("legacy-core-tables=preserved")
    print("legacy-data=preserved")


if __name__ == "__main__":
    main()
