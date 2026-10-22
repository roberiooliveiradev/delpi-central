from __future__ import annotations

import hashlib
import json
import uuid
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
    OperatorDirectoryUnavailable,
    OperatorInactive,
    OperatorNotFound,
    ProductionRunConflict,
    ProductionRunHandoffConflict,
    ProductionRunNotFound,
    SnapshotNotFound,
    PulseDeviceUnavailable,
    PulseGatewayError,
)
from production_control_app.domain.services.machine_load_transfer import (
    operation_identity,
)
from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
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
from production_control_app.domain.services.mes_auto_downtime_threshold import (
    AutoDowntimeThreshold,
    resolve_auto_downtime_threshold,
)
from production_control_app.domain.services.production_run_standard_time import (
    normalize_standard_time_snapshot,
    resolve_workstation_type_snapshot,
)
from production_control_app.infrastructure.gateways.production_pulse_gateway import (
    ProductionPulseGateway,
)
from production_control_app.infrastructure.persistence.postgres_machine_load_publication_repository import (
    PostgresMachineLoadPublicationRepository,
)
from production_control_app.infrastructure.persistence.postgres_production_run_repository import (
    PostgresProductionRunRepository,
    PostgresRunHandoffRequestRepository,
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
        operator_directory: Any | None = None,
        auto_downtime_seconds: int | None = None,
        dynamic_auto_downtime_enabled: bool | None = None,
        auto_downtime_min_seconds: int | None = None,
        auto_downtime_manual_cycle_multiplier: float | None = None,
        handoff_resolver: Callable[..., Any] | None = None,
        publications: Any | None = None,
        handoff_requests: Any | None = None,
    ) -> None:
        self._repo = repository or PostgresProductionRunRepository()
        self._audit_repo = audit
        self._clock = clock or _utc_now
        self._auto_downtime_seconds = (
            int(settings.PC_MES_AUTO_DOWNTIME_SECONDS or 0)
            if auto_downtime_seconds is None
            else int(auto_downtime_seconds)
        )
        self._dynamic_auto_downtime_enabled = (
            bool(settings.PC_MES_DYNAMIC_AUTO_DOWNTIME_ENABLED)
            if dynamic_auto_downtime_enabled is None
            else bool(dynamic_auto_downtime_enabled)
        )
        self._auto_downtime_min_seconds = (
            int(settings.PC_MES_AUTO_DOWNTIME_MIN_SECONDS or 0)
            if auto_downtime_min_seconds is None
            else int(auto_downtime_min_seconds)
        )
        self._auto_downtime_cycle_multiplier = (
            float(settings.PC_MES_AUTO_DOWNTIME_MANUAL_CYCLE_MULTIPLIER or 0)
            if auto_downtime_manual_cycle_multiplier is None
            else float(auto_downtime_manual_cycle_multiplier)
        )
        if self._dynamic_auto_downtime_enabled and (
            self._auto_downtime_cycle_multiplier <= 0
            or self._auto_downtime_min_seconds < 0
        ):
            logger.warning(
                "mes_auto_downtime_invalid_config min_seconds=%s multiplier=%s — "
                "fallback para o threshold legado",
                self._auto_downtime_min_seconds,
                self._auto_downtime_cycle_multiplier,
            )
        self._operator_directory = operator_directory
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
        self._handoff_resolver = handoff_resolver
        self._publications = (
            publications or PostgresMachineLoadPublicationRepository()
        )
        self._handoff_requests = (
            handoff_requests or PostgresRunHandoffRequestRepository()
        )

    def transaction(self) -> Any:
        """Transação compartilhada do run repo (uso por serviços compostos)."""
        return self._repo.transaction()

    def create_bench_session(
        self,
        *,
        branch: str,
        work_center: str,
        registration: str,
    ) -> dict[str, Any]:
        """Cria sessão de bancada resolvendo a identidade no Portal RH (C3).

        O lookup HTTP acontece ANTES da persistência — nenhuma transação
        PostgreSQL fica aberta durante a chamada ao diretório. O nome gravado
        é sempre o oficial (identity.full_name); o browser nunca é
        autoridade sobre operator_name.
        """
        wc = str(work_center or "").strip()
        if not wc:
            raise ValueError("Informe o centro de trabalho.")
        if branch not in {"01", "02"}:
            raise ValueError("Filial inválida.")
        if self._operator_directory is None:
            raise OperatorDirectoryUnavailable(
                "Diretório de colaboradores não configurado."
            )
        reg = str(registration or "")
        try:
            identity = self._operator_directory.find_by_registration(reg)
        except OperatorNotFound:
            logger.info("bench_session_operator_not_found registration=%s", reg)
            raise
        except OperatorDirectoryUnavailable:
            logger.warning(
                "bench_session_operator_directory_unavailable registration=%s",
                reg,
            )
            raise
        if not identity.active:
            logger.info(
                "bench_session_operator_inactive registration=%s",
                identity.registration,
            )
            raise OperatorInactive(
                "Esta matrícula não está ativa no cadastro de colaboradores."
            )
        logger.info(
            "bench_session_operator_resolved registration=%s",
            identity.registration,
        )

        raw_token = generate_session_token()
        row = self._repo.create_bench_session(
            branch=branch,
            work_center=wc,
            operator_code=identity.registration,
            operator_name=identity.full_name,
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

    def get_current_bench_session(self, raw_token: str | None) -> dict[str, Any]:
        """Snapshot da sessão atual (restore do cockpit) — sem lookup no RH."""
        session = self.resolve_bench_session(raw_token)
        return {
            "sessionToken": str(raw_token or "").strip(),
            "expiresAt": _iso(session.get("expires_at")),
            "branch": session.get("branch"),
            "workCenter": session.get("work_center"),
            "operatorCode": session.get("operator_code"),
            "operatorName": session.get("operator_name"),
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
            at = self._canonical_run_start(run)
            self._mes.record_run_started(run, conn=conn, at=at)
            self._audit(
                "run_started", run=run, session=session, conn=conn, occurred_at=at
            )
        self._notify(branch, work_center, reason="run_started")
        logger.info("mes_run_started run_id=%s", run["id"])
        return _run_to_api(run, device=device)

    def _canonical_run_start(self, run: dict[str, Any]) -> datetime:
        """Instante canonico do Play: o started_at persistido do run.

        O estado operacional inicial e o baseline de inatividade compartilham
        a mesma origem temporal gravada pelo banco — evita que o relogio da
        aplicacao abra producing num instante divergente do fato
        persistido."""
        started = run.get("started_at")
        if started is None:
            return self._clock()
        if getattr(started, "tzinfo", None) is None:
            started = started.replace(tzinfo=timezone.utc)
        return started

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

    # --- Troca guiada de OP (handoff E1) -----------------------------------
    #
    # Uma única amostra Pulse define a fronteira de contagem entre os runs:
    # o segmento aberto do run anterior fecha em boundary (counter +
    # counterEpoch da mesma observação) e o primeiro segmento do novo run
    # ancora exatamente nela. Não existem timestamps por golpe — a peça de
    # fronteira pertence sempre ao run anterior, nunca é contada duas vezes.
    #
    # HTTP externo (Pulse + tempo padrão) acontece ANTES da transação; dentro
    # dela só SQL: lock do run → idempotência → PUBLISHED FOR UPDATE →
    # re-resolução do alvo → consolidação → fatos MES → novo run/segmento →
    # auditoria → registro idempotente. Qualquer exceção faz rollback total.

    _HANDOFF_BLOCK_MESSAGES = {
        "current_not_in_queue": (
            "A operação em execução não está mais na fila publicada "
            "deste posto. Encerre a produção pelo Stop."
        ),
        "no_next_operation": (
            "Não há próxima operação elegível neste posto na fila "
            "publicada pelo PCP."
        ),
        "balance_unknown": (
            "O saldo da próxima operação não está confirmado na fila "
            "publicada. Atualize a carga máquina pelo PCP."
        ),
        "queue_changed": (
            "A fila publicada mudou desde a prévia. Revise a próxima "
            "operação sugerida."
        ),
        "device_mismatch": (
            "O contador elegível do posto não é o mesmo do run em "
            "execução. Regularize o cadastro no Pulso."
        ),
        "epoch_conflict": (
            "O contador foi reiniciado (epoch diferente do segmento "
            "aberto). Encerre pelo Stop e recomece."
        ),
        "run_not_active": (
            "A produção já foi encerrada. A troca não se aplica."
        ),
        "count_boundary_stale": (
            "O contador já registrou produção mais recente que a "
            "amostra da troca. Confirme novamente para reancorar."
        ),
        "request_conflict": (
            "O identificador desta confirmação já foi utilizado com "
            "outro pedido de troca."
        ),
        "pending_classification": (
            "Existe parada sem classificação obrigatória neste posto. "
            "Classifique-a antes de trocar de OP."
        ),
        "pulse_unavailable": (
            "Contador do posto indisponível. Aguarde a telemetria voltar "
            "para trocar de OP."
        ),
    }

    def _handoff_block_payload(
        self, code: str, *, detail: str | None = None
    ) -> dict[str, Any]:
        return {
            "code": code,
            "message": detail
            or self._HANDOFF_BLOCK_MESSAGES.get(
                code, "Troca indisponível no momento."
            ),
        }

    def _handoff_next_payload(self, resolution: Any) -> dict[str, Any] | None:
        target = resolution.target if resolution is not None else None
        if target is None:
            return None
        pending = target.get("operation_pending_qty")
        if pending is None:
            pending = target.get("pending_qty")
        return {
            "productionOrder": target.get("production_order"),
            "operationCode": target.get("operation_code"),
            "operationDescription": target.get("operation_description"),
            "productCode": target.get("product_code"),
            "productDescription": target.get("product_description"),
            "pendingQty": float(pending) if pending is not None else None,
            "queuePosition": resolution.target_position or None,
            "queueSize": resolution.queue_size or None,
        }

    def _handoff_resolve(
        self,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
        publication_row: dict[str, Any] | None = None,
    ) -> Any:
        if self._handoff_resolver is None:
            raise ProductionRunHandoffConflict(
                "no_next_operation",
                "Resolução da fila publicada indisponível.",
            )
        return self._handoff_resolver(
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
            publication_row=publication_row,
        )

    def _handoff_expected_matches(
        self, resolution: Any, expected_next: dict[str, Any] | None
    ) -> bool:
        if resolution.status != "ok" or resolution.target is None:
            return False
        target_identity = operation_identity(resolution.target)
        expected = expected_next or {}
        wanted = (
            normalize_order_code(expected.get("productionOrder")),
            normalize_order_code(expected.get("operationCode")),
        )
        return target_identity == wanted

    def _handoff_request_hash(
        self,
        *,
        run_id: str,
        branch: str,
        work_center: str,
        expected_next: dict[str, Any] | None,
    ) -> str:
        canonical = json.dumps(
            {
                "runId": str(run_id),
                "branch": str(branch),
                "workCenter": str(work_center),
                "expectedNext": {
                    "productionOrder": normalize_order_code(
                        (expected_next or {}).get("productionOrder")
                    ),
                    "operationCode": normalize_order_code(
                        (expected_next or {}).get("operationCode")
                    ),
                },
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _handoff_replay_response(
        self,
        existing: dict[str, Any],
        *,
        request_hash: str,
    ) -> dict[str, Any]:
        """requestId já confirmado: mesmo pedido → resposta original."""
        if str(existing.get("request_hash")) != request_hash:
            raise ProductionRunHandoffConflict(
                "request_conflict",
                self._HANDOFF_BLOCK_MESSAGES["request_conflict"],
            )
        response = existing.get("response")
        if not isinstance(response, dict):
            raise ProductionRunHandoffConflict(
                "request_conflict",
                self._HANDOFF_BLOCK_MESSAGES["request_conflict"],
            )
        return {**response, "replayed": True}

    def handoff_preview(
        self,
        run_id: str,
        *,
        session_token: str | None,
        branch: str,
        work_center: str,
    ) -> dict[str, Any]:
        """Leitura da troca guiada — nunca muta run, contagem nem fila.

        Devolve o run atual, a primeira próxima elegível da PUBLISHED do
        mesmo CT (ou null) e os impedimentos vigentes para a cockpit
        decidir se habilita a confirmação.
        """
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("branch") != branch or run.get("work_center") != work_center:
            raise ProductionRunNotFound("Produção não pertence a este posto.")

        block: dict[str, Any] | None = None
        resolution = None
        if run.get("status") not in {"running", "paused"}:
            block = self._handoff_block_payload("run_not_active")
        else:
            pending, pending_count = self._mes.pending_classification_view(run)
            if pending_count > 0:
                block = self._handoff_block_payload(
                    "pending_classification",
                    detail=(
                        "Existe parada sem classificação obrigatória neste "
                        "posto. Classifique-a antes de trocar de OP."
                    ),
                )
            else:
                resolution = self._handoff_resolve(
                    branch=branch,
                    work_center=work_center,
                    production_order=str(run.get("production_order") or ""),
                    operation_code=str(run.get("operation_code") or ""),
                )
                if resolution.status != "ok":
                    block = self._handoff_block_payload(resolution.status)

        device = None
        if block is None:
            try:
                device = self._pick_device(branch=branch, work_center=work_center)
            except PulseGatewayError:
                block = self._handoff_block_payload("pulse_unavailable")
            except PulseDeviceUnavailable:
                block = self._handoff_block_payload("pulse_unavailable")
            else:
                if classify_pulse_snapshot(device) != "usable":
                    block = self._handoff_block_payload("pulse_unavailable")
                elif str(device.get("deviceId")) != str(run.get("device_id")):
                    block = self._handoff_block_payload("device_mismatch")

        return {
            "currentRun": _run_to_api(run),
            "nextOperation": self._handoff_next_payload(resolution),
            "available": block is None,
            "block": block,
        }

    def confirm_handoff(
        self,
        run_id: str,
        *,
        request_id: str,
        branch: str,
        work_center: str,
        expected_next: dict[str, Any] | None,
        session_token: str | None,
    ) -> dict[str, Any]:
        """Confirmação da troca guiada — atômica e idempotente.

        Sequência transacional (qualquer falha = rollback integral):
        lock do run → revalida status → idempotência → PUBLISHED FOR
        UPDATE → re-resolve alvo e confere expectedNext → consolida
        contagem na fronteira Pulse única → encerra fatos MES do run
        anterior → completed + segmento handoff → novo run +
        segmento-âncora → producing do novo run → auditoria →
        registro idempotente → commit.
        """
        try:
            request_uuid = str(uuid.UUID(str(request_id)))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(
                "requestId deve ser um UUID gerado uma vez por confirmação."
            ) from exc

        session = self.resolve_bench_session(session_token)
        if session.get("branch") != branch or session.get("work_center") != work_center:
            raise BenchSessionRequired("Sessão não corresponde ao posto selecionado.")
        run = self._require_active_run(run_id, session=session)

        request_hash = self._handoff_request_hash(
            run_id=run_id,
            branch=branch,
            work_center=work_center,
            expected_next=expected_next,
        )
        # Idempotência ANTES do status: replay de uma troca já confirmada
        # devolve a resposta gravada mesmo com o run agora encerrado.
        existing = self._handoff_requests.get(request_uuid)
        if existing is not None:
            return self._handoff_replay_response(existing, request_hash=request_hash)
        if run.get("status") not in {"running", "paused"}:
            raise ProductionRunHandoffConflict(
                "run_not_active", self._HANDOFF_BLOCK_MESSAGES["run_not_active"]
            )

        # Pré-resolução fora da transação: define o alvo e alimenta o lookup
        # HTTP de tempo padrão abaixo. A revalidação canônica acontece de novo
        # dentro da transação, sobre a linha PUBLISHED travada.
        resolution = self._handoff_resolve(
            branch=branch,
            work_center=work_center,
            production_order=str(run.get("production_order") or ""),
            operation_code=str(run.get("operation_code") or ""),
        )
        if resolution.status != "ok":
            raise ProductionRunHandoffConflict(
                resolution.status,
                self._HANDOFF_BLOCK_MESSAGES.get(
                    resolution.status, "Troca indisponível."
                ),
            )
        if not self._handoff_expected_matches(resolution, expected_next):
            raise ProductionRunHandoffConflict(
                "queue_changed",
                self._HANDOFF_BLOCK_MESSAGES["queue_changed"],
            )
        target = resolution.target

        device = self._pick_device(branch=branch, work_center=work_center)
        if classify_pulse_snapshot(device) != "usable":
            raise PulseDeviceUnavailable(
                "Contador do posto indisponível. Aguarde a telemetria voltar."
            )
        if str(device.get("deviceId")) != str(run.get("device_id")):
            raise ProductionRunHandoffConflict(
                "device_mismatch",
                self._HANDOFF_BLOCK_MESSAGES["device_mismatch"],
            )
        boundary_counter = int(device.get("counter") or 0)
        boundary_epoch = int(device.get("counterEpoch") or 0)

        standard = self._resolve_standard_time(
            branch=branch,
            work_center=work_center,
            production_order=str(target.get("production_order") or "").strip(),
            operation_code=str(target.get("operation_code") or "").strip(),
        )
        response: dict[str, Any] | None = None
        try:
            with self._repo.transaction() as conn:
                locked = self._repo.lock_run(run_id, conn=conn)
                if locked is None:
                    raise ProductionRunNotFound("Produção não encontrada.")

                # Idempotência dentro da transação — serializa dois cliques
                # com o mesmo requestId através do lock do run. Antes do
                # status: o perdedor da corrida vê o run já completed e deve
                # receber a resposta gravada, não um conflito.
                existing = self._handoff_requests.get(request_uuid, conn=conn)
                if existing is not None:
                    return self._handoff_replay_response(
                        existing, request_hash=request_hash
                    )
                if locked.get("status") not in {"running", "paused"}:
                    raise ProductionRunHandoffConflict(
                        "run_not_active",
                        self._HANDOFF_BLOCK_MESSAGES["run_not_active"],
                    )

                locked_row = self._publications.get_locked(
                    branch=branch, conn=conn
                )
                if locked_row is None:
                    raise SnapshotNotFound(
                        "A fila desta filial ainda não foi enviada pelo PCP."
                    )
                locked_resolution = self._handoff_resolve(
                    branch=branch,
                    work_center=work_center,
                    production_order=str(locked.get("production_order") or ""),
                    operation_code=str(locked.get("operation_code") or ""),
                    publication_row=locked_row,
                )
                if locked_resolution.status != "ok":
                    raise ProductionRunHandoffConflict(
                        locked_resolution.status,
                        self._HANDOFF_BLOCK_MESSAGES.get(
                            locked_resolution.status, "Troca indisponível."
                        ),
                    )
                if not self._handoff_expected_matches(
                    locked_resolution, expected_next
                ):
                    raise ProductionRunHandoffConflict(
                        "queue_changed",
                        self._HANDOFF_BLOCK_MESSAGES["queue_changed"],
                    )
                locked_target = locked_resolution.target
                if operation_identity(locked_target) != operation_identity(target):
                    raise ProductionRunHandoffConflict(
                        "queue_changed",
                        self._HANDOFF_BLOCK_MESSAGES["queue_changed"],
                    )
                # Metas/conversão congeladas a partir do alvo revalidado
                # sob o lock — republicação entre prévia e confirmação não
                # congela saldo/fator desatualizado no novo run.
                locked_pending = locked_target.get("operation_pending_qty")
                if locked_pending is None:
                    locked_pending = locked_target.get("pending_qty")
                try:
                    planned = (
                        float(locked_pending)
                        if locked_pending is not None
                        else None
                    )
                except (TypeError, ValueError):
                    planned = None
                target_pieces = target_pieces_from_quantity(
                    planned, locked_target.get("pieces_conversion_factor")
                )
                workstation_type = resolve_workstation_type_snapshot(
                    locked_target
                )

                # Referência temporal única: NOW() do PostgreSQL é
                # constante dentro da transação — run/segmentos encerrados,
                # novo run, estados MES, count event e auditoria compartilham
                # exatamente este instante canônico.
                at = self._repo.now(conn)

                # Fronteira de contagem única: a mesma amostra Pulse
                # (boundary_counter/boundary_epoch) consolida o run anterior
                # e ancora o novo — nenhuma peça contada duas vezes.
                pieces_total = int(locked.get("pieces_total") or 0)
                open_pieces = 0
                if locked.get("status") == "running":
                    segment = self._repo.get_open_segment(run_id, conn=conn)
                    if segment is not None:
                        if str(segment.get("device_id")) != str(
                            device.get("deviceId")
                        ):
                            raise ProductionRunHandoffConflict(
                                "device_mismatch",
                                self._HANDOFF_BLOCK_MESSAGES["device_mismatch"],
                            )
                        if int(segment.get("anchor_epoch") or 0) != boundary_epoch:
                            raise ProductionRunHandoffConflict(
                                "epoch_conflict",
                                self._HANDOFF_BLOCK_MESSAGES["epoch_conflict"],
                            )
                        counted = pieces_from_anchor(
                            current_counter=boundary_counter,
                            current_epoch=boundary_epoch,
                            anchor_counter=int(segment.get("anchor_counter") or 0),
                            anchor_epoch=int(segment.get("anchor_epoch") or 0),
                        )
                        if counted.epoch_changed:
                            raise ProductionRunHandoffConflict(
                                "epoch_conflict",
                                self._HANDOFF_BLOCK_MESSAGES["epoch_conflict"],
                            )
                        open_pieces = counted.pieces
                        if open_pieces < int(segment.get("pieces") or 0):
                            raise ProductionRunHandoffConflict(
                                "count_boundary_stale",
                                self._HANDOFF_BLOCK_MESSAGES[
                                    "count_boundary_stale"
                                ],
                            )
                        closed_pieces = [
                            int(seg.get("pieces") or 0)
                            for seg in self._repo.list_segments(
                                run_id, conn=conn
                            )
                            if seg.get("ended_at") is not None
                        ]
                        observed_total = sum_segment_pieces(
                            closed_pieces, open_pieces
                        )
                        if observed_total < pieces_total:
                            raise ProductionRunHandoffConflict(
                                "count_boundary_stale",
                                self._HANDOFF_BLOCK_MESSAGES[
                                    "count_boundary_stale"
                                ],
                            )
                        # Amostra da troca é sempre a fronteira do novo
                        # run: consolidar para o observado é obrigatório —
                        # preservar um total persistido mais antigo sob uma
                        # âncora mais velha recontaria peças no run novo.
                        effective = observed_total
                        change = build_count_change(
                            previous_total=pieces_total,
                            observed_total=observed_total,
                        )
                    else:
                        effective, change = pieces_total, None
                else:
                    effective, change = pieces_total, None

                # Encerra fatos MES do run anterior — parada aberta sem
                # classificação obrigatória falha aqui e desfaz tudo.
                self._mes.record_run_finished(locked, conn=conn, at=at)
                if change is not None:
                    self._append_count_event(locked, change=change, at=at, conn=conn)
                updated = self._repo.set_run_status(
                    run_id,
                    status="completed",
                    pieces_total=effective,
                    close_open_segment=locked.get("status") == "running",
                    open_segment_pieces=open_pieces,
                    end_reason="handoff",
                    conn=conn,
                )

                new_run = self._repo.create_run_with_segment(
                    branch=branch,
                    work_center=work_center,
                    production_order=str(
                        locked_target.get("production_order") or ""
                    ).strip(),
                    operation_code=str(
                        locked_target.get("operation_code") or ""
                    ).strip(),
                    device_id=str(device["deviceId"]),
                    operator_code=session["operator_code"],
                    operator_name=session.get("operator_name"),
                    bench_session_id=session["id"],
                    planned_qty_snapshot=planned,
                    target_pieces_snapshot=target_pieces,
                    anchor_counter=boundary_counter,
                    anchor_epoch=boundary_epoch,
                    ideal_cycle_seconds_snapshot=standard[
                        "ideal_cycle_seconds_snapshot"
                    ],
                    setup_seconds_snapshot=standard["setup_seconds_snapshot"],
                    standard_time_source=standard["standard_time_source"],
                    standard_time_data_quality_snapshot=standard[
                        "standard_time_data_quality_snapshot"
                    ],
                    workstation_type_snapshot=workstation_type,
                    pieces_per_pulse_snapshot=1,
                    conn=conn,
                )
                self._mes.record_run_started(new_run, conn=conn, at=at)

                handoff_audit = None
                if self._audit_repo is not None:
                    handoff_audit = self._audit_repo.append(
                        branch=locked["branch"],
                        work_center=locked["work_center"],
                        run_id=str(locked["id"]),
                        action="run_handoff",
                        actor_type="operator",
                        actor_ref=session.get("operator_code"),
                        occurred_at=at,
                        details={
                            "requestId": request_uuid,
                            "previousRunId": str(locked["id"]),
                            "newRunId": str(new_run["id"]),
                            "boundaryCounter": boundary_counter,
                            "boundaryEpoch": boundary_epoch,
                            "previousProductionOrder": locked.get(
                                "production_order"
                            ),
                            "previousOperationCode": locked.get(
                                "operation_code"
                            ),
                            "nextProductionOrder": locked_target.get(
                                "production_order"
                            ),
                            "nextOperationCode": locked_target.get(
                                "operation_code"
                            ),
                            "boundaryNote": (
                                "Uma única amostra Pulse define a peça de "
                                "fronteira — sempre do run anterior."
                            ),
                        },
                        conn=conn,
                    )
                self._audit(
                    "run_started",
                    run=new_run,
                    session=session,
                    conn=conn,
                    occurred_at=at,
                )

                completed = _run_to_api(updated, device=device)
                started = _run_to_api(new_run, device=device)
                response = {
                    "requestId": request_uuid,
                    "replayed": False,
                    "transitionAt": at.isoformat(),
                    "boundary": {
                        "counter": boundary_counter,
                        "counterEpoch": boundary_epoch,
                    },
                    "auditId": (
                        handoff_audit.get("id")
                        if isinstance(handoff_audit, dict)
                        else None
                    ),
                    "completedRun": completed,
                    "newRun": started,
                }
                self._handoff_requests.insert(
                    request_id=request_uuid,
                    branch=branch,
                    work_center=work_center,
                    previous_run_id=str(locked["id"]),
                    new_run_id=str(new_run["id"]),
                    request_hash=request_hash,
                    response=response,
                    conn=conn,
                )
        except Exception:
            # Concorrência no INSERT da idempotência (PK) aborta a transação;
            # se a linha agora existe, este pedido é replay — senão propaga.
            replay = self._handoff_requests.get(request_uuid)
            if replay is not None:
                return self._handoff_replay_response(
                    replay, request_hash=request_hash
                )
            raise

        self._notify(branch, work_center, reason="run_stopped")
        self._notify(branch, work_center, reason="run_started")
        logger.info(
            "mes_run_handoff run_id=%s new_run_id=%s request_id=%s",
            run_id,
            response["newRun"]["id"],
            request_uuid,
        )
        return response

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

    def _auto_downtime_threshold(self, run: dict[str, Any]) -> AutoDowntimeThreshold:
        """Resolve o threshold efetivo do run (2.7) — puro, auditável.

        Dinâmico só quando: flag on + workstation manual + qualidade complete
        + ciclo válido. Todo o resto é fallback do legado; seconds <= 0
        é o kill switch soberano.
        """
        return resolve_auto_downtime_threshold(
            legacy_seconds=self._auto_downtime_seconds,
            dynamic_enabled=self._dynamic_auto_downtime_enabled,
            ideal_cycle_seconds=run.get("ideal_cycle_seconds_snapshot"),
            standard_time_data_quality=run.get(
                "standard_time_data_quality_snapshot"
            ),
            workstation_type=run.get("workstation_type_snapshot"),
            minimum_seconds=self._auto_downtime_min_seconds,
            manual_cycle_multiplier=self._auto_downtime_cycle_multiplier,
        )

    def _tick_idle(self, run: dict[str, Any], *, at: datetime) -> None:
        """Sem incremento: baseline legado ou parada automática no threshold."""
        resolution = self._auto_downtime_threshold(run)
        threshold = resolution.seconds
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
            # Re-resolve sobre o run bloqueado: a decisão final usa o estado
            # transacional, não a leitura pré-lock.
            locked_resolution = self._auto_downtime_threshold(locked)
            locked_threshold = locked_resolution.seconds
            if locked_threshold <= 0:
                return
            last2 = locked.get("last_count_activity_at")
            if last2 is None:
                self._repo.init_count_activity(str(locked["id"]), at=at, conn=conn)
                return
            if getattr(last2, "tzinfo", None) is None:
                last2 = last2.replace(tzinfo=timezone.utc)
            if (at - last2).total_seconds() < locked_threshold:
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
            dt = self._mes.record_automatic_stopped(
                locked, conn=conn, at=started_at, detected_at=detected_at
            )
            if dt is None:
                # já existe parada aberta (idempotente) ou transição adiada
                # (clamp legado no futuro — nenhum fato/auditoria gravado)
                return
            effective_started_at = dt.get("started_at")
            if effective_started_at is not None and getattr(
                effective_started_at, "tzinfo", None
            ) is None:
                effective_started_at = effective_started_at.replace(
                    tzinfo=timezone.utc
                )
            legacy_clamped = (
                effective_started_at is not None
                and effective_started_at > started_at
            )
            self._audit(
                "automatic_downtime_started",
                run=locked,
                session=None,
                conn=conn,
                occurred_at=detected_at,
                details={
                    "thresholdSeconds": locked_threshold,
                    "thresholdSource": locked_resolution.source,
                    "dynamicThresholdEnabled": locked_resolution.dynamic,
                    "idealCycleSeconds": locked_resolution.ideal_cycle_seconds,
                    "workstationType": locked_resolution.workstation_type,
                    "cycleMultiplier": locked_resolution.cycle_multiplier,
                    "minimumThresholdSeconds": locked_resolution.minimum_seconds,
                    "lastCountActivityAt": last2.isoformat(),
                    "effectiveStartedAt": (
                        effective_started_at.isoformat()
                        if effective_started_at is not None
                        else None
                    ),
                    "clampedToOpenStateStart": legacy_clamped,
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
