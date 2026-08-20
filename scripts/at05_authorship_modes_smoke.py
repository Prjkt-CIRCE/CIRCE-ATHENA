"""
Smoke tests AT-05.5 — modos de autoria.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.assistant_action_planner import (
    extract_literal_annotation_content,
    requests_assisted_drafting,
)


class AT05AuthorshipModeTests(unittest.TestCase):
    def test_extracts_literal_content_without_expansion(self):
        text = (
            "Coloca uma observação nesse caso dizendo que "
            "esse vínculo ainda precisa ser confirmado."
        )
        self.assertEqual(
            extract_literal_annotation_content(text),
            "esse vínculo ainda precisa ser confirmado.",
        )

    def test_detects_assisted_drafting(self):
        self.assertTrue(
            requests_assisted_drafting(
                "Fundamenta melhor essa observação e registra no caso."
            )
        )

    def test_direct_registration_is_not_assisted_drafting(self):
        self.assertFalse(
            requests_assisted_drafting(
                "Registra que esse vínculo ainda precisa ser confirmado."
            )
        )

    def test_colon_form_is_literal(self):
        self.assertEqual(
            extract_literal_annotation_content(
                "Anote no caso 2026-X: conferir vínculo com o veículo."
            ),
            "conferir vínculo com o veículo.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
