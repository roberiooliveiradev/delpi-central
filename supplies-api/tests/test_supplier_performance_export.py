from io import BytesIO
from unittest.mock import patch

from openpyxl import load_workbook
import pytest

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError

URL = "/analytics/supplier-performance/export?branch=01&date_from=2026-11-01&date_to=2026-11-16"
HEADERS = {"Authorization": "Bearer token"}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def auth(permissions=None):
    identity = AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br", name="Buyer",
    )
    user = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email=identity.email, name=identity.name,
        permissions=permissions if permissions is not None else {"supplies.access"},
        is_superadmin=False, keycloak_sub=identity.sub, access_token="user-jwt",
    )
    return (
        patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate", return_value=identity),
        patch("app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user", return_value=user),
    )


COMPONENT = dict(index=80.0, assessed_count=10, positive_count=8,
                 negative_count=2, unknown_count=0,
                 conditional_count=1, urgent_count=0)
DATA = dict(
    items=[dict(
        supplier_code="000001", supplier_store="01", supplier_name="Fornecedor teste",
        branches=["01"], quality=COMPONENT,
        delivery={**COMPONENT, "index": 60.0, "positive_count": 6, "negative_count": 4},
        idf=74.0, quality_contribution=56.0, delivery_contribution=18.0,
        status="complete",
    )],
    summary=dict(
        suppliers=1, evaluated=1, incomplete=0, average_idf=74.0,
        average_quality=80.0, average_delivery=60.0,
        inspection_count=10, receipt_count=10,
    ),
    methodology=dict(
        quality_weight=70, delivery_weight=30, scale=100,
        classification_bands=None,
    ),
    period={"from": "2026-11-01", "to": "2026-11-16"},
    branches=["01"], calculated_at="2026-11-16T08:00:00-03:00",
    supplier_selected={"code": "000001", "store": "01"},
    inspections=[dict(
        branch="01", supplier_code="000001", supplier_store="01",
        supplier_name="Fornecedor teste", inspection_id="000099",
        invoice_number="0012345", invoice_series="001", invoice_item="01",
        report_date="2026-11-14", receipt_date="2026-11-13",
        evidence_state="Aprovada", conditional=1, urgent=0,
    )],
    deliveries=[dict(
        branch="01", supplier_code="000001", supplier_store="01",
        supplier_name="Fornecedor teste", document="000098", order_number="001234",
        order_item="01", product_code="30190001", quantity=10,
        expected_delivery_date="2026-11-13", receipt_entry_date="2026-11-14",
        days_diff=-1, evidence_state="Atrasada",
    )],
)


def test_xlsx_export_has_evidence_styles_identifiers_and_auth_forwarding(client):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        gateway.get.return_value = {"success": True, "data": DATA}
        response = client.get(
            URL + "&supplier_code=000001&supplier_store=01", headers=HEADERS
        )
        assert response.status_code == 200
        assert "spreadsheetml.sheet" in response.mimetype
        assert "no-store" == response.headers["Cache-Control"]
        gateway.get.assert_called_once_with(
            "/supplies/supplier-performance/evidence-export",
            access_token="user-jwt",
            params=[
                ("branch", "01"), ("date_from", "2026-11-01"),
                ("date_to", "2026-11-16"),
                ("supplier_code", "000001"), ("supplier_store", "01"),
            ],
        )
    wb = load_workbook(BytesIO(response.data), data_only=False)
    assert wb.sheetnames == ["Resumo IDF", "Entregas", "Inspeções", "Critérios"]
    summary = wb["Resumo IDF"]
    assert summary["A6"].value == "000001"
    assert summary["A6"].number_format == "@"
    assert summary["S6"].value == 74.0
    assert summary["S6"].number_format == "0.00"
    assert summary["A5"].border.left.style == "thin"
    assert summary["A6"].border.top.style == "thin"
    assert summary.freeze_panes == "E6"
    assert summary.auto_filter.ref.startswith("A5:")
    assert wb["Entregas"]["F6"].value == "001234"
    assert wb["Entregas"]["M6"].number_format == "DD/MM/YYYY"
    assert wb["Inspeções"]["F6"].value == "0012345"


def test_export_denied_without_normal_permission_and_with_bad_scope(client):
    assert client.get(URL).status_code == 401
    validate, resolve = auth({"supplies.manage"})
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        assert client.get(URL, headers=HEADERS).status_code == 403
        gateway.get.assert_not_called()
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        assert client.get(URL.replace("branch=01&", ""), headers=HEADERS).status_code == 403
        assert client.get(URL.replace("branch=01", "branch=03"), headers=HEADERS).status_code == 403
        assert client.get(URL + "&supplier_code=000001", headers=HEADERS).status_code == 422
        assert client.get(URL + "&date_to=2026-01-01", headers=HEADERS).status_code == 422
        gateway.get.assert_not_called()


def test_export_validation_and_upstream_errors_are_not_empty_success(client):
    validate, resolve = auth()
    with validate, resolve, patch(
        "app.interfaces.http.routes.supplier_performance_routes._GATEWAY"
    ) as gateway:
        gateway.get.return_value = {"success": True, "data": {"items": []}}
        assert client.get(URL, headers=HEADERS).status_code == 502
        gateway.get.side_effect = DelpiApiGatewayError("private SQL error", status_code=422)
        response = client.get(URL, headers=HEADERS)
        assert response.status_code == 422
        assert b"private SQL error" not in response.data
        gateway.get.side_effect = DelpiApiGatewayError("private SQL error", status_code=503)
        assert client.get(URL, headers=HEADERS).status_code == 502


def test_spreadsheet_erp_text_cannot_run_as_formula():
    from app.infrastructure.export.supplier_performance_xlsx import build_supplier_performance_xlsx
    payload = {**DATA, "items": [{**DATA["items"][0], "supplier_name": "=1+1"}]}
    wb = load_workbook(BytesIO(build_supplier_performance_xlsx(payload)), data_only=False)
    assert wb["Resumo IDF"]["C6"].data_type != "f"
    assert wb["Resumo IDF"]["C6"].value == "'=1+1"
