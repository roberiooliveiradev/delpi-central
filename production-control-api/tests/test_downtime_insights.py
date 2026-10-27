"""Análise avançada de paradas (Etapa 6) — insights do owner.

Cobre reincidência, comparação de janelas equivalentes, criticidade
parametrizada, eficácia de ações (evidência, não causalidade),
pendências e lacunas de telemetria — sempre sobre fatos reais do
repositório, nunca inventados.
"""

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_integration_read_service import (
    MesIntegrationReadService,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)

NOW = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)


class FakeInsightsRepository:
    def __init__(self, facts=None, previous_facts=None):
        self.facts = facts or []
        self.previous_facts = previous_facts or []
        self.treatments = []
        self.observers = []
        self.open_treatments = 0
        self.occurrence_counts = {}
        self.analytics_calls = []

    def list_downtime_analytics_facts(self, **kwargs):
        self.analytics_calls.append(kwargs)
        # primeira chamada = janela corrente; segunda = janela anterior
        # equivalente (mesmo predicado, período deslocado).
        if len(self.analytics_calls) > 1:
            return {"facts": self.previous_facts, "capped": False}
        return {"facts": self.facts, "capped": False}

    def list_concluded_downtime_treatments(self, **kwargs):
        return list(self.treatments)

    def list_work_center_observer_states(self, **kwargs):
        return list(self.observers)

    def count_open_downtime_treatments(self, **kwargs):
        return self.open_treatments

    def count_downtime_occurrences(self, **kwargs):
        key = (
            kwargs["work_center"],
            kwargs["reason_code"],
            # conclusão do tratamento do teste = NOW - 3 dias; janelas que
            # terminam até ali são "before", as seguintes são "after".
            "before"
            if kwargs["period_to"] <= NOW - timedelta(days=3)
            else "after",
        )
        return self.occurrence_counts.get(
            key, {"occurrencesCount": 0, "seconds": 0}
        )


def make_service(repo):
    return MesIntegrationReadService(
        repository=repo,
        branch_access=BranchAccessService(),
        clock=lambda: NOW,
    )


def fact(id_, work_center, started, ended=None, reason=None, confirmed=True, label=None):
    return {
        "id": id_,
        "work_center": work_center,
        "started_at": started,
        "ended_at": ended,
        "source": "system",
        "reason_code": reason,
        "reason_label": label or reason,
        "category": None,
        "confirmed": confirmed,
    }


BASE_FROM = NOW - timedelta(days=7)


def test_insights_requires_from_and_valid_window():
    service = make_service(FakeInsightsRepository())
    with pytest.raises(ValueError, match="from"):
        service.get_downtime_insights(branch="01", period_from=None)
    with pytest.raises(ValueError):
        service.get_downtime_insights(
            branch="01", period_from=NOW, period_to=NOW - DAY
        )
    with pytest.raises(ValueError, match="92"):
        service.get_downtime_insights(
            branch="01", period_from=NOW - timedelta(days=93)
        )


def test_recurrence_groups_real_occurrences_by_center_and_reason():
    repo = FakeInsightsRepository(
        facts=[
            fact("a", "CT-35", NOW - timedelta(days=5), NOW - timedelta(days=5) + timedelta(hours=1), reason="SETUP"),
            fact("b", "CT-35", NOW - timedelta(days=3), NOW - timedelta(days=3) + timedelta(hours=2), reason="SETUP"),
            fact("c", "CT-35", NOW - timedelta(days=2), reason="SETUP"),  # aberta
            fact("d", "CT-41", NOW - timedelta(days=4), NOW - timedelta(days=4) + timedelta(hours=1), reason="SETUP"),
        ]
    )
    data = make_service(repo).get_downtime_insights(
        branch="01", period_from=BASE_FROM
    )
    rec = data["recurrence"]
    assert len(rec) == 1
    assert rec[0]["workCenter"] == "CT-35"
    assert rec[0]["reasonCode"] == "SETUP"
    assert rec[0]["occurrencesCount"] == 3
    assert set(rec[0]["downtimeIds"]) == {"a", "b", "c"}


def test_comparison_uses_immediately_preceding_equal_window():
    repo = FakeInsightsRepository(
        facts=[fact("a", "CT-35", NOW - DAY, NOW - DAY + timedelta(hours=2))],
        previous_facts=[
            fact("p", "CT-35", BASE_FROM - DAY, BASE_FROM - DAY + timedelta(hours=1))
        ],
    )
    data = make_service(repo).get_downtime_insights(
        branch="01", period_from=BASE_FROM, period_to=NOW
    )
    comp = data["comparison"]
    assert comp["criteria"] == "immediately-preceding equal-duration window"
    assert comp["previous"]["to"] == BASE_FROM.isoformat()
    assert comp["current"]["durationSeconds"] == comp["previous"]["durationSeconds"]
    delta = comp["deltas"]["occurrencesCount"]
    assert delta["current"] == 1 and delta["previous"] == 1


