#!/usr/bin/env python3
"""Smoke — planejamento e avaliação de fontes (Fases 2–3 playbook pesquisa web)."""

from __future__ import annotations

import sys

from app.domain.services.chat_web_search_planning_service import (
    ChatWebSearchPlanningService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.domain.services.chat_web_search_source_evaluation_service import (
    ChatWebSearchSourceEvaluationService,
)


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

    enriched = ChatWebSearchSourceEvaluationService.enrich_payload(
        {
            "searchStatus": "success",
            "preferOfficial": True,
            "results": [
                {
                    "title": "WEG manual",
                    "url": "https://www.weg.net/manual/cfw500",
                    "snippet": "doc",
                    "source": "tavily",
                },
            ],
        }
    )

    if not enriched or enriched.get("sourceEvaluation", {}).get("confidence") != "high":
        print(f"FAIL unit: enrich_payload sem confiança alta ({enriched})", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: avaliação de fontes (confidence high)")

    from app.domain.services.chat_web_search_integration_service import (
        ChatWebSearchIntegrationService,
    )

    integration = ChatWebSearchIntegrationService.resolve(
        "consulte nosso produto 10080001 e pesquise na web datasheet"
    )

    if not integration or integration.mode != "internal_product":
        print(f"FAIL unit: integração produto+web ({integration})", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: integração produto interno + web")

    from app.application.services.chat_web_search_follow_up_service import (
        ChatWebSearchFollowUpService,
    )

    metadata: dict = {}
    ChatWebSearchFollowUpService.attach_to_assistant_metadata(
        metadata,
        tool_context={
            "webSearchPayload": {
                "searchStatus": "success",
                "query": "DELPI Conexões Elétricas",
            },
        },
        message="pesquise na web sobre DELPI Conexões Elétricas",
    )

    if not metadata.get("webSearchFollowUpSuggestions"):
        print(f"FAIL unit: chips pós-pesquisa ({metadata})", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: webSearchFollowUpSuggestions")

    from app.application.services.chat_web_search_save_sources_service import (
        ChatWebSearchSaveSourcesService,
    )

    if not ChatWebSearchSaveSourcesService.is_save_request(
        "salve as fontes da pesquisa web no projeto"
    ):
        print("FAIL unit: detecção salvar fontes", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: detecção salvar fontes")

    labels = [item["label"] for item in metadata.get("webSearchFollowUpSuggestions") or []]

    if "Salvar fontes" not in labels:
        print(f"FAIL unit: chip Salvar fontes ausente ({labels})", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: chip Salvar fontes")

    if failed:
        return 1

    print("Smoke web search planning: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
