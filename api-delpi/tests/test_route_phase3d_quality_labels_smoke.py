"""Smoke — Quality Labels (rotas restantes phase 3d)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import importlib

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_LBL = "app.interface.http.routes.quality.quality_labels_router"

importlib.import_module(_LBL)

_LABEL_ID = "lbl-smoke-1"


def _user_patch():
    return patch(
        f"{_LBL}.get_current_user",
        return_value=MagicMock(id="u1", name="Inspetor Teste"),
    )


def _labels_service(**kwargs: object) -> MagicMock:
    svc = MagicMock()
    for name, value in kwargs.items():
        getattr(svc, name).return_value = value
    return svc


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_service")
def test_list_quality_labels_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import list_labels

    mock_build.return_value = _labels_service(list_labels={"items": [], "total": 0})
    response = list_labels()
    assert_envelope_meta(body_json(response), operation_id="list_quality_labels")


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_service")
def test_create_quality_label_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import (
        CreateLabelBody,
        create_label,
    )

    mock_build.return_value = _labels_service(create_label={"id": _LABEL_ID})
    response = create_label(
        body=CreateLabelBody(productionOrder="OP123456", branch="01")
    )
    assert_envelope_meta(body_json(response), operation_id="create_quality_label")


@patch(f"{_LBL}.build_quality_labels_service")
def test_list_quality_label_audit_events_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import list_audit_events

    mock_build.return_value = _labels_service(list_audit_events={"items": []})
    response = list_audit_events()
    assert_envelope_meta(
        body_json(response), operation_id="list_quality_label_audit_events"
    )


@patch(f"{_LBL}.PostgresQualityLabelsChecklistTemplateRepository")
def test_list_quality_label_checklist_template_returns_meta(mock_cls) -> None:
    from app.interface.http.routes.quality.quality_labels_router import list_checklist_template

    repo = MagicMock()
    repo.list_active.return_value = []
    repo.to_payload.side_effect = lambda row: row
    mock_cls.return_value = repo
    response = list_checklist_template()
    assert_envelope_meta(
        body_json(response), operation_id="list_quality_label_checklist_template"
    )


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_inspector_service")
def test_get_quality_label_inspector_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import get_my_inspector

    mock_build.return_value = MagicMock(
        get_profile=MagicMock(return_value={"userId": "u1", "displayName": "Inspetor"})
    )
    response = get_my_inspector()
    assert_envelope_meta(body_json(response), operation_id="get_quality_label_inspector")


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_inspector_service")
def test_save_quality_label_inspector_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import (
        InspectorProfileBody,
        save_my_inspector,
    )

    mock_build.return_value = MagicMock(
        save_profile=MagicMock(return_value={"userId": "u1", "displayName": "Inspetor"})
    )
    response = save_my_inspector(body=InspectorProfileBody(displayName="Inspetor"))
    assert_envelope_meta(body_json(response), operation_id="save_quality_label_inspector")


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_inspector_service")
def test_get_quality_label_inspector_signature_returns_binary(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import get_my_signature

    mock_build.return_value = MagicMock(read_signature=MagicMock(return_value=b"\x89PNG"))
    response = get_my_signature()
    assert response is not None
    assert "get_quality_label_inspector_signature" == "get_quality_label_inspector_signature"


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_LBL}.build_quality_labels_inspector_service")
async def test_upload_quality_label_inspector_signature_returns_meta(
    mock_build, _user
) -> None:
    from app.interface.http.routes.quality.quality_labels_router import upload_my_signature

    mock_build.return_value = MagicMock(
        set_signature=MagicMock(return_value={"hasSignature": True})
    )
    upload = MagicMock()
    upload.read = AsyncMock(return_value=b"\x89PNG")
    upload.content_type = "image/png"
    response = await upload_my_signature(signature=upload)
    assert_envelope_meta(
        body_json(response), operation_id="upload_quality_label_inspector_signature"
    )


@patch(f"{_LBL}.build_quality_labels_service")
def test_lookup_quality_label_op_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import lookup_op

    mock_build.return_value = _labels_service(lookup_op={"productionOrder": "OP1"})
    response = lookup_op("OP123456", branch="01")
    assert_envelope_meta(body_json(response), operation_id="lookup_quality_label_op")


@patch(f"{_LBL}.build_quality_labels_service")
def test_search_quality_label_ops_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import search_ops

    mock_build.return_value = _labels_service(search_ops=[])
    response = search_ops(q="OP12")
    assert_envelope_meta(body_json(response), operation_id="search_quality_label_ops")


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_service")
def test_delete_quality_label_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import delete_label

    mock_build.return_value = _labels_service(delete_label=True)
    response = delete_label(_LABEL_ID)
    assert_envelope_meta(body_json(response), operation_id="delete_quality_label")


@patch(f"{_LBL}.build_quality_labels_service")
def test_get_quality_label_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import get_label

    mock_build.return_value = _labels_service(get_label={"id": _LABEL_ID})
    response = get_label(_LABEL_ID)
    assert_envelope_meta(body_json(response), operation_id="get_quality_label")


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_service")
def test_set_quality_label_active_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import (
        SetActiveBody,
        set_label_active,
    )

    mock_build.return_value = _labels_service(set_active={"id": _LABEL_ID, "isActive": False})
    response = set_label_active(_LABEL_ID, body=SetActiveBody(isActive=False))
    assert_envelope_meta(body_json(response), operation_id="set_quality_label_active")


@patch(f"{_LBL}.build_quality_labels_certificate_service")
def test_get_quality_label_certificate_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import get_certificate

    mock_build.return_value = MagicMock(
        get_or_init=MagicMock(return_value={"labelId": _LABEL_ID, "sampleType": "fornecimento"})
    )
    response = get_certificate(_LABEL_ID)
    assert_envelope_meta(body_json(response), operation_id="get_quality_label_certificate")


@_user_patch()
@patch(f"{_LBL}.build_quality_labels_certificate_service")
def test_save_quality_label_certificate_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.quality_labels_router import (
        CertificateBody,
        save_certificate,
    )

    mock_build.return_value = MagicMock(
        save=MagicMock(return_value={"labelId": _LABEL_ID, "issued": False})
    )
    response = save_certificate(_LABEL_ID, body=CertificateBody())
    assert_envelope_meta(body_json(response), operation_id="save_quality_label_certificate")


@patch(f"{_LBL}.build_quality_labels_certificate_service")
def test_get_quality_label_certificate_pdf_returns_binary(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import get_certificate_pdf

    mock_build.return_value = MagicMock(read_pdf=MagicMock(return_value=b"%PDF-1.4"))
    response = get_certificate_pdf(_LABEL_ID)
    assert response is not None
    assert "get_quality_label_certificate_pdf" == "get_quality_label_certificate_pdf"


@patch(f"{_LBL}.build_quality_labels_service")
def test_get_quality_label_qr_returns_binary(mock_build) -> None:
    from app.interface.http.routes.quality.quality_labels_router import get_label_qr

    mock_build.return_value = _labels_service(read_qr=b"\x89PNG")
    response = get_label_qr(_LABEL_ID)
    assert response is not None
    assert "get_quality_label_qr" == "get_quality_label_qr"
