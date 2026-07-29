"""Testes de autorização por unidade — Kaizômetro."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.application.security.api_delpi_permissions import (
    KAIZOMETRO_BRANCH_01,
    KAIZOMETRO_BRANCH_02,
    KAIZOMETRO_VIEW,
)
from app.interface.http.routes.quality.kaizen_branch_access import (
    allowed_branch_codes,
    branch_access_error,
    branch_view_allowed,
    resolve_query_branch,
)

_MOD = "app.interface.http.routes.quality.kaizen_branch_access"


def _patch_user(user: SimpleNamespace):
    return (
        patch(f"{_MOD}.get_current_user", return_value=user),
        patch(
            f"{_MOD}.has_permission",
            side_effect=lambda _current_user, perm: perm in user.permissions,
        ),
    )


def test_view_alone_allows_no_branches() -> None:
    user = SimpleNamespace(is_superadmin=False, permissions=[KAIZOMETRO_VIEW])
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert allowed_branch_codes() == set()
        assert branch_view_allowed("01") is False
        err = branch_access_error("01")
        assert err is not None
        assert err.status_code == 403


def test_branch_01_only() -> None:
    user = SimpleNamespace(is_superadmin=False, permissions=[KAIZOMETRO_BRANCH_01])
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert allowed_branch_codes() == {"01"}
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is False
        branch, err = resolve_query_branch(None)
        assert err is None
        assert branch == "01"


def test_both_branches_resolve_all() -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[KAIZOMETRO_BRANCH_01, KAIZOMETRO_BRANCH_02],
    )
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert allowed_branch_codes() == {"01", "02"}
        branch, err = resolve_query_branch(None)
        assert err is None
        assert branch is None


def test_requested_branch_forbidden() -> None:
    user = SimpleNamespace(is_superadmin=False, permissions=[KAIZOMETRO_BRANCH_01])
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        branch, err = resolve_query_branch("02")
        assert branch is None
        assert err is not None
        assert err.status_code == 403


def test_superadmin_allows_all() -> None:
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    get_user, has_perm = _patch_user(user)
    with get_user, has_perm:
        assert allowed_branch_codes() == {"01", "02"}
        assert branch_access_error("02") is None
