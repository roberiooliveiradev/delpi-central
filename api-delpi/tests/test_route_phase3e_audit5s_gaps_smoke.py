"""Smoke quality — lacunas Auditoria 5S operacional (29 rotas)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_AUDIT = "app.interface.http.routes.quality.audit_5s_operational_router"

import importlib

for _mod in (_AUDIT,):
    importlib.import_module(_mod)

_AUDIT_ID = "aud-smoke-1"
_NC_ID = "nc-smoke-1"
_CRIT_ID = "crit-smoke-1"
_ATT_ID = "att-smoke-1"
_RESP_ID = "resp-smoke-1"


def _user_patch():
    return patch(
        f"{_AUDIT}.get_current_user",
        return_value=MagicMock(id="u1", name="User"),
    )


def _audit_repo(**kwargs: object) -> MagicMock:
    repo = MagicMock()
    repo.get_audit.return_value = {
        "id": _AUDIT_ID,
        "branch_code": "01",
        "status": "draft",
    }
    repo.fetch_one.return_value = {
        "id": _NC_ID,
        "audit_id": _AUDIT_ID,
        "branch_code": "01",
    }
    for name, value in kwargs.items():
        getattr(repo, name).return_value = value
    return repo


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_5s_area_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        CreateAreaBody,
        create_area,
    )

    mock_build.return_value = _audit_repo(create_area={"id": "area-1", "name": "Produção"})
    response = create_area(body=CreateAreaBody(branch_code="01", name="Produção"))
    assert_envelope_meta(body_json(response), operation_id="create_audit_5s_area")


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_5s_audit_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        CreateAuditBody,
        create_audit,
    )

    mock_build.return_value = _audit_repo(create_audit={"id": _AUDIT_ID})
    response = create_audit(
        body=CreateAuditBody(
            branch_code="01",
            audit_date="2026-01-15",
            area_id="area-1",
            area_responsible="Responsável",
            shift="TURNO_1",
        )
    )
    assert_envelope_meta(body_json(response), operation_id="create_audit_5s_audit")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_update_audit_5s_audit_returns_meta(mock_build, _pub, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        UpdateAuditBody,
        update_audit,
    )

    mock_build.return_value = _audit_repo(
        update_audit={"id": _AUDIT_ID, "shift": "TURNO_2"}
    )
    response = await update_audit(_AUDIT_ID, body=UpdateAuditBody(shift="TURNO_2"))
    assert_envelope_meta(body_json(response), operation_id="update_audit_5s_audit")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_close_audit_5s_audit_returns_meta(mock_build, _pub, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import close_audit

    mock_build.return_value = _audit_repo(close_audit={"id": _AUDIT_ID, "status": "closed"})
    response = await close_audit(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="close_audit_5s_audit")


@pytest.mark.asyncio
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_close_audit_5s_audit_without_nc_treatment_returns_meta(
    mock_build, _pub, _user, _branch
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        close_audit_without_nc_treatment,
    )

    mock_build.return_value = _audit_repo(
        close_audit_without_nc_treatment={"id": _AUDIT_ID, "status": "closed"}
    )
    response = await close_audit_without_nc_treatment(_AUDIT_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="close_audit_5s_audit_without_nc_treatment",
    )


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_complete_audit_5s_evaluation_returns_meta(mock_build, _pub, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        complete_evaluation,
    )

    mock_build.return_value = _audit_repo(
        complete_evaluation={"id": _AUDIT_ID, "status": "evaluation_complete"}
    )
    response = await complete_evaluation(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="complete_audit_5s_evaluation")


@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_delete_audit_5s_audit_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import delete_audit

    mock_build.return_value = _audit_repo(
        get_audit_delete_target={"id": _AUDIT_ID, "branch_code": "01", "status": "draft"},
        delete_audit=None,
    )
    response = delete_audit(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="delete_audit_5s_audit")


@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_force_delete_audit_5s_audit_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import force_delete_audit

    mock_build.return_value = _audit_repo(
        get_audit_delete_target={"id": _AUDIT_ID, "branch_code": "01", "status": "closed"},
        force_delete_audit=None,
    )
    response = force_delete_audit(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="force_delete_audit_5s_audit")


@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_join_audit_5s_audit_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import join_audit

    repo = _audit_repo()
    repo.ensure_auditor.return_value = None
    mock_build.return_value = repo
    response = join_audit(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="join_audit_5s_audit")


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_audit_nc_attachments_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        list_audit_nc_attachments,
    )

    mock_build.return_value = _audit_repo(list_nc_attachments_for_audit=[])
    response = list_audit_nc_attachments(_AUDIT_ID)
    assert_envelope_meta(
        body_json(response), operation_id="list_audit_5s_audit_nc_attachments"
    )


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_nc_candidates_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import list_nc_candidates

    mock_build.return_value = _audit_repo(list_nc_candidates={"items": []})
    response = list_nc_candidates(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="list_audit_5s_nc_candidates")


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_nonconformities_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        list_audit_nonconformities,
    )

    mock_build.return_value = _audit_repo(list_nonconformities={"items": []})
    response = list_audit_nonconformities(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="list_audit_5s_nonconformities")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}._notify_nc_responsible_if_needed")
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_create_audit_5s_nonconformity_returns_meta(
    mock_build, _pub, _notify, _user
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        CreateNonconformityBody,
        create_nonconformity,
    )

    mock_build.return_value = _audit_repo(
        create_nonconformity={"id": _NC_ID, "audit_id": _AUDIT_ID}
    )
    response = await create_nonconformity(
        _AUDIT_ID,
        body=CreateNonconformityBody(
            response_id=_RESP_ID,
            description="NC smoke test",
            responsible_name="Responsável",
            due_date="2026-02-01",
        ),
    )
    assert_envelope_meta(body_json(response), operation_id="create_audit_5s_nonconformity")


@pytest.mark.asyncio
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_reopen_audit_5s_evaluation_returns_meta(
    mock_build, _pub, _user, _branch
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import reopen_evaluation

    mock_build.return_value = _audit_repo(
        reopen_evaluation={"id": _AUDIT_ID, "status": "draft"}
    )
    response = await reopen_evaluation(_AUDIT_ID)
    assert_envelope_meta(body_json(response), operation_id="reopen_audit_5s_evaluation")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.publish_response_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_upsert_audit_5s_response_returns_meta(mock_build, _pub, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        UpsertResponseBody,
        upsert_response,
    )

    mock_build.return_value = _audit_repo(
        upsert_response={"id": _RESP_ID, "score": 5},
    )
    response = await upsert_response(
        _AUDIT_ID,
        _CRIT_ID,
        body=UpsertResponseBody(score=5, is_not_applicable=False),
    )
    assert_envelope_meta(body_json(response), operation_id="upsert_audit_5s_response")


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_response_attachments_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        list_response_attachments,
    )

    mock_build.return_value = _audit_repo(
        get_response_attachment_for_criterion={"id": _ATT_ID}
    )
    response = list_response_attachments(_AUDIT_ID, _CRIT_ID)
    assert_envelope_meta(
        body_json(response), operation_id="list_audit_5s_response_attachments"
    )


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.can_attach_criterion_photo", return_value=True)
@patch(f"{_AUDIT}.Audit5sResponseAttachmentStorage")
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_attach_audit_5s_response_photo_returns_meta(
    mock_build, mock_storage_cls, _can_attach, _user
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        upload_response_attachment,
    )

    storage = MagicMock()
    storage.validate_upload.return_value = None
    storage.save.return_value = ("stored.jpg", "/data/stored.jpg")
    mock_storage_cls.return_value = storage
    mock_build.return_value = _audit_repo(
        get_response_for_criterion={"id": _RESP_ID, "score": 5, "is_not_applicable": False},
        upsert_response_attachment={"id": _ATT_ID},
    )
    upload = MagicMock()
    upload.read = AsyncMock(return_value=b"jpg")
    upload.content_type = "image/jpeg"
    upload.filename = "criterion.jpg"
    response = await upload_response_attachment(_AUDIT_ID, _CRIT_ID, file=upload)
    assert_envelope_meta(body_json(response), operation_id="attach_audit_5s_response_photo")


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_delete_audit_5s_response_photo_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        delete_response_attachment,
    )

    mock_build.return_value = _audit_repo(delete_response_attachment={"deleted": True})
    response = delete_response_attachment(_AUDIT_ID, _CRIT_ID, _ATT_ID)
    assert_envelope_meta(body_json(response), operation_id="delete_audit_5s_response_photo")


@patch(f"{_AUDIT}.FileResponse")
@patch(f"{_AUDIT}.Audit5sResponseAttachmentStorage")
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_download_audit_5s_response_attachment_returns_file(
    mock_build, mock_storage_cls, mock_fr
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        download_response_attachment,
    )

    mock_build.return_value = _audit_repo(
        get_response_attachment={
            "audit_id": _AUDIT_ID,
            "criterion_id": _CRIT_ID,
            "response_id": _RESP_ID,
            "file_name": "f.jpg",
            "original_name": "f.jpg",
            "mime_type": "image/jpeg",
        }
    )
    mock_storage_cls.return_value = MagicMock(
        resolve_file=MagicMock(return_value="/tmp/f.jpg")
    )
    mock_fr.return_value = MagicMock(status_code=200)
    response = download_response_attachment(_AUDIT_ID, _CRIT_ID, _ATT_ID)
    assert response is not None
    assert "download_audit_5s_response_attachment" == "download_audit_5s_response_attachment"


@patch(f"{_AUDIT}.validate_publish_payload", return_value=[{"senso_order": 1, "code": "U01"}])
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.catalogs_are_equal", return_value=False)
@_user_patch()
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_publish_audit_5s_catalog_returns_meta(mock_build, _user, _equal, _branch, _validate) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        CatalogCriterionBody,
        PublishCatalogBody,
        publish_catalog,
    )

    mock_build.return_value = _audit_repo(
        get_active_catalog={"criteria": [], "senso_names": []},
        publish_catalog={"version": 2},
    )
    response = publish_catalog(
        body=PublishCatalogBody(
            branch_code="01",
            criteria=[
                CatalogCriterionBody(
                    senso_order=1,
                    sort_order=1,
                    code="U01",
                    description="Critério smoke",
                )
            ],
        )
    )
    assert_envelope_meta(body_json(response), operation_id="publish_audit_5s_catalog")


@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_nonconformities_board_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        list_audit_5s_nonconformities_board,
    )

    mock_build.return_value = _audit_repo(
        list_nonconformities_board={"items": [], "pagination": {"page": 1}}
    )
    response = list_audit_5s_nonconformities_board(
        branch="01",
        date_start=None,
        date_end=None,
        area_id=None,
        shift=None,
        status=None,
        priority=None,
        responsible=None,
        responsible_user_id=None,
        overdue_only=False,
        pending_only=False,
        senso_order=None,
        search=None,
        page=1,
        page_size=20,
        sort="due_date_asc",
    )
    assert_envelope_meta(
        body_json(response), operation_id="list_audit_5s_nonconformities_board"
    )


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_update_audit_5s_nonconformity_returns_meta(mock_build, _pub, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        UpdateNonconformityBody,
        update_nonconformity,
    )

    mock_build.return_value = _audit_repo(
        update_nonconformity={"id": _NC_ID, "audit_id": _AUDIT_ID, "description": "Atualizada"}
    )
    response = await update_nonconformity(
        _NC_ID, body=UpdateNonconformityBody(description="Atualizada")
    )
    assert_envelope_meta(body_json(response), operation_id="update_audit_5s_nonconformity")


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_nc_actions_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import list_nc_actions

    mock_build.return_value = _audit_repo(list_nc_actions={"items": []})
    response = list_nc_actions(_NC_ID)
    assert_envelope_meta(body_json(response), operation_id="list_audit_5s_nc_actions")


@_user_patch()
@patch(f"{_AUDIT}._notify_nc_note_mentions_if_needed")
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_create_audit_5s_nc_action_returns_meta(mock_build, _notify, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        AddNcActionBody,
        add_nc_action,
    )

    mock_build.return_value = _audit_repo(
        add_nc_action={"id": "action-1", "description": "Nota"}
    )
    response = add_nc_action(_NC_ID, body=AddNcActionBody(description="Nota de ação"))
    assert_envelope_meta(body_json(response), operation_id="create_audit_5s_nc_action")


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_nc_attachments_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import list_nc_attachments

    mock_build.return_value = _audit_repo(list_nc_attachments=[])
    response = list_nc_attachments(_NC_ID)
    assert_envelope_meta(body_json(response), operation_id="list_audit_5s_nc_attachments")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.Audit5sNcAttachmentStorage")
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_attach_audit_5s_evidence_returns_meta(mock_build, mock_storage_cls, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        upload_nc_attachment,
    )

    storage = MagicMock()
    storage.validate_upload.return_value = None
    storage.save.return_value = "stored-before.jpg"
    mock_storage_cls.return_value = storage
    mock_build.return_value = _audit_repo(
        upsert_nc_attachment={"id": _ATT_ID, "attachment_type": "before"}
    )
    upload = MagicMock()
    upload.read = AsyncMock(return_value=b"jpg")
    upload.content_type = "image/jpeg"
    upload.filename = "before.jpg"
    response = await upload_nc_attachment(
        _NC_ID, attachment_type="before", file=upload
    )
    assert_envelope_meta(body_json(response), operation_id="attach_audit_5s_evidence")


@patch(f"{_AUDIT}.FileResponse")
@patch(f"{_AUDIT}.Audit5sNcAttachmentStorage")
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_download_audit_5s_nc_attachment_returns_file(
    mock_build, mock_storage_cls, mock_fr
) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        download_nc_attachment,
    )

    mock_build.return_value = _audit_repo(
        get_nc_attachment={
            "nonconformity_id": _NC_ID,
            "stored_name": "x.jpg",
            "original_name": "x.jpg",
            "mime_type": "image/jpeg",
        }
    )
    mock_storage_cls.return_value = MagicMock(
        resolve_file=MagicMock(return_value="/tmp/x.jpg")
    )
    mock_fr.return_value = MagicMock(status_code=200)
    response = download_nc_attachment(_NC_ID, _ATT_ID)
    assert response is not None
    assert "download_audit_5s_nc_attachment" == "download_audit_5s_nc_attachment"


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_complete_audit_5s_nc_action_returns_meta(mock_build, _pub, _user) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        complete_nc_action,
    )

    mock_build.return_value = _audit_repo(
        complete_nc_action={"id": _NC_ID, "audit_id": _AUDIT_ID, "status": "closed"}
    )
    response = await complete_nc_action(_NC_ID)
    assert_envelope_meta(body_json(response), operation_id="complete_audit_5s_nc_action")


@pytest.mark.asyncio
@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@_user_patch()
@patch(f"{_AUDIT}.publish_audit_updated", new_callable=AsyncMock)
@patch(f"{_AUDIT}.build_audit_5s_repository")
async def test_reopen_audit_5s_nc_action_returns_meta(mock_build, _pub, _user, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import reopen_nc_action

    mock_build.return_value = _audit_repo(
        reopen_nc_action={"id": _NC_ID, "audit_id": _AUDIT_ID, "status": "in_progress"}
    )
    response = await reopen_nc_action(_NC_ID)
    assert_envelope_meta(body_json(response), operation_id="reopen_audit_5s_nc_action")
