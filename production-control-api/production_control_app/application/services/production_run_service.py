from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    ProductionRunConflict,
    ProductionRunNotFound,
    PulseDeviceUnavailable,
    PulseGatewayError,
)
from production_control_app.domain.services.production_run_counting import (
    pieces_from_anchor,
    sum_segment_pieces,
)
from production_control_app.infrastructure.gateways.production_pulse_gateway import (
    ProductionPulseGateway,
)
from production_control_app.infrastructure.persistence.postgres_production_run_repository import (
    PostgresProductionRunRepository,
    generate_session_token,
)


def _iso(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _run_to_api(run: dict[str, Any], *, device: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "piecesTotal": int(run.get("pieces_total") or 0),
        "plannedQty": (
            float(run["planned_qty_snapshot"])
            if run.get("planned_qty_snapshot") is not None
            else None
        ),
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
    ) -> None:
        self._repo = repository or PostgresProductionRunRepository()
        self._pulse = pulse_gateway or ProductionPulseGateway()
        self._queue_lookup = queue_lookup

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
        planned_qty: float | None = None,
    ) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        if session.get("branch") != branch or session.get("work_center") != work_center:
            raise BenchSessionRequired("Sessão não corresponde ao posto selecionado.")

        existing = self._repo.get_active_run(branch=branch, work_center=work_center)
        if existing is not None:
            raise ProductionRunConflict("Já existe produção em andamento neste posto.")

        device = self._pick_device(branch=branch, work_center=work_center)
        op = self._operation_from_queue(
            branch=branch,
            work_center=work_center,
            production_order=production_order,
            operation_code=operation_code,
        )
        planned = planned_qty
        if planned is None and op is not None:
            raw = op.get("operation_pending_qty")
            if raw is None:
                raw = op.get("planned_qty")
            try:
                planned = float(raw) if raw is not None else None
            except (TypeError, ValueError):
                planned = None

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
            anchor_counter=int(device.get("counter") or 0),
            anchor_epoch=int(device.get("counterEpoch") or 0),
        )
        self._notify(branch, work_center, reason="run_started")
        return _run_to_api(run, device=device)

    def _require_active_run(self, run_id: str, *, session: dict[str, Any]) -> dict[str, Any]:
        run = self._repo.get_run(run_id)
        if run is None:
            raise ProductionRunNotFound("Produção não encontrada.")
        if run.get("branch") != session.get("branch") or run.get("work_center") != session.get(
            "work_center"
        ):
            raise ProductionRunNotFound("Produção não pertence a este posto.")
        return run

    def pause_run(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("status") != "running":
            raise ProductionRunConflict("A produção não está em execução.")
        pieces_total, open_pieces, device = self._refresh_pieces(run, allow_epoch_roll=True)
        updated = self._repo.set_run_status(
            run_id,
            status="paused",
            pieces_total=pieces_total,
            close_open_segment=True,
            open_segment_pieces=open_pieces,
            end_reason="pause",
        )
        self._notify(run["branch"], run["work_center"], reason="run_paused")
        return _run_to_api(updated, device=device)

    def resume_run(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("status") != "paused":
            raise ProductionRunConflict("A produção não está pausada.")
        device = self._pulse.fetch_device_snapshot(str(run["device_id"]))
        updated = self._repo.reopen_segment_on_resume(
            run_id=run_id,
            device_id=str(run["device_id"]),
            anchor_counter=int(device.get("counter") or 0),
            anchor_epoch=int(device.get("counterEpoch") or 0),
        )
        run = self._repo.get_run(run_id) or run
        self._notify(run["branch"], run["work_center"], reason="run_resumed")
        return _run_to_api({**run, **updated}, device=device)

    def stop_run(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self.resolve_bench_session(session_token)
        run = self._require_active_run(run_id, session=session)
        if run.get("status") not in {"running", "paused"}:
            raise ProductionRunConflict("A produção já foi encerrada.")
        pieces_total = int(run.get("pieces_total") or 0)
        open_pieces = 0
        device = None
        if run.get("status") == "running":
            pieces_total, open_pieces, device = self._refresh_pieces(run, allow_epoch_roll=True)
        updated = self._repo.set_run_status(
            run_id,
            status="completed",
            pieces_total=pieces_total,
            close_open_segment=run.get("status") == "running",
            open_segment_pieces=open_pieces,
            end_reason="stop",
        )
        self._notify(run["branch"], run["work_center"], reason="run_stopped")
        return _run_to_api(updated, device=device)

    def get_active(
        self,
        *,
        branch: str,
        work_center: str,
        produced_qty_totvs: float | None = None,
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
                run = {**run, "pieces_total": pieces_total}
                self._repo.update_run_pieces(
                    run["id"],
                    pieces_total=pieces_total,
                    open_segment_pieces=open_pieces,
                )
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
        counted = int(run.get("pieces_total") or 0)
        payload["countedPieces"] = counted
        if produced_qty_totvs is not None:
            payload["totvsProducedQty"] = float(produced_qty_totvs)
            payload["divergencePieces"] = counted - float(produced_qty_totvs)
        return payload

    def tick_running_runs(self) -> int:
        """Atualiza peças dos runs running; retorna quantos foram atualizados."""
        updated = 0
        for run in self._repo.list_open_running_runs():
            try:
                pieces_total, open_pieces, _device = self._refresh_pieces(
                    run, allow_epoch_roll=True
                )
                if pieces_total != int(run.get("pieces_total") or 0):
                    self._repo.update_run_pieces(
                        run["id"],
                        pieces_total=pieces_total,
                        open_segment_pieces=open_pieces,
                    )
                    self._notify(run["branch"], run["work_center"], reason="pieces_updated")
                    updated += 1
            except (PulseGatewayError, PulseDeviceUnavailable, ProductionRunNotFound):
                continue
        return updated

    def _refresh_pieces(
        self,
        run: dict[str, Any],
        *,
        allow_epoch_roll: bool,
    ) -> tuple[int, int, dict[str, Any]]:
        device = self._pulse.fetch_device_snapshot(str(run["device_id"]))
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
            rolled = self._repo.close_segment_open_new(
                run_id=str(run["id"]),
                segment_id=str(segment["id"]),
                pieces=open_known,
                end_reason="epoch_change",
                device_id=str(run["device_id"]),
                anchor_counter=current_counter,
                anchor_epoch=current_epoch,
                pieces_total=pieces_total,
            )
            return int(rolled.get("pieces_total") or pieces_total), 0, device

        closed_pieces = [
            int(s.get("pieces") or 0)
            for s in self._repo.list_segments(str(run["id"]))
            if s.get("ended_at") is not None
        ]
        pieces_total = sum_segment_pieces(closed_pieces, result.pieces)
        return pieces_total, result.pieces, device

    def _notify(self, branch: str, work_center: str, *, reason: str) -> None:
        room = f"{branch}:{work_center}"
        machine_load_realtime_hub.schedule_broadcast(
            room if ":" in room else branch,
            {
                "type": "production_run_updated",
                "reason": reason,
                "branch": branch,
                "workCenter": work_center,
            },
        )
        # Também na sala por filial (cockpit WS atual).
        machine_load_realtime_hub.schedule_broadcast(
            branch,
            {
                "type": "production_run_updated",
                "reason": reason,
                "branch": branch,
                "workCenter": work_center,
            },
        )
