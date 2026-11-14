from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS,
)
from commercial_app.application.use_cases.manage_satisfaction_surveys import (
    CreateCampaignCommand,
    ManageSatisfactionSurveysUseCase,
    SatisfactionSurveyError,
    UpdateCampaignCommand,
    UpdateRecipientContactCommand,
)
from commercial_app.composition.commercial_composer import (
    build_manage_satisfaction_surveys_use_case,
)
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.domain.entities.satisfaction_survey import RecipientAddItem
from commercial_app.interface.http.schemas.satisfaction_survey_schemas import (
    AddRecipientsBody,
    CreateCampaignBody,
    UpdateCampaignBody,
    UpdateRecipientContactBody,
)

logger = logging.getLogger("commercial.satisfaction_survey.routes")

router = APIRouter(prefix="/satisfaction-surveys", tags=["Satisfaction surveys"])


def _use_case() -> ManageSatisfactionSurveysUseCase:
    return build_manage_satisfaction_surveys_use_case()


def _actor_id(request: Request) -> str | None:
    """Principal canônico do delpi_auth: `id` (JWT sub / Core), com fallbacks."""
    return actor_sub_from_request(request)


def _map_error(exc: SatisfactionSurveyError, *, operation_id: str):
    return fail(
        exc.message,
        exc.status_code,
        data={"code": exc.code} if exc.code else None,
        operation_id=operation_id,
    )


@router.get("/questionnaire", operation_id="get_satisfaction_questionnaire")
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def get_satisfaction_questionnaire(_request: Request):
    try:
        return ok(
            _use_case().get_questionnaire(),
            message="Questionário oficial carregado.",
            operation_id="get_satisfaction_questionnaire",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="get_satisfaction_questionnaire")
    except Exception:
        logger.exception("get_satisfaction_questionnaire_failed")
        return fail(
            "Erro interno ao carregar questionário.",
            500,
            operation_id="get_satisfaction_questionnaire",
        )


@router.get("/campaigns", operation_id="list_satisfaction_campaigns")
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def list_satisfaction_campaigns(_request: Request):
    try:
        items = _use_case().list_campaigns()
        return ok(
            {"items": items},
            message="Campanhas carregadas.",
            operation_id="list_satisfaction_campaigns",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="list_satisfaction_campaigns")
    except Exception:
        logger.exception("list_satisfaction_campaigns_failed")
        return fail(
            "Erro interno ao listar campanhas.",
            500,
            operation_id="list_satisfaction_campaigns",
        )


@router.post("/campaigns", operation_id="create_satisfaction_campaign")
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def create_satisfaction_campaign(request: Request, body: CreateCampaignBody):
    actor = _actor_id(request)
    if not actor:
        return fail(
            "Usuário não identificado.",
            401,
            operation_id="create_satisfaction_campaign",
        )
    try:
        campaign = _use_case().create_campaign(
            CreateCampaignCommand(
                name=body.name,
                starts_at=body.starts_at,
                ends_at=body.ends_at,
                invite_subject=body.invite_subject,
                invite_body=body.invite_body,
                created_by_user_id=str(actor),
            )
        )
        return ok(
            campaign,
            message="Campanha criada.",
            status_code=201,
            operation_id="create_satisfaction_campaign",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="create_satisfaction_campaign")
    except Exception:
        logger.exception("create_satisfaction_campaign_failed")
        return fail(
            "Erro interno ao criar campanha.",
            500,
            operation_id="create_satisfaction_campaign",
        )


@router.get("/campaigns/{campaign_id}", operation_id="get_satisfaction_campaign")
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def get_satisfaction_campaign(_request: Request, campaign_id: str):
    try:
        return ok(
            _use_case().get_campaign(campaign_id),
            message="Campanha carregada.",
            operation_id="get_satisfaction_campaign",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="get_satisfaction_campaign")
    except Exception:
        logger.exception("get_satisfaction_campaign_failed")
        return fail(
            "Erro interno ao carregar campanha.",
            500,
            operation_id="get_satisfaction_campaign",
        )


@router.patch("/campaigns/{campaign_id}", operation_id="update_satisfaction_campaign")
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def update_satisfaction_campaign(
    _request: Request, campaign_id: str, body: UpdateCampaignBody
):
    try:
        campaign = _use_case().update_campaign(
            UpdateCampaignCommand(
                campaign_id=campaign_id,
                expected_version=body.version,
                name=body.name,
                starts_at=body.starts_at,
                ends_at=body.ends_at,
                invite_subject=body.invite_subject,
                invite_body=body.invite_body,
            )
        )
        return ok(
            campaign,
            message="Campanha atualizada.",
            operation_id="update_satisfaction_campaign",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="update_satisfaction_campaign")
    except Exception:
        logger.exception("update_satisfaction_campaign_failed")
        return fail(
            "Erro interno ao atualizar campanha.",
            500,
            operation_id="update_satisfaction_campaign",
        )


