from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_operational_sufficiency_critic_content_service import (
    ChatOperationalSufficiencyCriticContentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def test_sufficiency_critic_bundle_has_required_plans():
    ids = ChatOperationalSufficiencyCriticContentService.plan_ids()
    assert "stock_low_needs_sales" in ids
    assert "sales_empty_clarify_invoice" in ids
    assert "dossier_cut_by_cap" in ids
    assert "single_source_needs_cross" in ids


def test_sufficiency_critic_follow_up_route_ids_resolve_in_registry():
    for plan in ChatOperationalSufficiencyCriticContentService.plans():
        then = plan.get("then") if isinstance(plan.get("then"), dict) else {}
        for route_id in then.get("followUpRouteIds") or []:
            key = str(route_id or "").strip()
            if not key:
                continue
            assert OperationalRouteRegistryService.route_by_id(key), key


def test_sufficiency_critic_clarify_keys_resolve():
    keys = ChatOperationalSufficiencyCriticContentService.clarify_keys()
    assert "clarifyInvoiceDirection" in keys
    assert "deferredScopes" in keys
    invoice = ChatOperationalSufficiencyCriticContentService.clarify_node(
        "clarifyInvoiceDirection"
    )
    assert invoice.get("inbound", {}).get("label")
    assert invoice.get("outbound", {}).get("label")


def test_sufficiency_critic_reasons_format():
    assert ChatOperationalSufficiencyCriticContentService.reason("sufficient")
    assert ChatOperationalSufficiencyCriticContentService.reason("stockLowNeedsSales")
    assert not ChatOperationalSufficiencyCriticContentService.llm_assist_enabled()
