"""Avaliador de alertas gerenciais de paradas MES (Etapa 6 — RQ-6.6/6.7).

Camada de ATENÇÃO apenas: reavalia fatos canônicos
(downtime_events / mes_downtime_treatments) em cadência própria dentro
do poller existente e dispara notificações Minha DELPI via Core API —
o mesmo mecanismo oficial do Operator Feedback, sem sino ou tabela de
notificações paralela.

Regras (todas parametrizadas por env — parâmetro ausente = regra
inativa, nenhum limite inventado):
- prolonged_open_stop   PC_MES_DOWNTIME_CRITICAL_OPEN_SECONDS
- unclassified_backlog  PC_MES_DOWNTIME_UNCLASSIFIED_ALERT_THRESHOLD
- overdue_action        PC_MES_DOWNTIME_OVERDUE_ACTION_DAYS

Dedup (RQ-6.7): cada candidato é persistido em
mes_downtime_alert_dispatches com assinatura do estado relevante —
o dispatch só acontece quando a assinatura muda, o que impede
notificação repetida da mesma condição sem mudança relevante.

Destinatários: gestores MES da filial — permissionCodes seleciona quem
trata paradas; requiredPermissionCodes impõe a filial (AND), evitando
vazamento entre filiais (mesmo padrão do Operator Feedback).

Best-effort absoluto: falha de leitura ou de dispatch vira log — nunca
afeta o poller nem os fatos.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

CATEGORY = "production_control_mes_downtime_alerts"
_SOURCE_APP = "production-control"
_TREAT_PERMISSION = "delpi-mes.downtimes.treat"
_BRANCH_PERMISSIONS = {"01": "delpi-mes.view.filial-01", "02": "delpi-mes.view.filial-02"}
_BRANCHES = ("01", "02")

# Throttle em memória: a avaliação é barata, mas não precisa rodar a
# cada tick (~500 ms) — um restart reavalia, o dedup persistido segura.
_next_due_monotonic: float | None = None


def evaluation_due(
    monotonic: float, *, interval_seconds: int
) -> bool:
    global _next_due_monotonic
    if _next_due_monotonic is None or monotonic >= _next_due_monotonic:
        _next_due_monotonic = monotonic + max(30, interval_seconds)
        return True
    return False


def reset_evaluation_schedule() -> None:
    """Test hook — limpa a cadência entre avaliações."""
    global _next_due_monotonic
    _next_due_monotonic = None


class MesDowntimeAlertService:
    """Avalia condições e dispara alertas deduplicados via Core API."""

    def __init__(
        self,
        *,
        repository: Any,
        notification_gateway: Any | None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        critical_open_seconds: int | None = None,
        unclassified_threshold: int | None = None,
        overdue_action_days: int | None = None,
    ) -> None:
        self._repository = repository
        self._gateway = notification_gateway
        self._clock = clock
        self._critical_open_seconds = critical_open_seconds
        self._unclassified_threshold = unclassified_threshold
        self._overdue_action_days = overdue_action_days

    def tick(self) -> dict[str, Any]:
        """Uma avaliação completa. Nunca levanta exceção."""
        now = self._clock()
        evaluated = {"candidates": 0, "dispatched": 0, "skipped": 0}
        if self._gateway is None:
            return {**evaluated, "enabled": False}
        for branch in _BRANCHES:
            for candidate in self._candidates(branch, now):
                evaluated["candidates"] += 1
                if self._claim(candidate, now):
                    if self._dispatch(candidate):
                        evaluated["dispatched"] += 1
                else:
                    evaluated["skipped"] += 1
        return {**evaluated, "enabled": True}

    # ---- candidatos -------------------------------------------------

    def _candidates(
        self, branch: str, now: datetime
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        if self._critical_open_seconds is not None:
            cutoff = now - timedelta(seconds=self._critical_open_seconds)
            for row in self._repository.list_open_downtimes_older_than(
                branch=branch, reference_before=cutoff
            ):
                elapsed = int((now - row["started_at"]).total_seconds())
                reason = row.get("reason_code") or "unclassified"
                candidates.append(
                    {
                        "rule": "prolonged_open_stop",
                        "branch": branch,
                        "subject_key": str(row["id"]),
                        # classificar a parada muda a assinatura — nova
                        # notificação com o motivo (mudança relevante).
                        "signature": f"{row['id']}:{reason}",
                        "title": "Parada prolongada em andamento",
                        "message": (
                            f"A bancada {row['work_center']} está parada há "
                            f"{elapsed // 3600}h{(elapsed % 3600) // 60:02d}min "
                            f"na filial {branch} — motivo: "
                            f"{row.get('reason_label') or 'não classificado'}."
                        ),
                        "target": (
                            f"/apps/delpi-mes/downtimes?branch={branch}"
                            f"&downtimeId={row['id']}"
                        ),
                        "metadata": {
                            "downtimeId": str(row["id"]),
                            "workCenter": row["work_center"],
                            "reasonCode": row.get("reason_code"),
                            "elapsedSeconds": elapsed,
                        },
                    }
                )
        if self._unclassified_threshold is not None:
            count = self._repository.count_unclassified_downtimes(
                branch=branch
            )
            if count > self._unclassified_threshold:
                candidates.append(
                    {
                        "rule": "unclassified_backlog",
                        "branch": branch,
                        "subject_key": "backlog",
                        # o contador é a assinatura — backlog estável não
                        # redispara; mudança de volume é mudança relevante.
                        "signature": f"count:{count}",
                        "title": "Paradas pendentes de classificação",
                        "message": (
                            f"A filial {branch} acumula {count} paradas "
                            f"sem classificação confirmada "
                            f"(limite: {self._unclassified_threshold})."
                        ),
                        "target": (
                            f"/apps/delpi-mes/downtimes?branch={branch}"
                            f"&classification=pending"
                        ),
                        "metadata": {
                            "unclassifiedCount": count,
                            "threshold": self._unclassified_threshold,
                        },
                    }
                )
        if self._overdue_action_days is not None:
            cutoff = now - timedelta(days=self._overdue_action_days)
            for row in self._repository.list_overdue_open_treatments(
                branch=branch, reference_before=cutoff
            ):
                days = int((now - row["created_at"]).total_seconds() // 86400)
                # bucket diário: cada novo dia de atraso é mudança
                # relevante; o mesmo dia não redispara.
                candidates.append(
                    {
                        "rule": "overdue_action",
                        "branch": branch,
                        "subject_key": str(row["downtime_id"]),
                        "signature": f"{row['downtime_id']}:{row['status']}:day{days}",
                        "title": "Tratamento de parada vencido",
                        "message": (
                            f"O tratamento da parada da bancada "
                            f"{row['work_center']} está "
                            f"{'em triagem' if row['status'] == 'pending' else 'encaminhado'} "
                            f"há {days} dias na filial {branch} "
                            f"(limite: {self._overdue_action_days})."
                        ),
                        "target": (
                            f"/apps/delpi-mes/downtimes?branch={branch}"
                            f"&downtimeId={row['downtime_id']}"
                        ),
                        "metadata": {
                            "downtimeId": str(row["downtime_id"]),
                            "workCenter": row["work_center"],
                            "treatmentStatus": row["status"],
                            "overdueDays": days,
                        },
                    }
                )
        return candidates

    # ---- dedup + dispatch --------------------------------------------

    def _claim(self, candidate: dict[str, Any], now: datetime) -> bool:
        alert_key = (
            f"{candidate['rule']}:{candidate['branch']}:"
            f"{candidate['subject_key']}"
        )
        candidate["alert_key"] = alert_key
        try:
            return self._repository.claim_if_signature_changed(
                alert_key=alert_key,
                branch=candidate["branch"],
                rule=candidate["rule"],
                subject_key=candidate["subject_key"],
                signature=candidate["signature"],
                now=now,
            )
        except Exception:  # noqa: BLE001 — dedup falho não derruba o tick
            logger.exception(
                "mes_downtime_alert_claim_failed alert_key=%s", alert_key
            )
            return False

    def _dispatch(self, candidate: dict[str, Any]) -> bool:
        branch_permission = _BRANCH_PERMISSIONS.get(candidate["branch"])
        if not branch_permission:
            return False
        payload = {
            "title": candidate["title"],
            "message": candidate["message"],
            "type": "warning",
            "category": CATEGORY,
            "presentation": "text",
            "sourceApp": _SOURCE_APP,
            "permissionCodes": [_TREAT_PERMISSION],
            "requiredPermissionCodes": [branch_permission],
            "action": {
                "type": "portal_route",
                "label": "Abrir Gestão de Paradas",
                "target": candidate["target"],
            },
            "metadata": {
                "event": candidate["rule"],
                "alertKey": candidate["alert_key"],
                "branch": candidate["branch"],
                **candidate["metadata"],
            },
        }
        try:
            self._gateway.dispatch(payload)
            return True
        except Exception:  # noqa: BLE001 — notificação nunca derruba o ciclo
            logger.warning(
                "mes_downtime_alert_dispatch_failed alert_key=%s",
                candidate["alert_key"],
                exc_info=True,
            )
            return False
