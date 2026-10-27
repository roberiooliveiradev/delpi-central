"""Gestão gerencial de paradas — autorização BFF + orquestração."""

from types import SimpleNamespace

import pytest

from delpi_mes_app.application.services.mes_downtime_management_service import (
    MesDowntimeManagementService,
)
from delpi_mes_app.domain.errors import (
    BranchAccessDenied,
    HumanPrincipalRequired,
    MesSourceConflict,
    MesSourceNotFound,
)


def user(*permissions, superadmin=False, principal_type="user"):
    return SimpleNamespace(
        id="user-1", name="Gestora", permissions=list(permissions),
        is_superadmin=superadmin, principal_type=principal_type,
        rbac_unavailable=False, access_token="tok-user-1",
    )


FULL = (
    "delpi-mes.access",
    "delpi-mes.downtimes.view",
    "delpi-mes.downtimes.classify",
    "delpi-mes.downtimes.treat",
    "delpi-mes.view.filial-01",
    "my-requests.process-issue.create",
)


class FakeMesGateway:
    def __init__(self):
        self.treatment = None
        self.downtime_item = {
            "id": "dt-1", "workCenter": "CT-41",
            "productionOrder": "100123", "operationCode": "10",
        }
        self.calls = []

    def classify_downtime(self, downtime_id, payload):
        self.calls.append(("classify", downtime_id, payload))
        return {
            "id": downtime_id,
            "reasonCode": payload["reasonCode"],
            "reasonLabel": "Setup", "category": "setup",
            "confirmed": True, "confirmedByType": "manager",
            "confirmedByRef": payload["actorRef"],
            "updatedAt": "2026-09-29T13:00:00+00:00",
            "internalField": "hidden",
        }

    def get_downtime_treatment(self, downtime_id, *, branch):
        return {"treatment": self.treatment}

    def upsert_downtime_treatment(self, downtime_id, payload):
        self.calls.append(("upsert", downtime_id, payload))
        return {
            "downtimeId": downtime_id, "status": "pending",
            "analysis": payload["analysis"], "causeKind": payload["causeKind"],
            "actionNeeded": payload["actionNeeded"],
            "justification": payload["justification"],
            "requestRef": None, "updatedAt": "2026-09-29T13:00:00+00:00",
        }

    def link_downtime_request(self, downtime_id, payload):
        self.calls.append(("link", downtime_id, payload))
        self.treatment = {
            "downtimeId": downtime_id, "status": "referred",
            "requestRef": {"requestId": payload["requestId"],
                           "typeCode": payload["requestTypeCode"]},
            "updatedAt": "2026-09-29T13:05:00+00:00",
        }
        return self.treatment

    def conclude_downtime_treatment(self, downtime_id, payload):
        self.calls.append(("conclude", downtime_id, payload))
        return {"downtimeId": downtime_id, "status": "concluded",
                "conclusionReason": payload["reason"]}

    def get_downtime_history(self, downtime_id, *, branch):
        return {"items": [
            {"id": "a1", "action": "downtime_classified",
             "actorType": "manager", "actorRef": "user-1",
             "occurredAt": "t", "details": {"downtimeId": downtime_id},
             "internal": "x"},
        ]}

    def get_downtimes(self, **kwargs):
        return {"items": [self.downtime_item] if self.downtime_item else [],
                "total": 1}


class FakeRequestsGateway:
    def __init__(self):
        self.created = []
        self.status = {"id": "req-1", "request_number": "REQ-77",
                       "type_code": "process-issue", "status": "completed",
                       "status_alias": None}
        self.raise_on_get = None

    def create_request_as_user(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "req-1", "request_number": "REQ-77",
                "type_code": "process-issue", "status": "submitted"}

    def get_request_as_user(self, **kwargs):
        if self.raise_on_get is not None:
            raise self.raise_on_get
        return self.status


def _svc(mes=None, req=None):
    return MesDowntimeManagementService(
        mes_gateway=mes or FakeMesGateway(),
        requests_gateway=req or FakeRequestsGateway(),
    )


