"""S2S scope-per-operation contract for Protheus supplier routes.

F3.4 evidence: PUT /integrations/protheus/suppliers returned
S2S_SCOPE_DENIED because the supplies-api service token only carried
``suppliers.read``. These tests pin the declared scope of each supplier
operation and prove the shared validator denies a token that lacks the
operation scope.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from delpi_auth.service_errors import (
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
)
from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_token_validator import (
    ServiceTokenValidator,
    ServiceTokenValidatorConfig,
)

from app.interface.http import s2s_service_access
from app.interface.http.routes.integrations import protheus_router


def _request() -> SimpleNamespace:
    return SimpleNamespace(
        headers={
            "X-Delpi-Service-Authorization": "Bearer svc-jwt",
            "X-Delpi-Caller-App": "supplies-api",
        },
        state=SimpleNamespace(),
    )


def _identity(*scopes: str) -> ServiceIdentity:
    return ServiceIdentity(
        client_id="supplies-api",
        subject="service-account-subject",
        scopes=frozenset(scopes),
        audience=("api-delpi",),
        issuer="https://portal.example/auth/realms/delpi",
    )


def _invoke_with_captured_validator(handler, *args, **kwargs):
    """Invoke a decorated route; return the kwargs used on validate()."""
    validator = Mock()
    validator.validate.return_value = _identity("suppliers.read")
    with (
        patch.object(
            s2s_service_access, "get_request", return_value=_request()
        ),
        patch.object(
            s2s_service_access.ServiceTokenValidator,
            "from_env",
            return_value=validator,
        ),
    ):
        try:
            handler(*args, **kwargs)
        except Exception:
            pass  # body/use-case failures are irrelevant to the contract
    assert validator.validate.called
    return validator.validate.call_args.kwargs


def test_get_supplier_declares_read_scope() -> None:
    kwargs = _invoke_with_captured_validator(
        protheus_router.get_protheus_rest_supplier_route,
        supplier_id="00246901",
    )
    assert kwargs["required_scopes"] == ("suppliers.read",)
    assert kwargs["allowed_clients"] == ("supplies-api",)


def test_post_supplier_declares_create_scope() -> None:
    kwargs = _invoke_with_captured_validator(
        protheus_router.create_protheus_rest_supplier_route,
        body={"fornecedor": {}},
    )
    assert kwargs["required_scopes"] == ("suppliers.create",)
    assert kwargs["allowed_clients"] == ("supplies-api",)


def test_put_supplier_declares_update_scope() -> None:
    kwargs = _invoke_with_captured_validator(
        protheus_router.update_protheus_rest_supplier_route,
        supplier_id="00246901",
        body={"fornecedor": {}},
    )
    assert kwargs["required_scopes"] == ("suppliers.update",)
    assert kwargs["allowed_clients"] == ("supplies-api",)


def _validator() -> ServiceTokenValidator:
    return ServiceTokenValidator(
        ServiceTokenValidatorConfig(
            audience="api-delpi",
            allowed_clients=frozenset({"supplies-api"}),
        )
    )


def test_validator_denies_read_only_token_on_update() -> None:
    """A token carrying only suppliers.read must not satisfy PUT."""
    claims = {
        "sub": "service-account-subject",
        "azp": "supplies-api",
        "scope": "suppliers.read",
        "aud": "api-delpi",
    }
    with patch(
        "delpi_auth.service_token_validator.validate_token",
        return_value=claims,
    ):
        with pytest.raises(ServiceScopeDeniedError):
            _validator().validate(
                "svc-jwt", required_scopes=("suppliers.update",)
            )


def test_validator_accepts_full_supplier_scope_set() -> None:
    """supplies-api token with read/create/update passes every route."""
    claims = {
        "sub": "service-account-subject",
        "azp": "supplies-api",
        "scope": "suppliers.read suppliers.create suppliers.update",
        "aud": "api-delpi",
    }
    with patch(
        "delpi_auth.service_token_validator.validate_token",
        return_value=claims,
    ):
        for scope in ("suppliers.read", "suppliers.create",
                      "suppliers.update"):
            identity = _validator().validate(
                "svc-jwt", required_scopes=(scope,)
            )
            assert identity.client_id == "supplies-api"


def test_validator_denies_foreign_client_even_with_scopes() -> None:
    """Another service client carrying suppliers scopes stays denied."""
    claims = {
        "sub": "other-service",
        "azp": "controllership-finance-api",
        "scope": "suppliers.update",
        "aud": "api-delpi",
    }
    with patch(
        "delpi_auth.service_token_validator.validate_token",
        return_value=claims,
    ):
        with pytest.raises(ServiceClientDeniedError):
            _validator().validate(
                "svc-jwt",
                required_scopes=("suppliers.update",),
                allowed_clients=("supplies-api",),
            )
