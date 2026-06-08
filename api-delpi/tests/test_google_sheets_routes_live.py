"""Testes de integração em rotas que leem Google Sheets (sem TOTVS)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient


def _service_headers(*, caller_app: str = "dashboard-quality") -> dict[str, str]:
    token = (os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
    if not token:
        pytest.skip("API_DELPI_INTERNAL_SERVICE_TOKEN não configurado")
    return {
        "Authorization": f"Bearer {token}",
        "X-Delpi-Caller-App": caller_app,
    }


@pytest.fixture(scope="module")
def sheets_client() -> GoogleSheetsClient:
    return GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT or 10))


@pytest.fixture(scope="module")
def api_client() -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest.mark.parametrize(
    ("name", "sheet_id_attr", "gid_attr"),
    [
        ("kaizen", "QUALITY_SHEET_ID", "QUALITY_KAIZEN_SHEET_GID"),
        ("audit-5s", "QUALITY_SHEET_ID", "QUALITY_AUDIT_5S_SHEET_GID"),
        ("ebitda", "FINANCIAL_EBITDA_SHEET_ID", "FINANCIAL_EBITDA_SHEET_GID"),
        ("direct_labor", "DIRECT_LABOR_SHEET_ID", "DIRECT_LABOR_SHEET_GID"),
        (
            "supplies-negotiation-savings",
            "SUPPLIES_IDD_SHEET_ID",
            "SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID",
        ),
    ],
)
def test_google_sheets_client_reads_rows(
    sheets_client: GoogleSheetsClient,
    name: str,
    sheet_id_attr: str,
    gid_attr: str,
) -> None:
    sheet_id = getattr(settings, sheet_id_attr, None)
    gid = getattr(settings, gid_attr, None)
    if not sheet_id or not gid:
        pytest.skip(f"{sheet_id_attr}/{gid_attr} não configurado")

    rows = sheets_client.read_csv_rows(sheet_id, gid)
    assert isinstance(rows, list)
    assert len(rows) > 0, f"planilha {name} vazia"
    assert isinstance(rows[0], dict)


def test_quality_kaizen_summary_route(api_client: TestClient) -> None:
    response = api_client.get(
        "/quality/kaizens/summary",
        headers=_service_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert isinstance(body.get("data"), dict)
    assert body["meta"]["operationId"] == "get_kaizen_summary"
    assert body["meta"]["shape"] == "scalar"


def test_quality_audit_5s_summary_route(api_client: TestClient) -> None:
    response = api_client.get(
        "/quality/audit-5s/summary",
        headers=_service_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert isinstance(body.get("data"), dict)
    assert body["meta"]["operationId"] == "get_audit_5s_summary"
    assert body["meta"]["shape"] == "scalar"


def test_supplies_negotiation_savings_summary_route(api_client: TestClient) -> None:
    response = api_client.get(
        "/supplies/negotiation-savings/summary",
        params={"start_date": "2026-05-01", "end_date": "2026-05-31"},
        headers=_service_headers(caller_app="dashboard-supplies"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    data = body.get("data") or {}
    assert "branches" in data
    assert body["meta"]["operationId"] == "get_supplies_negotiation_savings_summary"
    assert body["meta"]["shape"] == "scalar"


def test_quality_kaizen_summary_with_date_filter(api_client: TestClient) -> None:
    response = api_client.get(
        "/quality/kaizens/summary",
        params={"date_start": "01-01-2026", "date_end": "31-12-2026"},
        headers=_service_headers(caller_app="dashboard-quality"),
    )

    assert response.status_code == 200
    assert response.json().get("success") is True


def test_app_usage_not_recorded_for_internal_service_token(api_client: TestClient) -> None:
    with patch(
        "app.middleware.app_usage_tracking_middleware.schedule_app_usage_record"
    ) as schedule:
        response = api_client.get(
            "/quality/kaizens/summary",
            headers=_service_headers(),
        )

    assert response.status_code == 200
    schedule.assert_not_called()