class TestClassify:
    def test_classify_authorizes_and_forwards_actor(self):
        mes = FakeMesGateway()
        svc = _svc(mes=mes)
        out = svc.classify_downtime(
            user(*FULL), "dt-1", branch="01", reason_code="setup",
            note=None, expected_updated_at="2026-09-29T12:00:00+00:00",
        )
        kind, downtime_id, payload = mes.calls[0]
        assert kind == "classify"
        assert payload["actorRef"] == "user-1"
        assert payload["actorName"] == "Gestora"
        assert payload["expectedUpdatedAt"] == "2026-09-29T12:00:00+00:00"
        assert out["reasonCode"] == "setup"
        assert "internalField" not in out

    def test_classify_requires_permission(self):
        svc = _svc()
        with pytest.raises(PermissionError):
            svc.classify_downtime(
                user("delpi-mes.access", "delpi-mes.view.filial-01"),
                "dt-1", branch="01", reason_code="setup", note=None,
                expected_updated_at="t",
            )

    def test_classify_requires_human(self):
        svc = _svc()
        with pytest.raises(HumanPrincipalRequired):
            svc.classify_downtime(
                user(*FULL, principal_type="service"),
                "dt-1", branch="01", reason_code="setup", note=None,
                expected_updated_at="t",
            )

    def test_classify_branch_scoped(self):
        svc = _svc()
        with pytest.raises(BranchAccessDenied):
            svc.classify_downtime(
                user(*FULL), "dt-1", branch="02", reason_code="setup",
                note=None, expected_updated_at="t",
            )


class TestTreatment:
    def test_upsert_forwards_actor_and_precondition(self):
        mes = FakeMesGateway()
        svc = _svc(mes=mes)
        out = svc.upsert_treatment(
            user(*FULL), "dt-1", branch="01", analysis="análise",
            cause_kind="confirmed", cause_note=None, action_needed=False,
            justification="justificativa", expected_updated_at=None,
        )
        _, _, payload = mes.calls[0]
        assert payload["actorRef"] == "user-1"
        assert payload["expectedUpdatedAt"] is None
        assert out["treatment"]["status"] == "pending"

    def test_get_treatment_hydrates_request_status(self):
        mes = FakeMesGateway()
        mes.treatment = {
            "downtimeId": "dt-1", "status": "referred",
            "requestRef": {"requestId": "req-1", "typeCode": "process-issue"},
        }
        svc = _svc(mes=mes)
        out = svc.get_treatment(user(*FULL), "dt-1", branch="01")
        treatment = out["treatment"]
        assert treatment["requestStatusAvailable"] is True
        assert treatment["request"]["status"] == "completed"
        assert treatment["request"]["requestNumber"] == "REQ-77"

    def test_get_treatment_marks_unavailable_status(self):
        mes = FakeMesGateway()
        mes.treatment = {
            "downtimeId": "dt-1", "status": "referred",
            "requestRef": {"requestId": "req-1", "typeCode": "process-issue"},
        }
        req = FakeRequestsGateway()
        req.raise_on_get = PermissionError("denied")
        svc = _svc(mes=mes, req=req)
        out = svc.get_treatment(user(*FULL), "dt-1", branch="01")
        assert out["treatment"]["requestStatusAvailable"] is False
        assert out["treatment"]["request"] is None

    def test_history_allowlists_items(self):
        svc = _svc()
        out = svc.get_history(user(*FULL), "dt-1", branch="01")
        item = out["items"][0]
        assert item["action"] == "downtime_classified"
        assert "internal" not in item


