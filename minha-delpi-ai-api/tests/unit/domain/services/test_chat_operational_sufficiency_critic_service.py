from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_operational_sufficiency_critic_service import (
    ChatOperationalSufficiencyCriticService,
)


def _stock_low_call(**overrides):
    meta = {
        "ok": True,
        "path": "/products/10080047/stock",
        "emptyResult": False,
        "anomalies": [{"type": "zero_value"}],
        "dataAnswer": {"profileKey": "stock"},
        **overrides,
    }
    return {
        "name": "execute_external_action",
        "arguments": {"actionId": "stock-action", "path": meta["path"]},
        "metadata": meta,
    }


def _sales_empty_call():
    return {
        "name": "execute_external_action",
        "arguments": {"actionId": "sales-action", "path": "/products/10080047/sales"},
        "metadata": {
            "ok": True,
            "path": "/products/10080047/sales",
            "emptyResult": True,
            "dataAnswer": {"profileKey": "generic_list"},
            "anomalies": [{"type": "empty_list"}],
        },
    }


def test_evaluate_sufficient_when_no_match():
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/x/stock",
                    "dataAnswer": {"profileKey": "stock"},
                },
            }
        ],
        remaining_slots=2,
    )
    assert verdict.action == "sufficient"


def test_evaluate_stock_low_chips_with_slot():
    """Anomalia de estoque sugere vendas via chips — sem auto follow-up HTTP."""
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[_stock_low_call()],
        remaining_slots=2,
    )
    assert verdict.action == "chips"
    assert verdict.deferred_to_chips is True
    assert verdict.plan_id == "stock_low_needs_sales"
    assert "productSales" in verdict.follow_up_route_ids


def test_evaluate_stock_low_chips_when_no_slot():
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[_stock_low_call()],
        remaining_slots=0,
    )
    assert verdict.action == "chips"
    assert verdict.deferred_to_chips is True
    assert "productSales" in verdict.follow_up_route_ids


def test_evaluate_sales_empty_clarify_chips():
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[_sales_empty_call()],
        remaining_slots=2,
    )
    assert verdict.action == "chips"
    assert verdict.plan_id == "sales_empty_clarify_invoice"
    assert verdict.clarify_key == "clarifyInvoiceDirection"


def test_evaluate_dossier_cut_by_cap():
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/x/summary",
                    "dataAnswer": {"profileKey": "generic"},
                },
            }
        ],
        enrichment_plan={
            "kind": "product_enrichment_composition",
            "skippedByCap": 2,
            "plannedScopes": ["summary", "stock", "sales"],
            "executedCount": 1,
        },
        remaining_slots=0,
    )
    assert verdict.action == "chips"
    assert verdict.plan_id == "dossier_cut_by_cap"


def test_evaluate_single_source_needs_cross():
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[
            {
                "name": "execute_external_action",
                "arguments": {"actionId": "a1", "path": "/products/x/stock"},
                "metadata": {"ok": True, "path": "/products/x/stock"},
            }
        ],
        enrichment_plan={
            "kind": "product_enrichment_composition",
            "plannedScopes": ["summary", "stock", "sales"],
            "executedCount": 1,
            "skippedByCap": 0,
        },
        remaining_slots=2,
    )
    assert verdict.action == "execute"
    assert verdict.plan_id == "single_source_needs_cross"
    assert "productSales" in verdict.follow_up_route_ids
    assert "productStock" not in verdict.follow_up_route_ids


def test_no_auto_execute_when_stock_low_deferred_to_chips():
    class FakeSelection:
        def select_registry_route_id(self, route_id, message, **kwargs):
            return {
                "arguments": {
                    "actionId": f"id-{route_id}",
                    "path": f"/products/10080047/{route_id}",
                },
                "reason": "x",
            }

    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[_stock_low_call()],
        remaining_slots=2,
    )
    assert verdict.action == "chips"
    follow = ChatOperationalSufficiencyCriticService.plan_follow_up_selections(
        FakeSelection(),
        verdict=verdict,
        message="estoque 10080047",
        tool_calls=[_stock_low_call()],
        allowed_action_ids=["id-productSales"],
    )
    assert follow == []


def test_audit_payload_shape():
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[_stock_low_call()],
        remaining_slots=1,
    )
    payload = ChatOperationalSufficiencyCriticService.audit_payload(verdict)
    assert payload["verdict"] == "chips"
    assert payload["planId"] == "stock_low_needs_sales"
    assert "reasonKey" in payload
