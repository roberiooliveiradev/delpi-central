#!/usr/bin/env python3
"""Smoke — planejamento de pesquisa web (Fase 2 playbook)."""

from __future__ import annotations

import sys

from app.domain.services.chat_web_search_planning_service import (
    ChatWebSearchPlanningService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


def main() -> int:
    failed = 0

    plan = ChatWebSearchPlanningService.plan(
        "pesquise na internet sobre python"
    )

    if not plan or plan.mode != "quick":
        print(f"FAIL unit: plano rápido inválido ({plan})", file=sys.stderr)
        failed += 1
    else:
        print(f"OK unit: modo rápido ({len(plan.queries)} queries)")

    plan_deep = ChatWebSearchPlanningService.plan(
        "pesquisa profunda na web sobre manual oficial weg cfw500"
    )

    if not plan_deep or plan_deep.mode != "deep" or not plan_deep.prefer_official:
        print(f"FAIL unit: plano profundo/oficial ({plan_deep})", file=sys.stderr)
        failed += 1
    else:
        print(f"OK unit: modo profundo ({len(plan_deep.queries)} queries, oficial)")

    from unittest.mock import patch

    with patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True):
        resolved = ChatWebSearchIntentService.resolve(
            "busque na web sobre datasheet motor weg"
        )

    if not resolved or "plannedQueries" not in (resolved.get("arguments") or {}):
        print(f"FAIL unit: resolve sem plannedQueries ({resolved})", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: resolve inclui plannedQueries e searchMode")

    if failed:
        return 1

    print("Smoke web search planning: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
