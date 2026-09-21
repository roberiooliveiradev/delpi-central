from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.domain.services.customer_center_assignment_validation import (
    validate_customer_center_assignment,
)
import pytest


def test_unknown_center_is_rejected():
    with pytest.raises(ValueError):
        validate_customer_center_assignment("9999", ["1100", "1200"])


def test_known_center_is_accepted_and_sibling_is_distinct():
    assert validate_customer_center_assignment("1100", ["1100", "1200"]) == "1100"
    assert validate_customer_center_assignment("1200", ["1100", "1200"]) == "1200"


def test_store_without_centers_keeps_pair_fallback():
    assert validate_customer_center_assignment(None, []) is None


def test_open_order_scope_keeps_null_center_pair_and_hides_other_center():
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("000001", "01")}),
        center_rules=frozenset({("000001", "01", "1100")}),
    )
    service = FilterOpenOrdersByScopeService()
    data = service.apply(
        {
            "items": [
                {"codigo_cadastro": "000001", "loja_cadastro": "01", "customer_center": "1100", "valor_aberto": 1, "saldo": 1, "no_estoque": 1},
                {"codigo_cadastro": "000001", "loja_cadastro": "01", "customer_center": "1200", "valor_aberto": 1, "saldo": 1, "no_estoque": 1},
            ]
        },
        scope,
    )
    centers = [item["customer_center"] for item in data["items"]]
    assert centers == ["1100"]


def test_null_assignment_keeps_the_whole_pair():
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("000001", "01")}),
        center_rules=frozenset({("000001", "01", "")}),
    )
    assert scope.allows_open_order_line("000001", "01", "1200") is True
    assert scope.allows_open_order_line("000001", "01", "") is True


def test_migration_does_not_update_rows():
    text = open(
        "migrations/V023__seller_customer_center.sql",
        encoding="utf-8",
    ).read().upper()
    assert not any(line.strip().startswith("UPDATE") for line in text.splitlines())
    assert "CUSTOMER_CENTER" in text


def test_contacts_route_does_not_declare_customer_centers():
    text = open(
        "commercial_app/interface/http/routes/customer_routes.py",
        encoding="utf-8",
    ).read()
    start = text.index("def get_customer_contacts_bundle")
    end = text.index("\ndef ", start + 1)
    assert "customer_centers" not in text[start:end]
