"""Política de leitura no fallback semântico."""

from __future__ import annotations

from app.application.services.external_actions.external_action_generic_route_selection_service import (
    ExternalActionGenericRouteSelectionService,
)
from app.application.services.external_actions.external_action_selection_read_policy_service import (
    ExternalActionSelectionReadPolicyService,
)
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
    invalidate_department_kpi_rules_cache,
)


def test_token_and_matches_interleaved_new_business_rol():
    invalidate_department_kpi_rules_cache()
    match = ChatDepartmentKpiIntentService.resolve(
        "qual o percentual de rol de novos negócios da empresa?"
    )
    assert match is not None
    assert "new-business-rol-pct" in match.path_token


def test_read_policy_prefers_get_over_destructive():
    ranked = [
        {
            "actionId": "delete_quality_nc",
            "method": "DELETE",
            "sensitivity": "destructive",
            "selectionScore": 0.9,
            "selectionLexicalMatched": True,
            "parametersSchema": [],
        },
        {
            "actionId": "commercial-new-business-rol",
            "method": "GET",
            "sensitivity": "read",
            "selectionScore": 0.85,
            "selectionLexicalMatched": True,
            "parametersSchema": [],
        },
    ]

    action, reordered, reason = ExternalActionSelectionReadPolicyService.apply(ranked)
    assert action is not None
    assert action["actionId"] == "commercial-new-business-rol"
    assert reason == "readPolicyPreferSafe"
    assert reordered[0]["actionId"] == "commercial-new-business-rol"


def test_read_policy_clarifies_when_only_destructive():
    ranked = [
        {
            "actionId": "delete_quality_nc",
            "method": "DELETE",
            "sensitivity": "destructive",
            "selectionScore": 0.9,
            "selectionLexicalMatched": True,
            "parametersSchema": [],
        }
    ]

    action, _reordered, reason = ExternalActionSelectionReadPolicyService.apply(ranked)
    assert action is None
    assert reason == "readPolicyClarification"


def test_generic_fallback_does_not_execute_destructive():
    service = ExternalActionGenericRouteSelectionService()

    selected = service.select(
        "rol de novos negocios",
        ["delete_quality_nc", "commercial-new-business-rol"],
        candidates_loader=lambda *_a, **_k: [
            {
                "actionId": "delete_quality_nc",
                "method": "DELETE",
                "sensitivity": "destructive",
                "selectionScore": 0.91,
                "selectionLexicalMatched": True,
                "parametersSchema": [],
            },
            {
                "actionId": "commercial-new-business-rol",
                "method": "GET",
                "sensitivity": "read",
                "selectionScore": 0.88,
                "selectionLexicalMatched": True,
                "parametersSchema": [],
            },
        ],
        rank_candidates=lambda _message, candidates, **_k: list(candidates),
    )

    assert selected is not None
    assert selected["name"] == "execute_external_action"
    assert selected["arguments"]["actionId"] == "commercial-new-business-rol"
    assert "delete" not in str(selected["arguments"]["actionId"]).lower()
