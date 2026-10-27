"""Testes do avaliador de alertas gerenciais de paradas (Etapa 6).

Cobre: candidatos por regra parametrizada, dedup persistido por
assinatura, escopo de filial, dispatch via Core API (best-effort) e
cadência do tick.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_downtime_alert_service import (
    MesDowntimeAlertService,
    evaluation_due,
    reset_evaluation_schedule,
)

NOW = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)


class FakeAlertRepository:
    def __init__(self) -> None:
        self.open_downtimes: dict[str, list[dict]] = {"01": [], "02": []}
        self.unclassified: dict[str, int] = {"01": 0, "02": 0}
        self.overdue: dict[str, list[dict]] = {"01": [], "02": []}
        self.claims: list[dict] = []
        self.claim_results: dict[str, list[bool]] = {}
        self.fail_claim = False

    def list_open_downtimes_older_than(self, *, branch, reference_before):
        return [
            d
            for d in self.open_downtimes.get(branch, [])
            if d["started_at"] <= reference_before
        ]

    def count_unclassified_downtimes(self, *, branch):
        return self.unclassified.get(branch, 0)

    def list_overdue_open_treatments(self, *, branch, reference_before):
        return [
            t
            for t in self.overdue.get(branch, [])
            if t["created_at"] <= reference_before
        ]

    def claim_if_signature_changed(
        self, *, alert_key, branch, rule, subject_key, signature, now
    ):
        if self.fail_claim:
            raise RuntimeError("db down")
        self.claims.append(
            {"alert_key": alert_key, "signature": signature}
        )
        results = self.claim_results.setdefault(alert_key, [])
        return results.pop(0) if results else True


class SpyGateway:
    def __init__(self, fail: bool = False) -> None:
        self.payloads: list[dict] = []
        self.fail = fail

    def dispatch(self, payload):
        if self.fail:
            raise RuntimeError("core api down")
        self.payloads.append(payload)


def _service(
    repo: FakeAlertRepository,
    gateway,
    *,
    critical_open_seconds=3600,
    unclassified_threshold=3,
    overdue_action_days=7,
) -> MesDowntimeAlertService:
    return MesDowntimeAlertService(
        repository=repo,
        notification_gateway=gateway,
        clock=lambda: NOW,
        critical_open_seconds=critical_open_seconds,
        unclassified_threshold=unclassified_threshold,
        overdue_action_days=overdue_action_days,
    )


def _open_downtime(
    id_: str, started_at: datetime, reason_code: str | None = None
) -> dict:
    return {
        "id": id_,
        "work_center": "BANC-01",
        "started_at": started_at,
        "reason_code": reason_code,
        "reason_label": "Falta de material" if reason_code else None,
    }


@pytest.fixture(autouse=True)
def _reset_schedule():
    reset_evaluation_schedule()
    yield
    reset_evaluation_schedule()


class TestProlongedOpenStop:
    def test_dispatches_for_open_stop_older_than_threshold(self):
        repo = FakeAlertRepository()
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(hours=2), "MAT-FALTA")
        ]
        spy = SpyGateway()
        result = _service(repo, spy).tick()

        assert result["dispatched"] == 1
        payload = spy.payloads[0]
        assert payload["category"] == "production_control_mes_downtime_alerts"
        assert payload["metadata"]["event"] == "prolonged_open_stop"
        assert payload["metadata"]["downtimeId"] == "d1"
        assert payload["permissionCodes"] == ["delpi-mes.downtimes.treat"]
        assert payload["requiredPermissionCodes"] == [
            "delpi-mes.view.filial-01"
        ]

    def test_recent_stop_is_not_a_candidate(self):
        repo = FakeAlertRepository()
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(minutes=10))
        ]
        spy = SpyGateway()
        assert _service(repo, spy).tick()["candidates"] == 0
        assert spy.payloads == []

    def test_branch_scope_uses_branch_permission(self):
        repo = FakeAlertRepository()
        repo.open_downtimes["02"] = [
            _open_downtime("d9", NOW - timedelta(hours=5))
        ]
        spy = SpyGateway()
        _service(repo, spy).tick()
        assert spy.payloads[0]["requiredPermissionCodes"] == [
            "delpi-mes.view.filial-02"
        ]

    def test_classification_change_resigns_the_alert(self):
        repo = FakeAlertRepository()
        repo.claim_results[
            "prolonged_open_stop:01:d1"
        ] = [True, False, True]
        spy = SpyGateway()
        svc = _service(repo, spy)
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(hours=2))
        ]
        svc.tick()  # dispatch 1 (sem motivo)
        svc.tick()  # mesma assinatura → claim False → sem dispatch
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(hours=2), "MANUT")
        ]
        svc.tick()  # motivo mudou a assinatura → dispatch 2
        assert len(spy.payloads) == 2


class TestUnclassifiedBacklog:
    def test_above_threshold_dispatches_once_per_branch(self):
        repo = FakeAlertRepository()
        repo.unclassified["01"] = 5
        repo.unclassified["02"] = 1
        spy = SpyGateway()
        _service(repo, spy).tick()
        assert len(spy.payloads) == 1
        assert "5" in spy.payloads[0]["message"]

    def test_at_threshold_does_not_dispatch(self):
        repo = FakeAlertRepository()
        repo.unclassified["01"] = 3
        spy = SpyGateway()
        assert _service(repo, spy).tick()["candidates"] == 0


class TestOverdueAction:
    def test_overdue_treatment_dispatches_with_day_bucket(self):
        repo = FakeAlertRepository()
        repo.overdue["01"] = [
            {
                "downtime_id": "d7",
                "work_center": "BANC-02",
                "status": "forwarded",
                "created_at": NOW - timedelta(days=9),
            }
        ]
        spy = SpyGateway()
        _service(repo, spy).tick()
        payload = spy.payloads[0]
        assert payload["metadata"]["event"] == "overdue_action"
        assert payload["metadata"]["overdueDays"] == 9


class TestDisabledAndResilience:
    def test_no_parameters_means_no_candidates(self):
        repo = FakeAlertRepository()
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(days=2))
        ]
        repo.unclassified["01"] = 50
        spy = SpyGateway()
        result = _service(
            repo,
            spy,
            critical_open_seconds=None,
            unclassified_threshold=None,
            overdue_action_days=None,
        ).tick()
        assert result["candidates"] == 0
        assert spy.payloads == []

    def test_no_gateway_is_noop(self):
        repo = FakeAlertRepository()
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(hours=2))
        ]
        result = _service(repo, None).tick()
        assert result == {
            "candidates": 0,
            "dispatched": 0,
            "skipped": 0,
            "enabled": False,
        }

    def test_gateway_failure_does_not_raise(self):
        repo = FakeAlertRepository()
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(hours=2))
        ]
        result = _service(repo, SpyGateway(fail=True)).tick()
        assert result["dispatched"] == 0

    def test_claim_failure_skips_without_raising(self):
        repo = FakeAlertRepository()
        repo.fail_claim = True
        repo.open_downtimes["01"] = [
            _open_downtime("d1", NOW - timedelta(hours=2))
        ]
        spy = SpyGateway()
        result = _service(repo, spy).tick()
        assert result["dispatched"] == 0
        assert spy.payloads == []


class TestCadence:
    def test_evaluation_due_throttles_by_interval(self):
        assert evaluation_due(100.0, interval_seconds=300)
        assert not evaluation_due(150.0, interval_seconds=300)
        assert evaluation_due(500.0, interval_seconds=300)

    def test_interval_floor_is_30_seconds(self):
        assert evaluation_due(0.0, interval_seconds=5)
        assert not evaluation_due(10.0, interval_seconds=5)
        assert evaluation_due(40.0, interval_seconds=5)
