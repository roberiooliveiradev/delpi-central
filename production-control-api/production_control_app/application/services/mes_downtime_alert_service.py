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

Dedup (RQ-6.7): cada candidato reserva um claim com lease em
mes_downtime_alert_dispatches; a assinatura só vira "entregue" após
dispatch confirmado — falha transitória libera o claim para retry no
próximo tick, e crash do avaliador expira o lease. Mudança da
assinatura (estado relevante) reabre a notificação; a mesma condição
não redispara.

Telemetria (RQ-6.8): a parada prolongada só alerta quando o CT tem
sinal Pulse confiável — observador degradado/stale suprime o alerta,
e ocorrência de origem telemétrica sem observador nenhum também
(ausência de sinal ≠ máquina parada). Paradas manuais sem observador
seguem alertáveis.

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

# Lease do claim de dedup: cobre a latência máxima do dispatch (Core
# API timeout ~10s) com margem — após expirar, outro avaliador pode
# retentar o alerta sem risco de duplicar entrega concorrente.
_CLAIM_LEASE_SECONDS = 120

# Origens escritas por telemetria (contador/autônomo/recuperação): sem
# observador registrado, a parada aberta é indistinguível de falha de
# sinal e não deve alertar. Paradas manuais seguem alertáveis.
_TELEMETRY_SOURCES = {"automatic_detection", "system", "recovery"}

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
        telemetry_stale_minutes: int = 30,
        claim_lease_seconds: int = _CLAIM_LEASE_SECONDS,
    ) -> None:
        self._repository = repository
        self._gateway = notification_gateway
        self._clock = clock
        self._critical_open_seconds = critical_open_seconds
        self._unclassified_threshold = unclassified_threshold
        self._overdue_action_days = overdue_action_days
        self._telemetry_stale_minutes = telemetry_stale_minutes
        self._claim_lease_seconds = claim_lease_seconds

    def tick(self) -> dict[str, Any]:
        """Uma avaliação completa. Nunca levanta exceção."""
        now = self._clock()
        evaluated = {
            "candidates": 0,
            "dispatched": 0,
            "skipped": 0,
            "telemetrySuppressed": 0,
        }
        if self._gateway is None:
            return {**evaluated, "enabled": False}
        for branch in _BRANCHES:
            for candidate in self._candidates(branch, now):
                evaluated["candidates"] += 1
                if candidate.get("suppressed"):
                    evaluated["telemetrySuppressed"] += 1
                elif self._claim(candidate, now):
                    if self._dispatch(candidate):
                        self._confirm(candidate, now)
                        evaluated["dispatched"] += 1
                    else:
                        self._release(candidate)
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
            observers = {
                (o.get("work_center") or ""): o
                for o in self._repository.list_observer_states(
                    branch=branch
                )
            }
            for row in self._repository.list_open_downtimes_older_than(
                branch=branch, reference_before=cutoff
            ):
                if not self._telemetry_trusted(
                    row, observers.get(row["work_center"]), now
                ):
                    candidates.append(
                        {"rule": "prolonged_open_stop", "suppressed": True}
                    )
                    continue
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

    def _telemetry_trusted(
        self,
        row: dict[str, Any],
        observer: dict[str, Any] | None,
        now: datetime,
    ) -> bool:
        """A parada aberta é evidenciada por sinal confiável?

        Sem observador: só paradas manuais alertam — origem telemétrica
        sem vínculo é indistinguível de ausência de sinal (RQ-6.8).
        Com observador: exige dispositivo online e sinal recente —
        CT degradado/stale não prova que a máquina segue parada.
        """
        if observer is None:
            return (row.get("source") or "") not in _TELEMETRY_SOURCES
        if not observer.get("device_online"):
            return False
        last_seen = observer.get("last_seen_at")
        if isinstance(last_seen, str):
            try:
                last_seen = datetime.fromisoformat(
                    last_seen.replace("Z", "+00:00")
                )
            except ValueError:
                last_seen = None
        if last_seen is None:
            return False
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=now.tzinfo)
        return (now - last_seen).total_seconds() <= (
            self._telemetry_stale_minutes * 60
        )

    # ---- dedup + dispatch --------------------------------------------

    def _claim(self, candidate: dict[str, Any], now: datetime) -> bool:
        alert_key = (
            f"{candidate['rule']}:{candidate['branch']}:"
            f"{candidate['subject_key']}"
        )
        candidate["alert_key"] = alert_key
        try:
            return self._repository.claim_pending(
                alert_key=alert_key,
                branch=candidate["branch"],
                rule=candidate["rule"],
                subject_key=candidate["subject_key"],
                signature=candidate["signature"],
                now=now,
                lease_expiry=now
                - timedelta(seconds=self._claim_lease_seconds),
            )
        except Exception:  # noqa: BLE001 — dedup falho não derruba o tick
            logger.exception(
                "mes_downtime_alert_claim_failed alert_key=%s", alert_key
            )
            return False

    def _confirm(self, candidate: dict[str, Any], now: datetime) -> None:
        """Confirma entrega após dispatch — falha aqui só posterga o
        marco: a assinatura fica pendente e o lease permite retry
        (preferível duplicar a perder o alerta)."""
        try:
            self._repository.confirm_dispatch(
                alert_key=candidate["alert_key"],
                signature=candidate["signature"],
                now=now,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "mes_downtime_alert_confirm_failed alert_key=%s",
                candidate["alert_key"],
            )

    def _release(self, candidate: dict[str, Any]) -> None:
        """Falha transitória de dispatch NUNCA marca o alerta como
        entregue — libera o claim para o próximo tick retentar."""
        try:
            self._repository.release_claim(
                alert_key=candidate["alert_key"],
                signature=candidate["signature"],
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "mes_downtime_alert_release_failed alert_key=%s",
                candidate["alert_key"],
            )

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
