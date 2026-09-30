from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import logging

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.config import settings
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DelpiGatewayError,
    ProductionRunConflict,
    ProductionRunNotFound,
    PulseDeviceUnavailable,
    PulseGatewayError,
)
from production_control_app.domain.services.pulse_snapshot import (
    classify_pulse_snapshot,
)
from production_control_app.domain.services.production_run_counting import (
    CountChange,
    build_count_change,
    pieces_from_anchor,
    sum_segment_pieces,
    target_pieces_from_quantity,
)
from production_control_app.domain.services.production_run_standard_time import (
    normalize_standard_time_snapshot,
    resolve_workstation_type_snapshot,
)
from production_control_app.infrastructure.gateways.production_pulse_gateway import (
    ProductionPulseGateway,
)
from production_control_app.infrastructure.persistence.postgres_production_run_repository import (
    PostgresProductionRunRepository,
    generate_session_token,
)


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _run_to_api(run: dict[str, Any], *, device: dict[str, Any] | None = None) -> dict[str, Any]:
    counted = int(run.get("pieces_total") or 0)
    target_raw = run.get("target_pieces_snapshot")
    target = int(target_raw) if target_raw is not None and int(target_raw) > 0 else None
    remaining = max(target - counted, 0) if target is not None else None
    overproduction = max(counted - target, 0) if target is not None else None
    payload = {
        "id": run.get("id"),
        "branch": run.get("branch"),
        "workCenter": run.get("work_center"),
        "productionOrder": run.get("production_order"),
        "operationCode": run.get("operation_code"),
        "deviceId": run.get("device_id"),
        "operatorCode": run.get("operator_code"),
        "operatorName": run.get("operator_name"),
        "status": run.get("status"),
        "startedAt": _iso(run.get("started_at")),
        "endedAt": _iso(run.get("ended_at")),
        "piecesTotal": counted,
        "plannedQty": (
            float(run["planned_qty_snapshot"])
            if run.get("planned_qty_snapshot") is not None
            else None
        ),
        "targetPieces": target,
        "remainingPieces": remaining,
        "progressPercent": round(counted / target * 100, 2) if target is not None else None,
        "targetReached": target is not None and counted >= target,
        "overproductionPieces": overproduction,
    }
    if device is not None:
        payload["device"] = {
            "deviceId": device.get("deviceId"),
            "name": device.get("name"),
            "counter": int(device.get("counter") or 0),
            "counterEpoch": int(device.get("counterEpoch") or 0),
            "online": bool(device.get("online")),
            "status": device.get("status"),
            "lastSeenAt": device.get("lastSeenAt"),
            "pollIntervalMs": device.get("pollIntervalMs"),
        }
    return payload


