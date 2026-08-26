from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from delpi_auth.request_context import get_current_user

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_portal_user_manage,
)
from purchase_requests_app.application.use_cases.get_portal_user_protheus_mapping_use_case import (
    GetPortalUserProtheusMappingUseCase,
)
from purchase_requests_app.application.use_cases.sync_portal_user_protheus_mapping_by_email_use_case import (
    SyncPortalUserProtheusMappingByEmailUseCase,
    TotvsLookupUnavailableError,
)
from purchase_requests_app.core.responses import fail, ok

portal_rbac_router = APIRouter(
    prefix="/purchase-requests/rbac",
    tags=["Purchase Requests — Portal RBAC"],
)


def _current_user():
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return user


def _require_portal_user_manage(user=Depends(_current_user)):
    if not has_portal_user_manage(user):
        raise HTTPException(
            status_code=403,
            detail="Requer rbac.manage e users.manage no portal.",
        )
    return user


class SyncProtheusMappingByEmailBody(BaseModel):
    email: str = Field(min_length=3)
    portal_user_name: str | None = None


@portal_rbac_router.get("/user-protheus-mappings/{user_id}")
def get_portal_user_protheus_mapping(user_id: str, user=Depends(_require_portal_user_manage)):
    try:
        result = GetPortalUserProtheusMappingUseCase().execute(actor=user, user_id=user_id)
        return ok(result, message="Associação Protheus carregada.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except Exception:
        return fail("Erro interno ao carregar associação Protheus.", 500)


@portal_rbac_router.post("/user-protheus-mappings/{user_id}/sync-by-email")
def sync_portal_user_protheus_mapping_by_email(
    user_id: str,
    body: SyncProtheusMappingByEmailBody,
    user=Depends(_require_portal_user_manage),
):
    try:
        result = SyncPortalUserProtheusMappingByEmailUseCase().execute(
            actor=user,
            user_id=user_id,
            email=body.email,
            portal_user_name=body.portal_user_name,
        )
        return ok(result, message="Usuário Protheus associado por e-mail.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except ValueError as exc:
        return fail(str(exc), 422)
    except LookupError as exc:
        return fail(str(exc), 404)
    except TotvsLookupUnavailableError as exc:
        return fail(str(exc), 503)
    except Exception as exc:
        logging.getLogger(__name__).exception("sync_portal_user_protheus_mapping_failed")
        return fail("Erro interno ao sincronizar usuário Protheus.", 500)
