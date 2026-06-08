"""Garante que o envelope com meta permanece compatível com consumidores legados."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))

from delpi_api_client.envelope import parse_envelope  # noqa: E402

from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financial.financial_routes import get_rol


def test_mfe_consumer_pattern_reads_data_only() -> None:
    """Plugins fazem response.data após HTTP 200 — meta não interfere."""
    envelope = api_delpi_success(
        {"rol": 1_000_000},
        operation_id="get_financial_rol",
        message="ok",
    )
    raw = json.loads(envelope.body.decode())
    assert raw["success"] is True
    assert raw["data"] == {"rol": 1_000_000}
    assert raw["meta"]["operationId"] == "get_financial_rol"

    data, meta, error = parse_envelope(raw)
    assert data == {"rol": 1_000_000}
    assert meta is not None
    assert error is None


def test_si_client_parse_envelope_ignores_meta_for_payload() -> None:
    body = {
        "success": True,
        "message": "CPV buscado com sucesso.",
        "data": {"summary": {"value": 42}},
        "meta": {"entity": "supplies_cpv", "shape": "scalar"},
    }
    data, meta, _ = parse_envelope(body)
    assert data == {"summary": {"value": 42}}
    assert meta["entity"] == "supplies_cpv"


@patch("app.interface.http.routes.financial.financial_routes.build_get_rol_use_case")
def test_envelope_includes_meta_on_live_route(mock_build) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {"rol": 99}
    mock_build.return_value = mock_use_case

    response = get_rol()
    body = json.loads(response.body.decode())

    assert "meta" in body
    assert body["meta"]["shape"] == "scalar"
    data, meta, _ = parse_envelope(body)
    assert data == {"rol": 99}
    assert meta["operationId"] == "get_financial_rol"
