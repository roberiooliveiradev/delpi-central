from __future__ import annotations

import logging

from fastapi import APIRouter, File, Path, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_READ_PERMISSIONS,
)
from commercial_app.composition.commercial_composer import build_manage_user_profile_use_case
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users / profile"])


class PatchUserProfileBody(BaseModel):
    job_title: str | None = Field(default=None, max_length=200)
    phone_e164: str | None = Field(default=None, max_length=17)
    mobile_e164: str | None = Field(default=None, max_length=17)
    whatsapp_e164: str | None = Field(default=None, max_length=17)


def _user_id(request: Request) -> str | None:
    return actor_sub_from_request(request)


@router.get("/{user_id}/profile", operation_id="get_user_profile")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_user_profile(request: Request, user_id: str = Path(..., min_length=1)):
    try:
        data = build_manage_user_profile_use_case().get_profile(user_id=user_id)
        return ok(data, message="Perfil carregado.", operation_id="get_user_profile")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="get_user_profile")
    except Exception:
        logger.exception("get_user_profile_failed")
        return fail("Erro interno ao carregar perfil.", 500, operation_id="get_user_profile")


@router.patch("/{user_id}/profile", operation_id="patch_user_profile")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def patch_user_profile(
    request: Request,
    body: PatchUserProfileBody,
    user_id: str = Path(..., min_length=1),
):
    try:
        actor = _user_id(request)
        if not actor:
            return fail("Usuário não identificado.", 401, operation_id="patch_user_profile")
        data = build_manage_user_profile_use_case().update_profile(
            actor_user_id=actor,
            user_id=user_id,
            job_title=body.job_title,
            phone_e164=body.phone_e164,
            mobile_e164=body.mobile_e164,
            whatsapp_e164=body.whatsapp_e164,
        )
        return ok(data, message="Perfil atualizado.", operation_id="patch_user_profile")
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="patch_user_profile")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="patch_user_profile")
    except Exception:
        logger.exception("patch_user_profile_failed")
        return fail("Erro interno ao atualizar perfil.", 500, operation_id="patch_user_profile")


@router.get("/{user_id}/profile/photo", operation_id="get_user_profile_photo")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_user_profile_photo(request: Request, user_id: str = Path(..., min_length=1)):
    try:
        photo = build_manage_user_profile_use_case().get_photo_file(user_id=user_id)
        return FileResponse(
            path=photo.path,
            media_type=photo.content_type,
            filename=photo.file_name,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="get_user_profile_photo")
    except Exception:
        logger.exception("get_user_profile_photo_failed")
        return fail(
            "Erro interno ao carregar foto.",
            500,
            operation_id="get_user_profile_photo",
        )


@router.put("/{user_id}/profile/photo", operation_id="put_user_profile_photo")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
async def put_user_profile_photo(
    request: Request,
    user_id: str = Path(..., min_length=1),
    file: UploadFile = File(...),
):
    try:
        actor = _user_id(request)
        if not actor:
            return fail("Usuário não identificado.", 401, operation_id="put_user_profile_photo")
        content = await file.read()
        data = build_manage_user_profile_use_case().upload_photo(
            actor_user_id=actor,
            user_id=user_id,
            original_name=file.filename or "photo.bin",
            content=content,
            mime_type=file.content_type,
        )
        return ok(data, message="Foto atualizada.", operation_id="put_user_profile_photo")
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="put_user_profile_photo")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="put_user_profile_photo")
    except Exception:
        logger.exception("put_user_profile_photo_failed")
        return fail(
            "Erro interno ao enviar foto.",
            500,
            operation_id="put_user_profile_photo",
        )


@router.delete("/{user_id}/profile/photo", operation_id="delete_user_profile_photo")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def delete_user_profile_photo(request: Request, user_id: str = Path(..., min_length=1)):
    try:
        actor = _user_id(request)
        if not actor:
            return fail(
                "Usuário não identificado.",
                401,
                operation_id="delete_user_profile_photo",
            )
        data = build_manage_user_profile_use_case().delete_photo(
            actor_user_id=actor,
            user_id=user_id,
        )
        return ok(data, message="Foto removida.", operation_id="delete_user_profile_photo")
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="delete_user_profile_photo")
    except Exception:
        logger.exception("delete_user_profile_photo_failed")
        return fail(
            "Erro interno ao remover foto.",
            500,
            operation_id="delete_user_profile_photo",
        )
