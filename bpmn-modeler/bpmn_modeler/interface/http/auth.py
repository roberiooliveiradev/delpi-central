from __future__ import annotations

import logging
from types import SimpleNamespace

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import (
    _rbac_from_claims,
    load_user_rbac,
    normalize_path,
)
from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    get_current_user,
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from delpi_auth.service_token import request_has_valid_internal_service_token
from fastapi import Depends, Request

from bpmn_modeler.application.use_cases import CallerIdentity

from .responses import error_response

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/health", "/ready", "/openapi.json"}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _is_public(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized in PUBLIC_PATHS


def _route_path(request: Request) -> str:
    """ASGI path sem root_path — request.url.path inclui o prefixo do gateway."""
    path = request.scope.get("path") or "/"
    root_path = request.scope.get("root_path") or ""
    if root_path and path.startswith(root_path):
        path = path[len(root_path):] or "/"
    return path


async def auth_middleware(request: Request, call_next):
    """Envelope-aware auth middleware built on the shared delpi_auth stack."""
    clear_current_user()
    clear_request_authorization()

    path = _route_path(request)
    if _is_public(path):
        return await call_next(request)

    if request_has_valid_internal_service_token(request):
        service_user = SimpleNamespace(
            id="internal-service",
            email="service@delpi.internal",
            name="Serviço Interno",
            roles=["internal-service"],
            groups=[],
            permissions=[],
            is_superadmin=True,
            rbac_unavailable=False,
            access_token=None,
            principal_type="service",
        )
        request.state.user = service_user
        context_token = set_current_user(service_user)
        auth_context_token = set_request_authorization(
            request.headers.get("Authorization") or ""
        )
        try:
            return await call_next(request)
        finally:
            reset_request_authorization(auth_context_token)
            reset_current_user(context_token)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return error_response(401, "UNAUTHORIZED", "Autenticação necessária.",
                            _request_id(request))

    token = auth_header.split(" ", 1)[1]
    context_token = None
    auth_context_token = set_request_authorization(auth_header)

    try:
        claims = validate_token(token)
        sub = claims.get("sub")
        email = claims.get("email")
        if not sub or not email:
            reset_request_authorization(auth_context_token)
            return error_response(401, "UNAUTHORIZED", "Token inválido.",
                                  _request_id(request))

        try:
            rbac = await load_user_rbac(token)
        except Exception:
            logger.warning("rbac_lookup_unavailable path=%s", path, exc_info=True)
            rbac = _rbac_from_claims(claims, token, rbac_unavailable=True)

        user = SimpleNamespace(
            id=rbac.get("id") or sub,
            email=rbac.get("email") or email,
            name=rbac.get("name") or email or "Usuário",
            roles=rbac.get("roles", []),
            groups=rbac.get("groups", []),
            permissions=rbac.get("permissions", []),
            is_superadmin=rbac.get("is_superadmin", False),
            rbac_unavailable=bool(rbac.get("rbac_unavailable")),
            access_token=token,
            principal_type="user",
        )
        request.state.user = user
        context_token = set_current_user(user)
    except Exception:
        logger.exception("token_validation_failed path=%s", path)
        reset_request_authorization(auth_context_token)
        return error_response(401, "UNAUTHORIZED", "Token inválido.",
                              _request_id(request))

    try:
        return await call_next(request)
    finally:
        reset_request_authorization(auth_context_token)
        if context_token is not None:
            reset_current_user(context_token)
        else:
            clear_current_user()


def current_caller() -> CallerIdentity:
    user = get_current_user()
    if user is None:
        raise PermissionError("no authenticated user")
    permissions = set(getattr(user, "permissions", []) or [])
    if getattr(user, "is_superadmin", False):
        permissions |= {
            "bpmn-modeler.view", "bpmn-modeler.edit", "bpmn-modeler.manage"
        }
    subject = str(getattr(user, "id", "") or getattr(user, "sub", "") or "")
    display_name = str(getattr(user, "name", "") or "")
    return CallerIdentity(
        subject=subject,
        permissions=frozenset(permissions),
        display_name=display_name,
    )


from typing import Annotated

CallerDep = Annotated[CallerIdentity, Depends(current_caller)]
