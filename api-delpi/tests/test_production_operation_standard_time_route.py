"""Rota S2S — tempo padrão da operação de OP (contrato interno para o MES)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.use_cases.production.get_production_operation_standard_time_use_case import (
    GetProductionOperationStandardTimeUseCase,
)
from app.interface.http.routes.production.production_router import (
    get_production_operation_standard_time,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_OPERATION = "get_production_operation_standard_time"

_ROW = {
    "branch": "01",
    "production_order": "12345600101",
    "product_code": "PA123",
    "unit": "MI",
    "hy_tempad": 0.5,
    "hy_tempom": None,
    "hy_quant": None,
    "hy_setup": 0.25,
    "g2_tempad": None,
    "g2_setup": None,
    "operation_exists": 1,
}

_EXPECTED_DATA_KEYS = {
    "branch",
    "production_order",
    "operation_code",
    "product_code",
    "unit",
    "pieces_conversion_factor",
    "standard_time_unit_hours",
    "ideal_cycle_seconds",
    "setup_seconds",
    "standard_time_source",
    "data_quality",
}


def _repo(row):
    repo = MagicMock()
    repo.get_operation_standard_time_context.return_value = row
    return repo


def _call(row=_ROW, *, operation_code: str = "20", branch: str = "01"):
    """Chama o endpoint com token S2S válido e repository fakeado."""
    with (
        patch(
            "app.interface.http.routes.production.production_router."
            "request_has_valid_internal_service_token",
            return_value=True,
        ),
        patch(
            "app.interface.http.routes.production.production_router."
            "build_get_production_operation_standard_time_use_case"
        ) as mock_build,
    ):
        mock_build.return_value = GetProductionOperationStandardTimeUseCase(
            repository=_repo(row)
        )
        return get_production_operation_standard_time(
            request=MagicMock(),
            production_order="12345600101",
            operation_code=operation_code,
            branch=branch,
        )


def test_s2s_valid_returns_200_with_canonical_contract() -> None:
    response = _call()
    body = body_json(response)
    assert_envelope_meta(body, operation_id=_OPERATION, shape="scalar")

    data = body["data"]
    assert set(data.keys()) == _EXPECTED_DATA_KEYS  # sem campo extra
    assert data["branch"] == "01"
    assert data["production_order"] == "12345600101"
    assert data["operation_code"] == "20"
    assert data["product_code"] == "PA123"
    assert data["unit"] == "MI"
    # MI: 0,5 h/milheiro ÷ 1000 peças → 1,8 s/peça
    assert data["pieces_conversion_factor"] == 1000
    assert data["standard_time_unit_hours"] == 0.5
    assert data["ideal_cycle_seconds"] == 1.8
    assert data["setup_seconds"] == 900.0
    assert data["standard_time_source"] == "shy_tempad"
    assert data["data_quality"] == "complete"


def test_operation_without_standard_time_returns_200_unavailable() -> None:
    row = {
        **_ROW,
        "hy_tempad": None,
        "hy_tempom": None,
        "hy_quant": None,
        "g2_tempad": None,
    }
    body = body_json(_call(row))
    data = body["data"]
    assert data["ideal_cycle_seconds"] is None
    assert data["standard_time_source"] == "unavailable"
    assert data["data_quality"] == "standard_time_unavailable"


def test_operation_with_unconvertible_unit_returns_piece_quality() -> None:
    body = body_json(_call({**_ROW, "unit": "MT"}))
    data = body["data"]
    assert data["ideal_cycle_seconds"] is None
    assert data["pieces_conversion_factor"] is None
    assert data["data_quality"] == "piece_conversion_unavailable"


def test_missing_production_order_returns_404() -> None:
    response = _call(None)
    body = body_json(response)
    assert body["success"] is False
    assert response.status_code == 404


def test_missing_operation_returns_404() -> None:
    response = _call({**_ROW, "operation_exists": 0})
    body = body_json(response)
    assert body["success"] is False
    assert response.status_code == 404


def test_invalid_branch_returns_400() -> None:
    response = _call(branch="99")
    body = body_json(response)
    assert body["success"] is False
    assert response.status_code == 400


def test_without_service_token_is_rejected() -> None:
    with patch(
        "app.interface.http.routes.production.production_router."
        "request_has_valid_internal_service_token",
        return_value=False,
    ):
        response = get_production_operation_standard_time(
            request=MagicMock(),
            production_order="12345600101",
            operation_code="20",
            branch="01",
        )
    body = body_json(response)
    assert body["success"] is False
    assert response.status_code == 403
