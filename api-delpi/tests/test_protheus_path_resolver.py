"""Unit tests — Protheus PATH_AUTH / PATH_SUPPLIERS semantic resolution."""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_path_resolver import (
    resolve_protheus_rest_config,
)
from app.domain.integrations.protheus_rest import ProtheusRestError


def _base(**overrides: str) -> dict[str, str]:
    params = {
        "USR_PROTHEUS": "tech.user",
        "PSW_PROTHEUS": "secret-value",
        "URL_REST": "https://protheus.example/rest",
        "PATH_AUTH": "/api/oauth2/v1/token",
        "PATH_SUPPLIERS": "/delpi/api/v1/suppliers/",
    }
    params.update(overrides)
    return params


def test_resolve_aligned_paths() -> None:
    config = resolve_protheus_rest_config(_base())
    assert config.auth_path == "/api/oauth2/v1/token"
    assert config.suppliers_path == "/delpi/api/v1/suppliers/"
    assert config.path_label_mismatch is False


def test_resolve_inverted_labels_without_mutating_source() -> None:
    raw = _base(
        PATH_AUTH="/delpi/api/v1/suppliers/",
        PATH_SUPPLIERS="/api/oauth2/v1/token",
    )
    config = resolve_protheus_rest_config(raw)
    assert config.auth_path == "/api/oauth2/v1/token"
    assert config.suppliers_path == "/delpi/api/v1/suppliers/"
    assert config.path_label_mismatch is True
    # Source dict unchanged
    assert raw["PATH_AUTH"] == "/delpi/api/v1/suppliers/"


def test_missing_param_raises_controlled_error() -> None:
    raw = _base()
    del raw["URL_REST"]
    with pytest.raises(ProtheusRestError) as exc:
        resolve_protheus_rest_config(raw)
    assert exc.value.code == "PROTHEUS_CONFIG_MISSING"


def test_invalid_url_raises() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        resolve_protheus_rest_config(_base(URL_REST="not-a-url"))
    assert exc.value.code == "PROTHEUS_CONFIG_INVALID"
