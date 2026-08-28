"""Orquestração respeita continuityMode (sem discovery paralelo)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)


def test_continuity_consume_skips_parallel_discovery(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
        raising=False,
    )

    refinement_called = {"value": False}

    def _fake_grounded_plan(*_args, **_kwargs):
        return [
            {
                "name": "execute_external_action",
                "arguments": {"actionId": "financial-rol", "parameters": {"branch": "01"}},
                "reason": "reviseLastQuery",
                "actionId": "financial-rol",
            }
        ]

    def _fake_refinement(*_args, **_kwargs):
        refinement_called["value"] = True
        return []

    monkeypatch.setattr(
        "app.domain.services.chat_grounded_capability_planning_service."
        "ChatGroundedCapabilityPlanningService.plan_actions",
        _fake_grounded_plan,
    )
    monkeypatch.setattr(
        "app.domain.services.chat_operational_refinement_service."
        "ChatOperationalRefinementService.resolve_follow_ups",
        _fake_refinement,
        raising=False,
    )

    selection = MagicMock()
    selection.select_action.return_value = {
        "name": "execute_external_action",
        "arguments": {"actionId": "should-not-run"},
        "reason": "discovery",
    }

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection,
        message="somente da filial 01",
        allowed_action_ids=["financial-rol", "should-not-run"],
        workspace_context={
            "workingMemory": {
                "lastAction": {"path": "/financial/rol", "params": {}},
                "lastResultExcerpt": {"title": "ROL"},
            },
            "turnGrounding": {
                "status": "grounded",
                "stage": "grounded_revise_query",
                "followUp": {
                    "decision": "revise_last_query",
                    "continuityMode": "consume_last_action",
                    "allowsParallelDiscovery": False,
                },
            },
        },
    )

    assert len(planned) == 1
    assert planned[0]["actionId"] == "financial-rol"
    assert refinement_called["value"] is False
    selection.select_action.assert_not_called()


def test_continuity_challenge_returns_empty_without_bom(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
        raising=False,
    )

    monkeypatch.setattr(
        "app.domain.services.chat_grounded_capability_planning_service."
        "ChatGroundedCapabilityPlanningService.plan_actions",
        lambda *_a, **_k: [],
    )

    bom_called = {"value": False}

    def _fake_bom(*_args, **_kwargs):
        bom_called["value"] = True
        return [{"actionId": "product-structure"}]

    monkeypatch.setattr(
        "app.application.services.chat_structure_comparison_orchestration_service."
        "ChatStructureComparisonOrchestrationService.plan_structure_fetches",
        _fake_bom,
        raising=False,
    )

    selection = MagicMock()
    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection,
        message="o total não pode ser igual",
        allowed_action_ids=["product-structure"],
        workspace_context={
            "workingMemory": {
                "lastAction": {"path": "/financial/rol"},
                "lastResultExcerpt": {"title": "ROL", "preview": "R$ 1"},
            },
            "turnGrounding": {
                "status": "grounded",
                "stage": "grounded_challenge_result",
                "followUp": {
                    "decision": "challenge_last_result",
                    "continuityMode": "answer_without_tools",
                    "allowsParallelDiscovery": False,
                },
            },
        },
    )

    assert planned == []
    assert bom_called["value"] is False


def test_allow_discovery_keeps_current_behavior(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
        raising=False,
    )

    monkeypatch.setattr(
        "app.domain.services.chat_grounded_capability_planning_service."
        "ChatGroundedCapabilityPlanningService.plan_actions",
        lambda *_a, **_k: [],
    )

    selection = MagicMock()
    selection.select_action.return_value = {
        "name": "execute_external_action",
        "arguments": {"actionId": "financial-rol"},
        "reason": "discovery",
        "actionId": "financial-rol",
    }

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection,
        message="qual o rol desse mês?",
        allowed_action_ids=["financial-rol"],
        workspace_context={
            "workingMemory": {},
            "turnGrounding": {
                "status": "ungrounded",
                "followUp": {
                    "decision": "new_intent",
                    "continuityMode": "allow_discovery",
                    "allowsParallelDiscovery": True,
                },
            },
        },
    )

    assert planned
    assert planned[0].get("actionId") == "financial-rol"
