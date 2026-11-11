"""Domínio de observações: allowlist, divergências e status de apresentação."""

from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.application.observation_service import presentation_status
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.observations import build_observation_ingest, compute_divergences


def _realistic_collector_summary(**overrides):
    """Snapshot alinhado ao coletor Linux (`collectors/linux_host/diagnose.py`)."""
    summary = {
        "identity": {"hostname": "srv-api", "machine_id": "c2e084f1587642e69bae04b3ae9f9b6e"},
        "os": {
            "name": "Ubuntu",
            "version": "24.04",
            "pretty_name": "Ubuntu 24.04.4 LTS",
            "kernel": "6.8.0-84-generic",
            "architecture": "x86_64",
            "extra_unknown": "drop-me",
        },
        "virtualization": {
            "type": None,
            "hardware_model": "VMware Virtual Platform",
            "vendor": "VMware, Inc.",
            "bios_serial": "drop-me",
        },
        "cpu_logical": 16,
        "memory": {
            "total_bytes": 24_000_000_000,
            "available_bytes": 8_000_000_000,
            "buffers": 123,  # desconhecido → drop
        },
        "swap": {"total_bytes": 4_000_000_000, "free_bytes": 1_000_000},
        "volumes": [
            {
                "filesystem": "/dev/mapper/ubuntu--vg-ubuntu--lv",
                "mount_point": "/",
                "size_bytes": 197_000_000_000,
                "used_bytes": 163_000_000_000,
                "available_bytes": 34_000_000_000,
                "used_percent": 83.0,
                "inode_password": "must-not-survive-as-key-name-elsewhere",
            }
        ],
        "host_nics": [
            {"name": "ens160", "addresses": ["192.168.1.237/24"], "state": "up", "mac": "drop"},
            {"name": "docker0", "addresses": ["172.17.0.1/16"], "state": "up"},
            {"name": "br-abc123", "addresses": ["172.18.0.1/16"], "state": "up"},
            {"name": "veth9a2f", "addresses": [], "state": "up"},
        ],
        "systemd_services": [
            {
                "name": "docker.service",
                "active_state": "active",
                "sub_state": "running",
                "unit_file_state": "enabled",
                "FragmentPath": "/lib/systemd/system/docker.service",
            }
        ],
        "docker_summary": {
            "available": True,
            "server_version": "27.0",
            "containers_total": 114,
            "containers_running": 98,
            "images": 80,
            "container_names_sample": ["gateway", "postgres-plugins"],
            "unavailable_reason": None,
            "RegistryConfig": {"drop": True},
        },
        "unknown_top_level": {"should": "drop"},
    }
    summary.update(overrides)
    return summary


def _raw(**overrides):
    payload = {
        "run_id": "run-abcd-1234",
        "source": "linux_host_collector",
        "schema_version": "1",
        "status": "complete",
        "observed_at": "2026-11-11T10:00:00Z",
        "host_identity": {"hostname": "srv-api"},
        "summary": _realistic_collector_summary(),
        "sections_status": {
            "identity": "ok",
            "os": "ok",
            "memory": "ok",
            "volumes": "ok",
            "nics": "ok",
            "systemd": "ok",
            "docker": "ok",
            "zabbix": "ok",  # fora do contrato → drop
        },
    }
    payload.update(overrides)
    return payload


def test_build_observation_preserves_realistic_collector_snapshot_and_drops_unknown():
    ingest = build_observation_ingest(_raw())
    assert ingest.summary["cpu_logical"] == 16
    assert ingest.summary["os"]["pretty_name"] == "Ubuntu 24.04.4 LTS"
    assert "extra_unknown" not in ingest.summary["os"]
    assert "bios_serial" not in ingest.summary["virtualization"]
    assert "buffers" not in ingest.summary["memory"]
    assert "unknown_top_level" not in ingest.summary
    assert "mac" not in ingest.summary["host_nics"][0]
    assert [nic["name"] for nic in ingest.summary["host_nics"]] == ["ens160"]
    assert "FragmentPath" not in ingest.summary["systemd_services"][0]
    assert "RegistryConfig" not in ingest.summary["docker_summary"]
    assert "inode_password" not in ingest.summary["volumes"][0]
    assert set(ingest.sections_status) == {
        "identity",
        "os",
        "memory",
        "volumes",
        "nics",
        "systemd",
        "docker",
    }
    assert "zabbix" not in ingest.sections_status


def test_build_observation_rejects_short_run_id():
    with pytest.raises(ValidationError) as exc:
        build_observation_ingest(_raw(run_id="short"))
    assert "run_id" in exc.value.details["fields"]


