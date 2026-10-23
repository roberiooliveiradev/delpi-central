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

    Ambiguous or unrecognized path pairs fail with a controlled configuration
    error — never proceed with guesswork.
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

    auth_labeled_is_auth = _looks_like_auth_path(labeled_auth)
    auth_labeled_is_suppliers = _looks_like_suppliers_path(labeled_auth)
    suppliers_labeled_is_auth = _looks_like_auth_path(labeled_suppliers)
    suppliers_labeled_is_suppliers = _looks_like_suppliers_path(labeled_suppliers)

    # Aligned labels: PATH_AUTH looks like auth AND PATH_SUPPLIERS looks like suppliers.
    if auth_labeled_is_auth and suppliers_labeled_is_suppliers and not (
        auth_labeled_is_suppliers or suppliers_labeled_is_auth
    ):
        return ProtheusRestConfig(
            username=username,
            password=password,
            base_url=base_url,
            auth_path=labeled_auth,
            suppliers_path=labeled_suppliers,
            path_label_mismatch=False,
        )

    # Documented inversion: PATH_AUTH looks like suppliers AND PATH_SUPPLIERS looks like auth.
    if (
        auth_labeled_is_suppliers
        and suppliers_labeled_is_auth
        and not auth_labeled_is_auth
        and not suppliers_labeled_is_suppliers
    ):
        return ProtheusRestConfig(
            username=username,
            password=password,
            base_url=base_url,
            auth_path=labeled_suppliers,
            suppliers_path=labeled_auth,
            path_label_mismatch=True,
        )

    raise ProtheusRestError(
        "Paths Protheus ambíguos ou não reconhecidos. "
        "PATH_AUTH e PATH_SUPPLIERS devem mapear inequivocamente "
        "para autenticação (oauth/token) e fornecedores (supplier).",
        code="PROTHEUS_CONFIG_INVALID",
        status_code=503,
    )


def assert_protheus_write_target(
    config: ProtheusRestConfig, expected_base_url: str | None
) -> None:
    """Fail-closed guard: writes only reach the endpoint declared for this runtime.

    Each environment pins PROTHEUS_REST_EXPECTED_BASE_URL to its intended
    upstream (production → productive REST, local/homologation → TST REST).
    If the resolved PARAMETROS URL_REST diverges — or no expected target is
    declared — the write is blocked deterministically (STOP/NO WRITE).
    """
    expected = (expected_base_url or "").strip()
    if not expected:
        raise ProtheusRestError(
            "Destino REST de escrita não comprovado neste ambiente "
            "(PROTHEUS_REST_EXPECTED_BASE_URL ausente). "
            "Nenhuma escrita foi enviada ao ERP.",
            code="PROTHEUS_REST_TARGET_UNVERIFIED",
            status_code=503,
        )
    if expected.rstrip("/") != config.base_url:
        raise ProtheusRestError(
            "Destino REST configurado diverge do esperado para este ambiente. "
            "Escrita bloqueada por segurança (nenhuma escrita foi enviada ao ERP).",
            code="PROTHEUS_REST_TARGET_MISMATCH",
            status_code=503,
        )
