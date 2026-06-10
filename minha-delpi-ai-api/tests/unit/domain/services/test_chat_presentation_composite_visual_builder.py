"""Quartet visual declarativo — Playbook 12 R6."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_composite_visual_builder import (
    ChatPresentationCompositeVisualBuilder,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

configure_domain_infrastructure_ports()


def test_production_status_composite_spec_builds_kpi_chart_tree():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")
    root = envelope["data"]
    path = "/products/90269002/production-status"
    spec = ChatPresentationCompositeVisualBuilder.spec("production_status")

    kpi = ChatPresentationCompositeVisualBuilder.build_kpi(presenter, root, path, spec)
    chart = ChatPresentationCompositeVisualBuilder.build_chart(presenter, root, path, spec)
    tree = ChatPresentationCompositeVisualBuilder.build_tree(presenter, root, path, spec)

    assert kpi and kpi.get("type") == "kpi"
    assert chart and chart.get("type") == "chart"
    assert tree and tree.get("type") == "tree"


def test_structure_exclusivity_composite_spec_filters_exclusive_chart():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90269002.json")
    root = envelope["data"]
    path = "/products/90269002/structure/exclusivity"
    spec = ChatPresentationCompositeVisualBuilder.spec("structure_exclusivity")

    chart = ChatPresentationCompositeVisualBuilder.build_chart(presenter, root, path, spec)
    tree = ChatPresentationCompositeVisualBuilder.build_tree(presenter, root, path, spec)

    assert chart is None or chart.get("type") == "chart"
    assert tree and tree.get("type") == "tree"


def test_last_purchase_composite_spec_builds_kpi_chart_tree():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    root = envelope["data"]
    path = "/products/10080001/last-purchase"
    spec = ChatPresentationCompositeVisualBuilder.spec("last_purchase")

    kpi = ChatPresentationCompositeVisualBuilder.build_kpi(presenter, root, path, spec)
    chart = ChatPresentationCompositeVisualBuilder.build_chart(presenter, root, path, spec)
    tree = ChatPresentationCompositeVisualBuilder.build_tree(presenter, root, path, spec)

    assert kpi and kpi.get("type") == "kpi"
    assert chart and chart.get("type") == "chart"
    assert tree and tree.get("type") == "tree"


def test_factory_status_composite_spec_builds_section_kpi_and_tree():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    root = envelope["data"]
    path = "/products/90269002/factory-status"
    spec = ChatPresentationCompositeVisualBuilder.spec("factory_status")

    kpi = ChatPresentationCompositeVisualBuilder.build_kpi(presenter, root, path, spec)
    tree = ChatPresentationCompositeVisualBuilder.build_tree(presenter, root, path, spec)
    chart = ChatPresentationCompositeVisualBuilder.build_chart(presenter, root, path, spec)

    assert kpi and kpi.get("type") == "kpi"
    assert tree and tree.get("type") == "tree"
    assert chart and chart.get("type") == "chart"


def test_purchase_list_composite_spec_builds_kpi_from_items():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    root = envelope["data"]
    path = "/products/10080001/purchases"
    spec = ChatPresentationCompositeVisualBuilder.spec("purchase_list")

    kpi = ChatPresentationCompositeVisualBuilder.build_kpi(presenter, root, path, spec)

    assert kpi and kpi.get("type") == "kpi"
    assert len(kpi.get("cards") or []) >= 2

