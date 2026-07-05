import pytest

from tv_app.application.services.branch_access_scope_service import BranchAccessScopeService
from tv_app.application.services.branch_policy_service import validate_native_branch


class FakeUser:
    def __init__(self, *, permissions=None, is_superadmin=False):
        self.permissions = permissions or []
        self.is_superadmin = is_superadmin


def test_branch_allowed_when_policy_empty():
    validate_native_branch({"branch": "99"})


def test_branch_rejected_when_not_in_list(monkeypatch):
    import tv_app.application.services.tv_dashboard_content_service as content_module

    content_module._load_settings.cache_clear()
    monkeypatch.setattr(
        content_module,
        "_load_settings",
        lambda: {
            "branchPolicy": {
                "allowedBranches": ["01", "02"],
                "rejectionMessage": "Filial bloqueada.",
            }
        },
    )
    with pytest.raises(ValueError, match="Filial bloqueada"):
        validate_native_branch({"branch": "99"})


def test_scoped_user_cannot_use_other_branch():
    user = FakeUser(permissions=["tv-dashboard.view.filial-01"])
    validate_native_branch({"branch": "01"}, user=user)
    with pytest.raises(ValueError, match="Filial não autorizada"):
        validate_native_branch({"branch": "02"}, user=user)