class TestReferral:
    def test_refer_creates_request_and_links(self):
        mes = FakeMesGateway()
        mes.treatment = {
            "downtimeId": "dt-1", "status": "pending",
            "requestRef": None,
        }
        req = FakeRequestsGateway()
        svc = _svc(mes=mes, req=req)
        out = svc.refer_request(
            user(*FULL), "dt-1", branch="01",
            issue_code="tool_not_linked", note="sem vínculo",
            idempotency_key=None,
        )
        create = req.created[0]
        assert create["access_token"] == "tok-user-1"
        assert create["type_code"] == "process-issue"
        assert create["idempotency_key"] == "delpi-mes-downtime-dt-1-process-issue"
        payload = create["payload"]
        assert payload["source"] == "delpi_mes"
        assert payload["requester"]["name"] == "Gestora"
        assert payload["mesDowntime"] == {
            "downtimeId": "dt-1", "branch": "01", "workCenter": "CT-41",
        }
        assert payload["operation"] == {
            "productionOrder": "100123", "operationCode": "10",
            "reportedWorkCenter": "CT-41",
        }
        _, _, link = mes.calls[-1]
        assert link["requestId"] == "req-1"
        assert link["requestTypeCode"] == "process-issue"
        assert out["treatment"]["status"] == "referred"

    def test_refer_without_operation_omits_block(self):
        mes = FakeMesGateway()
        mes.treatment = {"downtimeId": "dt-1", "status": "pending",
                         "requestRef": None}
        mes.downtime_item = {"id": "dt-1", "workCenter": "CT-41",
                             "productionOrder": None, "operationCode": None}
        req = FakeRequestsGateway()
        svc = _svc(mes=mes, req=req)
        svc.refer_request(
            user(*FULL), "dt-1", branch="01",
            issue_code="other", note=None, idempotency_key=None,
        )
        assert "operation" not in req.created[0]["payload"]

    def test_refer_requires_treatment(self):
        mes = FakeMesGateway()
        mes.treatment = None
        svc = _svc(mes=mes)
        with pytest.raises(MesSourceConflict):
            svc.refer_request(
                user(*FULL), "dt-1", branch="01",
                issue_code="other", note=None, idempotency_key=None,
            )

    def test_refer_twice_conflicts(self):
        mes = FakeMesGateway()
        mes.treatment = {
            "downtimeId": "dt-1", "status": "referred",
            "requestRef": {"requestId": "req-1", "typeCode": "process-issue"},
        }
        svc = _svc(mes=mes)
        with pytest.raises(MesSourceConflict):
            svc.refer_request(
                user(*FULL), "dt-1", branch="01",
                issue_code="other", note=None, idempotency_key=None,
            )

    def test_refer_requires_create_permission(self):
        mes = FakeMesGateway()
        svc = _svc(mes=mes)
        perms = tuple(p for p in FULL if p != "my-requests.process-issue.create")
        with pytest.raises(PermissionError):
            svc.refer_request(
                user(*perms), "dt-1", branch="01",
                issue_code="other", note=None, idempotency_key=None,
            )


class TestConclusion:
    def test_conclude_without_request(self):
        mes = FakeMesGateway()
        mes.treatment = {"downtimeId": "dt-1", "status": "pending",
                         "requestRef": None}
        svc = _svc(mes=mes)
        out = svc.conclude_treatment(
            user(*FULL), "dt-1", branch="01", reason="resolvido",
        )
        _, _, payload = mes.calls[-1]
        assert payload["linkedRequestCompleted"] is False
        assert out["treatment"]["status"] == "concluded"

    def test_conclude_blocked_while_request_open(self):
        mes = FakeMesGateway()
        mes.treatment = {
            "downtimeId": "dt-1", "status": "referred",
            "requestRef": {"requestId": "req-1", "typeCode": "process-issue"},
        }
        req = FakeRequestsGateway()
        req.status = {"id": "req-1", "status": "in_progress",
                      "type_code": "process-issue"}
        svc = _svc(mes=mes, req=req)
        with pytest.raises(MesSourceConflict):
            svc.conclude_treatment(
                user(*FULL), "dt-1", branch="01", reason="ok",
            )

    def test_conclude_allowed_after_request_completed(self):
        mes = FakeMesGateway()
        mes.treatment = {
            "downtimeId": "dt-1", "status": "referred",
            "requestRef": {"requestId": "req-1", "typeCode": "process-issue"},
        }
        svc = _svc(mes=mes)
        out = svc.conclude_treatment(
            user(*FULL), "dt-1", branch="01", reason="atendida",
        )
        _, _, payload = mes.calls[-1]
        assert payload["linkedRequestCompleted"] is True
        assert out["treatment"]["status"] == "concluded"

    def test_conclude_requires_treatment(self):
        mes = FakeMesGateway()
        svc = _svc(mes=mes)
        with pytest.raises(MesSourceConflict):
            svc.conclude_treatment(
                user(*FULL), "dt-1", branch="01", reason="ok",
            )
