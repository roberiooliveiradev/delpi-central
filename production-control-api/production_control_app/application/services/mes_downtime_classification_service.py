"""Classificação do motivo de uma parada MES (Etapa 03).

O backend é a fonte de verdade: o frontend envia apenas ``reasonCode`` e,
quando o motivo exige, ``note``. Snapshots OEE (``planned``,
``counts_as_availability_loss``) e a identidade de quem confirmou são
aplicados aqui a partir do catálogo e da sessão — nunca do cliente.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.errors import (
    DowntimeNotFound,
    InvalidMesEvent,
)
from production_control_app.domain.ports.downtime_event_repository import (
    DowntimeEventRepositoryPort,
)
from production_control_app.domain.ports.downtime_reason_repository import (
    DowntimeReasonRepositoryPort,
)
from production_control_app.domain.services.mes_operational_state import (
    normalize_reason_code,
)


class MesDowntimeClassificationService:
    def __init__(
        self,
        *,
        run_service: Any,
        downtimes: DowntimeEventRepositoryPort,
        reasons: DowntimeReasonRepositoryPort,
        audit: Any | None = None,
    ) -> None:
        self._run_service = run_service
        self._downtimes = downtimes
        self._reasons = reasons
        self._audit = audit

    def list_reasons(self) -> list[dict[str, Any]]:
        """Catálogo público: somente motivos ativos, contrato mínimo."""
        return [
            {
                "code": row["code"],
                "label": row["label"],
                "category": row["category"],
                "requiresNote": bool(row.get("requires_note")),
            }
            for row in self._reasons.list_active()
        ]

    def classify(
        self,
        run_id: str,
        *,
        reason_code: str,
        note: str | None,
        session_token: str | None,
    ) -> dict[str, Any]:
        """Confirma/altera o motivo da parada aberta do run — nunca cria outra."""
        session = self._run_service.resolve_bench_session(session_token)
        run = self._run_service.require_active_run_for_session(run_id, session=session)

        open_dt = self._downtimes.get_open(
            branch=run["branch"], work_center=run["work_center"]
        )
        if open_dt is None or open_dt["run_id"] != run["id"]:
            raise DowntimeNotFound("Não há parada aberta para esta produção.")

        reason = self._reasons.get(normalize_reason_code(reason_code))
        if reason is None or not reason.get("active"):
            raise InvalidMesEvent("Motivo de parada inválido ou inativo.")
        clean_note = str(note or "").strip() or None
        if reason.get("requires_note") and not clean_note:
            raise InvalidMesEvent("Este motivo exige uma observação.")

        previous_reason = open_dt.get("reason_code")
        action = (
            "downtime_reason_changed" if previous_reason else "downtime_classified"
        )
        details: dict[str, Any] = {}
        if previous_reason:
            details = {
                "previousReasonCode": previous_reason,
                "newReasonCode": reason["code"],
            }

        def _persist(conn: Any | None) -> dict[str, Any]:
            row_ = self._downtimes.classify(
                open_dt["id"],
                reason_code=reason["code"],
                planned=reason.get("default_planned"),
                counts_as_availability_loss=reason.get(
                    "default_counts_as_availability_loss"
                ),
                note=clean_note,
                confirmed_by_type="operator",
                confirmed_by_ref=str(session["operator_code"]),
                conn=conn,
            )
            if self._audit is not None:
                self._audit.append(
                    branch=run["branch"],
                    work_center=run["work_center"],
                    run_id=run["id"],
                    action=action,
                    actor_type="operator",
                    actor_ref=str(session["operator_code"]),
                    details=details,
                    conn=conn,
                )
            return row_

        transaction = getattr(self._run_service, "transaction", None)
        row = _persist(None) if transaction is None else self._with_tx(transaction, _persist)
        payload = {
            "id": row["id"],
            "runId": run["id"],
            "reasonCode": row["reason_code"],
            "reasonLabel": reason["label"],
            "category": reason["category"],
            "note": row.get("note"),
            "confirmed": bool(row.get("confirmed")),
            "startedAt": row["started_at"].isoformat()
            if hasattr(row.get("started_at"), "isoformat")
            else row.get("started_at"),
            "endedAt": None,
        }
        self._notify(run, payload)
        return payload

    @staticmethod
    def _with_tx(transaction: Any, persist: Any) -> dict[str, Any]:
        with transaction() as conn:
            return persist(conn)

    @staticmethod
    def _notify(run: dict[str, Any], downtime: dict[str, Any]) -> None:
        from production_control_app.application.services.machine_load_realtime_hub import (  # noqa: E501
            machine_load_realtime_hub,
        )

        message = {
            "type": "production_run_updated",
            "reason": "downtime_classified",
            "branch": run["branch"],
            "workCenter": run["work_center"],
            "runId": run["id"],
            "downtime": downtime,
        }
        machine_load_realtime_hub.schedule_broadcast(
            f"{run['branch']}:{run['work_center']}", message
        )
        machine_load_realtime_hub.schedule_broadcast(run["branch"], message)
