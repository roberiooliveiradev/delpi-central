"""Monitoramento autônomo de paradas por CT (PC-MES-CT-AUTONOMOUS-DOWNTIME).

Acompanha os postos sensorizados (vínculo pulse_counter no Production
Pulse) **mesmo sem run MES ativo**: incremento real do contador abre
producing com run_id=NULL; inatividade além do threshold legado
abre stopped + parada source='system' sem vínculo de OP; o
retorno do contador encerra a parada automaticamente.

Regras de fronteira (doc MES-CT-AUTONOMOUS-DOWNTIME, ADR-03/04/05):

- CT com run running/paused → o caminho do run governa (skip);
- snapshot não usable → observabilidade degradada, nunca parada
  inventada;
- sem baseline de incremento → nenhuma parada retroativa;
- telemetria nunca gera produção — fatos autônomos não carregam OP;
- serialização por pg_advisory_xact_lock sobre a chave do CT — o
  tick contende com Play/Pause/Resume/Stop/handoff e com outra instância
  do poller sem nunca produzir fatos concorrentes.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Iterator

from production_control_app.domain.errors import PulseGatewayError
from production_control_app.domain.services.mes_autonomous_monitoring import (
    AutonomousAction,
    decide_autonomous_tick,
)
from production_control_app.domain.services.pulse_snapshot import (
    classify_pulse_snapshot,
)

logger = logging.getLogger(__name__)

_BRANCHED = ("01", "02")


def _parse_seen_at(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class MesAutonomousMonitorService:
    """Orquestra o tick autônomo: descobre CTs via Pulse, aplica a decisão
    de domínio e grava fatos/cursor em uma transação por CT."""

    def __init__(
        self,
        *,
        pulse_gateway: Any,
        run_repository: Any,
        observer_repository: Any,
        mes_lifecycle: Any,
        audit_repository: Any | None = None,
        connection_factory: Callable[[], Any],
        enabled: bool = False,
        work_centers_allowlist: str = "",
        auto_downtime_seconds: int = 120,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._pulse = pulse_gateway
        self._runs = run_repository
        self._observers = observer_repository
        self._mes = mes_lifecycle
        self._audit = audit_repository
        self._connection_factory = connection_factory
        self._enabled = bool(enabled)
        self._allowlist = self._parse_allowlist(work_centers_allowlist)
        self._threshold = max(int(auto_downtime_seconds or 0), 0)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _parse_allowlist(raw: str) -> set[str] | None:
        """* ou vazio com enabled=True → todos os sensorizados;
        senão conjunto branch:CT."""
        text = str(raw or "").strip()
        if text in {"", "*"}:
            return None
        return {item.strip() for item in text.split(",") if item.strip()}

    def _allowed(self, branch: str, work_center: str) -> bool:
        if self._allowlist is None:
            return True
        return f"{branch}:{work_center}" in self._allowlist

    @contextmanager
    def _transaction(self) -> Iterator[Any]:
        conn = self._connection_factory()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def tick_all(self) -> int:
        """Um ciclo de monitoramento — um GET de enumeração por filial."""
        if not self._enabled or self._threshold <= 0:
            return 0
        processed = 0
        for branch in _BRANCHED:
            try:
                payload = self._pulse.fetch_branch_counter_snapshots(
                    branch=branch, role_key="pulse_counter"
                )
            except PulseGatewayError as exc:
                # Indisponibilidade da telemetria NUNCA cria parada — só
                # observabilidade degradada no log (nenhum fato gravado).
                logger.warning(
                    "mes_autonomous_pulse_unavailable branch=%s err=%s",
                    branch,
                    exc,
                )
                continue
            items = payload.get("items") or []
            by_center: dict[str, list[dict[str, Any]]] = {}
            for item in items:
                if not isinstance(item, dict):
                    continue
                center = str(item.get("workCenterCode") or "").strip()
                if center:
                    by_center.setdefault(center, []).append(item)
            for work_center, devices in by_center.items():
                if not self._allowed(branch, work_center):
                    continue
                try:
                    processed += self._tick_work_center(
                        branch=branch, work_center=work_center, devices=devices
                    )
                except Exception:  # noqa: BLE001 — um CT ruim não derruba os demais
                    logger.exception(
                        "mes_autonomous_tick_failed branch=%s work_center=%s",
                        branch,
                        work_center,
                    )
        return processed

    def _tick_work_center(
        self, *, branch: str, work_center: str, devices: list[dict[str, Any]]
    ) -> int:
        at = self._clock()
        with self._transaction() as conn:
            if not self._observers.try_lock_work_center(
                branch=branch, work_center=work_center, conn=conn
            ):
                return 0  # outro writer no CT (Play/transição/poller)
            active = self._runs.get_active_run(
                branch=branch, work_center=work_center, conn=conn
            )
            observer = self._observers.get(
                branch=branch, work_center=work_center, conn=conn
            )
            device = devices[0] if len(devices) == 1 else None
            classification = classify_pulse_snapshot(device)
            decision = decide_autonomous_tick(
                has_active_run=active is not None,
                observer=observer,
                devices=devices,
                usable=classification == "usable",
                offline=classification == "offline",
                threshold_seconds=self._threshold,
                at=at,
            )
            action = decision.action

            if action is AutonomousAction.SKIP:
                return 0

            device_id = str(device.get("deviceId")) if device else None
            counter = int(device.get("counter") or 0) if device else 0
            epoch = int(device.get("counterEpoch") or 0) if device else 0
            seen_at = _parse_seen_at(device.get("lastSeenAt")) if device else None

            if action is AutonomousAction.DEGRADED:
                self._observers.upsert(
                    branch=branch,
                    work_center=work_center,
                    device_id=device_id or (observer or {}).get("device_id"),
                    counter_epoch=epoch if device else int((observer or {}).get("counter_epoch") or 0),
                    last_counter=counter if device else int((observer or {}).get("last_counter") or 0),
                    last_increment_at=(observer or {}).get("last_increment_at"),
                    baseline_established_at=(observer or {}).get("baseline_established_at"),
                    device_online=False,
                    degraded_reason=decision.degraded_reason,
                    last_seen_at=seen_at,
                    conn=conn,
                )
                if (observer or {}).get("degraded_reason") != decision.degraded_reason:
                    logger.info(
                        "mes_autonomous_degraded branch=%s work_center=%s reason=%s",
                        branch, work_center, decision.degraded_reason,
                    )
                return 0

            last_increment_at = (observer or {}).get("last_increment_at")
            baseline_at = (observer or {}).get("baseline_established_at")

            if action is AutonomousAction.OBSERVE:
                identity_changed = (
                    observer is not None
                    and (
                        str(observer.get("device_id") or "") != (device_id or "")
                        or int(observer.get("counter_epoch") or 0) != epoch
                    )
                )
                self._observers.upsert(
                    branch=branch,
                    work_center=work_center,
                    device_id=device_id,
                    counter_epoch=epoch,
                    last_counter=counter,
                    # Mudança de identidade do contador reinicia o baseline
                    # (nunca parada retroativa por troca/reset de sensor);
                    # realinhamento de regressão preserva o baseline.
                    last_increment_at=None if identity_changed else last_increment_at,
                    baseline_established_at=None if identity_changed else baseline_at,
                    device_online=True,
                    degraded_reason=None,
                    last_seen_at=seen_at,
                    conn=conn,
                )
                return 0

            if action is AutonomousAction.ACTIVITY:
                closed_dt = self._mes.record_autonomous_resumed(
                    branch=branch, work_center=work_center, conn=conn, at=at
                )
                if closed_dt is None:
                    self._mes.record_autonomous_producing(
                        branch=branch, work_center=work_center, conn=conn, at=at
                    )
                self._observers.upsert(
                    branch=branch,
                    work_center=work_center,
                    device_id=device_id,
                    counter_epoch=epoch,
                    last_counter=counter,
                    last_increment_at=at,
                    baseline_established_at=baseline_at or at,
                    device_online=True,
                    degraded_reason=None,
                    last_seen_at=seen_at,
                    conn=conn,
                )
                if self._audit is not None:
                    self._audit.append(
                        branch=branch,
                        work_center=work_center,
                        action=(
                            "automatic_downtime_ended"
                            if closed_dt is not None
                            else "autonomous_producing_started"
                        ),
                        actor_type="system",
                        actor_ref="autonomous-monitor",
                        occurred_at=at,
                        conn=conn,
                        details={
                            "autonomous": True,
                            "counter": counter,
                            "counterEpoch": epoch,
                            "deviceId": device_id,
                            "downtimeId": (
                                closed_dt.get("id") if closed_dt else None
                            ),
                        },
                    )
                self._notify(
                    branch,
                    work_center,
                    reason=(
                        "automatic_downtime_ended"
                        if closed_dt is not None
                        else "autonomous_activity"
                    ),
                    extra={"operationalState": "producing", "runId": None},
                )
                logger.info(
                    "mes_autonomous_activity branch=%s work_center=%s resumed=%s",
                    branch, work_center, closed_dt is not None,
                )
                return 1

            if action is AutonomousAction.STOPPED:
                started_at = decision.started_at or at
                created = self._mes.record_autonomous_stopped(
                    branch=branch,
                    work_center=work_center,
                    conn=conn,
                    at=started_at,
                )
                self._observers.upsert(
                    branch=branch,
                    work_center=work_center,
                    device_id=device_id,
                    counter_epoch=epoch,
                    last_counter=counter,
                    last_increment_at=last_increment_at,
                    baseline_established_at=baseline_at,
                    device_online=True,
                    degraded_reason=None,
                    last_seen_at=seen_at,
                    conn=conn,
                )
                if created is None:
                    return 0  # parada autônoma já existia (idempotente)
                if self._audit is not None:
                    self._audit.append(
                        branch=branch,
                        work_center=work_center,
                        action="automatic_downtime_started",
                        actor_type="system",
                        actor_ref="autonomous-monitor",
                        occurred_at=at,
                        conn=conn,
                        details={
                            "autonomous": True,
                            "thresholdSeconds": self._threshold,
                            "thresholdSource": "legacy",
                            "lastIncrementAt": (
                                last_increment_at.isoformat()
                                if hasattr(last_increment_at, "isoformat")
                                else last_increment_at
                            ),
                            "downtimeId": created.get("id"),
                            "deviceId": device_id,
                        },
                    )
                self._notify(
                    branch,
                    work_center,
                    reason="automatic_downtime_started",
                    extra={
                        "operationalState": "stopped",
                        "runId": None,
                        "downtime": {"id": created["id"], "startedAt": started_at.isoformat()},
                    },
                )
                logger.info(
                    "mes_autonomous_stopped branch=%s work_center=%s started_at=%s",
                    branch, work_center, started_at,
                )
                return 1

            # NOTHING: atualiza apenas saúde do vínculo (nenhum fato).
            self._observers.upsert(
                branch=branch,
                work_center=work_center,
                device_id=device_id,
                counter_epoch=epoch,
                last_counter=counter,
                last_increment_at=last_increment_at,
                baseline_established_at=baseline_at,
                device_online=True,
                degraded_reason=None,
                last_seen_at=seen_at,
                conn=conn,
            )
            return 0

    @staticmethod
    def _notify(
        branch: str,
        work_center: str,
        *,
        reason: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Mesmo barramento das transições do run — o cockpit reconcilia
        leitura MES do posto sem precisar de run."""
        from production_control_app.application.services.machine_load_realtime_hub import (  # noqa: E501
            machine_load_realtime_hub,
        )

        message: dict[str, Any] = {
            "type": "production_run_updated",
            "reason": reason,
            "branch": branch,
            "workCenter": work_center,
        }
        if extra:
            message.update(extra)
        machine_load_realtime_hub.schedule_broadcast(
            f"{branch}:{work_center}", message
        )
        machine_load_realtime_hub.schedule_broadcast(branch, message)
