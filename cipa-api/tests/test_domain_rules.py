from cipa_app.domain.services.minute_status_transition_service import (
    MinuteStatusTransitionError,
    MinuteStatusTransitionService,
)
from cipa_app.application.services.html_sanitizer import CipaHtmlSanitizer
from cipa_app.application.security import cipa_permissions as perms


def test_health_import():
    from cipa_app.main import app

    assert app.title == "CIPA API"


def test_allowed_transitions():
    MinuteStatusTransitionService.assert_transition("draft", "awaiting_signatures")
    MinuteStatusTransitionService.assert_transition("awaiting_signatures", "partially_signed")
    MinuteStatusTransitionService.assert_transition("signed", "finalized")
    try:
        MinuteStatusTransitionService.assert_transition("finalized", "draft")
        assert False, "should raise"
    except MinuteStatusTransitionError:
        pass


def test_signature_progress_status():
    assert (
        MinuteStatusTransitionService.status_after_signature_progress(
            signed_count=1, required_count=3
        )
        == "partially_signed"
    )
    assert (
        MinuteStatusTransitionService.status_after_signature_progress(
            signed_count=3, required_count=3
        )
        == "signed"
    )
    assert (
        MinuteStatusTransitionService.status_after_signature_progress(
            signed_count=1, required_count=3, refused=True
        )
        == "in_review"
    )


def test_html_sanitizer_strips_script():
    cleaned = CipaHtmlSanitizer.sanitize('<p>ok</p><script>alert(1)</script><a href="javascript:x">x</a>')
    assert "<script" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()
    assert "ok" in cleaned


def test_permission_codes():
    assert perms.unit_permission_code("01") == "cipa.unit.filial-01"
    assert perms.action_permission_code("create") == "cipa.manage"
    assert perms.action_permission_code("sign") == "cipa.sign"
    assert perms.normalize_unit_code("01") == "01"
    assert perms.normalize_unit_code("99") is None


def test_has_unit_action_requires_unit_and_action():
    from types import SimpleNamespace

    viewer = SimpleNamespace(
        permissions=["cipa.view", "cipa.unit.filial-01"],
        is_superadmin=False,
    )
    signer = SimpleNamespace(
        permissions=["cipa.sign", "cipa.unit.filial-02"],
        is_superadmin=False,
    )
    admin = SimpleNamespace(permissions=["cipa.admin"], is_superadmin=False)

    assert perms.has_unit_action(viewer, "view", "01")
    assert not perms.has_unit_action(viewer, "create", "01")
    assert not perms.has_unit_action(viewer, "view", "02")
    assert perms.has_unit_action(signer, "sign", "02")
    assert not perms.has_unit_action(signer, "view", "02")
    assert perms.has_unit_action(admin, "finalize", "02")


def test_build_access_payload():
    from types import SimpleNamespace

    viewer = SimpleNamespace(
        permissions=["cipa.view", "cipa.unit.filial-01"],
        is_superadmin=False,
    )
    payload = perms.build_access_payload(viewer)
    assert payload["can_view"] is True
    assert payload["can_manage"] is False
    assert len(payload["units"]) == 1
    assert payload["units"][0]["id"] == "01"
    assert payload["units"][0]["view"] is True
    assert payload["units"][0]["manage"] is False


def test_unit_codes_for_read():
    from types import SimpleNamespace

    manager = SimpleNamespace(
        permissions=["cipa.manage", "cipa.unit.filial-02"],
        is_superadmin=False,
    )
    assert perms.unit_codes_for_read(manager) == ["02"]


def test_content_editable_flags():
    assert MinuteStatusTransitionService.can_edit_content("draft")
    assert not MinuteStatusTransitionService.can_edit_content("awaiting_signatures")
    assert MinuteStatusTransitionService.requires_new_version_for_content_change(
        "awaiting_signatures"
    )
