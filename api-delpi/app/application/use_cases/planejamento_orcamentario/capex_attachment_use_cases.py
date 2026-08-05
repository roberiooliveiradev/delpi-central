"""Casos de uso — anexos de investimentos CAPEX (Fase 2B.3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.application.services.planejamento_orcamentario.document_storage import (
    ALLOWED_MIME_TYPES,
    EXT_TO_KIND,
    MAX_DOCUMENT_BYTES,
    BudgetDocumentStorage,
)
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.acknowledgement_guard import (
    BudgetGuidanceAcknowledgementGuard,
)
from app.domain.services.planejamento_orcamentario.capex_attachment_constants import (
    ALLOWED_ATTACHMENT_TYPES,
    AUDIT_ACTION_ACCESS_DENIED,
    AUDIT_ACTION_ARCHIVED,
    AUDIT_ACTION_DOWNLOADED,
    AUDIT_ACTION_UPLOAD_REJECTED,
    AUDIT_ACTION_UPLOADED,
    ENTITY_TYPE_CAPEX_ATTACHMENT,
)
from app.domain.services.planejamento_orcamentario.capex_investment_constants import (
    STATUS_ARCHIVED,
    STATUS_DRAFT,
)
from app.domain.services.planejamento_orcamentario.capex_plan_guard import (
    assert_plan_allows_mutation,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetDocumentTooLargeError,
    BudgetDocumentTypeNotAllowedError,
    BudgetResponsibilityForbiddenError,
    CapexAttachmentArchivedError,
    CapexAttachmentExtensionInvalidError,
    CapexAttachmentForbiddenError,
    CapexAttachmentInvalidError,
    CapexAttachmentInvestmentArchivedError,
    CapexAttachmentMimeInvalidError,
    CapexAttachmentNotFoundError,
    CapexAttachmentTooLargeError,
    CapexAttachmentTypeInvalidError,
    CapexInvestmentNotFoundError,
)
from app.domain.services.planejamento_orcamentario.responsibility_constants import (
    BUDGET_MODULE_CAPEX,
)
from app.domain.services.planejamento_orcamentario.responsibility_guard import (
    BudgetResponsibilityGuard,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)


def _require_access(actor: BudgetActor) -> None:
    allowed = {
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.admin",
        "planejamento-orcamentario.guidance.view",
        "planejamento-orcamentario.guidance.manage",
        "planejamento-orcamentario.scopes.manage",
    }
    if not (actor.permissions & allowed):
        raise CapexAttachmentForbiddenError(
            "Sem permissão de acesso aos anexos CAPEX."
        )


def _is_admin(actor: BudgetActor) -> bool:
    return "planejamento-orcamentario.admin" in actor.permissions


def _safe_filename(name: str) -> str:
    """Remove path traversal do nome informado pelo cliente; não controla o nome físico."""
    base = Path(str(name or "").replace("\\", "/")).name.strip()
    return base or "arquivo"


def _public_attachment(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "investment_id",
        "attachment_type",
        "display_name",
        "description",
        "original_filename",
        "mime_type",
        "file_size",
        "created_by",
        "created_at",
        "archived_by",
        "archived_at",
        "is_active",
    )
    return {k: row.get(k) for k in keys}


class CapexAttachmentUseCases:
    def __init__(
        self,
        repository: PostgresBudgetPlanningRepository | None = None,
        storage: BudgetDocumentStorage | None = None,
    ) -> None:
        self._repo = repository or PostgresBudgetPlanningRepository()
        self._storage = storage or BudgetDocumentStorage()
        self._ack_guard = BudgetGuidanceAcknowledgementGuard(self._repo)
        self._resp_guard = BudgetResponsibilityGuard(self._repo)

    def _assert_unlocked(self, actor: BudgetActor) -> dict[str, Any]:
        return self._ack_guard.assert_modules_unlocked(user_sub=actor.user_id)

    def _assert_responsibility(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> dict[str, Any]:
        return self._resp_guard.assert_user_has_budget_responsibility(
            actor.user_id,
            exercise_id,
            BUDGET_MODULE_CAPEX,
            cost_center_id,
            unit_id=unit_id,
        )

    def _load_investment_or_404(self, investment_id: str) -> dict[str, Any]:
        row = self._repo.get_capex_investment(investment_id)
        if not row:
            raise CapexInvestmentNotFoundError("Investimento CAPEX não encontrado.")
        return row

    def _assert_can_access_investment(
        self,
        actor: BudgetActor,
        investment: dict[str, Any],
        *,
        as_attachment: bool = False,
        audit_entity_id: str | None = None,
    ) -> None:
        if _is_admin(actor):
            return
        try:
            self._assert_responsibility(
                actor,
                exercise_id=str(investment["exercise_id"]),
                cost_center_id=str(investment["cost_center_id"]),
                unit_id=str(investment.get("unit_id") or "") or None,
            )
        except BudgetResponsibilityForbiddenError:
            self._repo.append_audit(
                exercise_id=str(investment.get("exercise_id") or "") or None,
                entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
                entity_id=audit_entity_id,
                action=AUDIT_ACTION_ACCESS_DENIED,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state={
                    "reason": "cost_center_forbidden",
                    "investment_id": investment.get("id"),
                },
            )
            if as_attachment:
                raise CapexAttachmentNotFoundError(
                    "Anexo CAPEX não encontrado."
                ) from None
            raise CapexInvestmentNotFoundError(
                "Investimento CAPEX não encontrado."
            ) from None

    def _validate_file(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str,
        investment_id: str,
        mime_type: str | None,
        size_bytes: int,
        original_filename: str,
    ) -> None:
        try:
            if size_bytes <= 0:
                raise CapexAttachmentInvalidError("Arquivo vazio.")
            if size_bytes > MAX_DOCUMENT_BYTES:
                raise CapexAttachmentTooLargeError(
                    "Arquivo excede o limite configurado de 25 MB."
                )
            normalized_mime = (mime_type or "").lower().strip()
            if normalized_mime not in ALLOWED_MIME_TYPES:
                raise CapexAttachmentMimeInvalidError(
                    "MIME type não permitido para anexo CAPEX."
                )
            extension = Path(original_filename or "").suffix.lower()
            if extension not in EXT_TO_KIND:
                raise CapexAttachmentExtensionInvalidError(
                    "Extensão de arquivo não permitida."
                )
            # Revalida no storage canônico (mesmas regras).
            self._storage.validate_upload(
                mime_type=normalized_mime,
                size_bytes=size_bytes,
                original_name=original_filename,
            )
        except (
            CapexAttachmentTooLargeError,
            CapexAttachmentMimeInvalidError,
            CapexAttachmentExtensionInvalidError,
            CapexAttachmentInvalidError,
        ) as exc:
            self._repo.append_audit(
                exercise_id=exercise_id,
                entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
                entity_id=None,
                action=AUDIT_ACTION_UPLOAD_REJECTED,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state={
                    "reason": exc.code,
                    "investment_id": investment_id,
                    "mime_type": (mime_type or "")[:120],
                    "original_filename": _safe_filename(original_filename)[:300],
                    "file_size": size_bytes,
                },
            )
            raise
        except BudgetDocumentTooLargeError as exc:
            mapped = CapexAttachmentTooLargeError(str(exc))
            self._repo.append_audit(
                exercise_id=exercise_id,
                entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
                entity_id=None,
                action=AUDIT_ACTION_UPLOAD_REJECTED,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state={
                    "reason": mapped.code,
                    "investment_id": investment_id,
                    "file_size": size_bytes,
                },
            )
            raise mapped from exc
        except BudgetDocumentTypeNotAllowedError as exc:
            mapped = CapexAttachmentMimeInvalidError(str(exc))
            self._repo.append_audit(
                exercise_id=exercise_id,
                entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
                entity_id=None,
                action=AUDIT_ACTION_UPLOAD_REJECTED,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state={
                    "reason": mapped.code,
                    "investment_id": investment_id,
                    "mime_type": (mime_type or "")[:120],
                    "original_filename": _safe_filename(original_filename)[:300],
                },
            )
            raise mapped from exc

    def list_attachments(
        self, actor: BudgetActor, investment_id: str
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        investment = self._load_investment_or_404(investment_id)
        self._assert_can_access_investment(actor, investment)
        rows = self._repo.list_capex_investment_attachments(
            investment_id=investment_id, active_only=True
        )
        return {"items": [_public_attachment(r) for r in rows]}

    def upload_attachment(
        self,
        actor: BudgetActor,
        *,
        investment_id: str,
        attachment_type: str,
        display_name: str,
        description: str | None,
        original_filename: str,
        content: bytes,
        mime_type: str | None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)

        investment = self._load_investment_or_404(investment_id)
        self._assert_can_access_investment(actor, investment)

        if investment.get("status") != STATUS_DRAFT:
            raise CapexAttachmentInvestmentArchivedError(
                "Não é possível anexar arquivos a investimento arquivado."
            )
        assert_plan_allows_mutation(
            self._repo,
            exercise_id=str(investment["exercise_id"]),
            cost_center_id=str(investment["cost_center_id"]),
            unit_id=str(investment.get("unit_id") or "") or None,
        )

        att_type = str(attachment_type or "").strip().lower()
        if att_type not in ALLOWED_ATTACHMENT_TYPES:
            raise CapexAttachmentTypeInvalidError("Tipo de anexo inválido.")

        name = str(display_name or "").strip()
        if not name:
            raise CapexAttachmentInvalidError("Nome de exibição é obrigatório.")

        safe_original = _safe_filename(original_filename)
        size_bytes = len(content)
        exercise_id = str(investment["exercise_id"])

        idem = (str(idempotency_key).strip() if idempotency_key else None) or None
        if idem:
            existing = self._repo.get_capex_investment_attachment_by_idempotency(
                investment_id=investment_id, idempotency_key=idem
            )
            if existing and existing.get("is_active"):
                return _public_attachment(existing)

        self._validate_file(
            actor,
            exercise_id=exercise_id,
            investment_id=investment_id,
            mime_type=mime_type,
            size_bytes=size_bytes,
            original_filename=safe_original,
        )

        storage_key, _kind = self._storage.save(
            exercise_id=exercise_id,
            original_name=safe_original,
            content=content,
            mime_type=mime_type,
        )

        payload = {
            "investment_id": investment_id,
            "attachment_type": att_type,
            "display_name": name[:300],
            "description": (str(description).strip() if description else None) or None,
            "original_filename": safe_original[:300],
            "mime_type": (mime_type or "").lower().strip(),
            "file_size": size_bytes,
            "storage_key": storage_key,
            "idempotency_key": idem,
            "created_by": actor.user_id,
        }
        try:
            created = self._repo.create_capex_investment_attachment(payload)
        except PluginsRepositoryError as exc:
            # Corrida de idempotência: retornar o registro existente.
            if idem:
                existing = self._repo.get_capex_investment_attachment_by_idempotency(
                    investment_id=investment_id, idempotency_key=idem
                )
                if existing:
                    return _public_attachment(existing)
            raise CapexAttachmentInvalidError(str(exc)) from exc

        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
            entity_id=created["id"],
            action=AUDIT_ACTION_UPLOADED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=_public_attachment(created),
        )
        return _public_attachment(created)

    def resolve_download(
        self, actor: BudgetActor, attachment_id: str
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)

        att = self._repo.get_capex_investment_attachment(attachment_id)
        if not att:
            raise CapexAttachmentNotFoundError("Anexo CAPEX não encontrado.")

        investment = self._load_investment_or_404(str(att["investment_id"]))
        self._assert_can_access_investment(
            actor, investment, as_attachment=True, audit_entity_id=attachment_id
        )

        if not att.get("is_active"):
            raise CapexAttachmentArchivedError(
                "Anexo arquivado não está disponível para download."
            )

        path = self._storage.resolve_file(
            exercise_id=str(investment["exercise_id"]),
            storage_key=str(att["storage_key"]),
        )
        self._repo.append_audit(
            exercise_id=str(investment["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
            entity_id=attachment_id,
            action=AUDIT_ACTION_DOWNLOADED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state={
                "attachment_id": attachment_id,
                "investment_id": investment["id"],
                "original_filename": att.get("original_filename"),
            },
        )
        return {
            "path": path,
            "filename": att.get("original_filename") or att.get("display_name") or "anexo",
            "mime_type": att.get("mime_type") or "application/octet-stream",
            "attachment": _public_attachment(att),
        }

    def archive_attachment(
        self, actor: BudgetActor, attachment_id: str
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)

        att = self._repo.get_capex_investment_attachment(attachment_id)
        if not att:
            raise CapexAttachmentNotFoundError("Anexo CAPEX não encontrado.")

        investment = self._load_investment_or_404(str(att["investment_id"]))
        self._assert_can_access_investment(
            actor, investment, as_attachment=True, audit_entity_id=attachment_id
        )
        assert_plan_allows_mutation(
            self._repo,
            exercise_id=str(investment["exercise_id"]),
            cost_center_id=str(investment["cost_center_id"]),
            unit_id=str(investment.get("unit_id") or "") or None,
        )

        if not att.get("is_active"):
            raise CapexAttachmentArchivedError("Anexo já está arquivado.")

        if investment.get("status") == STATUS_ARCHIVED and not _is_admin(actor):
            # Permite arquivar anexo de investimento arquivado apenas para admin;
            # usuários com responsabilidade ainda podem arquivar metadados.
            pass

        archived = self._repo.archive_capex_investment_attachment(
            attachment_id, actor_id=actor.user_id
        )
        self._repo.append_audit(
            exercise_id=str(investment["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_ATTACHMENT,
            entity_id=attachment_id,
            action=AUDIT_ACTION_ARCHIVED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_attachment(att),
            after_state=_public_attachment(archived),
        )
        return _public_attachment(archived)
