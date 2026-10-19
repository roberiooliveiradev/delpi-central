"""Tests — PARAMETROS_MINHADELPI loader."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)


def test_load_raw_params_maps_rows() -> None:
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        SimpleNamespace(param_key="USR_PROTHEUS", param_value="tech.user"),
        SimpleNamespace(param_key="PSW_PROTHEUS", param_value="secret"),
        SimpleNamespace(param_key="URL_REST", param_value="https://example/rest"),
        SimpleNamespace(param_key="PATH_AUTH", param_value="/api/oauth2/v1/token"),
        SimpleNamespace(
            param_key="PATH_SUPPLIERS", param_value="/delpi/api/v1/suppliers/"
        ),
    ]
    connection = MagicMock()
    connection.cursor.return_value = cursor

    repo = ProtheusIntegrationParamsRepository(connection_factory=lambda: connection)
    result = repo.load_raw_params()

    assert result["USR_PROTHEUS"] == "tech.user"
    assert result["PSW_PROTHEUS"] == "secret"
    connection.close.assert_called_once()


def test_connection_failure_is_controlled() -> None:
    def _boom():
        raise RuntimeError("odbc down")

    repo = ProtheusIntegrationParamsRepository(connection_factory=_boom)
    with pytest.raises(ProtheusRestError) as exc:
        repo.load_raw_params()
    assert exc.value.code == "PROTHEUS_CONFIG_UNAVAILABLE"
    assert "odbc" not in str(exc.value).lower()
