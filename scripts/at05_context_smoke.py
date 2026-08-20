"""
Smoke tests AT-05.1 — sem pytest.

Execução:
    python scripts/at05_context_smoke.py
"""

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Garante import do pacote app ao executar diretamente pelo path scripts/.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base
from app.models.platea import SharedCase, SharedPerson
from app.services.assistant_context_service import build_investigative_context


class AT05ContextSmokeTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        open_case = SharedCase(
            case_ref="2026-OPEN-001",
            title="Operacao Horizonte",
            status="aberto",
            classification="trafico",
            notes="Caso aberto de teste.",
            source_unit="Nucleo A",
            published_by="tester",
            published_at=now,
            published_version=1,
        )
        closed_case = SharedCase(
            case_ref="2026-CLOSED-002",
            title="Operacao Encerrada",
            status="encerrado",
            classification="patrimonial",
            notes="Caso encerrado de teste.",
            source_unit="Nucleo B",
            published_by="tester",
            published_at=now,
            published_version=1,
        )
        self.db.add_all([open_case, closed_case])
        self.db.flush()

        self.db.add(
            SharedPerson(
                shared_case_id=open_case.id,
                person_ref="P-001",
                full_name="Pessoa Teste",
                role_in_case="investigado",
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_open_cases_only_returns_open_case(self):
        ctx = build_investigative_context(
            self.db,
            "Quais casos estao abertos?",
        )
        self.assertEqual(ctx.sources, ["PLATEA:2026-OPEN-001"])
        self.assertIn("status: aberto", ctx.text)
        self.assertNotIn("2026-CLOSED-002", ctx.text)

    def test_explicit_case_reference_returns_exact_case(self):
        ctx = build_investigative_context(
            self.db,
            "Resuma o caso 2026-CLOSED-002.",
        )
        self.assertEqual(ctx.sources, ["PLATEA:2026-CLOSED-002"])
        self.assertIn("[PLATEA:2026-CLOSED-002]", ctx.text)
        self.assertNotIn("2026-OPEN-001", ctx.text)

    def test_unknown_explicit_reference_returns_no_sources(self):
        ctx = build_investigative_context(
            self.db,
            "Resuma o caso 2099-NAO-EXISTE.",
        )
        self.assertEqual(ctx.sources, [])
        self.assertEqual(ctx.case_refs, [])
        self.assertIn("nao foi encontrado", ctx.text.lower())
        self.assertNotIn("2026-OPEN-001", ctx.text)
        self.assertNotIn("2026-CLOSED-002", ctx.text)

    def test_person_data_is_carried_with_source(self):
        ctx = build_investigative_context(
            self.db,
            "Quem aparece no caso 2026-OPEN-001?",
        )
        self.assertEqual(ctx.sources, ["PLATEA:2026-OPEN-001"])
        self.assertIn("Pessoa Teste", ctx.text)
        self.assertIn("papel=investigado", ctx.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
