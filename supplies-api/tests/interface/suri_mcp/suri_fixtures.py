"""SURI MCP test helpers — fake transport context + gateway doubles."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from delpi_mcp.identity import McpRequestContext


def make_user_ns(
    *,
    permissions: list[str] | None = None,
    is_superadmin: bool = False,
    principal_type: str = "user",
    access_token: str = "token-abc",
    user_id: str = "user-1",
    email: str = "user@delpi.com.br",
    name: str = "Usuária Teste",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        email=email,
        name=name,
        roles=[],
        groups=["suprimentos"],
        permissions=list(permissions or []),
        is_superadmin=is_superadmin,
        access_token=access_token,
        principal_type=principal_type,
        rbac_unavailable=False,
    )


def make_context(user_ns: SimpleNamespace | None) -> McpRequestContext:
    return McpRequestContext(
        user=user_ns,
        authorization="Bearer token-abc" if user_ns is not None else "",
    )


class FakeGateway:
    """Captures calls and returns a canned api-delpi payload."""

    def __init__(self, payload: Any = None, error: Exception | None = None):
        self.payload = payload
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def get(self, path: str, *, access_token: str, params=None):
        self.calls.append(
            {"path": path, "access_token": access_token, "params": params}
        )
        if self.error is not None:
            raise self.error
        return self.payload


PO_PAYLOAD = {
    "success": True,
    "data": {
        "items": [
            {
                "branch": "01",
                "order_number": "000123",
                "order_item": "0010",
                "product_code": "MP001",
                "product_description": "Chapa de aço",
                "ordered_quantity": 10.0,
                "delivered_quantity": 4.0,
                "open_quantity": 6.0,
                "issue_date": "2026-10-01",
                "expected_delivery_date": "2026-10-20",
                "supplier_code": "F001",
                "supplier_store": "01",
                "supplier_name": "Fornecedor X",
                "unit_price": 100.0,
                "open_value": 600.0,
                "delivery_status": "late",
            },
            {
                "branch": "01",
                "order_number": "000124",
                "order_item": "0010",
                "product_code": "MP002",
                "product_description": "Tubo inox",
                "ordered_quantity": 5.0,
                "delivered_quantity": 0.0,
                "open_quantity": 5.0,
                "issue_date": "2026-10-05",
                "expected_delivery_date": "2026-11-30",
                "supplier_code": "F002",
                "supplier_store": "01",
                "supplier_name": "Fornecedor Y",
                "unit_price": 50.0,
                "open_value": 250.0,
                "delivery_status": "on_time",
            },
        ],
        "page": 1,
        "page_size": 25,
        "total": 2,
        "total_pages": 1,
        "summary": {
            "total_lines": 2,
            "total_open_value": 850.0,
            "late_lines": 1,
            "on_time_lines": 1,
            "no_date_lines": 0,
        },
    },
}
