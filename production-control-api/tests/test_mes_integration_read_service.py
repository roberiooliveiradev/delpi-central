from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_integration_read_service import (
    MesIntegrationReadService,
)
from production_control_app.domain.errors import ProductionRunNotFound
from production_control_app.domain.services.branch_access_service import BranchAccessService

NOW = datetime(2026, 9, 29, 13, 0, tzinfo=timezone.utc)


class FakeRepository:
    def __init__(self):
        self.live_rows = []
        self.run = None
        self.timeline_rows = []
        self.downtime_rows = []
        self.wc_timeline_rows = []
        self.last_wc_timeline_args = None
        self.live_calls = 0
        self.downtime_calls = 0
        self.last_downtime_args = None

    def list_live_work_centers(self, *, branch):
        self.live_calls += 1
        return self.live_rows

    def get_run(self, run_id):
        return self.run if self.run and self.run["id"] == run_id else None

    def list_timeline_facts(self, run_id):
        return self.timeline_rows

    def list_work_center_timeline_facts(self, **kwargs):
        self.last_wc_timeline_args = kwargs
        return self.wc_timeline_rows

    def list_downtimes(self, **kwargs):
        self.downtime_calls += 1
        self.last_downtime_args = kwargs
        return self.downtime_rows, len(self.downtime_rows)


def make_service(repo):
    return MesIntegrationReadService(
        repository=repo,
        branch_access=BranchAccessService(),
        clock=lambda: NOW,
    )


def live_row(**changes):
    row = {
        "run_id": "run-1", "branch": "01", "work_center": "CT-35",
        "run_status": "running", "production_order": "123456", "operation_code": "20",
        "operator_code": "000123", "operator_name": "Operador", "pieces_total": 384,
        "target_pieces": 500, "last_count_activity_at": NOW - timedelta(seconds=2),
        "state_id": "state-1", "operational_state": "producing",
        "state_started_at": NOW - timedelta(minutes=18), "state_source": "operator",
        "downtime_id": None, "downtime_started_at": None, "downtime_source": None,
        "reason_code": None, "reason_label": None, "category": None,
        "confirmed": False, "note": None,
    }
    row.update(changes)
    return row


def test_live_empty_has_zero_summary_and_one_bounded_read():
    repo = FakeRepository()
    data = make_service(repo).get_live_work_centers(branch="01")
    assert data["items"] == []
    assert data["summary"] == {
        "activeRuns": 0, "producing": 0, "stopped": 0,
        "paused": 0, "unclassifiedDowntimes": 0,
    }
    assert repo.live_calls == 1


def test_live_preserves_run_and_operational_state_and_derives_summary():
    repo = FakeRepository()
    repo.live_rows = [
        live_row(),
        live_row(
            run_id="run-2", work_center="CT-41", run_status="running",
            operational_state="stopped", state_source="system", downtime_id="down-1",
            downtime_started_at=NOW - timedelta(minutes=8), downtime_source="system",
            reason_code=None, confirmed=False,
        ),
        live_row(
            run_id="run-3", work_center="CT-42", run_status="paused",
            operational_state="stopped", downtime_id="down-2", reason_code="raw_material",
            reason_label="Falta de material", category="material", confirmed=True,
        ),
    ]
    data = make_service(repo).get_live_work_centers(branch="01")
    assert data["summary"] == {
        "activeRuns": 3, "producing": 1, "stopped": 2,
        "paused": 1, "unclassifiedDowntimes": 1,
    }
    assert data["items"][1]["runStatus"] == "running"
    assert data["items"][1]["operationalState"] == "stopped"
    assert data["items"][2]["downtime"]["reasonLabel"] == "Falta de material"


def test_live_does_not_invent_state_for_incomplete_run():
    repo = FakeRepository()
    repo.live_rows = [live_row(state_id=None, operational_state=None, state_started_at=None)]
    item = make_service(repo).get_live_work_centers(branch="01")["items"][0]
    assert item["operationalState"] is None
    assert item["integrityStatus"] == "incomplete"


def test_invalid_branch_is_controlled():
    with pytest.raises(Exception, match="Filial inválida"):
        make_service(FakeRepository()).get_live_work_centers(branch="99")


def test_timeline_uses_shared_builder_semantics_without_bench_session():
    repo = FakeRepository()
    repo.run = {
        "id": "run-1", "branch": "01", "work_center": "CT-35",
        "status": "running", "started_at": NOW - timedelta(minutes=10), "ended_at": None,
    }
    repo.timeline_rows = [
        {
            "id": "state-1", "state": "producing", "started_at": NOW - timedelta(minutes=10),
            "ended_at": NOW - timedelta(minutes=5), "source": "operator", "downtime_id": None,
        },
        {
            "id": "state-2", "state": "stopped", "started_at": NOW - timedelta(minutes=5),
            "ended_at": None, "source": "system", "downtime_id": "down-1",
            "reason_code": None, "reason_label": None, "category": None,
            "confirmed": False, "note": None, "downtime_source": "system",
        },
    ]
    data = make_service(repo).get_run_timeline("run-1")
    assert data["summary"] == {
        "elapsedSeconds": 600, "producingSeconds": 300,
        "stoppedSeconds": 300, "stopCount": 1,
    }
    assert data["items"][1]["downtime"]["confirmed"] is False


