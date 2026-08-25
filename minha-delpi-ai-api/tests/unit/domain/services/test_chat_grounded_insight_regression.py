"""Regressão dos três cenários grounded dos screenshots (E14)."""

from __future__ import annotations

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_grounded_capability_planning_service import (
    ChatGroundedCapabilityPlanningService,
)
from app.domain.services.chat_grounded_enrich_planning_service import (
    ChatGroundedEnrichPlanningService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)
from app.domain.services.chat_operational_llm_synthesis_context_service import (
    ChatOperationalLlmSynthesisContextService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService
from tests.fixtures.chat_intelligence_regression_cases import (
    GROUNDED_INSIGHT_REGRESSION_CASES,
)

configure_domain_infrastructure_ports()


class _SelectionStub:
    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids,
        intent,
        route_segment=None,
        previous_messages=None,
    ):
        return {
            "actionId": f"action-{intent}-{product_code}",
            "intent": intent,
            "productCode": product_code,
        }


@pytest.mark.parametrize(
    "case",
    GROUNDED_INSIGHT_REGRESSION_CASES,
    ids=[str(item["id"]) for item in GROUNDED_INSIGHT_REGRESSION_CASES],
)
def test_grounded_insight_regression(case: dict):
    case_id = str(case["id"])
    expects = case["expects"]
    message = str(case["message"])

    if case_id == "FF-GROUND-STRUCT-01":
        commentary = ChatOperationalDataCommentaryService.build(
            expects["profile_key"],
            case["structure_payload"],
        )

        assert commentary
        combined = "\n".join(
            str(line)
            for line in (
                *(commentary.get("highlights") or []),
                *(commentary.get("summaryLines") or []),
            )
        ).lower()

        for token in expects["must_not_contain"]:
            assert token.lower() not in combined

        for token in expects["must_contain"]:
            assert token in combined

        return

    if case_id == "FF-GROUND-INSIGHT-01":
        excerpt = case["excerpt"]
        stage = ChatTurnGroundingService.resolve_grounded_stage(
            message=message,
            excerpt=excerpt,
        )

        assert stage == expects["stage"]

        plan = ChatGroundedEnrichPlanningService.build_plan(
            message=message,
            workspace_context={},
            excerpt=excerpt,
            response_mode="normal",
        )

        assert plan is not None

        for scope in expects["planned_scopes"]:
            assert scope in plan.planned_scopes

        tool_calls = [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/90260149/structure",
                    "dataCommentary": {
                        "highlights": ["Árvore com 6 componentes"],
                    },
                },
            }
        ]
        facts = ChatOperationalLlmSynthesisContextService.build_facts_addon(
            tool_calls,
            message=message,
        ).lower()

        for token in expects["must_not_contain_in_facts"]:
            assert token.lower() not in facts

        return

    if case_id == "FF-GROUND-MP-STOCK-01":
        selection = _SelectionStub()
        planned = ChatGroundedCapabilityPlanningService.plan_actions(
            selection,
            message=message,
            allowed_action_ids=["get_product_stock"],
            workspace_context=case["workspace"],
        )

        codes = [item["productCode"] for item in planned]

        assert codes == expects["product_codes"]

        for blocked in expects["must_not_include"]:
            assert blocked not in codes

        assert all(item["intent"] == expects["intent"] for item in planned)

        return

    if case_id == "FF-BUDGET-ENRICH-01":
        from unittest.mock import patch

        from app.domain.services.chat_response_mode_context_budget_service import (
            ChatResponseModeContextBudgetService,
        )

        tool_context = dict(case["tool_context"])

        with patch.object(
            ChatResponseModeContextBudgetService,
            "current_profile",
            return_value="cloud",
        ):
            facts = ChatOperationalLlmSynthesisContextService.build_facts_addon(
                case["tool_calls"],
                response_mode=case["response_mode"],
                tool_context=tool_context,
                message=message,
            )

        assert len(facts.strip()) >= expects["min_facts_chars"]
        assert tool_context.get("synthesisFactsTruncated") is expects[
            "synthesis_facts_truncated"
        ]
        assert int(tool_context.get("synthesisFactsBudgetChars") or 0) >= expects[
            "min_budget_chars"
        ]

        return

    if case_id.startswith("FF-COMPOSE-"):
        from app.domain.services.chat_presentation_llm_composition_service import (
            ChatPresentationLlmCompositionService,
        )

        metadata = dict(case.get("metadata") or {})
        tool_calls = case.get("tool_calls")
        if tool_calls and not metadata:
            metadata = dict(tool_calls[0]["metadata"])
            tool_calls = [
                {**item, "metadata": dict(item["metadata"])} for item in tool_calls
            ]
            tool_calls[0]["metadata"] = metadata

        cleaned = ChatPresentationLlmCompositionService.apply(
            metadata,
            str(case["llm_answer"]),
            response_mode=str(case.get("response_mode") or "normal"),
            explicit_format=case.get("explicit_format"),
            tool_calls=tool_calls,
        )

        if expects.get("markers_remain") is False:
            assert "[[" not in cleaned

        if "cleaned_equals" in expects:
            assert cleaned == expects["cleaned_equals"]

        if "prose_composition_source" in expects:
            assert metadata.get("proseCompositionSource") == expects[
                "prose_composition_source"
            ]

        if "prose_composition_source_not" in expects:
            assert metadata.get("proseCompositionSource") != expects[
                "prose_composition_source_not"
            ]

        decision = metadata.get("presentationDecision") or {}
        if "prose_composition_allowed" in expects:
            assert decision.get("proseCompositionAllowed") is expects[
                "prose_composition_allowed"
            ]
        if "prose_composition_policy" in expects:
            assert decision.get("proseCompositionPolicy") == expects[
                "prose_composition_policy"
            ]

        plan = metadata.get("renderPlan") or {}
        kinds = [seg.get("kind") for seg in (plan.get("segments") or [])]

        if "layout_mode" in expects:
            assert plan.get("layoutMode") == expects["layout_mode"]
        if "segment_kinds" in expects:
            assert kinds == expects["segment_kinds"]
        if "min_segments" in expects:
            assert len(plan.get("segments") or []) >= expects["min_segments"]
        if "table_count" in expects:
            assert kinds.count("table") == expects["table_count"]
        if "must_include_kinds" in expects:
            for kind in expects["must_include_kinds"]:
                assert kind in kinds
        if expects.get("no_tree_in_plan"):
            assert "tree" not in kinds

        return

    raise AssertionError(f"Unhandled grounded insight case: {case_id}")
