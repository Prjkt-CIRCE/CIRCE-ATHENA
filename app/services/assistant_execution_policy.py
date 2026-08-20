"""
AT-05.4 — Política de modos de execução do Assistente.

Permissão e modo são conceitos distintos:
- permissão: o que o operador pode fazer;
- modo: quanta confirmação o Assistente exige.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ExecutionMode = Literal["safe", "agent"]
RiskLevel = Literal["low", "medium", "high", "critical"]

VALID_EXECUTION_MODES = {"safe", "agent"}

ACTION_RISK: dict[str, RiskLevel] = {
    "add_case_annotation": "low",
}


@dataclass(frozen=True)
class ExecutionDecision:
    action_type: str
    mode: ExecutionMode
    risk: RiskLevel
    requires_confirmation: bool


def normalize_execution_mode(value: str | None) -> ExecutionMode:
    return "agent" if (value or "").lower() == "agent" else "safe"


def risk_for_action(action_type: str) -> RiskLevel:
    # Ação desconhecida não deve receber tratamento permissivo.
    return ACTION_RISK.get(action_type, "critical")


def decide_execution(
    *,
    action_type: str,
    mode: str | None,
) -> ExecutionDecision:
    normalized_mode = normalize_execution_mode(mode)
    risk = risk_for_action(action_type)

    if normalized_mode == "agent":
        requires_confirmation = False
    else:
        # SAFE: baixo/médio risco seguem sem bloqueio;
        # alto/crítico exigem confirmação.
        requires_confirmation = risk in {"high", "critical"}

    return ExecutionDecision(
        action_type=action_type,
        mode=normalized_mode,
        risk=risk,
        requires_confirmation=requires_confirmation,
    )
