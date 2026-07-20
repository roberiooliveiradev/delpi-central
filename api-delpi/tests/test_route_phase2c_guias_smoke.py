"""Smoke — Guias e Procedimentos (leitura + admin + mídia sem upload binário)."""

from __future__ import annotations

from uuid import uuid4
from unittest.mock import MagicMock, patch

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_READ = "app.interface.http.routes.guias_procedimentos.guias_procedimentos_router"
_ADMIN = "app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router"
_MEDIA = "app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router"

_DEPT = uuid4()
_PROC = uuid4()
_MEDIA_ID = uuid4()
_ATT = uuid4()


@patch(f"{_READ}.build_get_guias_department_by_slug_use_case")
def test_get_guias_department_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_router import (
        get_guias_department,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"slug": "qualidade", "name": "Qualidade"})
    )
    response = get_guias_department(slug="qualidade")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_guias_procedimentos_department",
    )


@patch(f"{_READ}.build_get_guias_procedure_by_slug_use_case")
def test_get_guias_procedure_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_router import (
        get_guias_procedure,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"slug": "5s", "title": "5S"})
    )
    response = get_guias_procedure(slug="5s")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_guias_procedimentos_procedure",
    )


@patch(f"{_ADMIN}.build_get_admin_department_use_case")
def test_get_admin_department_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        get_admin_department,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_DEPT), "name": "Qualidade"})
    )
    response = get_admin_department(department_id=_DEPT)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_guias_procedimentos_admin_department",
    )


@patch(f"{_ADMIN}.build_create_department_use_case")
def test_create_admin_department_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        DepartmentBody,
        create_admin_department,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_DEPT), "slug": "qualidade"})
    )
    response = create_admin_department(
        body=DepartmentBody(name="Qualidade", slug="qualidade")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_guias_procedimentos_admin_department",
    )


@patch(f"{_ADMIN}.build_update_department_use_case")
def test_update_admin_department_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        DepartmentBody,
        update_admin_department,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_DEPT), "name": "Qualidade 2"})
    )
    response = update_admin_department(
        department_id=_DEPT,
        body=DepartmentBody(name="Qualidade 2", slug="qualidade"),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_guias_procedimentos_admin_department",
    )


@patch(f"{_ADMIN}.build_list_admin_procedures_use_case")
def test_list_admin_procedures_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        list_admin_procedures,
    )

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = list_admin_procedures(department_id=None, status=None, q=None)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_guias_procedimentos_admin_procedures",
    )


@patch(f"{_ADMIN}.build_get_admin_procedure_use_case")
def test_get_admin_procedure_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        get_admin_procedure,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_PROC), "title": "Proc"})
    )
    response = get_admin_procedure(procedure_id=_PROC)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_guias_procedimentos_admin_procedure",
    )


@patch(f"{_ADMIN}.build_create_procedure_use_case")
def test_create_admin_procedure_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        ProcedureBody,
        create_admin_procedure,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_PROC), "slug": "proc"})
    )
    response = create_admin_procedure(
        body=ProcedureBody(department_id=_DEPT, title="Proc", slug="proc")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_guias_procedimentos_admin_procedure",
    )


@patch(f"{_ADMIN}.build_update_procedure_use_case")
def test_update_admin_procedure_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        ProcedureBody,
        update_admin_procedure,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_PROC), "title": "Proc 2"})
    )
    response = update_admin_procedure(
        procedure_id=_PROC,
        body=ProcedureBody(department_id=_DEPT, title="Proc 2", slug="proc"),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_guias_procedimentos_admin_procedure",
    )


@pytest.mark.parametrize(
    ("handler_name", "builder_name", "operation_id"),
    [
        (
            "publish_admin_procedure",
            "build_publish_procedure_use_case",
            "publish_guias_procedimentos_admin_procedure",
        ),
        (
            "unpublish_admin_procedure",
            "build_unpublish_procedure_use_case",
            "unpublish_guias_procedimentos_admin_procedure",
        ),
        (
            "archive_admin_procedure",
            "build_archive_procedure_use_case",
            "archive_guias_procedimentos_admin_procedure",
        ),
        (
            "restore_admin_procedure",
            "build_restore_procedure_use_case",
            "restore_guias_procedimentos_admin_procedure",
        ),
    ],
)
def test_admin_procedure_lifecycle_returns_meta(
    handler_name: str, builder_name: str, operation_id: str
) -> None:
    import app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router as mod

    handler = getattr(mod, handler_name)
    with patch(f"{_ADMIN}.{builder_name}") as mock_build:
        mock_build.return_value = MagicMock(
            execute=MagicMock(return_value={"id": str(_PROC), "status": "ok"})
        )
        response = handler(procedure_id=_PROC)
    assert_envelope_meta(body_json(response), operation_id=operation_id)


@patch(f"{_MEDIA}.build_list_admin_procedure_media_use_case")
def test_list_admin_procedure_media_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        list_admin_procedure_media,
    )

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = list_admin_procedure_media(procedure_id=_PROC)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_guias_procedimentos_admin_procedure_media",
    )


