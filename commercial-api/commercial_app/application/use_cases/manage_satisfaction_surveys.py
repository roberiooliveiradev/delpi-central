from __future__ import annotations

import hashlib
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from commercial_app.config import settings
from commercial_app.domain.entities.satisfaction_survey import (
    RecipientAddItem,
    RecipientAddResult,
    SatisfactionCampaign,
    SatisfactionRecipient,
    SatisfactionResponse,
)
from commercial_app.domain.ports.satisfaction_survey_repository_port import (
    SatisfactionSurveyRepositoryPort,
)
from commercial_app.domain.ports.customer_eligibility_port import (
    CustomerEligibilityPort,
)
from commercial_app.domain.services.satisfaction_questionnaire import (
    DEFAULT_INVITE_BODY,
    DEFAULT_INVITE_SUBJECT,
    QUESTIONNAIRE_VERSION,
    assert_invite_placeholders_allowed,
    get_questionnaire_catalog,
    validate_dimensions_payload,
)
from commercial_app.infrastructure.crypto.token_cipher import TokenCipher
from commercial_app.infrastructure.persistence.repositories.postgres_satisfaction_survey_repository import (
    ConflictError,
)

logger = logging.getLogger("commercial.satisfaction_survey")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SatisfactionSurveyError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


@dataclass(frozen=True)
class CreateCampaignCommand:
    name: str
    starts_at: datetime
    ends_at: datetime
    created_by_user_id: str
    invite_subject: str | None = None
    invite_body: str | None = None


@dataclass(frozen=True)
class UpdateCampaignCommand:
    campaign_id: str
    expected_version: int
    name: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    invite_subject: str | None = None
    invite_body: str | None = None


@dataclass(frozen=True)
class UpdateRecipientContactCommand:
    campaign_id: str
    recipient_id: str
    expected_version: int
    contact_name: str | None
    contact_email: str | None


@dataclass(frozen=True)
class SubmitPublicResponseCommand:
    token: str
    overall_score: int
    recommendation_score: int
    dimensions: dict[str, Any]
    strengths: str | None = None
    improvements: str | None = None
    unmet_needs: str | None = None


