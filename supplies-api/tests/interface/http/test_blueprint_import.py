"""List/detail blueprints must boot even when export XLSX is unused."""

from __future__ import annotations


def test_purchase_request_routes_import_without_eager_openpyxl() -> None:
    from app.interfaces.http.routes.purchase_requests_routes import (
        list_portal_purchase_requests,
    )

    assert callable(list_portal_purchase_requests)


def test_purchase_order_routes_import_without_eager_openpyxl() -> None:
    from app.interfaces.http.routes.purchase_orders_routes import (
        list_portal_purchase_orders,
    )

    assert callable(list_portal_purchase_orders)
