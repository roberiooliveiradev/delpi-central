"""Entry-audit Protheus reads — SQL shape, filters and S2S HTTP contract."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from delpi_auth.service_errors import ServiceClientDeniedError, ServiceScopeDeniedError
from delpi_auth.service_identity import ServiceIdentity

from app.application.dto.financeiro_entry_audit.entry_audit_query import (
    EntryAuditPeriodQuery,
    EntryAuditQueryError,
    page_payload,
)
from app.infrastructure.persistence.totvs.financeiro_entry_audit import entry_audit_sql

VALID_IDENTITY = ServiceIdentity(
    client_id="controllership-finance-api",
    subject="service-account-cf",
    scopes=frozenset({"stock-inventory.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)

S2S_HEADERS = {
    "X-Delpi-Service-Authorization": "Bearer service-jwt",
    "X-Delpi-Caller-App": "controllership-finance-api",
    "Authorization": "Bearer user-jwt",
}

DOCS = "/financeiro/entry-audit/documents"
ITEMS = "/financeiro/entry-audit/items"
PERIOD = "branch=01&received_from=2026-11-12&received_to=2026-11-12"


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.entry_audit_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _headers(headers):
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _validator(identity=VALID_IDENTITY, error=None):
    validator = MagicMock()
    if error is not None:
        validator.validate.side_effect = error
    else:
        validator.validate.return_value = identity
    return validator


def _patch_s2s(monkeypatch, request, validator=None):
    monkeypatch.setattr(
        "app.interface.http.s2s_service_access.get_request",
        lambda: request,
    )
    if validator is not None:
        monkeypatch.setattr(
            "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
            classmethod(lambda cls: validator),
        )


def _patch_user(monkeypatch, principal_type="user"):
    user = SimpleNamespace(id="user-1", email="user@delpi.local", principal_type=principal_type)
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.stock_inventory_route_helpers.resolve_user_context",
        lambda: user,
    )


def test_router_declares_the_five_read_operations() -> None:
    from app.interface.http.routes.financeiro.entry_audit_router import router

    operation_ids = {getattr(route, "operation_id", None) for route in router.routes}
    assert operation_ids >= {
        "list_entry_audit_documents",
        "list_entry_audit_items",
        "list_entry_audit_fiscal_book",
        "list_entry_audit_tes",
        "list_entry_audit_branches",
    }


def test_documents_sql_filters_receipt_date_and_species() -> None:
    sql, names = entry_audit_sql.documents_sql(["SPED", "CTE"])
    assert "SF1010" in sql
    assert "F1_RECBMTO >= ?" in sql
    assert "F1_RECBMTO <= ?" in sql
    assert "F1_ESPECIE" in sql
    assert "SA2010" in sql
    assert "F1_CHVNFE" in sql
    assert names[:3] == ["branch", "received_from", "received_to"]
    assert names[3:5] == ["SPED", "CTE"]
    assert "DELETE" not in sql.upper() and "UPDATE" not in sql.upper() and "INSERT" not in sql.upper()


def test_items_and_fiscal_book_follow_the_same_document_filter() -> None:
    items, item_names = entry_audit_sql.items_sql(["SPED"])
    book, book_names = entry_audit_sql.fiscal_book_sql(["CTE"])
    assert "SD1010" in items and "F1_RECBMTO" in items
    assert "SFT010" in book and "FT_TIPOMOV = 'E'" in book
    assert "FT_VALICM" in book
    assert item_names[3] == "SPED"
    assert book_names[3] == "CTE"


def test_tes_and_branches_do_not_take_a_period() -> None:
    tes = entry_audit_sql.tes_sql()
    branches = entry_audit_sql.branches_sql()
    assert "SF4010" in tes and "F4_CREDICM" in tes and "F1_RECBMTO" not in tes
    assert "F4_TIPO" in tes and "F4_CF" in tes
    assert "tes_type" in tes and "fiscal_code" in tes
    assert "SYS_COMPANY" in branches and "M0_CODIGO" in branches
    assert "01" in branches and "02" in branches


def test_period_query_accepts_one_day_and_rejects_other_species() -> None:
    query = EntryAuditPeriodQuery.from_query(
        branch="01",
        received_from="2026-11-12",
        received_to="2026-11-12",
        species=["SPED"],
        page=2,
        page_size=50,
    )
    assert query.received_from == "20261112"
    assert query.offset == 50
    with pytest.raises(EntryAuditQueryError):
        EntryAuditPeriodQuery.from_query(
            branch="01",
            received_from="2026-11-12",
            received_to="2026-11-12",
            species=["NFS"],
            page=1,
            page_size=50,
        )


def test_period_query_rejects_inverted_dates_and_unknown_branch() -> None:
    with pytest.raises(EntryAuditQueryError):
        EntryAuditPeriodQuery.from_query(
            branch="02",
            received_from="2026-11-13",
            received_to="2026-11-12",
            species=None,
            page=1,
            page_size=50,
        )
    with pytest.raises(EntryAuditQueryError):
        EntryAuditPeriodQuery.from_query(
            branch="07",
            received_from="2026-11-12",
            received_to="2026-11-12",
            species=None,
            page=1,
            page_size=50,
        )


def test_page_payload_converts_protheus_dates_and_drops_the_count_column() -> None:
    payload = page_payload(
        [{"received_date": "20261112", "issue_date": "", "gross_amount": 10, "total_count": 3}],
        page=1,
        page_size=50,
    )
    assert payload["total"] == 3
    assert payload["items"][0]["received_date"] == "2026-11-12"
    assert payload["items"][0]["issue_date"] is None
    assert "total_count" not in payload["items"][0]


def test_missing_service_header_is_401(client: TestClient, monkeypatch) -> None:
    _patch_s2s(monkeypatch, _headers({}))
    response = client.get(f"{DOCS}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_wrong_client_and_scope_are_403(client: TestClient, monkeypatch) -> None:
    _patch_s2s(monkeypatch, _headers(S2S_HEADERS), _validator(error=ServiceClientDeniedError("x")))
    assert client.get(f"{DOCS}?{PERIOD}", headers=S2S_HEADERS).status_code == 403
    _patch_s2s(
        monkeypatch,
        _headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    assert client.get(f"{DOCS}?{PERIOD}", headers=S2S_HEADERS).status_code == 403


def test_service_principal_cannot_read(client: TestClient, monkeypatch) -> None:
    _patch_s2s(monkeypatch, _headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = client.get(f"{DOCS}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DELEGATED_USER_REQUIRED"


def test_invalid_species_is_422(client: TestClient, monkeypatch) -> None:
    _patch_s2s(monkeypatch, _headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = client.get(f"{DOCS}?{PERIOD}&species=NFS", headers=S2S_HEADERS)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_documents_and_items_share_the_period_contract(client: TestClient, monkeypatch) -> None:
    _patch_s2s(monkeypatch, _headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.documents.return_value = {"items": [], "page": 1, "page_size": 50, "total": 19, "total_pages": 1}
    use_case.items.return_value = {"items": [], "page": 1, "page_size": 50, "total": 4, "total_pages": 1}
    import app.interface.http.routes.financeiro.entry_audit_router as mod

    monkeypatch.setattr(mod, "build_list_entry_audit_use_case", lambda: use_case)
    documents = client.get(f"{DOCS}?{PERIOD}&species=SPED&species=CTE", headers=S2S_HEADERS)
    items = client.get(f"{ITEMS}?{PERIOD}&species=SPED", headers=S2S_HEADERS)
    assert documents.status_code == 200
    assert documents.json()["meta"]["operationId"] == "list_entry_audit_documents"
    assert documents.json()["data"]["total"] == 19
    assert items.status_code == 200
    assert items.json()["meta"]["operationId"] == "list_entry_audit_items"
    document_query = use_case.documents.call_args.args[0]
    item_query = use_case.items.call_args.args[0]
    assert document_query.species == ("SPED", "CTE")
    assert item_query.species == ("SPED",)
    assert document_query.received_from == item_query.received_from == "20261112"
