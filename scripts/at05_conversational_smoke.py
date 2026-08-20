"""
Smoke tests AT-05.3 — utilidades da camada conversacional.
Não depende do LLM para manter o teste determinístico.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.assistant_action_planner import (
    may_contain_write_intent,
    _extract_json_object,
)


class AT05ConversationalLayerTests(unittest.TestCase):
    def test_detects_natural_annotation_request(self):
        self.assertTrue(
            may_contain_write_intent(
                "Coloca uma observação nesse caso dizendo que o vínculo precisa ser confirmado."
            )
        )

    def test_normal_analysis_question_is_not_write_hint(self):
        self.assertFalse(
            may_contain_write_intent(
                "Quem aparece relacionado a esse caso?"
            )
        )

    def test_extracts_plain_json(self):
        data = _extract_json_object(
            '{"action_type":"add_case_annotation","case_ref":"2026-X","content":"teste","explanation":null}'
        )
        self.assertEqual(data["action_type"], "add_case_annotation")

    def test_extracts_fenced_json(self):
        data = _extract_json_object(
            '```json\n{"action_type":"none","case_ref":null,"content":null,"explanation":null}\n```'
        )
        self.assertEqual(data["action_type"], "none")


if __name__ == "__main__":
    unittest.main(verbosity=2)
