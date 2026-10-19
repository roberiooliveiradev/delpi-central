"""Resolve Protheus REST path parameters with semantic correction for label inversion."""

from __future__ import annotations

from urllib.parse import urlparse

from app.domain.integrations.protheus_rest import (
    REQUIRED_PARAM_KEYS,
    ProtheusRestConfig,
    ProtheusRestError,
)


def _looks_like_auth_path(path: str) -> bool:
    lowered = path.lower()
    return "oauth" in lowered or "token" in lowered


def _looks_like_suppliers_path(path: str) -> bool:
    return "supplier" in path.lower()


def _normalize_base_url(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        raise ProtheusRestError(
            "Parâmetro URL_REST ausente na configuração Protheus.",
            code="PROTHEUS_CONFIG_MISSING",
            status_code=503,
        )
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ProtheusRestError(
            "Parâmetro URL_REST inválido na configuração Protheus.",
            code="PROTHEUS_CONFIG_INVALID",
            status_code=503,
        )
    return value.rstrip("/")


def _normalize_path(raw: str, *, key: str) -> str:
    value = (raw or "").strip()
    if not value:
        raise ProtheusRestError(
            f"Parâmetro {key} ausente na configuração Protheus.",
            code="PROTHEUS_CONFIG_MISSING",
            status_code=503,
        )
    if not value.startswith("/"):
        value = f"/{value}"
    return value


def resolve_protheus_rest_config(raw_params: dict[str, str]) -> ProtheusRestConfig:
    """Build a safe config from PARAMETROS_MINHADELPI values.

    When PATH_AUTH / PATH_SUPPLIERS labels are inverted (documented case),
    resolve by path semantics without mutating the source table.
    """
    missing = [key for key in REQUIRED_PARAM_KEYS if not str(raw_params.get(key) or "").strip()]
    if missing:
        raise ProtheusRestError(
            "Configuração Protheus incompleta.",
            code="PROTHEUS_CONFIG_MISSING",
            status_code=503,
        )

    username = str(raw_params["USR_PROTHEUS"]).strip()
    password = str(raw_params["PSW_PROTHEUS"]).strip()
    base_url = _normalize_base_url(str(raw_params["URL_REST"]))
    labeled_auth = _normalize_path(str(raw_params["PATH_AUTH"]), key="PATH_AUTH")
    labeled_suppliers = _normalize_path(
        str(raw_params["PATH_SUPPLIERS"]), key="PATH_SUPPLIERS"
    )

    auth_ok = _looks_like_auth_path(labeled_auth)
    suppliers_ok = _looks_like_suppliers_path(labeled_suppliers)
    inverted = (
        _looks_like_suppliers_path(labeled_auth)
        and _looks_like_auth_path(labeled_suppliers)
        and not (auth_ok and suppliers_ok)
    )

    if inverted:
        auth_path = labeled_suppliers
        suppliers_path = labeled_auth
        mismatch = True
    elif auth_ok and suppliers_ok:
        auth_path = labeled_auth
        suppliers_path = labeled_suppliers
        mismatch = False
    else:
        auth_path = labeled_auth
        suppliers_path = labeled_suppliers
        mismatch = not (auth_ok and suppliers_ok)

    return ProtheusRestConfig(
        username=username,
        password=password,
        base_url=base_url,
        auth_path=auth_path,
        suppliers_path=suppliers_path,
        path_label_mismatch=mismatch,
    )
