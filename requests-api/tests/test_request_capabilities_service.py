from __future__ import annotations

from uuid import uuid4

from requests_app.domain.entities import Actor, Request
from requests_app.domain.services.request_capabilities_service import (
    resolve_request_capabilities,
)

_TERMINAL_WF = {"terminalStatuses": ["completed", "cancelled", "rejected"]}


def _actor(**kwargs) -> Actor:
    base = dict(
        user_id="u-1",
        user_name="User",
        has_access=True,
        has_create=False,
        has_process=False,
        has_manage=False,
        has_view_all=False,
    )
    base.update(kwargs)
    return Actor(**base)


def _request(*, owner: str = "u-owner", status: str = "submitted") -> Request:
    return Request(
        id=uuid4(),
        request_number="REQ-2026-000010",
        request_type_id=uuid4(),
        type_code="invoice-issuance",
        status=status,
        created_by_user_id=owner,
        created_by_name="Owner",
        version=1,
    )


def test_owner_submitted_cannot_manage_attachments_on_detail():
    """Capability is presentation-only: create bootstrap uses use-case, not this flag."""
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="submitted"),
        actor=_actor(user_id="u-owner", has_create=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_comment"] is True
    assert caps["can_upload_attachment"] is False
    assert caps["can_upload_artifact"] is False


def test_owner_needs_information_can_manage_attachments():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="needs_information"),
        actor=_actor(user_id="u-owner", has_create=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_upload_attachment"] is True
    assert caps["can_upload_artifact"] is False


def test_processor_can_upload_artifact_not_attachment():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="in_progress"),
        actor=_actor(user_id="u-proc", has_process=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_comment"] is True
    assert caps["can_upload_attachment"] is False
    assert caps["can_upload_artifact"] is True


def test_manage_same_as_process_for_artifacts():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="needs_information"),
        actor=_actor(user_id="u-mgr", has_manage=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_upload_attachment"] is False
    assert caps["can_upload_artifact"] is True


def test_view_all_readonly_can_comment_not_upload():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="needs_information"),
        actor=_actor(user_id="u-view", has_view_all=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_comment"] is True
    assert caps["can_upload_attachment"] is False
    assert caps["can_upload_artifact"] is False


def test_processor_cannot_upload_artifact_when_terminal():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="completed"),
        actor=_actor(user_id="u-proc", has_process=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_upload_artifact"] is False


def test_owner_terminal_cannot_upload_attachment():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="cancelled"),
        actor=_actor(user_id="u-owner", has_create=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_upload_attachment"] is False
    assert caps["can_comment"] is True


def test_owner_in_progress_cannot_manage_attachments():
    caps = resolve_request_capabilities(
        _request(owner="u-owner", status="in_progress"),
        actor=_actor(user_id="u-owner", has_create=True),
        workflow=_TERMINAL_WF,
    )
    assert caps["can_upload_attachment"] is False
