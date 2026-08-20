"""
Smoke tests AT-05.2 — escrita autorizada.
Atualizado na AT-05.5 para refletir modos de autoria.
"""

from datetime import datetime
from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base
from app.models.platea import SharedCase, SharedCaseAnnotation
from app.services.assistant_action_service import (
    parse_annotation_command,
    build_pending_annotation,
    create_case_annotation,
)


class AT05WriteSmokeTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()

        case = SharedCase(
            case_ref="2026-WRITE-001",
            title="Caso de Escrita",
            status="aberto",
            classification="teste",
            notes="NOTA ORIGINAL SINCRONIZADA",
            source_unit="Nucleo Teste",
            published_by="tester",
            published_at=datetime.utcnow(),
            published_version=1,
        )
        self.db.add(case)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_parser_accepts_explicit_annotation_command(self):
        cmd = parse_annotation_command(
            "Anote no caso 2026-WRITE-001: informação validada pelo usuário."
        )
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.case_ref, "2026-WRITE-001")
        self.assertEqual(
            cmd.content,
            "informação validada pelo usuário.",
        )

    def test_normal_question_is_not_a_write_command(self):
        cmd = parse_annotation_command(
            "Quem aparece no caso 2026-WRITE-001?"
        )
        self.assertIsNone(cmd)

    def test_prepare_unknown_case_does_not_create_action(self):
        cmd = parse_annotation_command(
            "Anote no caso 2099-NAO-EXISTE: teste."
        )
        action, error = build_pending_annotation(self.db, cmd)
        self.assertIsNone(action)
        self.assertIn("não foi encontrado", error)

    def test_annotation_does_not_modify_synchronized_notes(self):
        cmd = parse_annotation_command(
            "Anote no caso 2026-WRITE-001: nova anotação humana."
        )
        action, error = build_pending_annotation(
            self.db,
            cmd,
            authorship_mode="literal",
        )
        self.assertIsNone(error)

        annotation = create_case_annotation(
            self.db,
            case_ref=action["case_ref"],
            content=action["content"],
            operator_id=1,
            operator_username="tester",
            authorship_mode=action["authorship_mode"],
        )
        self.db.commit()

        case = self.db.query(SharedCase).filter_by(
            case_ref="2026-WRITE-001"
        ).first()
        annotations = self.db.query(SharedCaseAnnotation).all()

        self.assertEqual(case.notes, "NOTA ORIGINAL SINCRONIZADA")
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].content, "nova anotação humana.")
        self.assertEqual(annotations[0].source, "assistant_user_literal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
