"""Triagem e tratamento gerencial de paradas MES (Etapa 03).

O PC é o owner do registro de tratamento (1:1 com a parada canônica):
análise, natureza da causa, decisão, vínculo com a solicitação externa e
conclusão — tudo auditado em mes_audit_events. O lifecycle da
solicitação NÃO vive aqui: o vínculo guarda requestId/typeCode e o
status vivo é hidratado pelo BFF consultando o requests-api.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.errors import (
    DowntimeNotFound,
    DowntimeTreatmentConflict,
    DowntimeTreatmentNotFound,
    InvalidMesEvent,
)
from production_control_app.domain.ports.downtime_event_repository import (
    DowntimeEventRepositoryPort,
)
from production_control_app.domain.ports.downtime_treatment_repository import (
    DowntimeTreatmentRepositoryPort,
)

_CAUSE_KINDS = ("confirmed", "hypothesis")


class MesDowntimeTreatmentService:
    def __init__(
        self,
        *,
        downtimes: DowntimeEventRepositoryPort,
        treatments: DowntimeTreatmentRepositoryPort,
        audit: Any | None = None,
    ) -> None:
        self._downtimes = downtimes
        self._treatments = treatments
        self._audit = audit

    def get_treatment(
        self, downtime_id: str, *, branch: str
    ) -> dict[str, Any] | None:
        dt = self._require_downtime(downtime_id, branch)
        row = self._treatments.get(dt["id"])
        return self._view(row) if row else None

    def upsert_treatment(
        self,
        downtime_id: str,
        *,
        branch: str,
        analysis: str,
        cause_kind: str,
        cause_note: str | None,
        action_needed: bool,
        justification: str,
        expected_updated_at: Any | None,
        actor_ref: str,
        actor_name: str,
    ) -> dict[str, Any]:
        dt = self._require_downtime(downtime_id, branch)
        clean_analysis = str(analysis or "").strip()
        if not clean_analysis:
            raise InvalidMesEvent("A análise da parada é obrigatória.")
        if cause_kind not in _CAUSE_KINDS:
            raise InvalidMesEvent(
                "A causa deve ser 'confirmed' ou 'hypothesis'."
            )
        clean_justification = str(justification or "").strip()
        if not clean_justification:
            raise InvalidMesEvent(
                "A justificativa da decisão de tratamento é obrigatória."
            )
        clean_cause_note = str(cause_note or "").strip() or None

        previous = self._treatments.get(dt["id"])
        if previous is not None and previous.get("status") == "concluded":
            raise DowntimeTreatmentConflict(
                "O tratamento desta parada já foi concluído."
            )

        row = self._treatments.upsert(
            dt["id"],
            branch=dt["branch"],
            work_center=dt["work_center"],
            analysis=clean_analysis,
            cause_kind=cause_kind,
            cause_note=clean_cause_note,
            action_needed=bool(action_needed),
            justification=clean_justification,
            expected_updated_at=expected_updated_at,
            actor_ref=str(actor_ref),
            actor_name=str(actor_name),
        )
        self._audit_append(
            dt,
            action=(
                "downtime_triage_created" if previous is None
                else "downtime_triage_updated"
            ),
            actor_ref=actor_ref,
            details={
                "downtimeId": dt["id"],
                "causeKind": cause_kind,
                "actionNeeded": bool(action_needed),
            },
        )
        return self._view(row)

    def link_request(
        self,
        downtime_id: str,
        *,
        branch: str,
        request_id: str,
        request_type_code: str,
        actor_ref: str,
        actor_name: str,
    ) -> dict[str, Any]:
        dt = self._require_downtime(downtime_id, branch)
        clean_request = str(request_id or "").strip()
        clean_type = str(request_type_code or "").strip()
        if not clean_request or not clean_type:
            raise InvalidMesEvent("Solicitação e tipo são obrigatórios.")
        existing = self._treatments.get(dt["id"])
        if existing is not None and existing.get("request_id") == clean_request:
            return self._view(existing)
        row = self._treatments.link_request(
            dt["id"],
            request_id=clean_request,
            request_type_code=clean_type,
            actor_ref=str(actor_ref),
            actor_name=str(actor_name),
        )
        self._audit_append(
            dt,
            action="downtime_request_referred",
            actor_ref=actor_ref,
            details={
                "downtimeId": dt["id"],
                "requestId": clean_request,
                "requestTypeCode": clean_type,
            },
        )
        return self._view(row)

    def conclude(
        self,
        downtime_id: str,
        *,
        branch: str,
        reason: str,
        linked_request_completed: bool,
        actor_ref: str,
        actor_name: str,
    ) -> dict[str, Any]:
        dt = self._require_downtime(downtime_id, branch)
        clean_reason = str(reason or "").strip()
        if not clean_reason:
            raise InvalidMesEvent(
                "A justificativa de conclusão é obrigatória."
            )
        existing = self._treatments.get(dt["id"])
        if existing is None:
            raise DowntimeTreatmentNotFound(
                "Registre a triagem antes de concluir o tratamento."
            )
        if existing.get("request_id") and not linked_request_completed:
            raise DowntimeTreatmentConflict(
                "A solicitação vinculada ainda não foi concluída."
            )
        row = self._treatments.conclude(
            dt["id"],
            reason=clean_reason,
            actor_ref=str(actor_ref),
            actor_name=str(actor_name),
        )
        self._audit_append(
            dt,
            action="downtime_treatment_concluded",
            actor_ref=actor_ref,
            details={"downtimeId": dt["id"], "reason": clean_reason},
        )
        return self._view(row)

    def history(
        self, downtime_id: str, *, branch: str
    ) -> list[dict[str, Any]]:
        dt = self._require_downtime(downtime_id, branch)
        rows = self._audit.list_for_downtime(dt["id"]) if self._audit else []
        return [self._audit_view(row) for row in rows]

    def _require_downtime(self, downtime_id: str, branch: str) -> dict[str, Any]:
        dt = self._downtimes.get(str(downtime_id))
        if dt is None or dt.get("branch") != branch:
            raise DowntimeNotFound("Parada não encontrada.")
        return dt

    def _audit_append(
        self,
        dt: dict[str, Any],
        *,
        action: str,
        actor_ref: str,
        details: dict[str, Any],
    ) -> None:
        if self._audit is None:
            return
        self._audit.append(
            branch=dt["branch"],
            work_center=dt["work_center"],
            run_id=dt.get("run_id"),
            action=action,
            actor_type="manager",
            actor_ref=str(actor_ref),
            details=details,
        )

    @staticmethod
    def _view(row: dict[str, Any]) -> dict[str, Any]:
        def _iso(value: Any) -> Any:
            return value.isoformat() if hasattr(value, "isoformat") else value

        return {
            "downtimeId": row["downtime_id"],
            "status": row["status"],
            "analysis": row["analysis"],
            "causeKind": row["cause_kind"],
            "causeNote": row.get("cause_note"),
            "actionNeeded": bool(row["action_needed"]),
            "justification": row["justification"],
            "requestRef": (
                {
                    "requestId": row["request_id"],
                    "typeCode": row["request_type_code"],
                }
                if row.get("request_id")
                else None
            ),
            "linkedAt": _iso(row.get("linked_at")),
            "linkedBy": row.get("linked_by_name") or row.get("linked_by_ref"),
            "conclusionReason": row.get("conclusion_reason"),
            "concludedAt": _iso(row.get("concluded_at")),
            "concludedBy": row.get("concluded_by_name")
            or row.get("concluded_by_ref"),
            "createdBy": row.get("created_by_name") or row.get("created_by_ref"),
            "updatedBy": row.get("updated_by_name") or row.get("updated_by_ref"),
            "createdAt": _iso(row.get("created_at")),
            "updatedAt": _iso(row.get("updated_at")),
        }

    @staticmethod
    def _audit_view(row: dict[str, Any]) -> dict[str, Any]:
        occurred = row.get("occurred_at")
        return {
            "id": row["id"],
            "action": row["action"],
            "actorType": row.get("actor_type"),
            "actorRef": row.get("actor_ref"),
            "occurredAt": occurred.isoformat()
            if hasattr(occurred, "isoformat")
            else occurred,
            "details": row.get("details") or {},
        }
