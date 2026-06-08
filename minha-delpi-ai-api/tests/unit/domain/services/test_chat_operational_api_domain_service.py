from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)


def test_classify_product_path():
    assert (
        ChatOperationalApiDomainService.classify_path(
            "/products/{code}/stock"
        )
        == "product"
    )


def test_classify_product_search_path():
    assert (
        ChatOperationalApiDomainService.classify_path("/products/search")
        == "product_search"
    )


def test_classify_department_kpi_path():
    assert (
        ChatOperationalApiDomainService.classify_path(
            "/commercial/sales-order-otd"
        )
        == "department_kpi"
    )


def test_classify_supplies_kpi_path():
    assert (
        ChatOperationalApiDomainService.classify_path("/supplies/cpv")
        == "supplies_kpi"
    )


def test_parameter_strategy_from_domain_config():
    assert (
        ChatOperationalApiDomainService.parameter_strategy_for_domain(
            "department_kpi"
        )
        == "date_branch"
    )
