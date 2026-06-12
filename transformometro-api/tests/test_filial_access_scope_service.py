from __future__ import annotations

from types import SimpleNamespace

import pytest

from tm_app.application.security.transformometro_permissions import (
    TRANSFORMOMETRO_MANAGE_FILIAL_01,
    TRANSFORMOMETRO_PROCESSES_MANAGE,
    TRANSFORMOMETRO_VIEW_CONSOLIDATED,
    TRANSFORMOMETRO_VIEW_FILIAL_01,
    TRANSFORMOMETRO_VIEW_FILIAL_02,
)
from tm_app.application.services.filial_access_scope_service import FilialAccessScopeService


def _user(**kwargs):
    defaults = {
        "id": "user-1",
        "email": "user@test",
        "permissions": [],
        "is_superadmin": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_superadmin_is_unrestricted():
    scope = FilialAccessScopeService().resolve(_user(is_superadmin=True))
    assert scope.is_unrestricted
    assert scope.can_view_consolidated is True


def test_legacy_view_without_branch_perms_is_unrestricted():
    scope = FilialAccessScopeService().resolve(
        _user(permissions=["transformometro.view"])
    )
    assert scope.is_unrestricted
    assert scope.can_view_consolidated is True


def test_branch_view_scopes_allowed_filiais():
    scope = FilialAccessScopeService().resolve(
        _user(permissions=[TRANSFORMOMETRO_VIEW_FILIAL_01])
    )
    assert scope.mode == "scoped"
    assert scope.allowed_codigos == frozenset({"01"})
    assert scope.can_view_consolidated is False


def test_branch_view_with_consolidated_permission():
    scope = FilialAccessScopeService().resolve(
        _user(
            permissions=[
                TRANSFORMOMETRO_VIEW_FILIAL_01,
                TRANSFORMOMETRO_VIEW_CONSOLIDATED,
            ]
        )
    )
    assert scope.can_view_consolidated is True


def test_can_view_filial_respects_scope():
    svc = FilialAccessScopeService()
    scope = svc.resolve(_user(permissions=[TRANSFORMOMETRO_VIEW_FILIAL_01]))
    assert svc.can_view_filial(scope, "01") is True
    assert svc.can_view_filial(scope, "02") is False


def test_global_manage_on_unrestricted_scope():
    svc = FilialAccessScopeService()
    user = _user(permissions=[TRANSFORMOMETRO_PROCESSES_MANAGE])
    scope = svc.resolve(user)
    assert svc.can_manage_filial(scope, "02", user=user) is True


def test_branch_manage_only_on_matching_filial():
    svc = FilialAccessScopeService()
    user = _user(
        permissions=[
            TRANSFORMOMETRO_VIEW_FILIAL_01,
            TRANSFORMOMETRO_MANAGE_FILIAL_01,
        ]
    )
    scope = svc.resolve(user)
    assert svc.can_manage_filial(scope, "01", user=user) is True
    assert svc.can_manage_filial(scope, "02", user=user) is False


def test_filter_filiais_options():
    svc = FilialAccessScopeService()
    scope = svc.resolve(
        _user(permissions=[TRANSFORMOMETRO_VIEW_FILIAL_02])
    )
    filiais = [
        {"id": "01", "label": "Matriz"},
        {"id": "02", "label": "Filial"},
    ]
    filtered = svc.filter_filiais_options(filiais, scope)
    assert filtered == [{"id": "02", "label": "Filial"}]


def test_filter_rows_by_filial():
    svc = FilialAccessScopeService()
    scope = svc.resolve(
        _user(permissions=[TRANSFORMOMETRO_VIEW_FILIAL_01, TRANSFORMOMETRO_VIEW_FILIAL_02])
    )
    rows = [
        {"processo_id": "p1", "filial_id": "01"},
        {"processo_id": "p2", "filial_id": "02"},
    ]
    assert len(svc.filter_rows_by_filial(rows, scope)) == 2

    scope_one = svc.resolve(_user(permissions=[TRANSFORMOMETRO_VIEW_FILIAL_01]))
    filtered = svc.filter_rows_by_filial(rows, scope_one)
    assert len(filtered) == 1
    assert filtered[0]["processo_id"] == "p1"
