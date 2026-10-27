"""Etapa 03 — classificação gerencial + triagem/tratamento de paradas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_downtime_classification_service import (  # noqa: E501
    MesDowntimeClassificationService,
)
from production_control_app.application.services.mes_downtime_treatment_service import (  # noqa: E501
    MesDowntimeTreatmentService,
)
from production_control_app.domain.errors import (
    DowntimeConflict,
    DowntimeNotFound,
    DowntimeTreatmentConflict,
    DowntimeTreatmentNotFound,
    InvalidMesEvent,
)

from tests.test_production_run_service import (
    FakeDowntimeRepo,
    FakeReasonRepo,
)


class FakeAuditRepo:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, **kwargs):
        kwargs.pop("conn", None)
        kwargs.setdefault("id", f"audit-{len(self.events) + 1}")
        kwargs.setdefault("occurred_at", datetime.now(timezone.utc))
        self.events.append(dict(kwargs))
        return dict(kwargs)

    def list_for_downtime(self, downtime_id):
        return [
            e for e in self.events
            if (e.get("details") or {}).get("downtimeId") == downtime_id
        ]


class FakeTreatmentRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def get(self, downtime_id, *, conn=None):
        row = self.rows.get(downtime_id)
        return dict(row) if row else None

    def upsert(self, downtime_id, *, expected_updated_at, actor_ref, actor_name, **kw):
        row = self.rows.get(downtime_id)
        if expected_updated_at is None:
            if row is not None:
                raise DowntimeTreatmentConflict("exists")
            row = {
                "downtime_id": downtime_id,
                "status": "pending",
                "request_id": None,
                "request_type_code": None,
                "linked_at": None,
                "linked_by_ref": None,
                "linked_by_name": None,
                "conclusion_reason": None,
                "concluded_at": None,
                "concluded_by_ref": None,
                "concluded_by_name": None,
                "created_by_ref": actor_ref,
                "created_by_name": actor_name,
                "created_at": datetime.now(timezone.utc),
            }
        else:
            if row is None:
                raise DowntimeTreatmentNotFound("missing")
            if row["updated_at"] != expected_updated_at:
                raise DowntimeTreatmentConflict("stale")
        row.update(
            {
                "analysis": kw["analysis"],
                "cause_kind": kw["cause_kind"],
                "cause_note": kw.get("cause_note"),
                "action_needed": kw["action_needed"],
                "justification": kw["justification"],
                "branch": kw["branch"],
                "work_center": kw["work_center"],
                "updated_by_ref": actor_ref,
                "updated_by_name": actor_name,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self.rows[downtime_id] = row
        return dict(row)

    def link_request(self, downtime_id, *, request_id, request_type_code,
                     actor_ref, actor_name, conn=None):
        row = self.rows.get(downtime_id)
        if row is None:
            raise DowntimeTreatmentNotFound("missing")
        if row["status"] == "concluded" or (
            row["request_id"] and row["request_id"] != request_id
        ):
            raise DowntimeTreatmentConflict("linked")
        row.update(
            {
                "request_id": request_id,
                "request_type_code": request_type_code,
                "status": "referred",
                "linked_at": datetime.now(timezone.utc),
                "linked_by_ref": actor_ref,
                "linked_by_name": actor_name,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return dict(row)

    def conclude(self, downtime_id, *, reason, actor_ref, actor_name, conn=None):
        row = self.rows.get(downtime_id)
        if row is None:
            raise DowntimeTreatmentNotFound("missing")
        if row["status"] == "concluded":
            raise DowntimeTreatmentConflict("done")
        row.update(
            {
                "status": "concluded",
                "conclusion_reason": reason,
                "concluded_at": datetime.now(timezone.utc),
                "concluded_by_ref": actor_ref,
                "concluded_by_name": actor_name,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return dict(row)


def _downtime(downtimes, *, branch="01", work_center="CT01", run_id=None):
    return downtimes.create(
        branch=branch,
        work_center=work_center,
        source="operator_pause",
        run_id=run_id,
        production_order="OP1" if run_id else None,
        operation_code="10" if run_id else None,
    )


def _classification(downtimes, reasons, audit=None):
    return MesDowntimeClassificationService(
        run_service=object(), downtimes=downtimes, reasons=reasons, audit=audit
    )


def _treatment_svc(downtimes, treatments, audit):
    return MesDowntimeTreatmentService(
        downtimes=downtimes, treatments=treatments, audit=audit
    )


class TestManagedClassification:
    def test_manager_classifies_pending_downtime(self):
        downtimes = FakeDowntimeRepo()
        audit = FakeAuditRepo()
        dt = _downtime(downtimes)
        svc = _classification(downtimes, FakeReasonRepo(), audit=audit)

        result = svc.classify_managed(
            dt["id"],
            branch="01",
            reason_code="raw_material",
            note=None,
            expected_updated_at=dt["updated_at"],
            actor_ref="user-7",
            actor_name="Gestora",
        )
        assert result["reasonCode"] == "raw_material"
        assert result["confirmed"] is True
        assert result["confirmedByType"] == "manager"
        assert result["confirmedByRef"] == "user-7"
        event = audit.events[-1]
        assert event["action"] == "downtime_classified"
        assert event["actor_type"] == "manager"
        assert event["details"]["downtimeId"] == dt["id"]

    def test_manager_reclassifies_confirmed_reason(self):
        downtimes = FakeDowntimeRepo()
        audit = FakeAuditRepo()
        dt = _downtime(downtimes)
        svc = _classification(downtimes, FakeReasonRepo(), audit=audit)
        svc.classify_managed(
            dt["id"], branch="01", reason_code="raw_material", note=None,
            expected_updated_at=dt["updated_at"], actor_ref="u1",
        )
        current = downtimes.get(dt["id"])
        result = svc.classify_managed(
            dt["id"], branch="01", reason_code="setup", note=None,
            expected_updated_at=current["updated_at"], actor_ref="u2",
        )
        assert result["reasonCode"] == "setup"
        event = audit.events[-1]
        assert event["action"] == "downtime_reason_changed"
        assert event["details"]["previousReasonCode"] == "raw_material"
        assert event["details"]["newReasonCode"] == "setup"

    def test_stale_expected_updated_at_conflicts(self):
        downtimes = FakeDowntimeRepo()
        dt = _downtime(downtimes)
        svc = _classification(downtimes, FakeReasonRepo())
        svc.classify_managed(
            dt["id"], branch="01", reason_code="setup", note=None,
            expected_updated_at=dt["updated_at"], actor_ref="u1",
        )
        with pytest.raises(DowntimeConflict):
            svc.classify_managed(
                dt["id"], branch="01", reason_code="raw_material", note=None,
                expected_updated_at=dt["updated_at"], actor_ref="u2",
            )

    def test_idempotent_same_reason_note(self):
        downtimes = FakeDowntimeRepo()
        audit = FakeAuditRepo()
        dt = _downtime(downtimes)
        svc = _classification(downtimes, FakeReasonRepo(), audit=audit)
        svc.classify_managed(
            dt["id"], branch="01", reason_code="setup", note=None,
            expected_updated_at=dt["updated_at"], actor_ref="u1",
        )
        events_before = len(audit.events)
        current = downtimes.get(dt["id"])
        result = svc.classify_managed(
            dt["id"], branch="01", reason_code="setup", note=None,
            expected_updated_at=current["updated_at"], actor_ref="u1",
        )
        assert result["reasonCode"] == "setup"
        assert len(audit.events) == events_before

    def test_branch_mismatch_is_not_found(self):
        downtimes = FakeDowntimeRepo()
        dt = _downtime(downtimes, branch="01")
        svc = _classification(downtimes, FakeReasonRepo())
        with pytest.raises(DowntimeNotFound):
            svc.classify_managed(
                dt["id"], branch="02", reason_code="setup", note=None,
                expected_updated_at=dt["updated_at"], actor_ref="u1",
            )

    def test_unknown_downtime_is_not_found(self):
        svc = _classification(FakeDowntimeRepo(), FakeReasonRepo())
        with pytest.raises(DowntimeNotFound):
            svc.classify_managed(
                "dt-x", branch="01", reason_code="setup", note=None,
                expected_updated_at=datetime.now(timezone.utc), actor_ref="u1",
            )

    def test_inactive_or_unknown_reason_rejected(self):
        downtimes = FakeDowntimeRepo()
        dt = _downtime(downtimes)
        svc = _classification(downtimes, FakeReasonRepo())
        with pytest.raises(InvalidMesEvent):
            svc.classify_managed(
                dt["id"], branch="01", reason_code="obsolete", note=None,
                expected_updated_at=dt["updated_at"], actor_ref="u1",
            )

    def test_reason_requiring_note_rejected_without_note(self):
        downtimes = FakeDowntimeRepo()
        dt = _downtime(downtimes)
        svc = _classification(downtimes, FakeReasonRepo())
        with pytest.raises(InvalidMesEvent):
            svc.classify_managed(
                dt["id"], branch="01", reason_code="other", note="  ",
                expected_updated_at=dt["updated_at"], actor_ref="u1",
            )


class TestTreatment:
    def _svc(self):
        downtimes = FakeDowntimeRepo()
        treatments = FakeTreatmentRepo()
        audit = FakeAuditRepo()
        dt = _downtime(downtimes)
        return _treatment_svc(downtimes, treatments, audit), dt, treatments, audit

    def _upsert(self, svc, dt, expected=None):
        return svc.upsert_treatment(
            dt["id"],
            branch="01",
            analysis="Parada recorrente no turno",
            cause_kind="hypothesis",
            cause_note="suspeita de ferramenta",
            action_needed=True,
            justification="Impacto relevante no turno",
            expected_updated_at=expected,
            actor_ref="u1",
            actor_name="Gestora",
        )

    def test_create_treatment_positive(self):
        svc, dt, _, audit = self._svc()
        view = self._upsert(svc, dt)
        assert view["status"] == "pending"
        assert view["causeKind"] == "hypothesis"
        assert view["downtimeId"] == dt["id"]
        assert audit.events[-1]["action"] == "downtime_triage_created"
        assert audit.events[-1]["details"]["downtimeId"] == dt["id"]

    def test_create_when_exists_conflicts(self):
        svc, dt, _, _ = self._svc()
        self._upsert(svc, dt)
        with pytest.raises(DowntimeTreatmentConflict):
            self._upsert(svc, dt, expected=None)

    def test_update_with_precondition(self):
        svc, dt, treatments, _ = self._svc()
        self._upsert(svc, dt)
        current = treatments.get(dt["id"])["updated_at"]
        view = self._upsert(svc, dt, expected=current)
        assert view["causeKind"] == "hypothesis"

    def test_update_stale_conflicts(self):
        svc, dt, treatments, _ = self._svc()
        self._upsert(svc, dt)
        row = treatments.get(dt["id"])
        stale = row["updated_at"] - timedelta(seconds=1)
        with pytest.raises(DowntimeTreatmentConflict):
            self._upsert(svc, dt, expected=stale)

    def test_update_concluded_conflicts(self):
        svc, dt, _, _ = self._svc()
        created = self._upsert(svc, dt)
        svc.conclude(
            dt["id"], branch="01", reason="resolvido sem ação formal",
            linked_request_completed=False, actor_ref="u1", actor_name="G",
        )
        with pytest.raises(DowntimeTreatmentConflict):
            self._upsert(svc, dt, expected=created["updatedAt"])

    def test_upsert_validations(self):
        svc, dt, _, _ = self._svc()
        base = dict(
            branch="01", analysis="ok", cause_kind="confirmed", cause_note=None,
            action_needed=False, justification="ok",
            expected_updated_at=None, actor_ref="u1", actor_name="G",
        )
        with pytest.raises(InvalidMesEvent):
            svc.upsert_treatment(dt["id"], **{**base, "analysis": "  "})
        with pytest.raises(InvalidMesEvent):
            svc.upsert_treatment(dt["id"], **{**base, "cause_kind": "maybe"})
        with pytest.raises(InvalidMesEvent):
            svc.upsert_treatment(dt["id"], **{**base, "justification": ""})

    def test_branch_mismatch_not_found(self):
        svc, dt, _, _ = self._svc()
        with pytest.raises(DowntimeNotFound):
            svc.get_treatment(dt["id"], branch="02")

    def test_link_request_and_idempotent_relink(self):
        svc, dt, _, audit = self._svc()
        self._upsert(svc, dt)
        view = svc.link_request(
            dt["id"], branch="01", request_id="req-1",
            request_type_code="process-issue",
            actor_ref="u1", actor_name="G",
        )
        assert view["status"] == "referred"
        assert view["requestRef"] == {
            "requestId": "req-1", "typeCode": "process-issue",
        }
        assert audit.events[-1]["action"] == "downtime_request_referred"
        events = len(audit.events)
        # retry idempotente: mesmo requestId não escreve nem audita de novo
        again = svc.link_request(
            dt["id"], branch="01", request_id="req-1",
            request_type_code="process-issue",
            actor_ref="u1", actor_name="G",
        )
        assert again["requestRef"]["requestId"] == "req-1"
        assert len(audit.events) == events

    def test_link_different_request_conflicts(self):
        svc, dt, _, _ = self._svc()
        self._upsert(svc, dt)
        svc.link_request(
            dt["id"], branch="01", request_id="req-1",
            request_type_code="process-issue", actor_ref="u1", actor_name="G",
        )
        with pytest.raises(DowntimeTreatmentConflict):
            svc.link_request(
                dt["id"], branch="01", request_id="req-2",
                request_type_code="process-issue", actor_ref="u1", actor_name="G",
            )

    def test_link_without_treatment_not_found(self):
        svc, dt, _, _ = self._svc()
        with pytest.raises(DowntimeTreatmentNotFound):
            svc.link_request(
                dt["id"], branch="01", request_id="req-1",
                request_type_code="process-issue", actor_ref="u1", actor_name="G",
            )

    def test_conclude_without_request(self):
        svc, dt, _, audit = self._svc()
        self._upsert(svc, dt)
        view = svc.conclude(
            dt["id"], branch="01", reason="Ajuste local resolvido",
            linked_request_completed=False, actor_ref="u1", actor_name="G",
        )
        assert view["status"] == "concluded"
        assert view["conclusionReason"] == "Ajuste local resolvido"
        assert audit.events[-1]["action"] == "downtime_treatment_concluded"

    def test_conclude_with_open_request_conflicts(self):
        svc, dt, _, _ = self._svc()
        self._upsert(svc, dt)
        svc.link_request(
            dt["id"], branch="01", request_id="req-1",
            request_type_code="process-issue", actor_ref="u1", actor_name="G",
        )
        with pytest.raises(DowntimeTreatmentConflict):
            svc.conclude(
                dt["id"], branch="01", reason="fechando",
                linked_request_completed=False, actor_ref="u1", actor_name="G",
            )

    def test_conclude_with_completed_request(self):
        svc, dt, _, _ = self._svc()
        self._upsert(svc, dt)
        svc.link_request(
            dt["id"], branch="01", request_id="req-1",
            request_type_code="process-issue", actor_ref="u1", actor_name="G",
        )
        view = svc.conclude(
            dt["id"], branch="01", reason="Solicitação atendida",
            linked_request_completed=True, actor_ref="u1", actor_name="G",
        )
        assert view["status"] == "concluded"

    def test_double_conclusion_conflicts(self):
        svc, dt, _, _ = self._svc()
        self._upsert(svc, dt)
        svc.conclude(
            dt["id"], branch="01", reason="ok",
            linked_request_completed=False, actor_ref="u1", actor_name="G",
        )
        with pytest.raises(DowntimeTreatmentConflict):
            svc.conclude(
                dt["id"], branch="01", reason="again",
                linked_request_completed=False, actor_ref="u1", actor_name="G",
            )

    def test_conclude_requires_reason_and_treatment(self):
        svc, dt, _, _ = self._svc()
        with pytest.raises(InvalidMesEvent):
            svc.conclude(
                dt["id"], branch="01", reason=" ",
                linked_request_completed=False, actor_ref="u1", actor_name="G",
            )
        with pytest.raises(DowntimeTreatmentNotFound):
            svc.conclude(
                dt["id"], branch="01", reason="justificativa",
                linked_request_completed=False, actor_ref="u1", actor_name="G",
            )

    def test_history_returns_downtime_scoped_events(self):
        downtimes = FakeDowntimeRepo()
        audit = FakeAuditRepo()
        dt = _downtime(downtimes)
        other = _downtime(downtimes, work_center="CT02")
        svc = _treatment_svc(downtimes, FakeTreatmentRepo(), audit)
        audit.append(
            branch="01", work_center="CT01", action="downtime_classified",
            actor_type="manager", actor_ref="u1",
            details={"downtimeId": dt["id"]},
        )
        audit.append(
            branch="01", work_center="CT02", action="downtime_classified",
            actor_type="manager", actor_ref="u2",
            details={"downtimeId": other["id"]},
        )
        items = svc.history(dt["id"], branch="01")
        assert len(items) == 1
        assert items[0]["action"] == "downtime_classified"
        assert items[0]["details"]["downtimeId"] == dt["id"]
