"""Smoke HTTP — Protheus REST integration routes (AuthZ + envelope)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.application.security import api_delpi_permissions as perms
from app.domain.integrations.protheus_rest import ProtheusRestError


def _user(*permission_codes: str) -> SimpleNamespace:
    return SimpleNamespace(
        id="u-test",
        name="Tester",
        is_superadmin=False,
        permissions=list(permission_codes),
    )


def _body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def test_status_authorized_ok() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        get_protheus_integration_status_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    status_payload = {
        "integration": "protheus",
        "configuration": "ok",
        "authentication": "ok",
        "connection": "ok",
        "config_path_label_mismatch": True,
        "transport": "https",
    }
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "delpi_auth.request_context.get_current_user", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_get_protheus_integration_status_use_case"
    ) as build_uc:
        build_uc.return_value.execute.return_value = status_payload
        response = get_protheus_integration_status_route()

    body = _body(response)
    assert body["success"] is True
    assert body["data"] == status_payload
    assert body["meta"]["operationId"] == "get_protheus_integration_status"
    assert "token" not in json.dumps(body).lower()
    assert "password" not in json.dumps(body).lower()


def test_status_unauthorized_forbidden() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        get_protheus_integration_status_route,
    )

    user = _user("other.access")
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            get_protheus_integration_status_route()


def test_supplier_authorized_existing() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        get_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    payload = {"A2_COD": "000001", "A2_LOJA": "01", "A2_NOME": "ACME"}
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "delpi_auth.request_context.get_current_user", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_get_protheus_rest_supplier_use_case"
    ) as build_uc:
        build_uc.return_value.execute.return_value = payload
        response = get_protheus_rest_supplier_route(supplier_id="00000101")

    body = _body(response)
    assert body["success"] is True
    assert body["data"]["A2_COD"] == "000001"
    assert body["meta"]["operationId"] == "get_protheus_rest_supplier"
    build_uc.return_value.execute.assert_called_once_with("00000101")


def test_supplier_unauthorized_forbidden() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        get_protheus_rest_supplier_route,
    )

    user = _user("dashboard-financial.view")
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        with pytest.raises(Exception, match="Forbidden"):
            get_protheus_rest_supplier_route(supplier_id="00000101")


def test_supplier_not_found_maps_404() -> None:
    from app.interface.http.routes.integrations.protheus_router import (
        get_protheus_rest_supplier_route,
    )

    user = _user(perms.API_DELPI_INTEGRATIONS_PROTHEUS_READ)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), patch(
        "delpi_auth.request_context.get_current_user", return_value=user
    ), patch(
        "app.interface.http.routes.integrations.protheus_router.build_get_protheus_rest_supplier_use_case"
    ) as build_uc:
        build_uc.return_value.execute.side_effect = ProtheusRestError(
            "Fornecedor não encontrado no Protheus.",
            code="PROTHEUS_SUPPLIER_NOT_FOUND",
            status_code=404,
            recoverable=False,
        )
        response = get_protheus_rest_supplier_route(supplier_id="99999999")

    body = _body(response)
    assert body["success"] is False
    assert response.status_code == 404
    assert body["error"]["code"] == "PROTHEUS_SUPPLIER_NOT_FOUND"


def test_supplier_use_case_rejects_invalid_id_before_external_call() -> None:
    from app.application.use_cases.integrations.get_protheus_rest_supplier_use_case import (
        GetProtheusRestSupplierUseCase,
    )

    class _BoomRepo:
        def load_raw_params(self):
            raise AssertionError("params must not be loaded for invalid id")

    class _BoomToken:
        def get_valid_token(self, config):
            raise AssertionError("token must not be requested for invalid id")

    class _BoomGateway:
        def get_supplier(self, *args, **kwargs):
            raise AssertionError("external call must not happen for invalid id")

    uc = GetProtheusRestSupplierUseCase(
        params_repository=_BoomRepo(),  # type: ignore[arg-type]
        token_service=_BoomToken(),  # type: ignore[arg-type]
        gateway=_BoomGateway(),  # type: ignore[arg-type]
    )
    with pytest.raises(ProtheusRestError) as exc:
        uc.execute("ABC")
    assert exc.value.code == "PROTHEUS_SUPPLIER_ID_INVALID"


def test_status_use_case_missing_params() -> None:
    from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
        GetProtheusIntegrationStatusUseCase,
    )

    class _Repo:
        def load_raw_params(self):
            return {"USR_PROTHEUS": "x"}  # incomplete

    class _Unused:
        def get_valid_token(self, config):
            raise AssertionError("should not auth")

        def get_supplier(self, *args, **kwargs):
            raise AssertionError("should not call")

    uc = GetProtheusIntegrationStatusUseCase(
        params_repository=_Repo(),  # type: ignore[arg-type]
        token_service=_Unused(),  # type: ignore[arg-type]
        gateway=_Unused(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["configuration"] in {"missing", "invalid"}
    assert result["authentication"] == "unavailable"
    assert result["connection"] == "unavailable"


def test_status_use_case_upstream_error_is_not_healthy() -> None:
    from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
        GetProtheusIntegrationStatusUseCase,
    )
    from app.domain.integrations.protheus_rest import ProtheusRestConfig

    class _Repo:
        def load_raw_params(self):
            return {
                "USR_PROTHEUS": "tech.user",
                "PSW_PROTHEUS": "secret",
                "URL_REST": "https://protheus.example/rest",
                "PATH_AUTH": "/api/oauth2/v1/token",
                "PATH_SUPPLIERS": "/delpi/api/v1/suppliers/",
            }

    class _Token:
        def get_valid_token(self, config):
            assert isinstance(config, ProtheusRestConfig)
            return "tok"

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            raise ProtheusRestError(
                "Erro inesperado ao consultar fornecedor no Protheus.",
                code="PROTHEUS_UPSTREAM_ERROR",
                status_code=502,
            )

    uc = GetProtheusIntegrationStatusUseCase(
        params_repository=_Repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["configuration"] == "ok"
    assert result["authentication"] == "ok"
    assert result["connection"] == "failed"
    assert result["transport"] == "https"


def test_status_use_case_not_found_probe_counts_as_connected() -> None:
    from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
        GetProtheusIntegrationStatusUseCase,
    )

    class _Repo:
        def load_raw_params(self):
            return {
                "USR_PROTHEUS": "tech.user",
                "PSW_PROTHEUS": "secret",
                "URL_REST": "https://protheus.example/rest",
                "PATH_AUTH": "/api/oauth2/v1/token",
                "PATH_SUPPLIERS": "/delpi/api/v1/suppliers/",
            }

    class _Token:
        def get_valid_token(self, config):
            return "tok"

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            raise ProtheusRestError(
                "Fornecedor não encontrado no Protheus.",
                code="PROTHEUS_SUPPLIER_NOT_FOUND",
                status_code=404,
                recoverable=False,
            )

    uc = GetProtheusIntegrationStatusUseCase(
        params_repository=_Repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["connection"] == "ok"


def test_router_exposes_status_and_supplier_paths() -> None:
    from app.interface.http.routes.integrations.protheus_router import router

    paths = {getattr(route, "path", None) for route in router.routes}
    assert "/integrations/protheus/status" in paths
    assert "/integrations/protheus/suppliers/{supplier_id}" in paths
    assert "/integrations/protheus/suppliers" in paths
    operation_ids = {
        getattr(route, "operation_id", None)
        for route in router.routes
        if getattr(route, "operation_id", None)
    }
    assert "get_protheus_integration_status" in operation_ids
    assert "get_protheus_rest_supplier" in operation_ids
    assert "create_protheus_rest_supplier" in operation_ids
    assert "update_protheus_rest_supplier" in operation_ids


def _status_repo() -> object:
    class _Repo:
        def load_raw_params(self):
            return {
                "USR_PROTHEUS": "tech.user",
                "PSW_PROTHEUS": "secret",
                "URL_REST": "https://protheus.example/rest",
                "PATH_AUTH": "/api/oauth2/v1/token",
                "PATH_SUPPLIERS": "/delpi/api/v1/suppliers/",
            }

    return _Repo()


def test_status_use_case_auth_401_is_upstream_pending() -> None:
    from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
        GetProtheusIntegrationStatusUseCase,
    )

    class _Token:
        def get_valid_token(self, config):
            raise ProtheusRestError(
                "Falha na autenticação técnica com o Protheus.",
                code="PROTHEUS_AUTH_FAILED",
                status_code=502,
                upstream_status=401,
            )

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            raise AssertionError("read must not run without a token")

    uc = GetProtheusIntegrationStatusUseCase(
        params_repository=_status_repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["configuration"] == "ok"
    assert result["connectivity"] == "ok"
    assert result["authentication"] == "failed"
    assert result["authentication_http_status"] == 401
    assert result["suppliers_read"] == "not_checked"
    assert result["overall"] == "upstream_pending"
    assert result["checked_at"]


def test_status_use_case_transport_failure_is_unavailable() -> None:
    from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
        GetProtheusIntegrationStatusUseCase,
    )

    class _Token:
        def get_valid_token(self, config):
            raise ProtheusRestError(
                "Timeout ao contatar o Protheus.",
                code="PROTHEUS_TIMEOUT",
                status_code=504,
            )

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            raise AssertionError("unreachable")

    uc = GetProtheusIntegrationStatusUseCase(
        params_repository=_status_repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["connectivity"] == "failed"
    assert result["authentication"] == "not_checked"
    assert result["authentication_http_status"] is None
    assert result["overall"] == "unavailable"


def test_status_use_case_token_invalid_on_read_is_upstream_pending() -> None:
    from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
        GetProtheusIntegrationStatusUseCase,
    )

    class _Token:
        def get_valid_token(self, config):
            return "tok"

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            raise ProtheusRestError(
                "Token rejeitado.",
                code="PROTHEUS_TOKEN_INVALID",
                status_code=502,
            )

    uc = GetProtheusIntegrationStatusUseCase(
        params_repository=_status_repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["authentication"] == "ok"
    assert result["suppliers_read"] == "failed"
    assert result["connection"] == "failed"
    assert result["overall"] == "upstream_pending"


def test_status_use_case_ready_requires_guard_match(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        get_protheus_integration_status_use_case as uc_module,
    )

    class _Token:
        def get_valid_token(self, config):
            return "tok"

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            return {"supplier_id": "00000000"}

    uc = uc_module.GetProtheusIntegrationStatusUseCase(
        params_repository=_status_repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )

    monkeypatch.setattr(uc_module.settings, "PROTHEUS_REST_EXPECTED_BASE_URL", None)
    result = uc.execute()
    # Pin ausente → destino não comprovado → nunca "ready_for_attempt".
    assert result["write_target_guard"] == "unverified"
    assert result["overall"] == "unavailable"

    monkeypatch.setattr(
        uc_module.settings,
        "PROTHEUS_REST_EXPECTED_BASE_URL",
        "https://protheus.example/rest",
    )
    monkeypatch.setattr(uc_module.settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    monkeypatch.setattr(uc_module.settings, "PROTHEUS_SUPPLIER_UPDATE_ENABLED", False)
    result = uc.execute()
    assert result["write_target_guard"] == "ok"
    assert result["create_gate"] == "enabled"
    assert result["update_gate"] == "disabled"
    assert result["write_validation"] == "not_tested"
    assert result["overall"] == "ready_for_attempt"
    assert result["suppliers_read"] == "ok"


def test_status_use_case_guard_mismatch_is_unavailable(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        get_protheus_integration_status_use_case as uc_module,
    )

    class _Token:
        def get_valid_token(self, config):
            return "tok"

    class _Gateway:
        def get_supplier(self, *args, **kwargs):
            return {}

    monkeypatch.setattr(
        uc_module.settings,
        "PROTHEUS_REST_EXPECTED_BASE_URL",
        "https://other.example/rest",
    )
    uc = uc_module.GetProtheusIntegrationStatusUseCase(
        params_repository=_status_repo(),  # type: ignore[arg-type]
        token_service=_Token(),  # type: ignore[arg-type]
        gateway=_Gateway(),  # type: ignore[arg-type]
    )
    result = uc.execute()
    assert result["write_target_guard"] == "mismatch"
    assert result["overall"] == "unavailable"
