from __future__ import annotations

from fastapi import Request

from maint_app.application.services.filial_access_scope_service import (
    FilialAccessScope,
    FilialAccessScopeService,
)

_scope_service = FilialAccessScopeService()


def resolve_access_scope(request: Request) -> FilialAccessScope:
    user = getattr(request.state, "user", None)
    return _scope_service.resolve(user)


def resolve_user(request: Request):
    return getattr(request.state, "user", None)
