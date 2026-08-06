from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, File, Form, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_FOLLOWUPS_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    can_manage_portfolios,
)
from commercial_app.application.services.attachment_storage import AttachmentStorageError
from commercial_app.composition.commercial_composer import (
    build_attachment_repository,
    build_manage_attachments_use_case,
    build_task_repository,
)
from commercial_app.core.auth_actor import actor_sub_from_request, current_user_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.application.services.commercial_realtime_notify import notify_worklist_changed
from commercial_app.interface.http.client_id import client_id_from_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attachments", tags=["Attachments"])


def _user_id(request: Request) -> str | None:
    return actor_sub_from_request(request)


def _is_portfolio_manager(request: Request) -> bool:
    return can_manage_portfolios(current_user_from_request(request))


def _notify_task_attachment(task_id: str, request: Request) -> None:
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        return
    task = build_task_repository().get_by_id(task_uuid)
    if task is None:
        return
    notify_worklist_changed(
        reason="attachment.changed",
        task_id=str(task.id),
        assignee_user_ids=[task.assignee_user_id],
        actor_client_id=client_id_from_request(request),
    )


@router.get("", operation_id="list_attachments")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS, *COMMERCIAL_READ_PERMISSIONS)
def list_attachments(
    request: Request,
    owner_type: str = Query(..., min_length=1),
    owner_id: str = Query(..., min_length=1),
):
    user_id = _user_id(request)
    if not user_id:
        return fail("Usuário não identificado.", 401, operation_id="list_attachments")
    try:
        items = build_manage_attachments_use_case().list(
            owner_type=owner_type,
            owner_id=owner_id,
            actor_user_id=user_id,
            actor_is_portfolio_manager=_is_portfolio_manager(request),
        )
        return ok(
            {"items": [item.to_dict() for item in items]},
            message="Anexos listados.",
            operation_id="list_attachments",
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="list_attachments")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="list_attachments")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="list_attachments")
    except Exception:
        logger.exception("list_attachments_failed")
        return fail("Erro interno ao listar anexos.", 500, operation_id="list_attachments")


@router.post("", operation_id="upload_attachment")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS)
async def upload_attachment(
    request: Request,
    owner_type: str = Form(..., min_length=1),
    owner_id: str = Form(..., min_length=1),
    file: UploadFile = File(...),
):
    user_id = _user_id(request)
    if not user_id:
        return fail("Usuário não identificado.", 401, operation_id="upload_attachment")
    try:
        content = await file.read()
        record = build_manage_attachments_use_case().upload(
            owner_type=owner_type,
            owner_id=owner_id,
            original_name=file.filename or "anexo.bin",
            content=content,
            mime_type=file.content_type,
            uploaded_by_user_id=user_id,
            actor_is_portfolio_manager=_is_portfolio_manager(request),
        )
        if owner_type.strip().lower() == "task":
            _notify_task_attachment(owner_id.strip(), request)
        return ok(
            record.to_dict(),
            message="Anexo enviado com sucesso.",
            operation_id="upload_attachment",
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="upload_attachment")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="upload_attachment")
    except (ValueError, AttachmentStorageError) as exc:
        return fail(str(exc), 400, operation_id="upload_attachment")
    except Exception:
        logger.exception("upload_attachment_failed")
        return fail("Erro interno ao enviar anexo.", 500, operation_id="upload_attachment")


@router.get("/{attachment_id}/content", operation_id="download_attachment")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS, *COMMERCIAL_READ_PERMISSIONS)
def download_attachment(
    request: Request,
    attachment_id: UUID = Path(...),
):
    user_id = _user_id(request)
    if not user_id:
        return fail("Usuário não identificado.", 401, operation_id="download_attachment")
    try:
        attachment_file = build_manage_attachments_use_case().get_file(
            attachment_id=attachment_id,
            actor_user_id=user_id,
            actor_is_portfolio_manager=_is_portfolio_manager(request),
        )
        return FileResponse(
            path=attachment_file.path,
            media_type=attachment_file.content_type,
            filename=attachment_file.file_name,
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="download_attachment")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="download_attachment")
    except AttachmentStorageError as exc:
        return fail(str(exc), 404, operation_id="download_attachment")
    except Exception:
        logger.exception("download_attachment_failed")
        return fail(
            "Erro interno ao baixar anexo.",
            500,
            operation_id="download_attachment",
        )


@router.delete("/{attachment_id}", operation_id="delete_attachment")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS)
def delete_attachment(
    request: Request,
    attachment_id: UUID = Path(...),
):
    user_id = _user_id(request)
    if not user_id:
        return fail("Usuário não identificado.", 401, operation_id="delete_attachment")
    try:
        record = build_attachment_repository().get_by_id(attachment_id)
        payload = build_manage_attachments_use_case().delete(
            attachment_id=attachment_id,
            actor_user_id=user_id,
            actor_is_portfolio_manager=_is_portfolio_manager(request),
        )
        if record and record.owner_type == "task":
            _notify_task_attachment(record.owner_id, request)
        return ok(
            payload,
            message="Anexo removido.",
            operation_id="delete_attachment",
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="delete_attachment")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="delete_attachment")
    except Exception:
        logger.exception("delete_attachment_failed")
        return fail("Erro interno ao remover anexo.", 500, operation_id="delete_attachment")
