"""Smoke de contrato, autorização e regressão do router de Engenharia."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from app.interface.http.routes.engineering.engineering_router import router as engineering_router
from app.interface.http.routes.engineering.metallographic_reports_router import (
    MetallographicReportWriteBody,
    copy_metallographic_report,
    create_metallographic_report,
    delete_metallographic_report,
    export_metallographic_report_pdf,
    get_metallographic_image,
    get_metallographic_report,
    list_metallographic_reports,
    put_metallographic_image,
    router,
    update_metallographic_report,
)
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS
from delpi_auth.request_context import clear_current_user, set_current_user
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_REPORT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
_ROUTER = "app.interface.http.routes.engineering.metallographic_reports_router"
_OPERATION_IDS = {
    "engineering_create_metallographic_report",
    "engineering_list_metallographic_reports",
    "engineering_get_metallographic_report",
    "engineering_update_metallographic_report",
    "engineering_delete_metallographic_report",
    "engineering_copy_metallographic_report",
    "engineering_put_metallographic_image",
    "engineering_get_metallographic_image",
    "engineering_delete_metallographic_image",
    "engineering_export_metallographic_report_pdf",
}


def _user(*permissions: str) -> SimpleNamespace:
    return SimpleNamespace(
        id="user-1",
        email="user-1@delpi",
        permissions=list(permissions),
        is_superadmin=False,
        rbac_unavailable=False,
    )


def _report() -> dict:
    return {
        "id": str(_REPORT_ID),
        "report_number": "MET-2026-000001",
        "version": 1,
        "status": "draft",
    }


@pytest.fixture(autouse=True)
def _clear_user():
    clear_current_user()
    yield
    clear_current_user()


def test_operation_ids_are_explicit_and_registered() -> None:
    found = {route.operation_id for route in router.routes}
    assert found == _OPERATION_IDS
    for operation_id in _OPERATION_IDS:
        assert operation_id in ROUTE_CONTRACTS
    child_paths = {route.path for route in router.routes}
    assert "/metallographic-reports" in child_paths
    parent_paths = {getattr(route, "path", "") for route in engineering_router.routes}
    assert any("metallographic-reports" in path for path in parent_paths)
    assert any("/lmps" in path for path in parent_paths)


def test_unauthenticated_and_forbidden_and_read_only() -> None:
    body = MetallographicReportWriteBody()
    with patch("delpi_auth.authorization.resolve_user_context", return_value=None):
        with pytest.raises(Exception, match="Unauthorized"):
            create_metallographic_report(body=body, idempotency_key="create-key-01")

    reader = _user("metalography.view")
    with patch("delpi_auth.authorization.resolve_user_context", return_value=reader):
        with pytest.raises(Exception, match="Forbidden"):
            update_metallographic_report(
                report_id=_REPORT_ID,
                body=MetallographicReportWriteBody(revision="01"),
                if_match='"1"',
            )
        with pytest.raises(Exception, match="Forbidden"):
            export_metallographic_report_pdf(report_id=_REPORT_ID)

    stranger = _user("dashboard-engineering.view")
    with patch("delpi_auth.authorization.resolve_user_context", return_value=stranger):
        with pytest.raises(Exception, match="Forbidden"):
            get_metallographic_report(report_id=_REPORT_ID)
        with pytest.raises(Exception, match="Forbidden"):
            get_metallographic_image(report_id=_REPORT_ID, slot="original")


@patch(f"{_ROUTER}.MetallographicReportService")
def test_read_only_user_can_get_by_id(mock_service) -> None:
    service = MagicMock()
    service.get.return_value = _report()
    mock_service.return_value = service
    set_current_user(_user("metalography.view"))
    response = get_metallographic_report(report_id=_REPORT_ID)
    body = body_json(response)
    assert_envelope_meta(body, operation_id="engineering_get_metallographic_report", shape="scalar")
    assert response.headers["etag"] == '"1"'
    service.get.assert_called_once_with(str(_REPORT_ID))


@patch(f"{_ROUTER}.MetallographicReportService")
def test_create_list_update_delete_copy_envelope(mock_service) -> None:
    service = MagicMock()
    service.create.return_value = _report()
    service.list_reports.return_value = {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
        "has_next": False,
    }
    service.update.return_value = {**_report(), "version": 2}
    service.delete.return_value = {"id": str(_REPORT_ID), "deleted": True, "version": 2}
    service.copy.return_value = {**_report(), "id": "copy-id", "version": 1}
    mock_service.return_value = service
    set_current_user(_user(
        "metalography.view",
        "metalography.create",
        "metalography.edit",
        "metalography.delete",
    ))
    created = body_json(create_metallographic_report(
        body=MetallographicReportWriteBody(),
        idempotency_key="create-key-01",
    ))
    assert_envelope_meta(created, operation_id="engineering_create_metallographic_report", shape="scalar")
    listed = body_json(list_metallographic_reports(
        page=1,
        page_size=20,
        sort="created_at_desc",
        report_date_from=None,
        report_date_to=None,
        report_number=None,
        terminal_code="TERM",
        terminal_part_number=None,
        product_harness=None,
        cable=None,
        conductor_section=None,
        applicator_tool=None,
        press_equipment=None,
        batch_production_order=None,
        sample_identification=None,
        conclusion_result=None,
    ))
    assert_envelope_meta(listed, operation_id="engineering_list_metallographic_reports", shape="paged_list")
    assert listed["data"]["page_size"] == 20
    updated = body_json(update_metallographic_report(
        report_id=_REPORT_ID,
        body=MetallographicReportWriteBody(revision="01"),
        if_match='"1"',
    ))
    assert_envelope_meta(updated, operation_id="engineering_update_metallographic_report", shape="scalar")
    deleted = body_json(delete_metallographic_report(report_id=_REPORT_ID, if_match='"1"'))
    assert_envelope_meta(deleted, operation_id="engineering_delete_metallographic_report", shape="scalar")
    assert deleted["data"]["deleted"] is True
    copied = body_json(copy_metallographic_report(report_id=_REPORT_ID, idempotency_key="copy-key-0001"))
    assert_envelope_meta(copied, operation_id="engineering_copy_metallographic_report", shape="scalar")


def test_write_model_rejects_server_owned_field() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MetallographicReportWriteBody.model_validate({"report_number": "MET-1", "created_by": "intruso"})


@patch(f"{_ROUTER}.MetallographicReportService")
def test_pdf_response_is_binary_and_authorized(mock_service) -> None:
    service = MagicMock()
    service.export_pdf.return_value = {
        "content": b"%PDF-1.4 test",
        "filename": "metalografia-MET-2026-000001.pdf",
        "etag": '"3"',
    }
    mock_service.return_value = service
    set_current_user(_user("metalography.export"))
    response = export_metallographic_report_pdf(report_id=_REPORT_ID)
    assert response.media_type == "application/pdf"
    assert response.body == b"%PDF-1.4 test"
    assert "metalografia-MET-2026-000001.pdf" in response.headers["content-disposition"]


@patch(f"{_ROUTER}.MetallographicReportService")
def test_image_put_returns_envelope(mock_service) -> None:
    service = MagicMock()
    service.put_image.return_value = {
        "slot": "original",
        "content_type": "image/png",
        "size_bytes": 10,
        "sha256": "abc",
        "version": 2,
        "updated_at": "2026-10-21T00:00:00+00:00",
    }
    mock_service.return_value = service
    set_current_user(_user("metalography.edit"))
    upload = SimpleNamespace(content_type="image/png", file=SimpleNamespace(read=lambda _n: b"png"))
    response = put_metallographic_image(
        report_id=_REPORT_ID,
        slot="original",
        if_match='"1"',
        file=upload,
    )
    body = body_json(response)
    assert_envelope_meta(body, operation_id="engineering_put_metallographic_image", shape="scalar")
    assert body["data"]["slot"] == "original"