class ManageSatisfactionSurveysUseCase:
    def __init__(
        self,
        repository: SatisfactionSurveyRepositoryPort,
        *,
        token_cipher: TokenCipher,
        public_base_url: str | None = None,
        clock: Any | None = None,
        customer_eligibility: CustomerEligibilityPort | None = None,
    ) -> None:
        self._repository = repository
        self._cipher = token_cipher
        self._public_base_url = (public_base_url or settings.PUBLIC_BASE_URL or "").rstrip(
            "/"
        )
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._customer_eligibility = customer_eligibility

    def get_questionnaire(self) -> dict[str, Any]:
        return get_questionnaire_catalog()

    def list_campaigns(self) -> list[dict[str, Any]]:
        now = self._now()
        return [
            self.serialize_campaign(item, now=now)
            for item in self._repository.list_campaigns()
        ]

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        campaign = self._require_campaign(campaign_id)
        return self.serialize_campaign(campaign, now=self._now())

    def create_campaign(self, command: CreateCampaignCommand) -> dict[str, Any]:
        name = (command.name or "").strip()
        if not name:
            raise SatisfactionSurveyError("Nome da campanha é obrigatório.")
        starts_at = self._ensure_aware(command.starts_at)
        ends_at = self._ensure_aware(command.ends_at)
        if starts_at >= ends_at:
            raise SatisfactionSurveyError("A data de início deve ser anterior ao fim.")
        subject = (command.invite_subject or DEFAULT_INVITE_SUBJECT).strip()
        body = (command.invite_body or DEFAULT_INVITE_BODY).strip()
        if not subject or not body:
            raise SatisfactionSurveyError("Assunto e corpo da mensagem padrão são obrigatórios.")
        try:
            assert_invite_placeholders_allowed(subject, body)
        except ValueError as exc:
            raise SatisfactionSurveyError(str(exc)) from exc
        campaign = self._repository.create_campaign(
            name=name,
            starts_at=starts_at,
            ends_at=ends_at,
            questionnaire_version=QUESTIONNAIRE_VERSION,
            invite_subject=subject,
            invite_body=body,
            created_by_user_id=command.created_by_user_id,
        )
        logger.info(
            "satisfaction_campaign_created",
            extra={"campaign_id": campaign.id, "actor": command.created_by_user_id},
        )
        return self.serialize_campaign(campaign, now=self._now())

    def update_campaign(self, command: UpdateCampaignCommand) -> dict[str, Any]:
        campaign = self._require_campaign(command.campaign_id)
        response_count = campaign.response_count
        next_name = command.name.strip() if command.name is not None else None
        if command.name is not None and not next_name:
            raise SatisfactionSurveyError("Nome da campanha é obrigatório.")

        next_starts = (
            self._ensure_aware(command.starts_at)
            if command.starts_at is not None
            else None
        )
        next_ends = (
            self._ensure_aware(command.ends_at) if command.ends_at is not None else None
        )
        effective_starts = next_starts or campaign.starts_at
        effective_ends = next_ends or campaign.ends_at
        if effective_starts >= effective_ends:
            raise SatisfactionSurveyError("A data de início deve ser anterior ao fim.")

        if response_count > 0 and (
            (next_starts is not None and next_starts != campaign.starts_at)
            or (next_ends is not None and next_ends != campaign.ends_at)
        ):
            raise SatisfactionSurveyError(
                "Não é permitido alterar a janela após respostas definitivas.",
                status_code=409,
                code="window_locked",
            )

        next_subject = (
            command.invite_subject.strip()
            if command.invite_subject is not None
            else None
        )
        next_body = (
            command.invite_body.strip() if command.invite_body is not None else None
        )
        if command.invite_subject is not None and not next_subject:
            raise SatisfactionSurveyError("Assunto da mensagem padrão é obrigatório.")
        if command.invite_body is not None and not next_body:
            raise SatisfactionSurveyError("Corpo da mensagem padrão é obrigatório.")

        check_subject = next_subject if next_subject is not None else campaign.invite_subject
        check_body = next_body if next_body is not None else campaign.invite_body
        if command.invite_subject is not None or command.invite_body is not None:
            try:
                assert_invite_placeholders_allowed(check_subject, check_body)
            except ValueError as exc:
                raise SatisfactionSurveyError(str(exc)) from exc

        try:
            updated = self._repository.update_campaign(
                campaign_id=command.campaign_id,
                expected_version=command.expected_version,
                name=next_name,
                starts_at=next_starts,
                ends_at=next_ends,
                invite_subject=next_subject,
                invite_body=next_body,
            )
        except ConflictError as exc:
            raise SatisfactionSurveyError(
                str(exc), status_code=409, code="version_conflict"
            ) from exc
        except LookupError as exc:
            raise SatisfactionSurveyError(str(exc), status_code=404) from exc

        logger.info(
            "satisfaction_campaign_updated",
            extra={"campaign_id": updated.id},
        )
        return self.serialize_campaign(updated, now=self._now())

    def list_recipients(self, campaign_id: str) -> dict[str, Any]:
        campaign = self._require_campaign(campaign_id)
        recipients = self._repository.list_recipients(campaign_id)
        responded = sum(1 for item in recipients if item.has_response)
        return {
            "campaign_id": campaign.id,
            "counts": {
                "participants": len(recipients),
                "responded": responded,
                "pending": len(recipients) - responded,
            },
            "items": [self.serialize_recipient(item) for item in recipients],
        }

    def get_recipient(
        self,
        *,
        campaign_id: str,
        recipient_id: str,
        include_resolved_invite: bool = False,
    ) -> dict[str, Any]:
        self._require_campaign(campaign_id)
        recipient = self._repository.get_recipient(
            campaign_id=campaign_id, recipient_id=recipient_id
        )
        if recipient is None:
            raise SatisfactionSurveyError("Participante não encontrado.", status_code=404)
        return self.serialize_recipient(
            recipient, include_resolved_invite=include_resolved_invite
        )

    def add_recipients(
        self,
        *,
        campaign_id: str,
        items: list[RecipientAddItem],
        created_by_user_id: str,
    ) -> dict[str, Any]:
        campaign = self._require_campaign(campaign_id)
        now = self._now()
        if campaign.window_status(now=now) == "closed":
            raise SatisfactionSurveyError(
                "Campanha encerrada não recebe novos participantes.",
                status_code=409,
                code="campaign_closed",
            )
        if not items:
            raise SatisfactionSurveyError("Informe ao menos um participante.")

        eligibility_map: dict[tuple[str, str], Any] | None = None
        if self._customer_eligibility is not None:
            pairs = [
                ((raw.customer_code or "").strip(), (raw.customer_store or "").strip())
                for raw in items
            ]
            pairs = [(code, store) for code, store in pairs if code and store]
            try:
                eligibility_map = dict(self._customer_eligibility.lookup(pairs))
            except Exception:
                logger.exception(
                    "satisfaction_recipient_eligibility_lookup_failed",
                    extra={"campaign_id": campaign_id},
                )
                raise SatisfactionSurveyError(
                    "Não foi possível validar os clientes no cadastro TOTVS.",
                    status_code=502,
                    code="totvs_unavailable",
                )

        result = RecipientAddResult()
        seen: set[tuple[str, str]] = set()
        for raw in items:
            code = (raw.customer_code or "").strip()
            store = (raw.customer_store or "").strip()
            if not code or not store:
                result.failed.append(
                    {
                        "customer_code": code,
                        "customer_store": store,
                        "reason": "customer_identity_required",
                        "message": "Código e loja do cliente são obrigatórios.",
                    }
                )
                continue
            key = (code, store)
            if key in seen:
                result.failed.append(
                    {
                        "customer_code": code,
                        "customer_store": store,
                        "reason": "duplicate_in_request",
                        "message": "Cliente duplicado no mesmo lote.",
                    }
                )
                continue
            seen.add(key)

            existing = self._repository.find_recipient_by_customer(
                campaign_id=campaign_id,
                customer_code=code,
                customer_store=store,
            )
            if existing is not None:
                result.already_existing.append(existing)
                continue

            if eligibility_map is not None:
                info = eligibility_map.get(key)
                if info is None or not getattr(info, "exists", False):
                    result.failed.append(
                        {
                            "customer_code": code,
                            "customer_store": store,
                            "reason": "customer_not_found",
                            "message": "Cliente não encontrado no cadastro TOTVS.",
                        }
                    )
                    continue
                if not getattr(info, "active", False):
                    result.failed.append(
                        {
                            "customer_code": code,
                            "customer_store": store,
                            "reason": "customer_inactive",
                            "message": "Cliente bloqueado ou inativo no cadastro TOTVS.",
                        }
                    )
                    continue

            token = secrets.token_urlsafe(32)
            token_hash = self._hash_token(token)
            try:
                ciphertext = self._cipher.encrypt(token)
            except Exception as exc:
                raise SatisfactionSurveyError(
                    "Falha ao proteger o token do convite.",
                    status_code=500,
                ) from exc

            try:
                created = self._repository.create_recipient(
                    campaign_id=campaign_id,
                    customer_code=code,
                    customer_store=store,
                    customer_name_snapshot=(raw.customer_name or "").strip() or None,
                    contact_name=(raw.contact_name or "").strip() or None,
                    contact_email=self._normalize_email(raw.contact_email),
                    token_hash=token_hash,
                    token_ciphertext=ciphertext,
                    created_by_user_id=created_by_user_id,
                )
            except Exception as exc:
                # Unique race: treat as already existing when possible.
                raced = self._repository.find_recipient_by_customer(
                    campaign_id=campaign_id,
                    customer_code=code,
                    customer_store=store,
                )
                if raced is not None:
                    result.already_existing.append(raced)
                    continue
                logger.exception(
                    "satisfaction_recipient_create_failed",
                    extra={"campaign_id": campaign_id, "customer_code": code},
                )
                result.failed.append(
                    {
                        "customer_code": code,
                        "customer_store": store,
                        "reason": "persist_failed",
                        "message": "Não foi possível incluir o participante.",
                    }
                )
                continue
            result.included.append(created)

        logger.info(
            "satisfaction_recipients_batch",
            extra={
                "campaign_id": campaign_id,
                "included": len(result.included),
                "already_existing": len(result.already_existing),
                "failed": len(result.failed),
            },
        )
        return {
            "campaign_id": campaign_id,
            "included": [self.serialize_recipient(item) for item in result.included],
            "already_existing": [
                self.serialize_recipient(item) for item in result.already_existing
            ],
            "failed": result.failed,
            "counts": {
                "included": len(result.included),
                "already_existing": len(result.already_existing),
                "failed": len(result.failed),
            },
        }

    def update_recipient_contact(
        self, command: UpdateRecipientContactCommand
    ) -> dict[str, Any]:
        self._require_campaign(command.campaign_id)
        email = self._normalize_email(command.contact_email)
        name = (command.contact_name or "").strip() or None
        try:
            updated = self._repository.update_recipient_contact(
                campaign_id=command.campaign_id,
                recipient_id=command.recipient_id,
                expected_version=command.expected_version,
                contact_name=name,
                contact_email=email,
            )
        except ConflictError as exc:
            raise SatisfactionSurveyError(
                str(exc), status_code=409, code="version_conflict"
            ) from exc
        except LookupError as exc:
            raise SatisfactionSurveyError(str(exc), status_code=404) from exc
        return self.serialize_recipient(updated)

    def get_recipient_link(
        self, *, campaign_id: str, recipient_id: str
    ) -> dict[str, Any]:
        self._require_campaign(campaign_id)
        recipient = self._repository.get_recipient(
            campaign_id=campaign_id, recipient_id=recipient_id
        )
        if recipient is None:
            raise SatisfactionSurveyError("Participante não encontrado.", status_code=404)
        token = self._decrypt_token(recipient.token_ciphertext)
        return {
            "recipient_id": recipient.id,
            "campaign_id": campaign_id,
            "url": self._build_public_url(token),
        }

    def resolve_invite_preview(
        self, *, campaign_id: str, recipient_id: str
    ) -> dict[str, Any]:
        campaign = self._require_campaign(campaign_id)
        recipient = self._repository.get_recipient(
            campaign_id=campaign_id, recipient_id=recipient_id
        )
        if recipient is None:
            raise SatisfactionSurveyError("Participante não encontrado.", status_code=404)
        token = self._decrypt_token(recipient.token_ciphertext)
        link = self._build_public_url(token)
        company = recipient.customer_name_snapshot or (
            f"{recipient.customer_code}/{recipient.customer_store}"
        )
        subject = campaign.invite_subject.replace("{nome_empresa}", company).replace(
            "{link_pesquisa}", link
        )
        body = campaign.invite_body.replace("{nome_empresa}", company).replace(
            "{link_pesquisa}", link
        )
        return {
            "recipient_id": recipient.id,
            "campaign_id": campaign.id,
            "company_name": company,
            "subject": subject,
            "body": body,
            "link_url": link,
        }

    def load_public_form(self, token: str) -> dict[str, Any]:
        recipient, campaign = self._resolve_public_token(token)
        now = self._now()
        status = campaign.window_status(now=now)
        if recipient.has_response:
            form_status = "already_submitted"
        elif status == "scheduled":
            form_status = "not_open"
        elif status == "closed":
            form_status = "closed"
        else:
            form_status = "open"
        payload: dict[str, Any] = {
            "status": form_status,
            "campaign_name": campaign.name,
            "starts_at": campaign.starts_at.isoformat(),
            "ends_at": campaign.ends_at.isoformat(),
            "questionnaire_version": campaign.questionnaire_version,
        }
        if form_status == "open":
            payload["questionnaire"] = get_questionnaire_catalog()
            payload["company_name"] = recipient.customer_name_snapshot
        return payload

    def submit_public_response(
        self, command: SubmitPublicResponseCommand
    ) -> dict[str, Any]:
        recipient, campaign = self._resolve_public_token(command.token)
        now = self._now()
        if recipient.has_response:
            raise SatisfactionSurveyError(
                "Esta pesquisa já foi respondida.",
                status_code=409,
                code="already_submitted",
            )
        status = campaign.window_status(now=now)
        if status == "scheduled":
            raise SatisfactionSurveyError(
                "A pesquisa ainda não está aberta.",
                status_code=409,
                code="not_open",
            )
        if status == "closed":
            raise SatisfactionSurveyError(
                "A pesquisa está encerrada.",
                status_code=409,
                code="closed",
            )
        if campaign.questionnaire_version != QUESTIONNAIRE_VERSION:
            # Historical campaigns keep their version; validate against stored version texts.
            pass

        try:
            dimensions = validate_dimensions_payload(command.dimensions)
        except ValueError as exc:
            raise SatisfactionSurveyError(str(exc)) from exc

        if not isinstance(command.overall_score, int) or not (
            1 <= command.overall_score <= 5
        ):
            raise SatisfactionSurveyError("Satisfação geral deve ser um inteiro de 1 a 5.")
        if not isinstance(command.recommendation_score, int) or not (
            0 <= command.recommendation_score <= 10
        ):
            raise SatisfactionSurveyError(
                "Recomendação deve ser um inteiro de 0 a 10."
            )

        try:
            response = self._repository.create_response(
                recipient_id=recipient.id,
                overall_score=command.overall_score,
                recommendation_score=command.recommendation_score,
                dimensions=dimensions,
                strengths=self._normalize_optional_text(command.strengths),
                improvements=self._normalize_optional_text(command.improvements),
                unmet_needs=self._normalize_optional_text(command.unmet_needs),
                questionnaire_version=campaign.questionnaire_version,
            )
        except Exception as exc:
            existing = self._repository.get_response_by_recipient(recipient.id)
            if existing is not None:
                raise SatisfactionSurveyError(
                    "Esta pesquisa já foi respondida.",
                    status_code=409,
                    code="already_submitted",
                ) from exc
            logger.exception("satisfaction_response_create_failed")
            raise SatisfactionSurveyError(
                "Não foi possível registrar a resposta.",
                status_code=500,
            ) from exc

        logger.info(
            "satisfaction_response_submitted",
            extra={
                "campaign_id": campaign.id,
                "recipient_id": recipient.id,
                "response_id": response.id,
            },
        )
        return {
            "status": "submitted",
            "response_id": response.id,
            "submitted_at": response.submitted_at.isoformat(),
        }

    def serialize_campaign(
        self, campaign: SatisfactionCampaign, *, now: datetime | None = None
    ) -> dict[str, Any]:
        clock = now or self._now()
        return {
            "id": campaign.id,
            "name": campaign.name,
            "starts_at": campaign.starts_at.isoformat(),
            "ends_at": campaign.ends_at.isoformat(),
            "status": campaign.window_status(now=clock),
            "questionnaire_version": campaign.questionnaire_version,
            "invite_subject": campaign.invite_subject,
            "invite_body": campaign.invite_body,
            "created_by_user_id": campaign.created_by_user_id,
            "created_at": campaign.created_at.isoformat(),
            "updated_at": campaign.updated_at.isoformat(),
            "version": campaign.version,
            "counts": {
                "participants": campaign.recipient_count,
                "responded": campaign.response_count,
                "pending": max(campaign.recipient_count - campaign.response_count, 0),
            },
            # Taxa oficial (backend): None quando não há participantes — FE exibe "—".
            "response_rate": (
                round(
                    100.0 * campaign.response_count / campaign.recipient_count,
                    1,
                )
                if campaign.recipient_count > 0
                else None
            ),
        }

    def serialize_recipient(
        self,
        recipient: SatisfactionRecipient,
        *,
        include_resolved_invite: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": recipient.id,
            "campaign_id": recipient.campaign_id,
            "customer_code": recipient.customer_code,
            "customer_store": recipient.customer_store,
            "customer_name": recipient.customer_name_snapshot,
            "contact_name": recipient.contact_name,
            "contact_email": recipient.contact_email,
            "status": "responded" if recipient.has_response else "pending",
            "response_id": recipient.response_id,
            "submitted_at": (
                recipient.submitted_at.isoformat() if recipient.submitted_at else None
            ),
            "created_at": recipient.created_at.isoformat(),
            "updated_at": recipient.updated_at.isoformat(),
            "version": recipient.version,
        }
        if include_resolved_invite:
            try:
                invite = self.resolve_invite_preview(
                    campaign_id=recipient.campaign_id,
                    recipient_id=recipient.id,
                )
                payload["invite"] = {
                    "subject": invite["subject"],
                    "body": invite["body"],
                    "link_url": invite["link_url"],
                }
            except SatisfactionSurveyError:
                payload["invite"] = None
        return payload

    def _require_campaign(self, campaign_id: str) -> SatisfactionCampaign:
        campaign = self._repository.get_campaign(campaign_id)
        if campaign is None:
            raise SatisfactionSurveyError("Campanha não encontrada.", status_code=404)
        return campaign

    def _resolve_public_token(
        self, token: str
    ) -> tuple[SatisfactionRecipient, SatisfactionCampaign]:
        raw = (token or "").strip()
        if not raw or len(raw) < 16:
            raise SatisfactionSurveyError(
                "Link inválido ou expirado.",
                status_code=404,
                code="invalid_token",
            )
        token_hash = self._hash_token(raw)
        recipient = self._repository.get_recipient_by_token_hash(token_hash)
        if recipient is None:
            raise SatisfactionSurveyError(
                "Link inválido ou expirado.",
                status_code=404,
                code="invalid_token",
            )
        campaign = self._repository.get_campaign(recipient.campaign_id)
        if campaign is None:
            raise SatisfactionSurveyError(
                "Link inválido ou expirado.",
                status_code=404,
                code="invalid_token",
            )
        return recipient, campaign

    def _decrypt_token(self, ciphertext: str) -> str:
        try:
            return self._cipher.decrypt(ciphertext)
        except Exception as exc:
            raise SatisfactionSurveyError(
                "Não foi possível recuperar o link do convite.",
                status_code=500,
            ) from exc

    def _build_public_url(self, token: str) -> str:
        path = f"/p/commercial/form/{quote(token, safe='')}"
        if self._public_base_url:
            return f"{self._public_base_url}{path}"
        return path

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_email(value: str | None) -> str | None:
        email = (value or "").strip()
        if not email:
            return None
        if not _EMAIL_RE.match(email):
            raise SatisfactionSurveyError("E-mail de contato inválido.")
        return email

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        text = (value or "").strip()
        return text or None

    @staticmethod
    def _ensure_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
