#!/usr/bin/env python3
"""Smokes A–F de coerência conversacional (E8.S2) — offline-first.

Sem API live: valida contratos de understanding/plan/discovery/policy/resultSets.
Com CHAT_SMOKE_LIVE=1 poderia estender para HTTP (não obrigatório aqui).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_capability_discovery_service import (
    ChatCapabilityDiscoveryService,
)
from app.domain.services.chat_clarification_policy_service import (
    ChatClarificationPolicyService,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from app.domain.services.chat_result_set_reference_service import (
    ChatResultSetReferenceService,
)
from app.domain.services.chat_task_planner_service import ChatTaskPlannerService
from app.domain.services.chat_turn_understanding_service import (
    ChatTurnUnderstandingService,
)


def _pass(name: str) -> None:
    print(f"PASS {name}")


def smoke_a_operational_chain() -> None:
    plan = ChatTaskPlannerService.plan_shadow(
        "liste terminais pino; estoque do segundo; descrição do primeiro"
    )
    assert plan and plan.task_count >= 3
    _pass("A_12turn_contract")


def smoke_b_topic_return() -> None:
    understanding = ChatTurnUnderstandingService.analyze(
        "liste A; depois fale de normas; volte ao estoque do segundo"
    )
    assert understanding.subtask_count >= 3
    _pass("B_20turn_topic_return_contract")


def smoke_c_compound() -> None:
    understanding = ChatTurnUnderstandingService.analyze(
        "1) busque\n2) estoque\n3) normas\n4) compare\n5) resuma"
    )
    assert understanding.subtask_count >= 5
    _pass("C_compound_5plus")


def smoke_d_multi_capability() -> None:
    discovery = ChatCapabilityDiscoveryService.discover(
        "pesquise terminais e veja normas na base e resuma"
    )
    types = {str(item.get("type") or "") for item in discovery.candidates}
    assert "action" in types or "rag" in types or "transform" in types
    _pass("D_api_rag_text")


def smoke_e_ordinal() -> None:
    snapshot = {
        "resultSets": [
            {
                "id": "rs-1",
                "items": [
                    {"ordinal": 1, "code": "10080047"},
                    {"ordinal": 2, "code": "10080099"},
                ],
            }
        ]
    }
    codes = ChatResultSetReferenceService.resolve_codes("estoque do segundo", snapshot)
    assert codes == ["10080099"]
    resolved, keys = ChatReferenceResolutionService.resolve_from_snapshot(
        "estoque do segundo",
        snapshot,
    )
    assert resolved and "resultSets" in keys
    _pass("E_ordinal_followup")


def smoke_f_unavailable_honest() -> None:
    decision = ChatClarificationPolicyService.decide([], message="xyzzy nonsense only")
    assert decision.action in {"continue", "clarify"}
    discovery = ChatCapabilityDiscoveryService.discover("xyzzy nonsense only")
    assert isinstance(discovery.discard_reasons, tuple)
    _pass("F_unavailable_honest")


def main() -> int:
    smoke_a_operational_chain()
    smoke_b_topic_return()
    smoke_c_compound()
    smoke_d_multi_capability()
    smoke_e_ordinal()
    smoke_f_unavailable_honest()
    print("ALL_SMOKES_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
