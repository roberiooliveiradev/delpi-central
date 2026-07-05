import pytest

from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.tv_dashboard_content_service import message


def test_message_loads_pt_br():
    assert "Programação" in message("playlistNotFound")


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
