"""Domínio de observações: sanitização, divergências e status de apresentação."""

from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.application.observation_service import presentation_status
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.observations import build_observation_ingest, compute_divergences


def _raw(**overrides):
    payload = {
        "run_id": "run-abcd-1234",
        "source": "linux_host_collector",
        "schema_version": "1",
        "status": "complete",
        "observed_at": "2026-11-11T10:00:00Z",
        "host_identity": {"hostname": "srv-api.delpi.local"},
        "summary": {
            "os": {"name": "Ubuntu", "version": "24.04", "kernel": "6.8.0", "architecture": "x86_64"},
            "cpu_logical": 8,
            "memory": {"total_bytes": 16_000_000_000, "available_bytes": 8_000_000_000},
            "host_nics": [
                {"name": "eth0", "addresses": ["192.168.1.237/24"], "state": "up"},
                {"name": "docker0", "addresses": ["172.17.0.1/16"], "state": "up"},
                {"name": "br-abc123", "addresses": ["172.18.0.1/16"], "state": "up"},
                {"name": "veth9a2f", "addresses": [], "state": "up"},
            ],
            "volumes": [{"mount_point": "/", "size_bytes": 100, "used_bytes": 40, "used_percent": 40}],
            "systemd_services": [{"name": "docker.service", "active_state": "active"}],
            "docker_summary": {
                "available": True,
                "server_version": "27.0",
                "containers_total": 3,
                "containers_running": 2,
                "images": 10,
                "container_names_sample": ["gateway", "postgres"],
            },
            "env": {"SECRET": "should-drop"},
            "cmdline": "should-drop",
        },
        "sections_status": {"os": "ok", "docker": "ok", "nics": "ok"},
    }
    payload.update(overrides)
    return payload


def test_build_observation_filters_docker_nics_and_secrets():
    ingest = build_observation_ingest(_raw())
    names = [nic["name"] for nic in ingest.summary["host_nics"]]
    assert names == ["eth0"]
    assert "env" not in ingest.summary
    assert "cmdline" not in ingest.summary
    assert ingest.summary["docker_summary"]["available"] is True


def test_build_observation_rejects_short_run_id():
    with pytest.raises(ValidationError) as exc:
        build_observation_ingest(_raw(run_id="short"))
    assert "run_id" in exc.value.details["fields"]


def test_compute_divergences_for_os_and_ip():
    ingest = build_observation_ingest(_raw())
    server = {
        "hostname": "srv-api.delpi.local",
        "operating_system": "Windows Server 2022",
        "ip_address": "10.0.0.1",
    }
    divergences = {item["field"]: item for item in compute_divergences(server, ingest)}
    assert "operating_system" in divergences
    assert "ip_address" in divergences
    assert "hostname" not in divergences


def test_presentation_status_stale_and_partial():
    now = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    fresh = {
        "status": "complete",
        "observed_at": now - timedelta(hours=1),
    }
    partial = {
        "status": "partial",
        "observed_at": now - timedelta(hours=1),
    }
    stale = {
        "status": "complete",
        "observed_at": now - timedelta(hours=40),
    }
    assert presentation_status(None, now=now) == "unavailable"
    assert presentation_status(fresh, now=now) == "available"
    assert presentation_status(partial, now=now) == "partial"
    assert presentation_status(stale, now=now) == "stale"
