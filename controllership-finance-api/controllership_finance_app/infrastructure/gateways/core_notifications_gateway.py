"""Dispatch de notificações via Core `POST /integrations/notifications` (T02).

Contrato PROVEN (doc 17/T02): S2S service token, `sourceApp`, action
`portal_route`, recipients por `userIds`. Best-effort explícito:

```text
NOTIFICATION_FAILURE != BUSINESS_STATE_CHANGE
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
```

A outbox `closing_notification_event` é a prova de emissão; o estado de
entrega (`EMITTED → DISPATCHED | FAILED`) reflete a resposta do Core e
nunca altera estado de negócio.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.config import settings
from controllership_finance_app.domain.closing_checklist.errors import (
    PersistenceUnavailable,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

logger = logging.getLogger("controllership_finance.notifications")

_SCHEMA = SCHEMA_NAME
SOURCE_APP = "controllership-finance"


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


_EVENT_TITLES = {
    "PACKAGE_SUBMITTED_FOR_REVIEW": "Pacote de fechamento enviado para revisão",
    "PACKAGE_CLARIFICATION_OPENED": "Esclarecimento solicitado no pacote",
    "PACKAGE_CLARIFICATION_RESOLVED": "Esclarecimento respondido no pacote",
    "COMPETENCE_TERMINALLY_REJECTED": "Competência rejeitada terminalmente",
    "COMPETENCE_REJECTION_REVERTED": "Rejeição terminal revertida",
}

_EVENT_MESSAGES = {
    "PACKAGE_SUBMITTED_FOR_REVIEW": (
        "Um pacote da competência {period} ({area}) aguarda sua revisão "
        "na área {review_area}."
    ),
    "PACKAGE_CLARIFICATION_OPENED": (
        "Foi aberto um esclarecimento no pacote da competência {period}."
    ),
    "PACKAGE_CLARIFICATION_RESOLVED": (
        "Um esclarecimento do pacote da competência {period} foi "
        "respondido."
    ),
    "COMPETENCE_TERMINALLY_REJECTED": (
        "A competência {period} foi rejeitada terminalmente."
    ),
    "COMPETENCE_REJECTION_REVERTED": (
        "A rejeição terminal da competência {period} foi revertida."
    ),
}


def _action_target(payload: dict[str, Any]) -> str:
    period = str(payload.get("period") or "")
    return f"/apps/controllership-finance/closing/packages/{period}"


class CoreNotificationsDispatcher:
    """Best-effort dispatcher da outbox para o Core Notifications.

    Não é port de negócio: chamado após a mutação que emitiu o evento,
    fora da transação, e tolera indisponibilidade — evento permanece
    `EMITTED`/`FAILED` sem reverter nada.
    """

    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        timeout: float | None = None,
        http_post=None,
    ) -> None:
        self.core_api_url = (
            core_api_url or settings.CORE_API_BASE_URL
        ).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.timeout = float(
            timeout
            if timeout is not None
            else (settings.CORE_API_TIMEOUT or 10)
        )
        self._http_post = http_post or httpx.post

    def dispatch_pending(
        self, period: str | None = None, *, limit: int = 50
    ) -> dict[str, int]:
        """Despacha eventos `EMITTED`/`FAILED` pendentes; retorna contagens."""
        if not plugins_db_configured():
            raise PersistenceUnavailable(
                "Persistência do workflow não configurada."
            )
        counts = {"dispatched": 0, "failed": 0, "skipped": 0}
        if not self.service_token:
            logger.warning("cf_notifications_skipped_no_service_token")
            return {**counts, "skipped": -1}
        with plugins_db_connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                clauses = ["delivery_state IN ('EMITTED','FAILED')"]
                params: list[Any] = []
                if period:
                    clauses.append(
                        "competence_id = (SELECT competence_id FROM "
                        f"{_q('monthly_competence')} WHERE period = %s)"
                    )
                    params.append(period)
                cur.execute(
                    f"""
                    SELECT notification_id
                      FROM {_q('closing_notification_event')}
                     WHERE {" AND ".join(clauses)}
                     ORDER BY emitted_at
                     LIMIT %s
                    """,
                    (*params, limit),
                )
                event_ids = [
                    row["notification_id"] for row in cur.fetchall()
                ]
            for event_id in event_ids:
                # R-105-05: claim por evento com FOR UPDATE SKIP LOCKED —
                # réplicas/poller e dispatcher pós-commit nunca despacham
                # o mesmo evento duas vezes (dedupe local; o Core ainda
                # recebe dedupeKey no metadata).
                with conn.transaction():
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(
                            f"""
                            SELECT notification_id, event_type,
                                   recipient_subject, payload, emitted_at
                              FROM {_q('closing_notification_event')}
                             WHERE notification_id = %s
                               AND delivery_state IN ('EMITTED','FAILED')
                             FOR UPDATE SKIP LOCKED
                            """,
                            (event_id,),
                        )
                        event = cur.fetchone()
                        if event is None:
                            counts["skipped"] += 1
                            continue
                        outcome = self._dispatch_one(event)
                        state = (
                            "DISPATCHED" if outcome["ok"] else "FAILED"
                        )
                        cur.execute(
                            f"""
                            UPDATE {_q('closing_notification_event')}
                               SET delivery_state = %s,
                                   dispatched_at = now(),
                                   dispatch_error = %s
                             WHERE notification_id = %s
                            """,
                            (
                                state,
                                outcome.get("error"),
                                event["notification_id"],
                            ),
                        )
                counts["dispatched" if outcome["ok"] else "failed"] += 1
        return counts

    def _dispatch_one(self, event: dict) -> dict[str, Any]:
        payload = event.get("payload") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        event_type = event["event_type"]
        title = _EVENT_TITLES.get(
            event_type, "Atualização do fechamento mensal"
        )
        message = _EVENT_MESSAGES.get(
            event_type,
            "Há uma atualização na competência {period}.",
        ).format(
            period=payload.get("period", ""),
            area=payload.get("recipient_area", ""),
            review_area=payload.get("area", ""),
        )
        body: dict[str, Any] = {
            "title": title,
            "message": message,
            "type": "info",
            "category": "controllership_finance",
            "sourceApp": SOURCE_APP,
            "action": {
                "type": "portal_route",
                "label": "Abrir pacotes",
                "target": _action_target(payload),
            },
            "userIds": [str(event["recipient_subject"])],
            "requiredPermissionCodes": [
                "controllership-finance.access"
            ],
            "metadata": {
                "source": SOURCE_APP,
                "event": event_type,
                "dedupeKey": str(event["notification_id"]),
                "competence": payload.get("period"),
            },
        }
        try:
            response = self._http_post(
                f"{self.core_api_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {self.service_token}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                error = f"core_{response.status_code}"
                logger.warning(
                    "cf_notification_rejected event=%s status=%s",
                    event_type,
                    response.status_code,
                )
                return {"ok": False, "error": error[:255]}
            return {"ok": True}
        except Exception as exc:
            logger.warning(
                "cf_notification_dispatch_failed event=%s err=%s",
                event_type,
                exc,
            )
            return {"ok": False, "error": str(exc)[:255]}
