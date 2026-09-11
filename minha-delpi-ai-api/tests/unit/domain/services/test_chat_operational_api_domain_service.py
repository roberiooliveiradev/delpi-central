from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)


def test_classify_action_product_entity():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"delpi_metadata": {"entity": "product_stock", "category": "products"}}
        )
        == "product"
    )


def test_classify_action_product_search_entity():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"delpiMetadata": {"entity": "product_search", "category": "products"}}
        )
        == "product_search"
    )


def test_classify_action_department_kpi_category():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"delpiMetadata": {"category": "commercial"}}
        )
        == "department_kpi"
    )


def test_classify_action_supplies_kpi_category():
    assert (
        ChatOperationalApiDomainService.classify_action(
            {"delpiMetadata": {"category": "supplies"}}
        )
        == "supplies_kpi"
    )


def test_classify_path_has_no_authority():
    assert ChatOperationalApiDomainService.classify_path("/products/{code}/stock") == (
        "generic"
    )


def test_parameter_strategy_from_domain_config():
    # Domains no longer declare parameterStrategy (E9.S12.E); default is semantic.
    assert (
        ChatOperationalApiDomainService.parameter_strategy_for_domain(
            "department_kpi"
        )
        == "semantic"
    )


def test_parameter_strategy_ids_include_declarative_strategies():
    strategy_ids = ChatOperationalApiDomainService.parameter_strategy_ids()

    assert "date_branch" in strategy_ids
    assert "sale_orders" in strategy_ids
    assert "supplies_stock" in strategy_ids


def test_parameter_strategy_spec_date_branch_has_bindings():
    spec = ChatOperationalApiDomainService.parameter_strategy_spec("date_branch")

    assert isinstance(spec.get("bindings"), list)
    assert spec.get("granularityDefault") == "month"
    assert isinstance(spec.get("patterns"), dict)