def test_critical_rules_inactive_without_parameters(monkeypatch):
    from production_control_app.application.services import (
        mes_integration_read_service as module,
    )
    monkeypatch.setattr(
        module.settings, "PC_MES_DOWNTIME_CRITICAL_OPEN_SECONDS", None
    )
    monkeypatch.setattr(
        module.settings,
        "PC_MES_DOWNTIME_CRITICAL_RECURRENCE_OCCURRENCES",
        None,
    )
    data = make_service(FakeInsightsRepository()).get_downtime_insights(
        branch="01", period_from=BASE_FROM
    )
    assert data["critical"]["items"] == []
    assert data["critical"]["rules"]["openStopLongDuration"]["configured"] is False
    assert data["critical"]["rules"]["recurrenceBurst"]["configured"] is False


def test_critical_open_stop_uses_configured_threshold(monkeypatch):
    from production_control_app.application.services import (
        mes_integration_read_service as module,
    )
    monkeypatch.setattr(
        module.settings, "PC_MES_DOWNTIME_CRITICAL_OPEN_SECONDS", 3600
    )
    monkeypatch.setattr(
        module.settings,
        "PC_MES_DOWNTIME_CRITICAL_RECURRENCE_OCCURRENCES",
        None,
    )
    repo = FakeInsightsRepository(
        facts=[
            fact("long", "CT-35", NOW - timedelta(hours=5), None),
            fact("short", "CT-41", NOW - timedelta(minutes=10), None),
            fact("closed", "CT-35", NOW - timedelta(hours=6), NOW - timedelta(hours=4)),
        ]
    )
    data = make_service(repo).get_downtime_insights(
        branch="01", period_from=BASE_FROM
    )
    items = data["critical"]["items"]
    assert len(items) == 1
    assert items[0]["downtimeId"] == "long"
    assert items[0]["elapsedSeconds"] == 5 * 3600


def test_critical_recurrence_burst_uses_configured_count(monkeypatch):
    from production_control_app.application.services import (
        mes_integration_read_service as module,
    )
    monkeypatch.setattr(
        module.settings, "PC_MES_DOWNTIME_CRITICAL_OPEN_SECONDS", None
    )
    monkeypatch.setattr(
        module.settings,
        "PC_MES_DOWNTIME_CRITICAL_RECURRENCE_OCCURRENCES",
        3,
    )
    repo = FakeInsightsRepository(
        facts=[
            fact(f"r{i}", "CT-35", NOW - timedelta(days=i + 1), reason="X")
            for i in range(3)
        ]
    )
    data = make_service(repo).get_downtime_insights(
        branch="01", period_from=BASE_FROM
    )
    bursts = [i for i in data["critical"]["items"] if i["rule"] == "recurrenceBurst"]
    assert len(bursts) == 1
    assert bursts[0]["occurrencesCount"] == 3


def test_effectiveness_reports_before_after_evidence_without_causality():
    repo = FakeInsightsRepository()
    repo.treatments = [
        {
            "downtime_id": "dt-9",
            "request_id": "00000000-0000-0000-0000-000000000042",
            "concluded_at": NOW - timedelta(days=3),
            "work_center": "CT-35",
            "reason_code": "SETUP",
            "reason_label": "Setup",
        }
    ]
    repo.occurrence_counts = {
        ("CT-35", "SETUP", "before"): {"occurrencesCount": 4, "seconds": 7200},
        ("CT-35", "SETUP", "after"): {"occurrencesCount": 1, "seconds": 900},
    }
    data = make_service(repo).get_downtime_insights(
        branch="01", period_from=BASE_FROM
    )
    records = data["actionEffectiveness"]
    assert len(records) == 1
    rec = records[0]
    assert rec["before"]["occurrencesCount"] == 4
    assert rec["after"]["occurrencesCount"] == 1
    assert rec["evidence"] == "pre_post_occurrence_comparison"
    assert rec["requestId"] == "00000000-0000-0000-0000-000000000042"
    assert rec["windowDays"] == 30


def test_pendencies_and_telemetry_gaps():
    repo = FakeInsightsRepository(
        facts=[
            fact("a", "CT-35", NOW - DAY, reason="SETUP", confirmed=False),
            fact("b", "CT-99", NOW - DAY, reason="SETUP"),  # sem observer
        ]
    )
    repo.open_treatments = 2
    repo.observers = [
        {
            "work_center": "CT-35",
            "device_online": False,
            "degraded_reason": "offline",
            "last_seen_at": NOW - timedelta(minutes=5),
        }
    ]
    data = make_service(repo).get_downtime_insights(
        branch="01", period_from=BASE_FROM
    )
    assert data["pendencies"] == {
        "unclassifiedCount": 1,
        "openTreatmentsCount": 2,
        "openStopsCount": 2,
    }
    gaps = {g["workCenter"]: g["state"] for g in data["quality"]["telemetryGaps"]}
    assert gaps["CT-35"] == "degraded"
    assert gaps["CT-99"] == "no_observation"


def test_applied_filters_follow_shared_normalization():
    service = make_service(FakeInsightsRepository())
    with pytest.raises(ValueError, match="status"):
        service.get_downtime_insights(
            branch="01", period_from=BASE_FROM, status="bogus"
        )
    with pytest.raises(ValueError, match="classification"):
        service.get_downtime_insights(
            branch="01", period_from=BASE_FROM, classification="bogus"
        )
