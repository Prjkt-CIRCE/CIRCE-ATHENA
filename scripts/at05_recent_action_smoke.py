"""
Smoke tests AT-05.6 — referências a ações recentes.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.assistant_action_planner import (
    refers_to_recent_annotation,
    requests_assisted_drafting,
    _normalize_recent_action,
)


class AT05RecentActionContextTests(unittest.TestCase):
    def test_recognizes_essa_observacao(self):
        self.assertTrue(
            refers_to_recent_annotation(
                "Fundamenta melhor essa observação e registra no caso."
            )
        )

    def test_recognizes_o_que_acabou_de_registrar(self):
        self.assertTrue(
            refers_to_recent_annotation(
                "Melhora o que você acabou de registrar."
            )
        )

    def test_assisted_drafting_and_reference_can_coexist(self):
        message = "Fundamenta melhor essa observação e registra no caso."
        self.assertTrue(requests_assisted_drafting(message))
        self.assertTrue(refers_to_recent_annotation(message))

    def test_normalizes_valid_recent_annotation(self):
        action = _normalize_recent_action({
            "type": "case_annotation",
            "case_ref": "2026-X",
            "annotation_id": 7,
            "content": "vínculo pendente de confirmação.",
        })
        self.assertEqual(action["case_ref"], "2026-X")
        self.assertEqual(action["annotation_id"], 7)

    def test_rejects_recent_action_without_content(self):
        action = _normalize_recent_action({
            "type": "case_annotation",
            "case_ref": "2026-X",
            "annotation_id": 7,
        })
        self.assertIsNone(action)


if __name__ == "__main__":
    unittest.main(verbosity=2)