@pytest.mark.parametrize(
    "poison",
    [
        {"env": {"PATH": "/bin", "SECRET": "x"}},
        {"os": {"name": "Ubuntu", "password": "hunter2"}},
        {"memory": {"total_bytes": 1, "token": "abc"}},
        {"docker_summary": {"available": True, "credentials": {"user": "a", "pass": "b"}}},
        {"host_nics": [{"name": "eth0", "addresses": ["10.0.0.1/24"], "authorization": "Bearer x"}]},
        {"volumes": [{"mount_point": "/", "private_key": "-----BEGIN PRIVATE KEY-----"}]},
        {"systemd_services": [{"name": "ssh.service", "secret": "nope"}]},
        {"virtualization": {"vendor": "VMware", "client_secret": "xyz"}},
    ],
)
def test_build_observation_rejects_nested_sensitive_keys(poison):
    summary = _realistic_collector_summary()
    summary.update(poison)
    with pytest.raises(ValidationError) as exc:
        build_observation_ingest(_raw(summary=summary))
    assert "summary" in exc.value.details["fields"]
    assert "sensíveis" in exc.value.details["fields"]["summary"].lower() or "proibidos" in exc.value.details[
        "fields"
    ]["summary"].lower()


def test_compute_divergences_for_os_and_ip():
    ingest = build_observation_ingest(_raw())
    server = {
        "hostname": "srv-api",
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



def _windows_raw(**overrides):
    """JSON equivalente ao Collect-ItPortalWindowsInventory.ps1 validado no SRV-DB01."""
    body = {
        "run_id": "windows-pilot-0001",
        "source": "windows_host_collector",
        "schema_version": "1",
        "status": "complete",
        "observed_at": "2026-11-11T16:49:09.732Z",
        "host_identity": {"hostname": "win-pilot-01", "machine_id": None},
        "summary": {
            "identity": {"hostname": "win-pilot-01", "machine_id": None},
            "os": {
                "name": "Microsoft Windows Server 2019 Standard",
                "version": "10.0.17763",
                "pretty_name": "Microsoft Windows Server 2019 Standard",
                "kernel": None,
                "architecture": "64-bit",
            },
            "virtualization": {"type": None, "hardware_model": "Virtual Machine", "vendor": "Microsoft"},
            "cpu_logical": 8,
            "cpu_usage_percent": 33.0,
            "uptime_seconds": 7_824_971,
            "memory": {"total_bytes": 47_243_603_968, "available_bytes": 5_511_974_912},
            "volumes": [
                {"mount_point": "I:", "filesystem": "NTFS", "size_bytes": 323_175_000_000,
                 "used_bytes": 314_775_000_000, "available_bytes": 8_400_000_000, "used_percent": 97.39}
            ],
            "host_nics": [{"name": "Ethernet", "addresses": ["192.0.2.10"], "state": "up"}],
            "windows_services": [
                {"name": "EventLog", "active_state": "running", "sub_state": "automatic", "unit_file_state": None}
            ],
            "docker_summary": {"available": True},  # Linux-only: descartar no Windows
        },
        "sections_status": {
            "identity": "ok", "os": "ok", "cpu": "ok", "memory": "ok",
            "volumes": "ok", "nics": "ok", "windows_services": "ok",
            "docker": "ok",  # Linux-only: descartar no Windows
        },
    }
    body.update(overrides)
    return body


def test_windows_snapshot_preserves_metrics_and_separates_linux_fields():
    ingest = build_observation_ingest(_windows_raw())
    assert ingest.source == "windows_host_collector"
    assert ingest.summary["cpu_logical"] == 8
    assert ingest.summary["cpu_usage_percent"] == 33.0
    assert ingest.summary["uptime_seconds"] == 7_824_971
    assert ingest.summary["memory"]["available_bytes"] == 5_511_974_912
    assert ingest.summary["volumes"][0]["used_percent"] == 97.39
    assert ingest.summary["windows_services"][0]["active_state"] == "running"
    assert "docker_summary" not in ingest.summary
    assert set(ingest.sections_status) == {
        "identity", "os", "cpu", "memory", "volumes", "nics", "windows_services"
    }


def test_linux_snapshot_does_not_accept_windows_only_fields():
    linux = _raw()
    linux["summary"]["cpu_usage_percent"] = 42.0
    linux["summary"]["windows_services"] = [{"name": "EventLog", "active_state": "running"}]
    linux["sections_status"]["windows_services"] = "ok"
    ingest = build_observation_ingest(linux)
    assert "cpu_usage_percent" not in ingest.summary
    assert "windows_services" not in ingest.summary
    assert "windows_services" not in ingest.sections_status


@pytest.mark.parametrize(
    "poison", [
        {"windows_services": [{"name": "MSSQLSERVER", "token": "secret"}]},
        {"volumes": [{"mount_point": "I:", "credentials": {"password": "bad"}}]},
        {"identity": {"hostname": "win-pilot-01", "client_secret": "bad"}},
    ],
)
def test_windows_rejects_nested_secrets(poison):
    body = _windows_raw()
    body["summary"].update(poison)
    with pytest.raises(ValidationError) as exc:
        build_observation_ingest(body)
    assert "summary" in exc.value.details["fields"]


@pytest.mark.parametrize("value", ["nan", "inf", "-4", "101"])
def test_windows_invalid_cpu_percent_does_not_enter_snapshot(value):
    ingest = build_observation_ingest(_windows_raw(summary={
        "cpu_usage_percent": value, "cpu_logical": 8
    }))
    assert ingest.summary["cpu_usage_percent"] is None
