"""
Smoke tests AT-05.4 — modos de execução.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.assistant_execution_policy import (
    decide_execution,
    normalize_execution_mode,
    risk_for_action,
)


class AT05ExecutionModeTests(unittest.TestCase):
    def test_default_mode_is_safe(self):
        self.assertEqual(normalize_execution_mode(None), "safe")

    def test_annotation_is_low_risk(self):
        self.assertEqual(risk_for_action("add_case_annotation"), "low")

    def test_safe_low_risk_does_not_require_confirmation(self):
        decision = decide_execution(
            action_type="add_case_annotation",
            mode="safe",
        )
        self.assertFalse(decision.requires_confirmation)

    def test_safe_unknown_action_is_critical_and_confirmed(self):
        decision = decide_execution(
            action_type="unknown_action",
            mode="safe",
        )
        self.assertEqual(decision.risk, "critical")
        self.assertTrue(decision.requires_confirmation)

    def test_agent_does_not_require_confirmation_for_supported_flow(self):
        decision = decide_execution(
            action_type="add_case_annotation",
            mode="agent",
        )
        self.assertFalse(decision.requires_confirmation)


if __name__ == "__main__":
    unittest.main(verbosity=2)