@patch(f"{_MEDIA}.build_list_admin_procedure_attachments_use_case")
def test_list_admin_procedure_attachments_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        list_admin_procedure_attachments,
    )

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = list_admin_procedure_attachments(procedure_id=_PROC)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_guias_procedimentos_admin_procedure_attachments",
    )


@patch(f"{_MEDIA}.build_list_readable_procedure_media_use_case")
def test_list_procedure_media_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        list_readable_procedure_media,
    )

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    with patch(f"{_MEDIA}._can_manage", return_value=False):
        response = list_readable_procedure_media(procedure_id=_PROC)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_guias_procedimentos_procedure_media",
    )


@patch(f"{_MEDIA}.build_list_readable_procedure_attachments_use_case")
def test_list_procedure_attachments_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        list_readable_procedure_attachments,
    )

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    with patch(f"{_MEDIA}._can_manage", return_value=False):
        response = list_readable_procedure_attachments(procedure_id=_PROC)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_guias_procedimentos_procedure_attachments",
    )


@patch(f"{_MEDIA}.build_create_external_video_use_case")
def test_create_external_video_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        ExternalVideoBody,
        create_external_video,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_MEDIA_ID), "url": "https://x"})
    )
    response = create_external_video(
        procedure_id=_PROC,
        body=ExternalVideoBody(url="https://example.com/v", title="Vídeo"),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_guias_procedimentos_admin_external_video",
    )


@patch(f"{_MEDIA}.build_update_media_metadata_use_case")
def test_update_media_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        MediaMetadataBody,
        update_media_metadata,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_MEDIA_ID)})
    )
    response = update_media_metadata(
        media_id=_MEDIA_ID, body=MediaMetadataBody(title="t")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_guias_procedimentos_admin_media",
    )


@patch(f"{_MEDIA}.build_archive_media_use_case")
def test_archive_media_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        archive_media,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_MEDIA_ID), "archived": True})
    )
    response = archive_media(media_id=_MEDIA_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="archive_guias_procedimentos_admin_media",
    )


@patch(f"{_MEDIA}.build_update_attachment_metadata_use_case")
def test_update_attachment_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        AttachmentMetadataBody,
        update_attachment_metadata,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_ATT)})
    )
    response = update_attachment_metadata(
        attachment_id=_ATT, body=AttachmentMetadataBody(title="a")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_guias_procedimentos_admin_attachment",
    )


@patch(f"{_MEDIA}.build_archive_attachment_use_case")
def test_archive_attachment_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        archive_attachment,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_ATT), "archived": True})
    )
    response = archive_attachment(attachment_id=_ATT)
    assert_envelope_meta(
        body_json(response),
        operation_id="archive_guias_procedimentos_admin_attachment",
    )


@pytest.mark.asyncio
@patch(f"{_MEDIA}.build_upload_procedure_video_use_case")
async def test_upload_procedure_video_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        upload_procedure_video,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_MEDIA_ID)})
    )
    upload = MagicMock()
    upload.filename = "v.mp4"
    upload.content_type = "video/mp4"
    upload.read = MagicMock(return_value=b"data")
    # UploadFile.read is async
    async def _read():
        return b"data"

    upload.read = _read
    response = await upload_procedure_video(
        procedure_id=_PROC, file=upload, title="", order_index=0
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="upload_guias_procedimentos_admin_procedure_video",
    )


@pytest.mark.asyncio
@patch(f"{_MEDIA}.build_upload_procedure_attachment_use_case")
async def test_upload_procedure_attachment_returns_meta(mock_build) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        upload_procedure_attachment,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"id": str(_ATT)})
    )

    async def _read():
        return b"pdf"

    upload = MagicMock()
    upload.filename = "a.pdf"
    upload.content_type = "application/pdf"
    upload.read = _read
    response = await upload_procedure_attachment(
        procedure_id=_PROC, file=upload, title="", order_index=0
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="upload_guias_procedimentos_admin_procedure_attachment",
    )


@patch(f"{_MEDIA}.build_file_response")
@patch(f"{_MEDIA}._can_manage", return_value=False)
@patch(f"{_MEDIA}.build_resolve_media_file_use_case")
def test_download_media_file_covered(
    mock_build, _manage, mock_file_response
) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        download_media_file,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "path": "/tmp/x.bin",
                "mime_type": "application/octet-stream",
                "filename": "x.bin",
                "media_kind": "image",
            }
        )
    )
    mock_file_response.return_value = MagicMock(status_code=200)
    request = MagicMock()
    response = download_media_file(media_id=_MEDIA_ID, request=request)
    assert response is not None
    assert "download_guias_procedimentos_media_file"


@patch(f"{_MEDIA}.build_file_response")
@patch(f"{_MEDIA}._can_manage", return_value=False)
@patch(f"{_MEDIA}.build_resolve_attachment_file_use_case")
def test_download_attachment_file_covered(
    mock_build, _manage, mock_file_response
) -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
        download_attachment_file,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "path": "/tmp/a.pdf",
                "mime_type": "application/pdf",
                "filename": "a.pdf",
            }
        )
    )
    mock_file_response.return_value = MagicMock(status_code=200)
    request = MagicMock()
    response = download_attachment_file(attachment_id=_ATT, request=request)
    assert response is not None
    assert "download_guias_procedimentos_attachment_file"
