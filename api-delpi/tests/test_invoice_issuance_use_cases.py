"""Use cases — invoice-issuance (fakes, sem TOTVS/Postgres reais)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.application.use_cases.invoice_issuance.invoice_issuance_use_cases import (
    Actor,
    CancelInvoiceIssuanceRequestUseCase,
    CreateInvoiceIssuanceRequestUseCase,
    GetInvoiceIssuanceRequestUseCase,
    GetWarehouse01BalanceUseCase,
    IssueInvoiceIssuanceRequestUseCase,
    ListInvoiceIssuanceRequestsUseCase,
    ResubmitInvoiceIssuanceRequestUseCase,
    ReturnInvoiceIssuanceRequestUseCase,
    SearchIssuanceCarriersUseCase,
    SearchIssuanceProductsUseCase,
    SearchPartiesUseCase,
    StartInvoiceIssuanceRequestUseCase,
    UpdateReturnedInvoiceIssuanceRequestUseCase,
    allowed_actions,
)
from app.domain.services.invoice_issuance.exceptions import (
    InvoiceIssuanceForbiddenError,
    InvoiceIssuanceInvalidTransitionError,
    InvoiceIssuanceValidationError,
    PartyBlockedError,
    PartyNotFoundError,
    ProductNotFoundError,
)

_NOTIFY = (
    "app.application.use_cases.invoice_issuance.invoice_issuance_use_cases"
)


@pytest.fixture(autouse=True)
def _stub_notifications():
    with (
        patch(f"{_NOTIFY}.notify_request_created", return_value=False) as created,
        patch(f"{_NOTIFY}.notify_request_returned", return_value=False) as returned,
        patch(f"{_NOTIFY}.notify_request_issued", return_value=False) as issued,
        patch(f"{_NOTIFY}.notify_request_cancelled", return_value=False) as cancelled,
    ):
        yield {
            "created": created,
            "returned": returned,
            "issued": issued,
            "cancelled": cancelled,
        }


def _creator(**kwargs: Any) -> Actor:
    base = dict(user_id="u-create", user_name="Criador", has_create=True)
    base.update(kwargs)
    return Actor(**base)


def _processor(**kwargs: Any) -> Actor:
    base = dict(user_id="u-process", user_name="Faturamento", has_process=True)
    base.update(kwargs)
    return Actor(**base)


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "branch_code": "01",
        "party_type": "customer",
        "party_code": "000001",
        "party_store": "01",
        "invoice_type": "sale",
        "freight_mode": "cif",
        "carrier_name": "Transp Alpha",
        "weight_kg": "12,5",
        "volume_count": 2,
        "observation": "Urgente",
        "items": [
            {
                "product_code": "90260001",
                "product_description": "Conector",
                "quantity": 1,
                "unit_price": "10,00",
                "stock_write_off": False,
            }
        ],
    }
    payload.update(overrides)
    return payload


class FakeLookups:
    def __init__(self) -> None:
        self.customers = [
            {
                "party_type": "customer",
                "party_code": "000001",
                "party_store": "01",
                "party_name": "ACME LTDA",
                "tax_id": "12345678000199",
                "blocked": False,
            },
            {
                "party_type": "customer",
                "party_code": "000099",
                "party_store": "01",
                "party_name": "Bloqueado",
                "tax_id": "11111111000111",
                "blocked": True,
            },
        ]
        self.products = [
            {
                "code": "90260001",
                "description": "Conector",
                "unit": "UN",
                "blocked": False,
            },
            {
                "code": "90260999",
                "description": "Bloqueado",
                "unit": "UN",
                "blocked": True,
            },
        ]
        self.carriers = [
            {
                "carrier_code": "000001",
                "carrier_name": "JADLOG",
                "legal_name": "JADLOG LOGISTICA LTDA",
                "tax_id": "12345678000199",
                "blocked": False,
            },
            {
                "carrier_code": "000099",
                "carrier_name": "BLOQ",
                "legal_name": "Transportadora Bloqueada",
                "tax_id": None,
                "blocked": True,
            },
        ]

    def search_customers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            row
            for row in self.customers
            if q in row["party_code"].lower()
            or q in row["party_name"].lower()
            or q in (row.get("tax_id") or "")
        ][:limit]

    def get_customer(self, *, party_code: str, party_store: str) -> dict[str, Any] | None:
        for row in self.customers:
            if row["party_code"] == party_code and row["party_store"] == party_store:
                return dict(row)
        return None

    def search_products(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            row
            for row in self.products
            if q in row["code"].lower() or q in row["description"].lower()
        ][:limit]

    def get_product(self, *, code: str) -> dict[str, Any] | None:
        for row in self.products:
            if row["code"] == code:
                return dict(row)
        return None

    def get_warehouse_01_balance(self, *, product_code: str, branch_code: str) -> dict[str, Any]:
        return {
            "product_code": product_code,
            "branch_code": branch_code,
            "warehouse": "01",
            "quantity": 12.0,
        }

    def search_carriers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            row
            for row in self.carriers
            if q in row["carrier_code"].lower()
            or q in row["carrier_name"].lower()
            or q in row["legal_name"].lower()
        ][:limit]

    def get_carrier(self, *, carrier_code: str) -> dict[str, Any] | None:
        for row in self.carriers:
            if row["carrier_code"] == carrier_code:
                return dict(row)
        return None


class FakeSuppliers:
    def __init__(self) -> None:
        self.suppliers = [
            {
                "supplier_code": "000010",
                "supplier_store": "01",
                "supplier_name": "Fornecedor Beta",
                "tax_id": "98765432000111",
                "blocked": False,
            }
        ]

    def search_suppliers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            row
            for row in self.suppliers
            if q in row["supplier_code"].lower() or q in row["supplier_name"].lower()
        ][:limit]

    def get_supplier(self, *, supplier_code: str, supplier_store: str) -> dict[str, Any] | None:
        for row in self.suppliers:
            if row["supplier_code"] == supplier_code and row["supplier_store"] == supplier_store:
                return dict(row)
        return None


class FakeRequests:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.history: dict[str, list[dict[str, Any]]] = {}

    def create_request_with_history(
        self,
        *,
        request_fields: dict[str, Any],
        items: list[dict[str, Any]],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        request_id = str(uuid4())
        row = {
            **request_fields,
            "id": request_id,
            "items": deepcopy(items),
            "attachments": [],
            "return_reason": None,
            "assignee_user_id": None,
            "assignee_name": None,
            "items_count": len(items),
            "total_amount": sum(
                float(item["quantity"]) * float(item["unit_price"]) for item in items
            ),
        }
        self.rows[request_id] = row
        self.history[request_id] = [{**history_fields, "request_id": request_id}]
        return deepcopy(row)

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        row = self.rows.get(request_id)
        return deepcopy(row) if row else None

    def list_history(self, request_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.history.get(request_id) or [])

    def list_requests(
        self,
        *,
        filters: dict[str, Any],
        created_by_user_id: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        items = list(self.rows.values())
        if created_by_user_id:
            items = [row for row in items if row["created_by_user_id"] == created_by_user_id]
        if filters.get("branch"):
            items = [row for row in items if row["branch_code"] == filters["branch"]]
        return {
            "items": deepcopy(items),
            "total": len(items),
            "page": page,
            "page_size": page_size,
            "total_pages": 1,
        }

    def update_returned_request(
        self,
        *,
        request_id: str,
        request_fields: dict[str, Any],
        items: list[dict[str, Any]],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        row = self.rows[request_id]
        row.update(request_fields)
        row["items"] = deepcopy(items)
        self.history[request_id].append({**history_fields, "request_id": request_id})
        return deepcopy(row)

    def update_status(
        self,
        *,
        request_id: str,
        status: str,
        extra: dict[str, Any] | None = None,
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        extra = extra or {}
        row = self.rows[request_id]
        row["status"] = status
        if extra.get("clear_return_reason"):
            row["return_reason"] = None
        if extra.get("return_reason"):
            row["return_reason"] = extra["return_reason"]
        if extra.get("assignee_user_id"):
            row["assignee_user_id"] = extra["assignee_user_id"]
            row["assignee_name"] = extra.get("assignee_name")
        if extra.get("issued_at"):
            row["issued_at"] = extra["issued_at"]
        if extra.get("cancelled_at"):
            row["cancelled_at"] = extra["cancelled_at"]
            row["cancelled_by_user_id"] = extra.get("cancelled_by_user_id")
            row["cancelled_by_name"] = extra.get("cancelled_by_name")
            row["cancel_justification"] = extra.get("cancel_justification")
        self.history[request_id].append({**history_fields, "request_id": request_id})
        return deepcopy(row)


def test_search_parties_customers_and_suppliers() -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    use_case = SearchPartiesUseCase(lookups, suppliers)
    customers = use_case.execute(party_type="customer", query="acme")
    assert customers[0]["party_code"] == "000001"
    suppliers_found = use_case.execute(party_type="supplier", query="beta")
    assert suppliers_found[0]["party_type"] == "supplier"
    with pytest.raises(InvoiceIssuanceValidationError):
        use_case.execute(party_type="other", query="xx")


def test_search_products_and_warehouse_balance() -> None:
    lookups = FakeLookups()
    products = SearchIssuanceProductsUseCase(lookups).execute(query="9026")
    assert products[0]["code"] == "90260001"
    balance = GetWarehouse01BalanceUseCase(lookups).execute(
        product_code="90260001", branch_code="01"
    )
    assert balance["quantity"] == 12.0
    assert balance["warehouse"] == "01"


def test_search_carriers_uses_short_name() -> None:
    lookups = FakeLookups()
    found = SearchIssuanceCarriersUseCase(lookups).execute(query="jad")
    assert found[0]["carrier_code"] == "000001"
    assert found[0]["carrier_name"] == "JADLOG"


def test_create_snapshots_carrier_from_sa4(_stub_notifications) -> None:
    created = CreateInvoiceIssuanceRequestUseCase(
        FakeRequests(), FakeLookups(), FakeSuppliers()
    ).execute(_valid_payload(carrier_code="000001", carrier_name="x"), _creator())
    assert created["carrier_code"] == "000001"
    assert created["carrier_name"] == "JADLOG"
    with pytest.raises(InvoiceIssuanceValidationError):
        CreateInvoiceIssuanceRequestUseCase(
            FakeRequests(), FakeLookups(), FakeSuppliers()
        ).execute(_valid_payload(carrier_code="000099"), _creator())


def test_create_requires_totvs_party_and_derives_review(_stub_notifications) -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    use_case = CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers)
    created = use_case.execute(_valid_payload(), _creator())
    assert created["status"] == "pending"
    assert created["party_name"] == "ACME LTDA"
    assert created["purchase_order_number"] is None
    assert created["observation"] == "Urgente"
    assert created["checklist"]["recipient"] is True
    assert created["checklist"]["weight_volumes"] is True
    assert "purchase_order" not in created["checklist"]
    _stub_notifications["created"].assert_called_once()


def test_sale_and_return_default_stock_write_off(_stub_notifications) -> None:
    items = [
        {
            "product_code": "90260001",
            "product_description": "Conector",
            "quantity": 1,
            "unit_price": "10,00",
        }
    ]
    use_case = CreateInvoiceIssuanceRequestUseCase(
        FakeRequests(), FakeLookups(), FakeSuppliers()
    )
    sale = use_case.execute(_valid_payload(items=items), _creator())
    assert sale["items"][0]["stock_write_off"] is True
    returned = use_case.execute(
        _valid_payload(invoice_type="return", items=items), _creator()
    )
    assert returned["items"][0]["stock_write_off"] is True
    sample = use_case.execute(
        _valid_payload(invoice_type="sample", items=items), _creator()
    )
    assert sample["items"][0]["stock_write_off"] is False
    explicit = use_case.execute(
        _valid_payload(items=[{**items[0], "stock_write_off": False}]), _creator()
    )
    assert explicit["items"][0]["stock_write_off"] is False


def test_create_keeps_sales_order_on_items(_stub_notifications) -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    created = CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers).execute(
        _valid_payload(
            items=[
                {
                    "product_code": "90260001",
                    "product_description": "Conector",
                    "quantity": 2,
                    "unit_price": "10,00",
                    "stock_write_off": False,
                    "sales_order": "000111",
                    "sales_order_item": "01",
                    "customer_order_number": "PC-9",
                }
            ]
        ),
        _creator(),
    )
    item = created["items"][0]
    assert item["sales_order"] == "000111"
    assert item["sales_order_item"] == "01"
    assert item["customer_order_number"] == "PC-9"
    with pytest.raises(InvoiceIssuanceValidationError):
        CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers).execute(
            _valid_payload(
                items=[
                    {
                        "product_code": "90260001",
                        "product_description": "Conector",
                        "quantity": 1,
                        "unit_price": 1,
                        "stock_write_off": False,
                        "sales_order": "000111",
                    }
                ]
            ),
            _creator(),
        )


def test_create_party_errors(_stub_notifications) -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    use_case = CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers)
    with pytest.raises(PartyNotFoundError):
        use_case.execute(_valid_payload(party_code="999999"), _creator())
    with pytest.raises(PartyBlockedError):
        use_case.execute(_valid_payload(party_code="000099"), _creator())
    with pytest.raises(ProductNotFoundError):
        use_case.execute(
            _valid_payload(
                items=[
                    {
                        "product_code": "missing",
                        "product_description": "x",
                        "quantity": 1,
                        "unit_price": 1,
                        "stock_write_off": False,
                    }
                ]
            ),
            _creator(),
        )


def test_list_scopes_creator_without_view() -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    created = CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers).execute(
        _valid_payload(), _creator()
    )
    listed = ListInvoiceIssuanceRequestsUseCase(requests).execute(
        actor=_creator(),
        filters={"branch": "01"},
        page=1,
        page_size=20,
    )
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == created["id"]
    other = ListInvoiceIssuanceRequestsUseCase(requests).execute(
        actor=_creator(user_id="other"),
        filters={"branch": "01"},
        page=1,
        page_size=20,
    )
    assert other["total"] == 0


def test_transitions_start_return_resubmit_issue_cancel(_stub_notifications) -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    created = CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers).execute(
        _valid_payload(), _creator()
    )
    request_id = created["id"]
    processor = _processor()
    started = StartInvoiceIssuanceRequestUseCase(requests).execute(request_id, processor)
    assert started["status"] == "in_progress"
    with pytest.raises(InvoiceIssuanceInvalidTransitionError):
        StartInvoiceIssuanceRequestUseCase(requests).execute(request_id, processor)
    returned = ReturnInvoiceIssuanceRequestUseCase(requests).execute(
        request_id, processor, reason="Falta peso"
    )
    assert returned["status"] == "returned"
    _stub_notifications["returned"].assert_called_once()
    updated = UpdateReturnedInvoiceIssuanceRequestUseCase(
        requests, lookups, suppliers
    ).execute(request_id, _valid_payload(weight_kg="20"), _creator())
    assert updated["weight_kg"] == 20 or float(updated["weight_kg"]) == 20
    pending = ResubmitInvoiceIssuanceRequestUseCase(requests).execute(
        request_id, _creator()
    )
    assert pending["status"] == "pending"
    started = StartInvoiceIssuanceRequestUseCase(requests).execute(request_id, processor)
    issued = IssueInvoiceIssuanceRequestUseCase(requests).execute(request_id, processor)
    assert issued["status"] == "issued"
    _stub_notifications["issued"].assert_called_once()
    detail = GetInvoiceIssuanceRequestUseCase(requests).execute(request_id, processor)
    assert "issue" not in detail["allowed_actions"]
    assert "view" in detail["allowed_actions"]


def test_creator_can_cancel_pending(_stub_notifications) -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    created = CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers).execute(
        _valid_payload(), _creator()
    )
    cancelled = CancelInvoiceIssuanceRequestUseCase(requests).execute(
        created["id"], _creator(), justification="Pedido cancelado"
    )
    assert cancelled["status"] == "cancelled"
    _stub_notifications["cancelled"].assert_called_once()
    with pytest.raises(InvoiceIssuanceInvalidTransitionError):
        CancelInvoiceIssuanceRequestUseCase(requests).execute(
            created["id"], _creator(), justification="de novo"
        )


def test_create_forbidden_without_permission() -> None:
    lookups = FakeLookups()
    suppliers = FakeSuppliers()
    requests = FakeRequests()
    with pytest.raises(InvoiceIssuanceForbiddenError):
        CreateInvoiceIssuanceRequestUseCase(requests, lookups, suppliers).execute(
            _valid_payload(), Actor(user_id="u-none", user_name="Sem papel")
        )


def test_allowed_actions_matrix() -> None:
    pending = {
        "status": "pending",
        "created_by_user_id": "u-create",
    }
    assert "start" in allowed_actions(pending, _processor())
    assert "cancel" in allowed_actions(pending, _creator())
    assert "start" not in allowed_actions(pending, _creator())
    assert "attach" not in allowed_actions(pending, _processor())
