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
    assert perms.permission_code("view", "01") == "cipa.minutes.view.filial-01"
    assert perms.permission_code("admin", "02") == "cipa.admin.filial-02"
    assert perms.normalize_unit_code("01") == "01"
    assert perms.normalize_unit_code("99") is None


def test_content_editable_flags():
    assert MinuteStatusTransitionService.can_edit_content("draft")
    assert not MinuteStatusTransitionService.can_edit_content("awaiting_signatures")
    assert MinuteStatusTransitionService.requires_new_version_for_content_change(
        "awaiting_signatures"
    )
