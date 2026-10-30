"""Consumption-audit route — S2S auth, validation and envelope (GLPI #1353).

The route is the producer of the `supplies-api → api-delpi → Protheus` flow:
``GET /supplies/consumption-audit/orders/{production_order}`` guarded by
``require_s2s_or_any_permission`` with scope ``consumption-audit.read`` and
client allowlist ``supplies-api`` — the shared legacy token never authorizes.

operationId: get_consumption_audit_order
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from delpi_auth.service_errors import (
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceTokenInvalidError,
)
from delpi_auth.service_identity import ServiceIdentity

from app.interface.http import s2s_service_access
from app.interface.http.routes.supplies import consumption_audit_router


OP = "24884201006"

IDENTITY = ServiceIdentity(
    client_id="supplies-api",
    subject="service-account-subject",
    scopes=frozenset({"consumption-audit.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)


def _request(*, s2s_header: str | None = None):
    headers = {}
    if s2s_header is not None:
        headers["X-Delpi-Service-Authorization"] = s2s_header
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _validator(*, identity=IDENTITY, error=None):
    validator = Mock()
    if error is not None:
        validator.validate.side_effect = error
    else:
        validator.validate.return_value = identity
    return validator


def _use_case(*, result=None, error=None):
    use_case = Mock()
    if error is not None:
        use_case.execute.side_effect = error
    else:
        use_case.execute.return_value = result
    return use_case


def _call(*, s2s_header=None, user=None, validator=None, use_case=None,
          production_order=OP, branch="01"):
    request = _request(s2s_header=s2s_header)
    patches = [
        patch.object(s2s_service_access, "get_request", return_value=request),
        patch.object(
            consumption_audit_router,
            "build_get_consumption_audit_order_use_case",
            return_value=use_case or _use_case(result={"order": {}}),
        ),
    ]
    if validator is not None:
        patches.append(
            patch.object(
                s2s_service_access.ServiceTokenValidator,
                "from_env",
                return_value=validator,
            )
        )
    if user is not None:
        patches.append(
            patch.object(
                s2s_service_access, "resolve_user_context", return_value=user
            )
        )
    try:
        for patcher in patches:
            patcher.start()
        response = consumption_audit_router.get_consumption_audit_order(
            production_order=production_order, branch=branch
        )
    finally:
        for patcher in reversed(patches):
            patcher.stop()
    return response


def _body(response):
    return json.loads(response.body)


# ------------------------------------------------------------- S2S strict


def test_valid_s2s_credential_executes_and_envelopes():
    validator = _validator()
    use_case = _use_case(result={"order": {"product_code": "50226108"}})
    response = _call(s2s_header="Bearer svc-jwt", validator=validator,
                     use_case=use_case)
    assert response.status_code == 200
    payload = _body(response)
    assert payload["success"] is True
    assert payload["data"]["order"]["product_code"] == "50226108"
    validator.validate.assert_called_once_with(
        "svc-jwt",
        required_scopes=("consumption-audit.read",),
        allowed_clients=("supplies-api",),
    )
    use_case.execute.assert_called_once()
    request = use_case.execute.call_args.args[0]
    assert request.production_order == OP
    assert request.branch == "01"


def test_invalid_s2s_token_is_401():
    request = _request(s2s_header="Bearer bad")
    validator = _validator(error=ServiceTokenInvalidError())
    with patch.object(s2s_service_access, "get_request", return_value=request), \
            patch.object(s2s_service_access.ServiceTokenValidator,
                         "from_env", return_value=validator):
        with pytest.raises(HTTPException) as exc:
            consumption_audit_router.get_consumption_audit_order(
                production_order=OP, branch="01"
            )
    assert exc.value.status_code == 401


def test_wrong_scope_and_wrong_client_are_403():
    request = _request(s2s_header="Bearer svc-jwt")
    for error in (ServiceScopeDeniedError(), ServiceClientDeniedError()):
        with patch.object(s2s_service_access, "get_request",
                          return_value=request), \
                patch.object(s2s_service_access.ServiceTokenValidator,
                             "from_env",
                             return_value=_validator(error=error)):
            with pytest.raises(HTTPException) as exc:
                consumption_audit_router.get_consumption_audit_order(
                    production_order=OP, branch="01"
                )
        assert exc.value.status_code == 403


def test_legacy_service_principal_denied():
    """Shared-token service principal never authorizes this surface."""
    user = SimpleNamespace(principal_type="service")
    with pytest.raises(HTTPException) as exc:
        _call(s2s_header=None, user=user)
    assert exc.value.status_code == 403
    assert exc.value.error_code == "LEGACY_SERVICE_TOKEN"


def test_user_path_still_works_without_s2s_header():
    """Sem header S2S, cai no caminho de permissão de usuário (superadmin da
    fixture autouse autoriza; legacy service é o único negado)."""
    user = SimpleNamespace(principal_type="user")
    response = _call(s2s_header=None, user=user,
                     use_case=_use_case(result={"order": {}}))
    assert response.status_code == 200


# ------------------------------------------------------------- validation


def test_invalid_branch_is_400():
    response = _call(s2s_header="Bearer svc-jwt", validator=_validator(),
                     branch="03")
    assert response.status_code == 400
    assert _body(response)["error"]["code"] == "INVALID_REQUEST"


def test_missing_branch_is_invalid():
    # Query(...) na definição exige o parâmetro; chamada direta com valor
    # inválido também é rejeitada pelo DTO antes do use case.
    response = _call(s2s_header="Bearer svc-jwt", validator=_validator(),
                     branch="")
    assert response.status_code == 400


def test_malformed_production_order_is_400():
    for bad in ("2488420100", "248842010061", "24884201*06"):
        use_case = _use_case(result={"order": {}})
        response = _call(s2s_header="Bearer svc-jwt", validator=_validator(),
                         use_case=use_case, production_order=bad)
        assert response.status_code == 400
        assert _body(response)["error"]["code"] == "INVALID_REQUEST"
        use_case.execute.assert_not_called()


def test_order_not_found_is_404():
    response = _call(s2s_header="Bearer svc-jwt", validator=_validator(),
                     use_case=_use_case(result=None))
    assert response.status_code == 404
    payload = _body(response)
    assert payload["error"]["code"] == "PRODUCTION_ORDER_NOT_FOUND"
    assert payload["error"]["recoverable"] is False


def test_unexpected_use_case_failure_is_500_sanitized():
    response = _call(
        s2s_header="Bearer svc-jwt",
        validator=_validator(),
        use_case=_use_case(error=RuntimeError("pyodbc boom")),
    )
    assert response.status_code == 500
    payload = _body(response)
    assert payload["success"] is False
    assert "pyodbc" not in json.dumps(payload)