@router.get(
    "/campaigns/{campaign_id}/recipients",
    operation_id="list_satisfaction_recipients",
)
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def list_satisfaction_recipients(_request: Request, campaign_id: str):
    try:
        return ok(
            _use_case().list_recipients(campaign_id),
            message="Participantes carregados.",
            operation_id="list_satisfaction_recipients",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="list_satisfaction_recipients")
    except Exception:
        logger.exception("list_satisfaction_recipients_failed")
        return fail(
            "Erro interno ao listar participantes.",
            500,
            operation_id="list_satisfaction_recipients",
        )


@router.post(
    "/campaigns/{campaign_id}/recipients",
    operation_id="add_satisfaction_recipients",
)
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def add_satisfaction_recipients(
    request: Request, campaign_id: str, body: AddRecipientsBody
):
    actor = _actor_id(request)
    if not actor:
        return fail(
            "Usuário não identificado.",
            401,
            operation_id="add_satisfaction_recipients",
        )
    try:
        result = _use_case().add_recipients(
            campaign_id=campaign_id,
            items=[
                RecipientAddItem(
                    customer_code=item.customer_code,
                    customer_store=item.customer_store,
                    customer_name=item.customer_name,
                    contact_name=item.contact_name,
                    contact_email=item.contact_email,
                )
                for item in body.items
            ],
            created_by_user_id=str(actor),
        )
        return ok(
            result,
            message="Inclusão de participantes processada.",
            status_code=201,
            operation_id="add_satisfaction_recipients",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="add_satisfaction_recipients")
    except Exception:
        logger.exception("add_satisfaction_recipients_failed")
        return fail(
            "Erro interno ao incluir participantes.",
            500,
            operation_id="add_satisfaction_recipients",
        )


@router.get(
    "/campaigns/{campaign_id}/recipients/{recipient_id}",
    operation_id="get_satisfaction_recipient",
)
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def get_satisfaction_recipient(
    _request: Request, campaign_id: str, recipient_id: str
):
    try:
        return ok(
            _use_case().get_recipient(
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                include_resolved_invite=True,
            ),
            message="Participante carregado.",
            operation_id="get_satisfaction_recipient",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="get_satisfaction_recipient")
    except Exception:
        logger.exception("get_satisfaction_recipient_failed")
        return fail(
            "Erro interno ao carregar participante.",
            500,
            operation_id="get_satisfaction_recipient",
        )


@router.patch(
    "/campaigns/{campaign_id}/recipients/{recipient_id}",
    operation_id="update_satisfaction_recipient_contact",
)
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def update_satisfaction_recipient_contact(
    _request: Request,
    campaign_id: str,
    recipient_id: str,
    body: UpdateRecipientContactBody,
):
    try:
        recipient = _use_case().update_recipient_contact(
            UpdateRecipientContactCommand(
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                expected_version=body.version,
                contact_name=body.contact_name,
                contact_email=body.contact_email,
            )
        )
        return ok(
            recipient,
            message="Contato do convite atualizado.",
            operation_id="update_satisfaction_recipient_contact",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="update_satisfaction_recipient_contact")
    except Exception:
        logger.exception("update_satisfaction_recipient_contact_failed")
        return fail(
            "Erro interno ao atualizar contato.",
            500,
            operation_id="update_satisfaction_recipient_contact",
        )


@router.get(
    "/campaigns/{campaign_id}/recipients/{recipient_id}/link",
    operation_id="get_satisfaction_recipient_link",
)
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def get_satisfaction_recipient_link(
    _request: Request, campaign_id: str, recipient_id: str
):
    try:
        return ok(
            _use_case().get_recipient_link(
                campaign_id=campaign_id, recipient_id=recipient_id
            ),
            message="Link exclusivo recuperado.",
            operation_id="get_satisfaction_recipient_link",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="get_satisfaction_recipient_link")
    except Exception:
        logger.exception("get_satisfaction_recipient_link_failed")
        return fail(
            "Erro interno ao recuperar link.",
            500,
            operation_id="get_satisfaction_recipient_link",
        )


@router.get(
    "/campaigns/{campaign_id}/recipients/{recipient_id}/invite",
    operation_id="get_satisfaction_recipient_invite",
)
@require_any_permission(*COMMERCIAL_SATISFACTION_MANAGE_PERMISSIONS)
def get_satisfaction_recipient_invite(
    _request: Request, campaign_id: str, recipient_id: str
):
    """Resolved default message for one recipient (subject/body/link)."""
    try:
        return ok(
            _use_case().resolve_invite_preview(
                campaign_id=campaign_id, recipient_id=recipient_id
            ),
            message="Convite personalizado resolvido.",
            operation_id="get_satisfaction_recipient_invite",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="get_satisfaction_recipient_invite")
    except Exception:
        logger.exception("get_satisfaction_recipient_invite_failed")
        return fail(
            "Erro interno ao resolver convite.",
            500,
            operation_id="get_satisfaction_recipient_invite",
        )
