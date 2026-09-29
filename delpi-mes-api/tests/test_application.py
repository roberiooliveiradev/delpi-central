from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from delpi_mes_app.application.services.mes_read_service import MesReadService
from delpi_mes_app.core.security import MES_DOWNTIMES_VIEW, MES_HISTORY_VIEW, MES_MONITORING_VIEW
from delpi_mes_app.domain.errors import HumanPrincipalRequired, MesSourceNotFound


def user(*permissions, superadmin=False, principal_type="user"):
    return SimpleNamespace(
        permissions=list(permissions), is_superadmin=superadmin,
        principal_type=principal_type, rbac_unavailable=False,
    )


class Gateway:
    def __init__(self):
        self.monitoring = {"branch": "01", "referenceAt": "ref", "summary": {}, "items": []}
        self.timeline = {"runId": "run-1", "branch": "01", "workCenter": "CT", "status": "running", "referenceAt": "ref", "summary": {"producingSeconds": 10}, "items": [{"durationSeconds": 10}]}
        self.downtimes = {"branch": "01", "referenceAt": "ref", "page": 1, "pageSize": 50, "total": 0, "items": []}
        self.args = None
    def get_monitoring(self, **kwargs): self.args = kwargs; return self.monitoring
    def get_timeline(self, run_id): return self.timeline
    def get_downtimes(self, **kwargs): self.args = kwargs; return self.downtimes


FULL = (
    "delpi-mes.access", "delpi-mes.monitoring.view", "delpi-mes.downtimes.view",
    "delpi-mes.history.view", "delpi-mes.view.filial-01",
)


def test_monitoring_empty_and_explicit_dto():
    gateway = Gateway()
    data = MesReadService(gateway).get_monitoring(user(*FULL), branch="01", permission=MES_MONITORING_VIEW)
    assert data["items"] == []
    gateway.monitoring["items"] = [{
        "branch": "01", "workCenter": "CT", "runId": "run", "runStatus": "running",
        "operationalState": "stopped", "integrityStatus": "incomplete", "deviceOnline": True,
        "downtime": {"confirmed": False},
    }]
    item = MesReadService(gateway).get_monitoring(user(*FULL), branch="01", permission=MES_MONITORING_VIEW)["items"][0]
    assert item["runStatus"] == "running" and item["operationalState"] == "stopped"
    assert item["integrityStatus"] == "incomplete"
    assert "deviceOnline" not in item


@pytest.mark.parametrize("run_status", ["running", "paused"])
def test_monitoring_preserves_stopped_siblings(run_status):
    gateway = Gateway()
    gateway.monitoring["items"] = [{"runStatus": run_status, "operationalState": "stopped", "downtime": {"reasonCode": "raw_material", "confirmed": True}}]
    item = MesReadService(gateway).get_monitoring(user(*FULL), branch="01", permission=MES_MONITORING_VIEW)["items"][0]
    assert item["runStatus"] == run_status
    assert item["operationalState"] == "stopped"


def test_monitoring_preserves_producing_and_pending_downtime():
    gateway = Gateway()
    gateway.monitoring["items"] = [
        {"runStatus": "running", "operationalState": "producing", "downtime": None},
        {"runStatus": "running", "operationalState": "stopped", "downtime": {"reasonCode": None, "confirmed": False}},
    ]
    items = MesReadService(gateway).get_monitoring(
        user(*FULL), branch="01", permission=MES_MONITORING_VIEW
    )["items"]
    assert items[0]["operationalState"] == "producing"
    assert items[1]["downtime"]["reasonCode"] is None
    assert items[1]["downtime"]["confirmed"] is False


def test_timeline_is_forwarded_without_recalculation():
    gateway = Gateway()
    data = MesReadService(gateway).get_timeline(user(*FULL), "run-1", permission=MES_HISTORY_VIEW)
    assert data["summary"]["producingSeconds"] == 10
    assert data["items"][0]["durationSeconds"] == 10


def test_timeline_not_found_propagates():
    gateway = Gateway()
    gateway.get_timeline = lambda run_id: (_ for _ in ()).throw(MesSourceNotFound())
    with pytest.raises(MesSourceNotFound):
        MesReadService(gateway).get_timeline(user(*FULL), "missing", permission=MES_HISTORY_VIEW)


def test_downtime_filters_and_pagination_are_forwarded():
    gateway = Gateway()
    start = datetime(2026, 9, 29, 10, tzinfo=timezone.utc)
    end = datetime(2026, 9, 29, 11, tzinfo=timezone.utc)
    MesReadService(gateway).get_downtimes(
        user(*FULL), branch="01", work_center="CT", period_from=start, period_to=end,
        page=2, page_size=25, permission=MES_DOWNTIMES_VIEW,
    )
    assert gateway.args == {"branch": "01", "work_center": "CT", "period_from": start, "period_to": end, "page": 2, "page_size": 25}


@pytest.mark.parametrize(
    ("start", "end"),
    [(datetime(2026, 1, 1), None), (datetime(2026, 1, 2, tzinfo=timezone.utc), datetime(2026, 1, 1, tzinfo=timezone.utc))],
)
def test_invalid_period_rejected(start, end):
    with pytest.raises(ValueError):
        MesReadService(Gateway()).get_downtimes(
            user(*FULL), branch="01", work_center=None, period_from=start, period_to=end,
            page=1, page_size=50, permission=MES_DOWNTIMES_VIEW,
        )


def test_service_principal_is_rejected_even_if_superadmin():
    with pytest.raises(HumanPrincipalRequired):
        MesReadService(Gateway()).get_monitoring(
            user(superadmin=True, principal_type="service"), branch="01", permission=MES_MONITORING_VIEW
        )
