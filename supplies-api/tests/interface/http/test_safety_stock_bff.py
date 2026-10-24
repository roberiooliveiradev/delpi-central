"""HTTP BFF — safety stock (E11.S1)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.exceptions import CoreApiUnavailableError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def _filters_envelope() -> dict:
    return {
        "success": True,
        "data": {
            "branch": "all",
            "product_groups": ["MP", "EMB"],
            "units": ["PC", "KG"],
            "statuses": [
                "above_safety_stock",
                "at_safety_stock",
                "below_safety_stock",
                "without_safety_stock",
            ],
            "warehouses": ["01", "50", "98", "99"],
            "primary_warehouse": "01",
            "work_in_process_warehouses": ["50", "98", "99"],
            "work_in_process_note": "Saldo disponível = armazéns 01 + 98 + 99.",
            "authorized_branches": [],
        },
    }


def _summary_envelope() -> dict:
    return {
        "success": True,
        "data": {
            "total_materials": 120,
            "with_safety_stock": 100,
            "without_safety_stock": 20,
            "below_safety_stock": 15,
            "at_safety_stock": 5,
            "above_safety_stock": 80,
            "with_primary_stock": 95,
            "without_primary_stock": 25,
            "with_work_in_process_stock": 10,
            "deficit_by_unit": [
                {"unit": "PC", "material_count": 10, "deficit_quantity": 500.0}
            ],
        },
    }


def _items_envelope() -> dict:
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "product_code": "10070821",
                    "product_description": "CABO PP",
                    "product_type": "MP",
                    "unit": "PC",
                    "product_group": "MP",
                    "branch": "01",
                    "blocked": False,
                    "safety_stock": 100.0,
                    "primary_stock": 80.0,
                    "work_in_process_stock": 5.0,
                    "warehouse_50_stock": 0.0,
                    "warehouse_98_stock": 3.0,
                    "warehouse_99_stock": 2.0,
                    "work_in_process_committed": 4.0,
                    "work_in_process_available": 1.0,
                    "deficit_quantity": 20.0,
                    "status": "below_safety_stock",
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
            "sort_by": "product_code",
            "sort_direction": "asc",
        },
    }


def _details_envelope() -> dict:
    return {
        "success": True,
        "data": {
            "product": {
                "product_code": "10070821",
                "branch": "01",
                "safety_stock": 100.0,
                "available_stock": 85.0,
                "secondary_unit": "KG",
                "conversion_factor": 0.5,
            },
            "stock": {
                "safety_stock": 100.0,
                "available_stock": 85.0,
                "primary_stock": 60.0,
                "deficit_quantity": 15.0,
            },
            "purchase_coverage": {"status": "partial"},
            "open_purchase_orders": {"items": [], "total": 0},
            "open_purchase_requests": {"items": [], "total": 0},
            "stock_projection": {"status": "sufficient"},
            "monthly_consumption": {"series": []},
            "annual_comparison": {"series": []},
        },
        "meta": {"sections": {"open_purchase_orders": "ok"}},
    }


def _suppliers_envelope() -> dict:
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "supplier_code": "F000123",
                    "supplier_store": "01",
                    "supplier_name": "FORNECEDOR X",
                    "last_purchase_date": "2026-09-01",
                }
            ],
            "total": 1,
        },
    }


_AUTH_MIDDLEWARE = (
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
_JWT = "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate"
_GATEWAY = "app.infrastructure.gateways.supplies_delpi_reads.DelpiApiGateway"


def _client_with_gateway(gateway, *, permissions: set[str] | None = None):
    permissions = permissions or {"supplies.access"}
    return create_app().test_client(), permissions


def _get(client, gateway, path, envelope):
    gateway.get.return_value = envelope
    with patch(_GATEWAY, return_value=gateway):
        return client.get(path, headers={"Authorization": "Bearer tok"})


# ---------- AuthZ ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_anonymous_401(mock_resolve, mock_validate):
    mock_validate.side_effect = Exception("no token")
    client = create_app().test_client()
    response = client.get("/safety-stock/summary")
    assert response.status_code == 401


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_forbidden_without_supplies_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.manage"})
    gateway = MagicMock()
    client = create_app().test_client()
    for path in (
        "/safety-stock/filters",
        "/safety-stock/summary",
        "/safety-stock/items",
        "/safety-stock/items/ABC/details?branch=01",
        "/safety-stock/items/ABC/suppliers?branch=01",
    ):
        response = client.get(path, headers={"Authorization": "Bearer tok"})
        assert response.status_code == 403, path
    assert gateway.get.call_count == 0


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_core_unavailable_fail_closed(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.side_effect = CoreApiUnavailableError("Core down")
    client = create_app().test_client()
    response = client.get(
        "/safety-stock/summary", headers={"Authorization": "Bearer tok"}
    )
    assert response.status_code == 503


# ---------- Filters ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_exposes_branch_catalog_not_authorized_branches(
    mock_resolve, mock_validate
):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(client, gateway, "/safety-stock/filters", _filters_envelope())
    assert response.status_code == 200
    body = response.get_json()
    assert body["branch_catalog"] == ["01", "02"]
    assert body["all_scope"] == "all"
    assert "authorized_branches" not in body
    assert body["product_groups"] == ["MP", "EMB"]
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == "all"
    assert params["includeBlocked"] == "false"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_branch_and_blocked_passthrough(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(
        client,
        gateway,
        "/safety-stock/filters?branch=01&includeBlocked=true",
        _filters_envelope(),
    )
    assert response.status_code == 200
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == "01"
    assert params["includeBlocked"] == "true"


# ---------- Summary ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_summary_all_is_single_upstream_call(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(
        client, gateway, "/safety-stock/summary?branch=all", _summary_envelope()
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["below_safety_stock"] == 15
    assert body["deficit_by_unit"][0]["unit"] == "PC"
    assert gateway.get.call_count == 1
    assert gateway.get.call_args.kwargs["params"]["branch"] == "all"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_summary_branches_01_02_and_domain_filters(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    r01 = _get(
        client, gateway, "/safety-stock/summary?branch=01", _summary_envelope()
    )
    r02 = _get(
        client,
        gateway,
        "/safety-stock/summary?branch=02&status=below_safety_stock"
        "&productGroup=MP&unit=PC&search=cabo&includeBlocked=true"
        "&includeWithoutSafetyStock=false",
        _summary_envelope(),
    )
    assert r01.status_code == 200
    assert r02.status_code == 200
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == "02"
    assert params["status"] == "below_safety_stock"
    assert params["productGroup"] == "MP"
    assert params["unit"] == "PC"
    assert params["search"] == "cabo"
    assert params["includeBlocked"] == "true"
    assert params["includeWithoutSafetyStock"] == "false"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_summary_default_branch_is_all(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(client, gateway, "/safety-stock/summary", _summary_envelope())
    assert response.status_code == 200
    assert gateway.get.call_args.kwargs["params"]["branch"] == "all"


# ---------- Items ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_items_passthrough_and_params(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(
        client,
        gateway,
        "/safety-stock/items?branch=all&page=2&page_size=100&sortBy=deficit_quantity"
        "&sortDirection=desc&status=below_safety_stock",
        _items_envelope(),
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["items"][0]["status"] == "below_safety_stock"
    assert body["items"][0]["deficit_quantity"] == 20.0
    params = gateway.get.call_args.kwargs["params"]
    assert params["branch"] == "all"
    assert params["page"] == 2
    assert params["page_size"] == 100
    assert params["sortBy"] == "deficit_quantity"
    assert params["sortDirection"] == "desc"
    assert params["status"] == "below_safety_stock"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_items_validation_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    cases = [
        "/safety-stock/items?branch=03",
        "/safety-stock/items?branch=99",
        "/safety-stock/items?page=0",
        "/safety-stock/items?page_size=201",
        "/safety-stock/items?sortBy=hack",
        "/safety-stock/items?sortDirection=sideways",
        "/safety-stock/items?status=not_a_status",
    ]
    for path in cases:
        response = client.get(path, headers={"Authorization": "Bearer tok"})
        assert response.status_code == 422, path
    assert gateway.get.call_count == 0


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_items_empty_real_result(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    empty = {
        "success": True,
        "data": {
            "items": [],
            "page": 1,
            "page_size": 50,
            "total": 0,
            "total_pages": 0,
            "sort_by": "product_code",
            "sort_direction": "asc",
        },
    }
    response = _get(client, gateway, "/safety-stock/items?branch=01", empty)
    assert response.status_code == 200
    assert response.get_json()["items"] == []
    assert response.get_json()["total"] == 0


# ---------- Details ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_details_requires_concrete_branch(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    for path in (
        "/safety-stock/items/ABC/details",
        "/safety-stock/items/ABC/details?branch=all",
        "/safety-stock/items/ABC/details?branch=03",
    ):
        response = client.get(path, headers={"Authorization": "Bearer tok"})
        assert response.status_code == 422, path
    assert gateway.get.call_count == 0


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_details_passthrough_sections(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(
        client,
        gateway,
        "/safety-stock/items/10070821/details?branch=02",
        _details_envelope(),
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["product"]["product_code"] == "10070821"
    assert body["stock_projection"]["status"] == "sufficient"
    assert gateway.get.call_args.args[0] == (
        "/supplies/safety-stock/items/10070821/details"
    )
    assert gateway.get.call_args.kwargs["params"]["branch"] == "02"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_details_404_when_item_missing(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error", status_code=404
    )
    with patch(_GATEWAY, return_value=gateway):
        client = create_app().test_client()
        response = client.get(
            "/safety-stock/items/NOPE/details?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
    assert response.get_json()["code"] == "not_found"


# ---------- Suppliers ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_suppliers_preserves_code_and_store(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    response = _get(
        client,
        gateway,
        "/safety-stock/items/10070821/suppliers?branch=01",
        _suppliers_envelope(),
    )
    assert response.status_code == 200
    item = response.get_json()["items"][0]
    assert item["supplier_code"] == "F000123"
    assert item["supplier_store"] == "01"
    assert gateway.get.call_args.args[0] == (
        "/supplies/safety-stock/items/10070821/suppliers"
    )
    assert gateway.get.call_args.kwargs["params"]["branch"] == "01"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_suppliers_requires_concrete_branch(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    for path in (
        "/safety-stock/items/ABC/suppliers",
        "/safety-stock/items/ABC/suppliers?branch=all",
    ):
        response = client.get(path, headers={"Authorization": "Bearer tok"})
        assert response.status_code == 422, path


# ---------- Upstream errors ----------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_error_mapping(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    client = create_app().test_client()
    cases = [
        (401, 401, "unauthorized"),
        (403, 403, "forbidden"),
        (422, 422, "upstream_client_error"),
        (500, 502, "bad_gateway"),
    ]
    for upstream, expected, code in cases:
        gateway = MagicMock()
        gateway.get.side_effect = DelpiApiGatewayError(
            "api-delpi client error", status_code=upstream
        )
        with patch(_GATEWAY, return_value=gateway):
            response = client.get(
                "/safety-stock/summary?branch=01",
                headers={"Authorization": "Bearer tok"},
            )
        assert response.status_code == expected
        assert response.get_json()["code"] == code

    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/safety-stock/summary?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 502
    assert response.get_json()["code"] == "bad_gateway"



# ---------- E11.S4 — envelope inválido upstream (residual S1) ----------
#
# Reproduzido: `unwrap_delpi_envelope` devolvia `data` tal qual e o método
# convertia payload não-dict em `{}` com HTTP 200, confundindo sucesso,
# vazio legítimo, payload malformado e `success=false` (data=None).
# Agora payload sem shape contratual mínimo → 502 `bad_gateway`.


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_malformed_envelope_data_none_returns_502(mock_resolve, mock_validate):
    """`data=None` (inclui `success=false`) nunca vira `{}` com 200."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    malformed = {"success": False, "data": None}
    for path in (
        "/safety-stock/filters",
        "/safety-stock/summary?branch=01",
        "/safety-stock/items?branch=01",
        "/safety-stock/items/ABC/details?branch=01",
        "/safety-stock/items/ABC/suppliers?branch=01",
    ):
        response = _get(client, gateway, path, malformed)
        assert response.status_code == 502, path
        assert response.get_json()["code"] == "bad_gateway"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_malformed_envelope_data_list_returns_502(mock_resolve, mock_validate):
    """`data=[]` onde se espera objeto → 502."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    malformed = {"success": True, "data": []}
    for path in (
        "/safety-stock/summary?branch=01",
        "/safety-stock/items/ABC/details?branch=01",
        "/safety-stock/items/ABC/suppliers?branch=01",
    ):
        response = _get(client, gateway, path, malformed)
        assert response.status_code == 502, path


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_malformed_envelope_empty_object_returns_502(mock_resolve, mock_validate):
    """`data={}` sem as chaves contratuais mínimas → 502 (não 200 vazio)."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    malformed = {"success": True, "data": {}}
    for path in (
        "/safety-stock/filters",
        "/safety-stock/summary?branch=01",
        "/safety-stock/items?branch=01",
        "/safety-stock/items/ABC/details?branch=01",
        "/safety-stock/items/ABC/suppliers?branch=01",
    ):
        response = _get(client, gateway, path, malformed)
        assert response.status_code == 502, path


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_missing_envelope_wrapper_returns_502(mock_resolve, mock_validate):
    """Payload sem envelope compatível (string/scalar) → 502."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    for path in (
        "/safety-stock/summary?branch=01",
        "/safety-stock/items?branch=01",
        "/safety-stock/items/ABC/details?branch=01",
    ):
        response = _get(client, gateway, path, "unexpected-scalar")
        assert response.status_code == 502, path


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_details_legitimate_404_preserved(mock_resolve, mock_validate):
    """404 real do produtor (item inexistente) continua 404, não 502 nem 200."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    gateway.get.side_effect = DelpiApiGatewayError(
        "not found", status_code=404
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/safety-stock/items/ZZZ/details?branch=01",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
    assert response.get_json()["code"] == "not_found"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_details_empty_sections_are_legitimate(mock_resolve, mock_validate):
    """Coleções vazias dentro de um detalhe válido seguem 200 (empty real)."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = MagicMock()
    client = create_app().test_client()
    envelope = _details_envelope()
    envelope["data"]["open_purchase_orders"] = {"items": [], "total": 0}
    envelope["data"]["open_commitments"] = {"items": [], "total": 0}
    response = _get(
        client, gateway, "/safety-stock/items/ABC/details?branch=01", envelope
    )
    assert response.status_code == 200
    assert response.get_json()["open_purchase_orders"]["items"] == []


def test_safety_stock_routes_registered():
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/safety-stock/filters" in rules
    assert "/safety-stock/summary" in rules
    assert "/safety-stock/items" in rules
    assert "/safety-stock/items/<code>/details" in rules
    assert "/safety-stock/items/<code>/suppliers" in rules
