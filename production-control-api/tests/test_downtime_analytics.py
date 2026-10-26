"""Etapa 2 — Gestão de Paradas: agregações gerenciais.

Cobre o agregador puro (janela, união temporal por CT, pendências, dias
civis de America/Sao_Paulo, células dia-da-semana x hora, parada aberta,
DST histórico) e o contrato do service (validações, referenceAt único,
limite de janela, fatos truncados).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.downtime_analytics import (
    aggregate_downtime_analytics,
)
from production_control_app.application.services.mes_integration_read_service import (
    MesIntegrationReadService,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

NOW = datetime(2026, 2, 11, 15, 0, tzinfo=timezone.utc)  # qua 12:00 SP
WINDOW_FROM = datetime(2026, 2, 9, 3, 0, tzinfo=timezone.utc)   # seg 00:00 SP
WINDOW_TO = datetime(2026, 2, 11, 3, 0, tzinfo=timezone.utc)    # qua 00:00 SP


def dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def fact(id_, wc, start, end=None, reason="SETUP", label="Setup",
         confirmed=True, source="operator"):
    return {
        "id": id_, "work_center": wc, "started_at": dt(start),
        "ended_at": dt(end) if end else None, "reason_code": reason,
        "reason_label": label, "category": "setup", "confirmed": confirmed,
        "source": source,
    }


def run(facts, window_from=WINDOW_FROM, window_to=WINDOW_TO, capped=False):
    return aggregate_downtime_analytics(
        facts, window_from=window_from, window_to=window_to,
        facts_capped=capped,
    )


def by_key(rows, field="key"):
    return {r[field]: r for r in rows}


# ---------- agregador: indicadores ----------

def test_summary_totals_and_average():
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T15:00:00+00:00"),
        fact("b", "CT2", "2026-02-10T12:00:00+00:00", "2026-02-10T13:00:00+00:00",
             reason="QUEBRA", label="Quebra"),
    ])
    s = r["summary"]
    assert s["totalStoppedSeconds"] == 7200 + 3600
    assert s["attributedSeconds"] == 7200 + 3600
    assert s["occurrencesCount"] == 2
    assert s["averageOccurrenceSeconds"] == 5400
    assert s["pendingCount"] == 0 and s["openCount"] == 0
    assert r["quality"] == {
        "overlapDetected": False, "overlapSeconds": 0,
        "partial": False, "factsCapped": False,
    }


def test_overlap_deduplicates_physical_time_and_reports_quality():
    # A 10h-12h SP e B 11h-13h SP no mesmo CT: 3h físicas, 4h atribuídas.
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T15:00:00+00:00"),
        fact("b", "CT1", "2026-02-09T14:00:00+00:00", "2026-02-09T16:00:00+00:00",
             reason="QUEBRA"),
    ])
    s = r["summary"]
    assert s["totalStoppedSeconds"] == 10800
    assert s["attributedSeconds"] == 14400
    assert r["quality"]["overlapDetected"] is True
    assert r["quality"]["overlapSeconds"] == 3600
    ct = by_key(r["byWorkCenter"], "workCenter")["CT1"]
    assert ct["seconds"] == 10800 and ct["occurrencesCount"] == 2


def test_different_work_centers_accumulate():
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T15:00:00+00:00"),
        fact("b", "CT2", "2026-02-09T13:00:00+00:00", "2026-02-09T15:00:00+00:00"),
    ])
    assert r["summary"]["totalStoppedSeconds"] == 14400
    assert r["quality"]["overlapDetected"] is False


def test_open_downtime_is_clipped_at_window_to():
    r = run([
        fact("a", "CT1", "2026-02-11T01:00:00+00:00", None, confirmed=False),
    ])  # aberta: ter 22h SP até qua 00:00 SP (fim efetivo) = 2h
    s = r["summary"]
    assert s["openCount"] == 1 and s["pendingCount"] == 1
    assert s["totalStoppedSeconds"] == 7200


def test_downtime_crossing_window_start_contributes_only_inside():
    r = run([
        fact("a", "CT1", "2026-02-09T01:00:00+00:00", "2026-02-09T05:00:00+00:00"),
    ])  # domingo 22h SP até seg 02h SP: só 2h dentro da janela
    assert r["summary"]["totalStoppedSeconds"] == 7200
    days = by_key(r["byDay"], "date")
    assert days["2026-02-09"]["seconds"] == 7200
    assert "2026-02-08" not in days or days["2026-02-08"]["seconds"] == 0


def test_downtime_crossing_window_end_contributes_only_inside():
    r = run([
        fact("a", "CT1", "2026-02-11T01:00:00+00:00", "2026-02-11T06:00:00+00:00"),
    ])  # ter 22h até qua 03h SP: só até qua 00:00 = 2h
    assert r["summary"]["totalStoppedSeconds"] == 7200


def test_pending_groups_never_become_definitive_causes():
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T14:00:00+00:00",
             reason=None, label=None, confirmed=False, source="autonomous"),
        fact("b", "CT1", "2026-02-09T15:00:00+00:00", "2026-02-09T16:00:00+00:00",
             reason=None, label=None, confirmed=True),  # confirmada sem código
        fact("c", "CT1", "2026-02-09T17:00:00+00:00", "2026-02-09T18:00:00+00:00",
             reason=None, label=None, confirmed=False),
    ])
    groups = by_key(r["byReason"])
    assert groups["pending"]["reasonCode"] is None
    assert groups["pending"]["occurrencesCount"] == 2
    assert groups["pending"]["seconds"] == 7200
    assert groups["unrecorded"]["label"] == "Motivo não informado"
    assert r["summary"]["pendingCount"] == 2


def test_inactive_reason_still_in_history():
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T15:00:00+00:00",
             reason="OLD_CODE", label="Motivo legado"),
    ])
    g = by_key(r["byReason"])["OLD_CODE"]
    assert g["label"] == "Motivo legado" and g["seconds"] == 7200


# ---------- agregador: agrupamentos ----------

def test_pareto_sorted_desc_with_cumulative():
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T16:00:00+00:00",
             reason="SETUP"),                     # 3h
        fact("b", "CT1", "2026-02-09T16:30:00+00:00", "2026-02-09T17:00:00+00:00",
             reason="QUEBRA"),                    # 0,5h
        fact("c", "CT1", "2026-02-09T18:00:00+00:00", "2026-02-09T19:00:00+00:00",
             reason="FALTA_MAT"),                 # 1h
    ])
    keys = [g["key"] for g in r["byReason"]]
    assert keys == ["SETUP", "FALTA_MAT", "QUEBRA"]
    setup = r["byReason"][0]
    assert setup["occurrencesCount"] == 1
    assert setup["percentOfAttributed"] == pytest.approx(66.67, abs=0.01)
    assert setup["cumulativePercent"] == pytest.approx(66.67, abs=0.01)
    assert r["byReason"][2]["cumulativePercent"] == 100.0


def test_by_day_fills_zero_days_and_splits_midnight():
    r = run([
        fact("e", "CT1", "2026-02-10T02:00:00+00:00", "2026-02-10T04:00:00+00:00"),
    ])  # seg 23h -> ter 01h SP
    days = by_key(r["byDay"], "date")
    # a janela cobre seg e ter completos; qua (borda superior 00:00 SP)
    # entra com zero — dias sem parada aparecem com valor zero
    assert list(days) == ["2026-02-09", "2026-02-10", "2026-02-11"]
    assert days["2026-02-09"]["seconds"] == 3600
    assert days["2026-02-10"]["seconds"] == 3600
    assert days["2026-02-11"]["seconds"] == 0
    assert days["2026-02-09"]["occurrencesCount"] == 1
    assert days["2026-02-10"]["occurrencesCount"] == 1
    assert days["2026-02-11"]["occurrencesCount"] == 0


def test_weekday_hour_cells_use_sao_paulo_civil_time():
    r = run([
        fact("a", "CT1", "2026-02-09T13:00:00+00:00", "2026-02-09T15:30:00+00:00"),
    ])  # seg 10h-12h30 SP: células 10, 11 e 12 (meia hora)
    cells = by_key(r["byWeekdayHour"], "hour")
    assert cells[10]["weekday"] == 0 and cells[10]["seconds"] == 3600
    assert cells[11]["seconds"] == 3600
    assert cells[12]["seconds"] == 1800
    assert cells[10]["weekdayLabel"] == "seg"


def test_dst_boundary_uses_historical_offsets():
    # 04/11/2018: horário de verão começou em SP (UTC-2). Uma parada de
    # 00h30-01h30 UTC (22h30-23h30 SP do dia 03) não deve escorregar.
    w0 = dt("2018-11-03T03:00:00+00:00")  # sáb 00:00 SP (UTC-3)
    w1 = dt("2018-11-05T02:00:00+00:00")  # seg 00:00 SP (UTC-2 após DST)
    r = run([
        fact("a", "CT1", "2018-11-04T02:30:00+00:00", "2018-11-04T05:30:00+00:00"),
    ], window_from=w0, window_to=w1)
    # 02h30-05h30 UTC = sáb 23h30-24h (UTC-3) + dom 01h-03h30 (UTC-2;
    # a hora 00h de domingo não existe na transição)
    cells = {(c["weekday"], c["hour"]): c for c in r["byWeekdayHour"]}
    assert cells[(5, 23)]["seconds"] == 1800   # sáb 23h30-24h (UTC-3)
    assert cells[(6, 1)]["seconds"] == 3600    # dom 01h-02h (UTC-2)
    assert cells[(6, 2)]["seconds"] == 3600    # dom 02h-03h (UTC-2)
    assert cells[(6, 3)]["seconds"] == 1800    # dom 03h-03h30 (UTC-2)
    assert (6, 0) not in cells                 # hora inexistente no DST
    assert r["summary"]["totalStoppedSeconds"] == 10800


def test_empty_window_returns_safe_zeros():
    r = run([])
    s = r["summary"]
    assert s["totalStoppedSeconds"] == 0 and s["occurrencesCount"] == 0
    assert s["averageOccurrenceSeconds"] == 0
    assert s["pendingCount"] == 0 and s["openCount"] == 0
    assert r["byReason"] == [] and r["byWorkCenter"] == []
    assert r["byWeekdayHour"] == []
    assert len(r["byDay"]) == 3 and all(d["seconds"] == 0 for d in r["byDay"])


def test_capped_facts_flag_partial_quality():
    r = run([fact("a", "CT1", "2026-02-09T13:00:00+00:00",
                  "2026-02-09T14:00:00+00:00")], capped=True)
    assert r["quality"]["partial"] is True and r["quality"]["factsCapped"] is True


# ---------- service: contrato e validações ----------

class FakeAnalyticsRepository:
    def __init__(self, facts=None, capped=False):
        self.facts = facts or []
        self.capped = capped
        self.args = None

    def list_downtime_analytics_facts(self, **kwargs):
        self.args = kwargs
        return {"facts": self.facts, "capped": self.capped}


def make_service(repo):
    return MesIntegrationReadService(
        repository=repo,
        branch_access=BranchAccessService(),
        clock=lambda: NOW,
    )


def test_service_requires_from():
    with pytest.raises(ValueError, match="from"):
        make_service(FakeAnalyticsRepository()).get_downtime_analytics(
            branch="01", period_from=None,
        )


def test_service_rejects_inverted_and_oversized_windows():
    service = make_service(FakeAnalyticsRepository())
    with pytest.raises(ValueError):
        service.get_downtime_analytics(
            branch="01", period_from=NOW, period_to=NOW - timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="92"):
        service.get_downtime_analytics(
            branch="01",
            period_from=NOW - timedelta(days=93), period_to=NOW,
        )


def test_service_rejects_invalid_classification_and_source():
    service = make_service(FakeAnalyticsRepository())
    for kw in ({"classification": "closed"}, {"source": "bogus"}):
        with pytest.raises(ValueError):
            service.get_downtime_analytics(
                branch="01", period_from=NOW - timedelta(hours=2), **kw,
            )


def test_service_caps_effective_to_at_reference_at():
    repo = FakeAnalyticsRepository()
    data = make_service(repo).get_downtime_analytics(
        branch="01",
        period_from=NOW - timedelta(days=2),
        period_to=NOW + timedelta(days=30),  # futuro é cortado no referenceAt
    )
    assert data["to"] == NOW.isoformat()
    assert data["referenceAt"] == NOW.isoformat()
    assert repo.args["period_to"] == NOW


def test_service_forwards_filters_and_echoes_context():
    repo = FakeAnalyticsRepository()
    start = NOW - timedelta(days=7)
    data = make_service(repo).get_downtime_analytics(
        branch="01", work_center=" CT-35 ", reason_code=" Setup ",
        source="AUTOMATIC_DETECTION", classification="PENDING",
        period_from=start, period_to=None,
    )
    assert repo.args["branch"] == "01"
    assert repo.args["work_center"] == "CT-35"
    assert repo.args["reason_code"] == "setup"
    assert repo.args["source"] == "automatic_detection"
    assert repo.args["classification"] == "pending"
    assert repo.args["period_from"] == start
    assert repo.args["period_to"] == NOW  # sem to: fim efetivo = referenceAt
    assert data["branch"] == "01" and data["timezone"] == "America/Sao_Paulo"
    assert data["appliedFilters"] == {
        "workCenter": "CT-35", "reasonCode": "setup",
        "source": "automatic_detection", "classification": "pending",
    }
    assert set(data) >= {
        "summary", "byReason", "byWorkCenter", "byDay", "byWeekdayHour",
        "quality",
    }


def test_service_marks_partial_when_facts_capped():
    data = make_service(FakeAnalyticsRepository(capped=True)).get_downtime_analytics(
        branch="01", period_from=NOW - timedelta(days=2),
    )
    assert data["quality"]["partial"] is True
