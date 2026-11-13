"""Regras: 100% apenas com TODOS os serviços críticos verificados rodando."""
from datetime import datetime, timedelta, timezone

from it_portal_app.application.windows_service_health import (
    summarize_windows_services_health,
)

NOW = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)


def row(name="appserver", *, server_id="host-1", state="running",
        is_present=True, criticality="critical", age=4, observed=None):
    return {
        "server_id": server_id,
        "server_name": "SRV-DB01" if server_id == "host-1" else "SRV-PROTHEUS01",
        "hostname": "srv-db01" if server_id == "host-1" else "srv-protheus01",
        "service_key": name.casefold(),
        "service_name": name,
        "criticality": criticality,
        "state": state,
        "is_present": is_present,
        "collected_at": observed if observed is not None else NOW - timedelta(minutes=age),
    }


def test_two_servers_count_only_real_running_and_stopped():
    result = summarize_windows_services_health([
        row("Protheus", criticality="critical"),
        row("Minha Produção", state="stopped", criticality="critical"),
        row("APS", server_id="host-2", criticality="high"),
    ], now=NOW)
    assert (result["total"], result["running"], result["stopped"]) == (3, 2, 1)
    assert result["health_percent"] == 66
    assert len(result["servers"]) == 2
    assert result["issues_total"] == 1
    assert result["issues"][0]["reason"] == "Parado"


def test_missing_and_stale_samples_cannot_report_healthy():
    result = summarize_windows_services_health([
        row("A", age=16),
        row("B", is_present=False),
        row("C", state="paused"),
        row("D", observed=NOW + timedelta(minutes=6)),
        row("E"),
    ], now=NOW)
    assert result["unverified"] == 2
    assert result["attention"] == 2
    assert result["running"] == 1
    assert result["health_percent"] == 20
    assert result["issues_total"] == 4


def test_no_monitored_service_is_not_100_percent():
    result = summarize_windows_services_health([], now=NOW)
    assert result["total"] == 0
    assert result["health_percent"] is None
    assert result["servers"] == []


def test_critical_incidents_sort_first_without_hiding_stale_state():
    result = summarize_windows_services_health([
        row("High stop", state="stopped", criticality="high"),
        row("Critical stale", age=25, criticality="critical"),
        row("Critical stop", state="stopped", criticality="critical"),
    ], now=NOW)
    assert [item["service_name"] for item in result["issues"]] == [
        "Critical stop", "Critical stale", "High stop",
    ]
