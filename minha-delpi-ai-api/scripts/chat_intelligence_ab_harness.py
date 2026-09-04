#!/usr/bin/env python3
"""Harness A/B — inteligência conversacional (E8.S1).

Compara decisões pré-LLM (baseline routing) com shadow understanding/plan/discovery.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
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
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_product_search_intent_service import (
    ChatProductSearchIntentService,
)
from app.domain.services.chat_task_planner_service import ChatTaskPlannerService
from app.domain.services.chat_turn_understanding_service import (
    ChatTurnUnderstandingService,
)

_FIXTURE = ROOT / "tests" / "fixtures" / "intelligence_baseline" / "routing_cases.json"
_OUT = ROOT / "docs" / "testing" / "evidence" / "chat-intelligence-ab-report.json"


def main() -> int:
    cases = json.loads(_FIXTURE.read_text(encoding="utf-8")).get("cases") or []
    rows = []
    for case in cases:
        message = str(case.get("message") or "")
        route = ChatIntentRouterService.classify(message)
        understanding = ChatTurnUnderstandingService.analyze(message)
        plan = ChatTaskPlannerService.plan_shadow(message)
        discovery = ChatCapabilityDiscoveryService.discover(message)
        clarify = ChatClarificationPolicyService.decide([], message=message)
        rows.append(
            {
                "caseId": case.get("id"),
                "message": message,
                "pipeline": {
                    "decision": getattr(route, "decision", None),
                    "subIntent": getattr(route, "sub_intent", None),
                    "looksLikeProductSearch": ChatProductSearchIntentService.looks_like_product_search(
                        message
                    ),
                },
                "shadow": {
                    "subtaskCount": understanding.subtask_count,
                    "taskCount": plan.task_count if plan else 0,
                    "topCapabilities": [
                        item.get("capabilityId") for item in discovery.candidates[:3]
                    ],
                    "clarification": clarify.to_admin_debug(),
                },
            }
        )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "E8.S1",
        "caseCount": len(rows),
        "rows": rows,
    }
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {_OUT} cases={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
