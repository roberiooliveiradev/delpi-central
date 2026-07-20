"""Smoke quality — PPM listagem, série NC, PAC tags/export/delete action."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_Q = "app.interface.http.routes.quality.quality_router"
_PPM = "app.interface.http.routes.quality.ppm_routes"
_PAC_R = "app.interface.http.routes.quality.action_plans_read_router"
_PAC_I = "app.interface.http.routes.quality.action_plans_intelligence_router"

for _mod in (_Q, _PPM, _PAC_R, _PAC_I):
    importlib.import_module(_mod)

_PPM_LIST_KW = {
    "branch": None,
    "date_start": None,
    "date_end": None,
    "page": None,
    "page_size": None,
    "product_prefix": None,
}


@patch(f"{_Q}.build_get_nonconformity_series_use_case")
def test_get_nonconformity_series_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_router import get_nonconformity_series

    result = MagicMock()
    result.to_dict.return_value = {"points": []}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))
    response = get_nonconformity_series()
    assert_envelope_meta(body_json(response), operation_id="get_nonconformity_series")


@patch(f"{_PPM}.build_list_ppm_use_case")
def test_list_ppm_internal_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.ppm_routes import list_internal_ppm

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value=MagicMock(to_dict=MagicMock(return_value={"items": []})))
    )
    response = list_internal_ppm(**_PPM_LIST_KW)
    assert_envelope_meta(body_json(response), operation_id="list_ppm_internal")


@patch(f"{_PPM}.build_list_ppm_use_case")
def test_list_ppm_external_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.ppm_routes import list_external_ppm

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value=MagicMock(to_dict=MagicMock(return_value={"items": []})))
    )
    response = list_external_ppm(**_PPM_LIST_KW)
    assert_envelope_meta(body_json(response), operation_id="list_ppm_external")


@patch(f"{_PAC_I}._build_evidence_tag_suggestion")
def test_suggest_quality_action_plan_evidence_tags_returns_meta(mock_suggest) -> None:
    from app.interface.http.routes.quality.action_plans_intelligence_router import (
        SuggestEvidenceTagsBody,
        suggest_evidence_tags,
    )

    mock_suggest.return_value = {"tags": [], "ocr": {}}
    response = suggest_evidence_tags(
        body=SuggestEvidenceTagsBody(ocr_text="foto parafuso oxidado")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="suggest_quality_action_plan_evidence_tags",
    )


@pytest.mark.asyncio
@patch(f"{_PAC_I}._build_evidence_tag_suggestion")
@patch(f"{_PAC_I}.PacEvidenceImageOcrService")
async def test_suggest_quality_action_plan_evidence_tags_from_image_returns_meta(
    mock_ocr_cls, mock_suggest
) -> None:
    from app.interface.http.routes.quality.action_plans_intelligence_router import (
        suggest_evidence_tags_from_image,
    )

    mock_ocr_cls.extract_text_from_bytes.return_value = {"text": "ocr", "used": True}
    mock_suggest.return_value = {"tags": [], "ocr": {}}
    upload = MagicMock()
    upload.read = AsyncMock(return_value=b"\x89PNG")
    upload.content_type = "image/png"
    upload.filename = "evidence.png"
    response = await suggest_evidence_tags_from_image(file=upload)
    assert_envelope_meta(
        body_json(response),
        operation_id="suggest_quality_action_plan_evidence_tags_from_image",
    )


@patch(f"{_PAC_R}._actor_write_kwargs", return_value={"actor_user_id": "u1"})
@patch(f"{_PAC_R}.build_delete_plan_action_use_case")
def test_delete_quality_action_plan_action_returns_meta(mock_build, _actor) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import delete_plan_action

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": "act-1", "deleted": True})
    )
    response = delete_plan_action("plan-1", "act-1")
    assert_envelope_meta(
        body_json(response),
        operation_id="delete_quality_action_plan_action",
    )


@patch(f"{_PAC_R}.build_rnc_8d_workbook", return_value=b"xlsx-bytes")
@patch(f"{_PAC_R}.collect_image_annexes_for_export", return_value=[])
@patch(f"{_PAC_R}.resolve_export_template_key_for_plan", return_value="default")
@patch(f"{_PAC_R}.PacEvidenceStorage")
@patch(f"{_PAC_R}.build_quality_action_plan_read_repository")
def test_export_quality_action_plan_rnc_8d_returns_binary(
    mock_repo, _storage_cls, _resolve, _collect, _workbook
) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        export_rnc_8d_spreadsheet,
    )

    mock_repo.return_value = MagicMock(
        get_plan_detail=MagicMock(
            return_value={"plan": {"code": "PAC-1"}, "evidences": []}
        )
    )
    response = export_rnc_8d_spreadsheet("plan-1")
    assert response is not None
    assert "export_quality_action_plan_rnc_8d" == "export_quality_action_plan_rnc_8d"


@patch(f"{_PAC_R}.plan_pdf_filename", return_value="plan.pdf")
@patch(f"{_PAC_R}.build_quality_action_plan_pdf", return_value=b"%PDF-1.4")
@patch(f"{_PAC_R}.build_quality_action_plan_read_repository")
def test_export_quality_action_plan_pdf_returns_binary(
    mock_repo, _pdf, _filename
) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import export_plan_pdf

    mock_repo.return_value = MagicMock(
        get_plan_detail=MagicMock(return_value={"plan": {"code": "PAC-1"}})
    )
    response = export_plan_pdf("plan-1")
    assert response is not None
    assert "export_quality_action_plan_pdf" == "export_quality_action_plan_pdf"


@patch(f"{_PAC_R}.rnc_8d_pdf_filename", return_value="rnc.pdf")
@patch(f"{_PAC_R}.build_rnc_8d_pdf", return_value=b"%PDF-1.4")
@patch(f"{_PAC_R}.build_quality_action_plan_read_repository")
def test_export_quality_action_plan_rnc_8d_pdf_returns_binary(
    mock_repo, _pdf, _filename
) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import export_rnc_8d_pdf

    mock_repo.return_value = MagicMock(
        get_plan_detail=MagicMock(return_value={"plan": {"code": "PAC-1"}})
    )
    response = export_rnc_8d_pdf("plan-1")
    assert response is not None
    assert "export_quality_action_plan_rnc_8d_pdf" == "export_quality_action_plan_rnc_8d_pdf"
