"""Smoke — rotas de aprovação de eficácia PAC (Onda 4.3)."""

from __future__ import annotations

from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

EFFECTIVENESS_APPROVAL_OPERATION_IDS = frozenset(
    {
        "submit_quality_action_plan_effectiveness_review",
        "approve_quality_action_plan_effectiveness_review",
        "reject_quality_action_plan_effectiveness_review",
        "list_quality_action_plan_pending_effectiveness_reviews",
    }
)


def test_effectiveness_approval_operation_ids_registered() -> None:
    missing = sorted(EFFECTIVENESS_APPROVAL_OPERATION_IDS - ROUTE_CONTRACTS.keys())
    assert not missing, f"operation_id ausente em ROUTE_CONTRACTS: {missing}"


def test_pending_effectiveness_reviews_contract_shape() -> None:
    contract = ROUTE_CONTRACTS["list_quality_action_plan_pending_effectiveness_reviews"]
    assert contract.entity == "quality_action_plan"
    assert contract.shape == "paged_list"