class ProductionRunService:
    """Owner do ciclo de vida do run MES shadow no cockpit."""

    def __init__(
        self,
        *,
        repository: PostgresProductionRunRepository | None = None,
        pulse_gateway: ProductionPulseGateway | None = None,
        queue_lookup: Callable[..., dict[str, Any] | None] | None = None,
        standard_time_lookup: Callable[..., dict[str, Any] | None] | None = None,
        mes_lifecycle: Any | None = None,
        audit: Any | None = None,
        clock: Callable[[], datetime] | None = None,
        auto_downtime_seconds: int | None = None,
    ) -> None:
        self._repo = repository or PostgresProductionRunRepository()
        self._audit_repo = audit
        self._clock = clock or _utc_now
        self._auto_downtime_seconds = (
            int(settings.PC_MES_AUTO_DOWNTIME_SECONDS or 0)
            if auto_downtime_seconds is None
            else int(auto_downtime_seconds)
        )
        self._pulse = pulse_gateway or ProductionPulseGateway()
        self._queue_lookup = queue_lookup
        self._standard_time_lookup = standard_time_lookup
        if mes_lifecycle is None:
            from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
                MesRunLifecycleService,
            )
            from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
                PostgresDowntimeEventRepository,
                PostgresDowntimeReasonRepository,
                PostgresWorkCenterStateRepository,
            )

            mes_lifecycle = MesRunLifecycleService(
                states=PostgresWorkCenterStateRepository(),
                downtimes=PostgresDowntimeEventRepository(),
                reasons=PostgresDowntimeReasonRepository(),
                run_lookup=self._repo.get_run,
            )
        self._mes = mes_lifecycle

    def transaction(self) -> Any:
        """Transação compartilhada do run repo (uso por serviços compostos)."""
        return self._repo.transaction()

    def create_bench_session(
        self,
        *,
        branch: str,
        work_center: str,
        operator_code: str,
        operator_name: str | None = None,
    ) -> dict[str, Any]:
        code = str(operator_code or "").strip()
        wc = str(work_center or "").strip()
        if not code:
            raise ValueError("Informe o código do operador.")
        if not wc:
            raise ValueError("Informe o centro de trabalho.")
        if branch not in {"01", "02"}:
            raise ValueError("Filial inválida.")

        raw_token = generate_session_token()
        row = self._repo.create_bench_session(
            branch=branch,
            work_center=wc,
            operator_code=code,
            operator_name=(operator_name or "").strip() or None,
            raw_token=raw_token,
        )
        return {
            "sessionToken": raw_token,
            "expiresAt": _iso(row.get("expires_at")),
            "branch": row.get("branch"),
            "workCenter": row.get("work_center"),
            "operatorCode": row.get("operator_code"),
            "operatorName": row.get("operator_name"),
        }

    def resolve_bench_session(self, raw_token: str | None) -> dict[str, Any]:
        token = str(raw_token or "").strip()
        if not token:
            raise BenchSessionRequired("Identifique-se no posto antes de iniciar a produção.")
        session = self._repo.get_bench_session_by_token(token)
        if session is None or session.get("ended_at") is not None:
            raise BenchSessionRequired("Sessão inválida. Identifique-se novamente.")
        expires = session.get("expires_at")
        if expires is not None:
            exp = expires if expires.tzinfo else expires.replace(tzinfo=timezone.utc)
            if exp < datetime.now(timezone.utc):
                raise BenchSessionRequired("Sessão expirada. Identifique-se novamente.")
        return session

    def end_bench_session(self, raw_token: str | None) -> None:
        session = self.resolve_bench_session(raw_token)
        self._repo.end_bench_session(session["id"])

    def _pick_device(self, *, branch: str, work_center: str) -> dict[str, Any]:
        try:
            snapshot = self._pulse.fetch_work_center_snapshot(
                branch=branch,
                work_center=work_center,
            )
        except PulseGatewayError:
            raise
        items = snapshot.get("items") if isinstance(snapshot, dict) else None
        devices = items if isinstance(items, list) else []
        if not devices:
            raise PulseDeviceUnavailable(
                "Nenhum contador Pulse amarrado a este posto. Cadastre o device no Pulso."
            )
        if len(devices) > 1:
            raise PulseDeviceUnavailable(
                "Há mais de um contador neste posto. Deixe apenas um device pulse_counter ativo."
            )
        return devices[0]

    def _operation_from_queue(
        self,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any] | None:
        if self._queue_lookup is None:
            return None
        return self._queue_lookup(
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
        )

    def start_run(
        self,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
        session_token: str | None,
    ) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        if session.get("branch") != branch or session.get("work_center") != work_center:
            raise BenchSessionRequired("Sessão não corresponde ao posto selecionado.")

        existing = self._repo.get_active_run(branch=branch, work_center=work_center)
        if existing is not None:
            raise ProductionRunConflict("Já existe produção em andamento neste posto.")

        device = self._pick_device(branch=branch, work_center=work_center)
        if classify_pulse_snapshot(device) != "usable":
            raise PulseDeviceUnavailable(
                "Contador do posto indisponível ou inválido. Não é possível iniciar."
            )
        op = self._operation_from_queue(
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
        )
        planned = None
        target_pieces = None
        if op is not None:
            raw = op.get("operation_pending_qty")
            if raw is None:
                raw = op.get("pending_qty")
            try:
                planned = float(raw) if raw is not None else None
            except (TypeError, ValueError):
                planned = None
            target_pieces = target_pieces_from_quantity(
                planned,
                op.get("pieces_conversion_factor"),
            )

        # Best-effort: tempo padrão/setup congelados no Play. Falha da
        # api-delpi não bloqueia produção — persiste degradação explícita.
        # Nenhuma chamada HTTP dentro da transação abaixo.
        standard = self._resolve_standard_time(
            branch=branch,
            work_center=work_center,
            production_order=str(production_order).strip(),
            operation_code=str(operation_code).strip(),
        )
        workstation_type = resolve_workstation_type_snapshot(op)

        with self._repo.transaction() as conn:
            run = self._repo.create_run_with_segment(
                branch=branch,
                work_center=work_center,
                production_order=str(production_order).strip(),
                operation_code=str(operation_code).strip(),
                device_id=str(device["deviceId"]),
                operator_code=session["operator_code"],
                operator_name=session.get("operator_name"),
                bench_session_id=session["id"],
                planned_qty_snapshot=planned,
                target_pieces_snapshot=target_pieces,
                anchor_counter=int(device.get("counter") or 0),
                anchor_epoch=int(device.get("counterEpoch") or 0),
                ideal_cycle_seconds_snapshot=standard["ideal_cycle_seconds_snapshot"],
                setup_seconds_snapshot=standard["setup_seconds_snapshot"],
                standard_time_source=standard["standard_time_source"],
                standard_time_data_quality_snapshot=standard[
                    "standard_time_data_quality_snapshot"
                ],
                workstation_type_snapshot=workstation_type,
                pieces_per_pulse_snapshot=1,
                conn=conn,
            )
            at = self._clock()
            self._mes.record_run_started(run, conn=conn, at=at)
            self._audit(
                "run_started", run=run, session=session, conn=conn, occurred_at=at
            )
        self._notify(branch, work_center, reason="run_started")
        logger.info("mes_run_started run_id=%s", run["id"])
        return _run_to_api(run, device=device)

    def _resolve_standard_time(
        self,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        """Consulta o tempo padrão canônico na api-delpi (best-effort).

        Nunca levanta exceção: falha do upstream congela ``unavailable`` +
        ``upstream_unavailable`` e o Play segue — o chão de fábrica não para
        por causa de métrica futura.
        """
        payload: dict[str, Any] | None = None
        if self._standard_time_lookup is not None:
            try:
                payload = self._standard_time_lookup(
                    branch=branch,
                    production_order=production_order,
                    operation_code=operation_code,
                )
            except DelpiGatewayError as exc:
                logger.warning(
                    "mes_run_standard_time_unavailable branch=%s work_center=%s "
                    "production_order=%s operation_code=%s status=%s",
                    branch,
                    work_center,
                    production_order,
                    operation_code,
                    exc.status_code,
                )
            except Exception:  # noqa: BLE001 — falha inesperada não bloqueia o Play
                logger.exception(
                    "mes_run_standard_time_failed branch=%s work_center=%s "
                    "production_order=%s operation_code=%s",
                    branch,
                    work_center,
                    production_order,
                    operation_code,
                )
        snapshot = normalize_standard_time_snapshot(payload)
        if snapshot["standard_time_data_quality_snapshot"] != "complete":
            logger.info(
                "mes_run_standard_time_degraded branch=%s work_center=%s "
                "production_order=%s operation_code=%s source=%s quality=%s",
                branch,
                work_center,
                production_order,
                operation_code,
                snapshot["standard_time_source"],
                snapshot["standard_time_data_quality_snapshot"],
            )
        return snapshot

    def _require_active_run(self, run_id: str, *, session: dict[str, Any]) -> dict[str, Any]:
        run = self._repo.get_run(run_id)
        if run is None:
            raise ProductionRunNotFound("Produção não encontrada.")
        if run.get("branch") != session.get("branch") or run.get("work_center") != session.get(
            "work_center"
        ):
            raise ProductionRunNotFound("Produção não pertence a este posto.")
        return run

    def require_active_run_for_session(
        self, run_id: str, *, session: dict[str, Any]
    ) -> dict[str, Any]:
        """Run existente e pertencente à filial/posto da sessão resolvida."""
        return self._require_active_run(run_id, session=session)

    def pause_run(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("status") != "running":
            raise ProductionRunConflict("A produção não está em execução.")
        pieces_total, open_pieces, device, degraded = self._pieces_for_close(run)
        with self._repo.transaction() as conn:
            locked = self._repo.lock_run(run_id, conn=conn)
            if locked is None:
                raise ProductionRunNotFound("Produção não encontrada.")
            if locked.get("status") != "running":
                raise ProductionRunConflict("A produção não está em execução.")
            at = self._clock()
            effective, change = self._resolve_count_observation(
                run=locked,
                baseline_total=int(run.get("pieces_total") or 0),
                locked_total=int(locked.get("pieces_total") or 0),
                observed_total=pieces_total,
            )
            if change is not None:
                self._append_count_event(locked, change=change, at=at, conn=conn)
            updated = self._repo.set_run_status(
                run_id,
                status="paused",
                pieces_total=effective,
                close_open_segment=True,
                open_segment_pieces=open_pieces,
                end_reason="pause",
                conn=conn,
            )
            self._mes.record_run_paused(locked, conn=conn, at=at)
            self._audit(
                "run_paused", run=locked, session=session, conn=conn,
                occurred_at=at,
            )
            if degraded:
                self._audit(
                    "telemetry_fallback_used",
                    run=locked,
                    session=session,
                    conn=conn,
                    occurred_at=at,
                    details={"transition": "pause"},
                )
        payload = _run_to_api(updated, device=device)
        payload["downtime"] = self._mes.open_downtime_view(locked)
        self._notify(run["branch"], run["work_center"], reason="run_paused")
        logger.info("mes_run_paused run_id=%s degraded=%s", run["id"], degraded)
        return payload

    def resume_run(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("status") != "paused":
            raise ProductionRunConflict("A produção não está pausada.")
        device = self._usable_device_snapshot(run)
        with self._repo.transaction() as conn:
            locked = self._repo.lock_run(run_id, conn=conn)
            if locked is None:
                raise ProductionRunNotFound("Produção não encontrada.")
            if locked.get("status") != "paused":
                raise ProductionRunConflict("A produção não está pausada.")
            at = self._clock()
            self._mes.record_run_resumed(locked, conn=conn, at=at)
            self._audit(
                "run_resumed", run=locked, session=session, conn=conn,
                occurred_at=at,
            )
            updated = self._repo.reopen_segment_on_resume(
                run_id=run_id,
                device_id=str(run["device_id"]),
                anchor_counter=int(device.get("counter") or 0),
                anchor_epoch=int(device.get("counterEpoch") or 0),
                conn=conn,
            )
        run = {**run, **updated}
        self._notify(run["branch"], run["work_center"], reason="run_resumed")
        logger.info("mes_run_resumed run_id=%s", run["id"])
        return _run_to_api(run, device=device)

    def stop_run(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("status") not in {"running", "paused"}:
            raise ProductionRunConflict("A produção já foi encerrada.")
        pieces_total = int(run.get("pieces_total") or 0)
        open_pieces = 0
        device = None
        degraded = False
        if run.get("status") == "running":
            pieces_total, open_pieces, device, degraded = self._pieces_for_close(run)
        with self._repo.transaction() as conn:
            locked = self._repo.lock_run(run_id, conn=conn)
            if locked is None:
                raise ProductionRunNotFound("Produção não encontrada.")
            if locked.get("status") not in {"running", "paused"}:
                raise ProductionRunConflict("A produção já foi encerrada.")
            at = self._clock()
            # Fecha fatos MES antes de mutar o status — se a parada aberta
            # estiver sem classificação, a transição inteira falha aqui.
            self._mes.record_run_finished(locked, conn=conn, at=at)
            effective, change = self._resolve_count_observation(
                run=locked,
                baseline_total=int(run.get("pieces_total") or 0),
                locked_total=int(locked.get("pieces_total") or 0),
                observed_total=pieces_total,
            )
            if change is not None:
                self._append_count_event(locked, change=change, at=at, conn=conn)
            updated = self._repo.set_run_status(
                run_id,
                status="completed",
                pieces_total=effective,
                close_open_segment=locked.get("status") == "running",
                open_segment_pieces=open_pieces,
                end_reason="stop",
                conn=conn,
            )
            self._audit(
                "run_stopped", run=locked, session=session, conn=conn,
                occurred_at=at,
            )
            if degraded:
                self._audit(
                    "telemetry_fallback_used",
                    run=locked,
                    session=session,
                    conn=conn,
                    occurred_at=at,
                    details={"transition": "stop"},
                )
        self._notify(run["branch"], run["work_center"], reason="run_stopped")
        logger.info("mes_run_stopped run_id=%s", run["id"])
        return _run_to_api(updated, device=device)

    def get_active(
        self,
        *,
        branch: str,
        work_center: str,
    ) -> dict[str, Any] | None:
        run = self._repo.get_active_run(branch=branch, work_center=work_center)
        if run is None:
            return None
        device = None
        if run.get("status") == "running":
            try:
                pieces_total, open_pieces, device = self._refresh_pieces(
                    run, allow_epoch_roll=True
                )
                # Trilha de count events (V014): GET que observa mudança
                # persiste update + evento na mesma transação; sem mudança,
                # nenhuma escrita (e nenhum lock — fast path de leitura).
                persisted = int(run.get("pieces_total") or 0)
                if pieces_total != persisted:
                    with self._repo.transaction() as conn:
                        locked = self._repo.lock_run(str(run["id"]), conn=conn)
                        if locked is None or locked.get("status") != "running":
                            # Transição concorrente: responde com o persistido.
                            pieces_total = int(
                                (locked or run).get("pieces_total") or 0
                            )
                        else:
                            effective, change = self._resolve_count_observation(
                                run=locked,
                                baseline_total=int(run.get("pieces_total") or 0),
                                locked_total=int(locked.get("pieces_total") or 0),
                                observed_total=pieces_total,
                            )
                            if change is not None:
                                self._repo.update_run_pieces(
                                    str(run["id"]),
                                    pieces_total=effective,
                                    open_segment_pieces=open_pieces,
                                    conn=conn,
                                )
                                self._append_count_event(
                                    locked,
                                    change=change,
                                    at=self._clock(),
                                    conn=conn,
                                )
                            pieces_total = effective
                run = {**run, "pieces_total": pieces_total}
            except (PulseGatewayError, PulseDeviceUnavailable):
                device = {
                    "deviceId": run.get("device_id"),
                    "online": False,
                    "status": "offline",
                    "counter": None,
                    "counterEpoch": None,
                }
        else:
            try:
                device = self._pulse.fetch_device_snapshot(str(run["device_id"]))
            except PulseGatewayError:
                device = {"deviceId": run.get("device_id"), "online": False, "status": "offline"}

        payload = _run_to_api(run, device=device)
        payload["countedPieces"] = int(run.get("pieces_total") or 0)
        payload["downtime"] = self._mes.open_downtime_view(run)
        payload["operationalState"] = self._mes.open_state_view(run)
        pending, pending_count = self._mes.pending_classification_view(run)
        payload["pendingDowntime"] = pending
        payload["pendingDowntimeCount"] = pending_count
        return payload

    def tick_running_runs(self) -> int:
        """Atualiza peças dos runs ``running`` e detecta parada automática.

        Regras (Etapa 05+auto-stop):
        - snapshot Pulse não ``usable`` → nada muda (offline não é parada);
        - incremento real de peças → atualiza ``last_count_activity_at`` e, se
          houver parada automática aberta, encerra-a e reabre ``producing``;
        - sem incremento → verifica threshold sobre ``last_count_activity_at``.
        """
        updated = 0
        for run in self._repo.list_open_running_runs():
            try:
                updated += self._tick_run(run)
            except (PulseGatewayError, PulseDeviceUnavailable, ProductionRunNotFound):
                continue
            except Exception:  # noqa: BLE001 — um run ruim não derruba os demais
                logger.exception("mes_tick_run_failed run_id=%s", run.get("id"))
        return updated

    def _tick_run(self, run: dict[str, Any]) -> int:
        pieces_total, open_pieces, _device = self._refresh_pieces(
            run, allow_epoch_roll=True
        )
        prev_total = int(run.get("pieces_total") or 0)
        at = self._clock()
        if pieces_total > prev_total:
            self._tick_counted(
                run, pieces_total=pieces_total, open_pieces=open_pieces, at=at
            )
            return 1
        if pieces_total != prev_total:
            # Correção/decaimento do contador não é golpe: atualiza e notifica,
            # mas sem tocar `last_count_activity_at` nem auto-resumir.
            applied = self._tick_correction(
                run, pieces_total=pieces_total, open_pieces=open_pieces, at=at
            )
            self._tick_idle(run, at=at)
            return applied
        self._tick_idle(run, at=at)
        return 0

    def _tick_counted(
        self, run: dict[str, Any], *, pieces_total: int, open_pieces: int, at: datetime
    ) -> None:
        """Incremento real: atualiza contagem + atividade; auto-resume se
        estiver em ``stopped`` automático (run continua ``running``)."""
        closed_dt = None
        applied_total = pieces_total
        with self._repo.transaction() as conn:
            locked = self._repo.lock_run(str(run["id"]), conn=conn)
            if locked is None or locked.get("status") != "running":
                return
            effective, change = self._resolve_count_observation(
                run=locked,
                baseline_total=int(run.get("pieces_total") or 0),
                locked_total=int(locked.get("pieces_total") or 0),
                observed_total=pieces_total,
            )
            if change is None:
                return
            applied_total = effective
            self._repo.update_run_pieces(
                str(run["id"]),
                pieces_total=effective,
                open_segment_pieces=open_pieces,
                activity_at=at,
                conn=conn,
            )
            self._append_count_event(locked, change=change, at=at, conn=conn)
            closed_dt = self._mes.record_automatic_resumed(locked, conn=conn, at=at)
            if closed_dt is not None:
                self._audit(
                    "automatic_downtime_ended",
                    run=locked,
                    session=None,
                    conn=conn,
                    occurred_at=at,
                    details={
                        "downtimeId": closed_dt["id"],
                        "endedAt": at.isoformat(),
                    },
                )
        self._notify(
            run["branch"],
            run["work_center"],
            reason="pieces_updated",
            run_id=str(run["id"]),
            pieces_total=applied_total,
        )
        if closed_dt is not None:
            ended = closed_dt.get("ended_at")
            self._notify(
                run["branch"],
                run["work_center"],
                reason="automatic_downtime_ended",
                extra={
                    "runId": str(run["id"]),
                    "operationalState": "producing",
                    "piecesTotal": pieces_total,
                    "downtime": {
                        "id": closed_dt["id"],
                        "endedAt": ended.isoformat()
                        if hasattr(ended, "isoformat")
                        else str(ended or at.isoformat()),
                    },
                },
            )
            logger.info("mes_auto_downtime_ended run_id=%s", run["id"])

    def _tick_correction(
        self, run: dict[str, Any], *, pieces_total: int, open_pieces: int, at: datetime
    ) -> int:
        """Decaimento de contagem: persiste correction atômica, sem atividade."""
        applied_total = int(run.get("pieces_total") or 0)
        applied = False
        with self._repo.transaction() as conn:
            locked = self._repo.lock_run(str(run["id"]), conn=conn)
            if locked is None or locked.get("status") != "running":
                return 0
            effective, change = self._resolve_count_observation(
                run=locked,
                baseline_total=int(run.get("pieces_total") or 0),
                locked_total=int(locked.get("pieces_total") or 0),
                observed_total=pieces_total,
            )
            if change is None:
                return 0
            applied_total = effective
            # Correction NÃO atualiza last_count_activity_at: não é produção.
            self._repo.update_run_pieces(
                str(run["id"]),
                pieces_total=effective,
                open_segment_pieces=open_pieces,
                conn=conn,
            )
            self._append_count_event(locked, change=change, at=at, conn=conn)
            applied = True
        if applied:
            self._notify(
                run["branch"],
                run["work_center"],
                reason="pieces_updated",
                run_id=str(run["id"]),
                pieces_total=applied_total,
            )
        return int(applied)

    def _resolve_count_observation(
        self,
        *,
        run: dict[str, Any],
        baseline_total: int,
        locked_total: int,
        observed_total: int,
    ) -> tuple[int, CountChange | None]:
        """Regra central de mudança de contagem, já com o run locado.

        baseline_total é o total persistido quando a observação foi
        produzida (pré-lock). Se outro writer mudou o run desde então, a
        observação é stale: retorna o total locado sem evento — o próximo
        ciclo reconcilia. Nunca transforma observação antiga em correction
        falsa.
        """
        if baseline_total != locked_total:
            logger.info(
                "mes_count_observation_stale run_id=%s baseline=%s locked=%s observed=%s",
                run.get("id"),
                baseline_total,
                locked_total,
                observed_total,
            )
            return locked_total, None
        change = build_count_change(
            previous_total=locked_total, observed_total=observed_total
        )
        if change is None:
            return locked_total, None
        return change.pieces_total, change

    def _append_count_event(
        self,
        run: dict[str, Any],
        *,
        change: CountChange,
        at: datetime,
        conn: Any,
    ) -> None:
        self._repo.append_count_event(
            run_id=str(run["id"]),
            pieces_total=change.pieces_total,
            delta_pieces=change.delta_pieces,
            event_type=change.event_type,
            occurred_at=at,
            conn=conn,
        )

    def _tick_idle(self, run: dict[str, Any], *, at: datetime) -> None:
        """Sem incremento: baseline legado ou parada automática no threshold."""
        threshold = self._auto_downtime_seconds
        if threshold <= 0:
            return
        last = run.get("last_count_activity_at")
        if last is None:
            # Run legado/ativo sem baseline: marca agora — janela começa daqui.
            self._repo.init_count_activity(str(run["id"]), at=at)
            return
        if getattr(last, "tzinfo", None) is None:
            last = last.replace(tzinfo=timezone.utc)
        idle = (at - last).total_seconds()
        if idle < threshold:
            return

        created = False
        detected_at = at
        started_at = last
        with self._repo.transaction() as conn:
            locked = self._repo.lock_run(str(run["id"]), conn=conn)
            if locked is None or locked.get("status") != "running":
                return
            last2 = locked.get("last_count_activity_at")
            if last2 is None:
                self._repo.init_count_activity(str(locked["id"]), at=at, conn=conn)
                return
            if getattr(last2, "tzinfo", None) is None:
                last2 = last2.replace(tzinfo=timezone.utc)
            if (at - last2).total_seconds() < threshold:
                return
            # started_at retroage à última atividade — os minutos de inatividade
            # contam como parada, não como produção.
            # Não retroagir além do início do próprio run.
            run_started = locked.get("started_at")
            if run_started is not None:
                if getattr(run_started, "tzinfo", None) is None:
                    run_started = run_started.replace(tzinfo=timezone.utc)
                started_at = max(last2, run_started)
            else:
                started_at = last2
            dt = self._mes.record_automatic_stopped(locked, conn=conn, at=started_at)
            if dt is None:
                return  # já existe parada aberta — tick idempotente
            self._audit(
                "automatic_downtime_started",
                run=locked,
                session=None,
                conn=conn,
                occurred_at=detected_at,
                details={
                    "thresholdSeconds": threshold,
                    "lastCountActivityAt": last2.isoformat(),
                    "detectedAt": detected_at.isoformat(),
                    "idleSecondsAtDetection": int((detected_at - last2).total_seconds()),
                    "initialReasonCode": dt.get("reason_code"),
                },
            )
            created = True
        if created:
            self._notify(
                run["branch"],
                run["work_center"],
                reason="automatic_downtime_started",
                extra={
                    "runId": str(run["id"]),
                    "operationalState": "stopped",
                    "downtime": self._mes.open_downtime_view(run),
                },
            )
            logger.info(
                "mes_auto_downtime_started run_id=%s started_at=%s",
                run["id"],
                started_at,
            )

    def _usable_device_snapshot(self, run: dict[str, Any]) -> dict[str, Any]:
        """Snapshot Pulse do device do run; exige utilizável (Etapa 05)."""
        try:
            device = self._pulse.fetch_device_snapshot(str(run["device_id"]))
        except PulseGatewayError as exc:
            raise PulseDeviceUnavailable(
                "Contador indisponível no momento. Aguarde a telemetria voltar."
            ) from exc
        status = classify_pulse_snapshot(device)
        if status != "usable":
            raise PulseDeviceUnavailable(
                "Contador indisponível no momento. Aguarde a telemetria voltar."
            )
        return device

    def _pieces_for_close(
        self, run: dict[str, Any]
    ) -> tuple[int, int, dict[str, Any] | None, bool]:
        """Consolida peças antes de Pause/Stop.

        Retorna (pieces_total, open_pieces, device, degraded). Quando o Pulse
        está indisponível, usa somente os últimos valores persistidos —
        nunca inventa contagem.
        """
        try:
            pieces_total, open_pieces, device = self._refresh_pieces(
                run, allow_epoch_roll=True
            )
            return pieces_total, open_pieces, device, False
        except (PulseGatewayError, PulseDeviceUnavailable):
            segment = self._repo.get_open_segment(str(run["id"]))
            pieces_total = int(run.get("pieces_total") or 0)
            open_pieces = int(segment.get("pieces") or 0) if segment else 0
            logger.warning(
                "mes_telemetry_fallback run_id=%s branch=%s work_center=%s",
                run.get("id"), run.get("branch"), run.get("work_center"),
            )
            return pieces_total, open_pieces, None, True

    def _audit(
        self,
        action: str,
        *,
        run: dict[str, Any] | None,
        session: dict[str, Any] | None,
        conn: Any | None = None,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        if self._audit_repo is None:
            return
        if run is None:
            return
        actor_type = "operator" if session else "system"
        self._audit_repo.append(
            branch=run["branch"],
            work_center=run["work_center"],
            run_id=str(run["id"]),
            action=action,
            actor_type=actor_type,
            actor_ref=(session or {}).get("operator_code"),
            occurred_at=occurred_at,
            details=details or {},
            conn=conn,
        )

    def _refresh_pieces(
        self,
        run: dict[str, Any],
        *,
        allow_epoch_roll: bool,
    ) -> tuple[int, int, dict[str, Any]]:
        device = self._pulse.fetch_device_snapshot(str(run["device_id"]))
        if classify_pulse_snapshot(device) != "usable":
            raise PulseDeviceUnavailable(
                "Snapshot do contador indisponível ou inválido."
            )
        segment = self._repo.get_open_segment(str(run["id"]))
        if segment is None:
            return int(run.get("pieces_total") or 0), 0, device

        current_counter = int(device.get("counter") or 0)
        current_epoch = int(device.get("counterEpoch") or 0)
        result = pieces_from_anchor(
            current_counter=current_counter,
            current_epoch=current_epoch,
            anchor_counter=int(segment["anchor_counter"]),
            anchor_epoch=int(segment["anchor_epoch"]),
        )

        if result.epoch_changed and allow_epoch_roll:
            # Fecha segmento com peças anteriores (já em segment.pieces / total) e reabre.
            closed_pieces = [
                int(s.get("pieces") or 0)
                for s in self._repo.list_segments(str(run["id"]))
                if s.get("ended_at") is not None
            ]
            # Peças do segmento aberto sob o epoch antigo: usar last known segment.pieces
            # (última atualização antes do bump). Sem histórico do counter antigo, não
            # inventa — preserva pieces do segmento aberto.
            open_known = int(segment.get("pieces") or 0)
            pieces_total = sum_segment_pieces(closed_pieces, open_known)
            with self._repo.transaction() as conn:
                locked = self._repo.lock_run(str(run["id"]), conn=conn)
                if locked is None:
                    return int(run.get("pieces_total") or 0), 0, device
                effective, change = self._resolve_count_observation(
                    run=locked,
                    baseline_total=int(run.get("pieces_total") or 0),
                    locked_total=int(locked.get("pieces_total") or 0),
                    observed_total=pieces_total,
                )
                rolled = self._repo.close_segment_open_new(
                    run_id=str(run["id"]),
                    segment_id=str(segment["id"]),
                    pieces=open_known,
                    end_reason="epoch_change",
                    device_id=str(run["device_id"]),
                    anchor_counter=current_counter,
                    anchor_epoch=current_epoch,
                    pieces_total=effective,
                    conn=conn,
                )
                if change is not None:
                    self._append_count_event(
                        locked, change=change, at=self._clock(), conn=conn
                    )
                self._audit(
                    "counter_epoch_changed",
                    run=locked,
                    session=None,
                    conn=conn,
                    details={
                        "previousEpoch": int(segment["anchor_epoch"]),
                        "newEpoch": current_epoch,
                    },
                )
            return int(rolled.get("pieces_total") or effective), 0, device

        closed_pieces = [
            int(s.get("pieces") or 0)
            for s in self._repo.list_segments(str(run["id"]))
            if s.get("ended_at") is not None
        ]
        pieces_total = sum_segment_pieces(closed_pieces, result.pieces)
        return pieces_total, result.pieces, device

    def _notify(
        self,
        branch: str,
        work_center: str,
        *,
        reason: str,
        run_id: str | None = None,
        pieces_total: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        room = f"{branch}:{work_center}"
        message: dict[str, Any] = {
            "type": "production_run_updated",
            "reason": reason,
            "branch": branch,
            "workCenter": work_center,
        }
        if run_id is not None and pieces_total is not None:
            message["runId"] = run_id
            message["piecesTotal"] = pieces_total
        if extra:
            message.update(extra)
        machine_load_realtime_hub.schedule_broadcast(room if ":" in room else branch, message)
        # Também na sala por filial (cockpit WS atual).
        machine_load_realtime_hub.schedule_broadcast(branch, message)