def test_unknown_timeline_run_is_not_found():
    with pytest.raises(ProductionRunNotFound):
        make_service(FakeRepository()).get_run_timeline("missing")


def wc_event(**changes):
    row = {
        "id": "state-1", "branch": "01", "work_center": "CT-35", "run_id": "run-1",
        "state": "producing", "started_at": NOW - timedelta(hours=2),
        "ended_at": NOW - timedelta(hours=1), "source": "operator",
        "production_order": "123456", "operation_code": "20",
        "downtime_id": None,
    }
    row.update(changes)
    return row


def test_work_center_timeline_spans_multiple_runs_and_downtimes():
    repo = FakeRepository()
    repo.wc_timeline_rows = [
        wc_event(),
        wc_event(
            id="state-2", state="stopped",
            started_at=NOW - timedelta(hours=1), ended_at=NOW - timedelta(minutes=50),
            source="system", downtime_id="down-1", reason_code="raw_material",
            reason_label="Falta de material", category="material",
            confirmed=True, note=None, downtime_source="system",
        ),
        wc_event(
            id="state-3", run_id="run-2", production_order="654321",
            operation_code="10", started_at=NOW - timedelta(minutes=50),
            ended_at=None,
        ),
    ]
    start = NOW - timedelta(hours=6)
    data = make_service(repo).get_work_center_timeline(
        branch="01", work_center="CT-35", period_from=start, period_to=NOW,
    )
    assert data["branch"] == "01" and data["workCenter"] == "CT-35"
    assert data["from"] == start.isoformat() and data["to"] == NOW.isoformat()
    assert [item["productionOrder"] for item in data["items"]] == ["123456", "123456", "654321"]
    assert data["items"][1]["downtime"]["reasonLabel"] == "Falta de material"
    assert data["items"][2]["endedAt"] is None
    assert repo.last_wc_timeline_args == {
        "branch": "01", "work_center": "CT-35",
        "period_from": start, "period_to": NOW,
    }


def test_work_center_timeline_defaults_to_now_and_keeps_pending_downtime():
    repo = FakeRepository()
    repo.wc_timeline_rows = [
        wc_event(
            state="stopped", ended_at=None, downtime_id="down-9",
            reason_code=None, reason_label=None, category=None,
            confirmed=False, note=None, downtime_source="operator",
        ),
    ]
    data = make_service(repo).get_work_center_timeline(
        branch="01", work_center="CT-35",
        period_from=NOW - timedelta(hours=6),
    )
    assert data["to"] == NOW.isoformat()
    assert repo.last_wc_timeline_args["period_to"] == NOW
    assert data["items"][0]["downtime"]["confirmed"] is False
    assert data["items"][0]["downtime"]["reasonCode"] is None


def test_work_center_timeline_empty_and_validations():
    repo = FakeRepository()
    data = make_service(repo).get_work_center_timeline(
        branch="01", work_center="CT-35", period_from=NOW - timedelta(hours=1),
    )
    assert data["items"] == []
    service = make_service(repo)
    with pytest.raises(Exception, match="Filial inválida"):
        service.get_work_center_timeline(
            branch="99", work_center="CT-35", period_from=NOW - timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="Centro de trabalho"):
        service.get_work_center_timeline(
            branch="01", work_center="  ", period_from=NOW - timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="anterior ao fim"):
        service.get_work_center_timeline(
            branch="01", work_center="CT-35",
            period_from=NOW, period_to=NOW - timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="timezone"):
        service.get_work_center_timeline(
            branch="01", work_center="CT-35",
            period_from=datetime(2026, 9, 29),
        )


def test_downtime_filters_are_forwarded_with_pagination():
    repo = FakeRepository()
    start = NOW - timedelta(hours=1)
    make_service(repo).list_downtimes(
        branch="01", work_center="CT-35", period_from=start,
        period_to=NOW, page=2, page_size=25,
    )
    assert repo.downtime_calls == 1
    assert repo.last_downtime_args == {
        "branch": "01", "work_center": "CT-35", "period_from": start,
        "period_to": NOW, "page": 2, "page_size": 25,
    }


def test_downtime_page_size_is_limited():
    with pytest.raises(ValueError, match="pageSize"):
        make_service(FakeRepository()).list_downtimes(branch="01", page_size=101)
