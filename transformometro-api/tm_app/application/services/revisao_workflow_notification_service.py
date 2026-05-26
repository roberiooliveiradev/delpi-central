from __future__ import annotations

import logging
from typing import Any

from tm_app.config import settings
from tm_app.infrastructure.integrations.core_notifications_client import CoreNotificationsClient
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository

logger = logging.getLogger(__name__)


def _parse_csv_list(raw: str) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def _build_revisao_deep_path(processo_id: str, revisao_id: str) -> str:
    base = (settings.TM_PORTAL_ROUTE or "/apps/transformometro").rstrip("/")
    return f"{base}/processos/{processo_id}/revisoes/{revisao_id}"


class RevisaoWorkflowNotificationService:
    def __init__(self, client: CoreNotificationsClient | None = None) -> None:
        self._client = client or CoreNotificationsClient()

    def notify_submitted(
        self,
        revisao: dict[str, Any],
        *,
        actor_email: str | None,
    ) -> None:
        if not self._client.is_configured:
            return

        processo_id = str(revisao.get("processo_id") or "")
        revisao_id = str(revisao.get("revisao_id") or "")
        if not processo_id or not revisao_id:
            return

        label = self._processo_label(processo_id)
        versao = revisao.get("versao_revisao")
        message = f"{label} — revisão v{versao} aguarda aprovação."

        recipients = self._approver_recipients(exclude_email=actor_email)
        if not recipients:
            logger.info("workflow_notify_submitted_skipped no_recipients revisao=%s", revisao_id)
            return

        self._dispatch(
            title="Transformômetro — revisão para aprovar",
            message=message,
            notification_type="info",
            processo_id=processo_id,
            revisao_id=revisao_id,
            event="revisao:submitted",
            recipients=recipients,
        )

    def notify_decision(
        self,
        revisao: dict[str, Any],
        *,
        decision: str,
        actor_email: str | None,
        motivo: str | None = None,
    ) -> None:
        if not self._client.is_configured:
            return

        processo_id = str(revisao.get("processo_id") or "")
        revisao_id = str(revisao.get("revisao_id") or "")
        if not processo_id or not revisao_id:
            return

        submitter_info = self._submitter_info(revisao_id, exclude_email=actor_email)
        if not submitter_info:
            logger.info(
                "workflow_notify_decision_skipped no_submitter revisao=%s decision=%s",
                revisao_id,
                decision,
            )
            return

        label = self._processo_label(processo_id)
        versao = revisao.get("versao_revisao")
        approved = decision == "aprovada"
        title = (
            "Transformômetro — revisão aprovada"
            if approved
            else "Transformômetro — revisão rejeitada"
        )
        message = f"{label} — revisão v{versao} foi {'aprovada' if approved else 'rejeitada'}."
        if not approved and motivo:
            message += f" Motivo: {motivo.strip()}"

        recipients: dict[str, list[str]] = {}
        if submitter_info.get("user_id"):
            recipients["userIds"] = [submitter_info["user_id"]]
        elif submitter_info.get("email"):
            recipients["emails"] = [submitter_info["email"]]

        self._dispatch(
            title=title,
            message=message,
            notification_type="success" if approved else "warning",
            processo_id=processo_id,
            revisao_id=revisao_id,
            event=f"revisao:{decision}",
            recipients=recipients,
        )

    def _dispatch(
        self,
        *,
        title: str,
        message: str,
        notification_type: str,
        processo_id: str,
        revisao_id: str,
        event: str,
        recipients: dict[str, list[str]],
    ) -> None:
        deep_path = _build_revisao_deep_path(processo_id, revisao_id)
        portal_route = (settings.TM_PORTAL_ROUTE or "/apps/transformometro").rstrip("/") or "/apps/transformometro"

        payload: dict[str, Any] = {
            "title": title,
            "message": message,
            "type": notification_type,
            "category": "transformometro",
            "sourceApp": "transformometro",
            "action": {
                "type": "portal_route",
                "label": "Abrir revisão",
                "target": portal_route,
            },
            "metadata": {
                "source": "transformometro",
                "event": event,
                "deepPath": deep_path,
                "dedupeKey": f"transformometro:{event}:{revisao_id}",
                "processoId": processo_id,
                "revisaoId": revisao_id,
            },
            **recipients,
        }

        result = self._client.dispatch(payload)
        if result is None and self._client.is_configured:
            logger.warning("workflow_notification_dispatch_empty event=%s", event)

    def _approver_recipients(self, *, exclude_email: str | None) -> dict[str, list[str]]:
        role_ids = _parse_csv_list(settings.TM_WORKFLOW_APPROVER_ROLE_IDS)

        if role_ids:
            return {"roleIds": role_ids}

        emails = _parse_csv_list(settings.TM_WORKFLOW_APPROVER_EMAILS)
        if exclude_email:
            normalized = exclude_email.strip().lower()
            emails = [e for e in emails if e.lower() != normalized]

        if emails:
            return {"emails": emails}

        return {}

    @staticmethod
    def _submitter_info(revisao_id: str, *, exclude_email: str | None) -> dict[str, str] | None:
        """Retorna {user_id, email} do submitter, preferindo user_id (LGPD minimização)."""
        row = AuditRepository().fetch_one(
            """
            SELECT user_id, user_email FROM transformometro.audit_logs
            WHERE entity_type = 'revisao'
              AND entity_id = %s
              AND action = 'workflow_submeter'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (revisao_id,),
        )
        if not row:
            return None
        user_id = str(row.get("user_id") or "").strip()
        email = str(row.get("user_email") or "").strip()
        if exclude_email and email and email.lower() == exclude_email.strip().lower():
            return None
        if not user_id and not email:
            return None
        return {"user_id": user_id, "email": email}

    @staticmethod
    def _processo_label(processo_id: str) -> str:
        processo = ProcessoRepository().get(processo_id)
        if not processo:
            return f"Processo {processo_id[:8]}"
        codigo = processo.get("codigo_processo")
        nome = processo.get("nome_processo")
        if codigo and nome:
            return f"{codigo} — {nome}"
        return str(codigo or nome or processo_id[:8])
