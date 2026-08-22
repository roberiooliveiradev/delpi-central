from __future__ import annotations

import pytest

from financial_app.domain.errors import BranchAccessDenied, InvalidBranch
from financial_app.domain.services.branch_access_service import BranchAccessService
from tests.conftest import full_user, user


def service() -> BranchAccessService:
    return BranchAccessService()


def test_branch_scope_requires_matching_branch_permission() -> None:
    allowed = user("financial.access", "financial.view.filial-01")
    assert service().resolve_branch_scope(allowed, "01") == "01"

    with pytest.raises(BranchAccessDenied):
        service().resolve_branch_scope(allowed, "02")


def test_consolidated_requires_both_branches() -> None:
    single_branch = user("financial.access", "financial.view.filial-01")
    with pytest.raises(BranchAccessDenied):
        service().resolve_branch_scope(single_branch, None)

    assert service().resolve_branch_scope(full_user(), None) is None
    assert service().resolve_branch_scope(full_user(), "all") is None


def test_invalid_branch_is_rejected() -> None:
    with pytest.raises(InvalidBranch):
        service().resolve_branch_scope(full_user(), "07")


def test_access_permission_is_required_before_branch() -> None:
    with pytest.raises(PermissionError):
        service().assert_can_access(user("financial.view.filial-01"))


def test_module_permission_is_enforced() -> None:
    with pytest.raises(PermissionError):
        service().assert_can_use(user("financial.access"), "financial.delinquency.view")


def test_superadmin_passes_every_gate() -> None:
    admin = user(superadmin=True)
    service().assert_can_access(admin)
    service().assert_can_use(admin, "financial.cost-centers.view")
    assert service().resolve_branch_scope(admin, None) is None
    assert service().resolve_branch_scope(admin, "02") == "02"
