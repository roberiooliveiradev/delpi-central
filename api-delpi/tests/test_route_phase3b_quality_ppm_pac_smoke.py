"""Smoke — PPM, NC series e PAC restante (tags, delete action, exports PDF)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_Q = "app.interface.http.routes.quality.quality_router"
_PPM = "app.interface.http.routes.quality.ppm_routes"
_PAC_R = "app.interface.http.routes.quality.action_plans_read_router"
_PAC_I = "app.interface.http.routes.quality.action_plans_intelligence_router"


@patch(f"{_Q}.build_get_nonconformity_series_use_case")
def test_get_nonconformity_series_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_router import get_nonconformity_series

    result = MagicMock()
    result.to_dict.return_value = {"points": []}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))
    response = get_nonconformity_series(
        type="all",
        granularity="month",
        branch=None,
        date_start=None,
        date_end=None,
        status=None,
        item_code=None,
        description=None,
    )
    assert_envelope_meta(body_json(response), operation_id="get_nonconformity_series")


@patch(f"{_PPM}.build_list_ppm_use_case")
def test_list_ppm_internal_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.ppm_routes import list_internal_ppm

    result = MagicMock()
    result.to_dict.return_value = {"items": [], "page": 1, "total": 0}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))
    response = list_internal_ppm(
        branch=None,
        date_start=None,
        date_end=None,
        page=None,
        page_size=None,
        product_prefix=None,
    )
    assert_envelope_meta(body_json(response), operation_id="list_ppm_internal")


@patch(f"{_PPM}.build_list_ppm_use_case")
def test_list_ppm_external_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.ppm_routes import list_external_ppm

    result = MagicMock()
    result.to_dict.return_value = {"items": [], "page": 1, "total": 0}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))
    response = list_external_ppm(
        branch=None,
        date_start=None,
        date_end=None,
        page=None,
        page_size=None,
        product_prefix=None,
    )
    assert_envelope_meta(body_json(response), operation_id="list_ppm_external")


def test_suggest_evidence_tags_returns_meta() -> None:
    from app.interface.http.routes.quality.action_plans_intelligence_router import (
        SuggestEvidenceTagsBody,
        suggest_evidence_tags,
    )

    response = suggest_evidence_tags(
        body=SuggestEvidenceTagsBody(description="foto parafuso")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="suggest_quality_action_plan_evidence_tags",
    )


@pytest.mark.asyncio
@patch(f"{_PAC_I}.PacEvidenceImageOcrService.extract_text_from_bytes")
async def test_suggest_evidence_tags_from_image_returns_meta(mock_ocr) -> None:
    from app.interface.http.routes.quality.action_plans_intelligence_router import (
        suggest_evidence_tags_from_image,
    )

    mock_ocr.return_value = {"text": "parafuso", "used": True, "reason": "ok"}

    async def _read():
        return b"fake-image"

    upload = MagicMock()
    upload.filename = "ev.jpg"
    upload.content_type = "image/jpeg"
    upload.read = _read
    response = await suggest_evidence_tags_from_image(
        file=upload, file_name="ev.jpg", description=None
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="suggest_quality_action_plan_evidence_tags_from_image",
    )


@patch(f"{_PAC_R}.get_current_user", return_value=MagicMock(id="u1", name="User"))
@patch(f"{_PAC_R}.build_delete_plan_action_use_case")
def test_delete_plan_action_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        delete_plan_action,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": "act-1", "deleted": True})
    )
    response = delete_plan_action("plan-1", "act-1")
    assert_envelope_meta(
        body_json(response),
        operation_id="delete_quality_action_plan_action",
    )


@patch(f"{_PAC_R}.build_quality_action_plan_pdf", return_value=b"%PDF-1.4")
@patch(f"{_PAC_R}.plan_pdf_filename", return_value="plan.pdf")
@patch(f"{_PAC_R}.build_quality_action_plan_read_repository")
def test_export_plan_pdf_covered(mock_repo, _fn, _pdf) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import export_plan_pdf

    mock_repo.return_value = MagicMock(
        get_plan_detail=MagicMock(return_value={"plan": {"id": "plan-1"}})
    )
    response = export_plan_pdf("plan-1")
    assert response is not None
    assert response.media_type == "application/pdf"
    assert "export_quality_action_plan_pdf"


@patch(f"{_PAC_R}.build_rnc_8d_pdf", return_value=b"%PDF-1.4")
@patch(f"{_PAC_R}.rnc_8d_pdf_filename", return_value="rnc.pdf")
@patch(f"{_PAC_R}.build_quality_action_plan_read_repository")
def test_export_rnc_8d_pdf_covered(mock_repo, _fn, _pdf) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import export_rnc_8d_pdf

    mock_repo.return_value = MagicMock(
        get_plan_detail=MagicMock(return_value={"plan": {"id": "plan-1"}})
    )
    response = export_rnc_8d_pdf("plan-1")
    assert response is not None
    assert response.media_type == "application/pdf"
    assert "export_quality_action_plan_rnc_8d_pdf"
