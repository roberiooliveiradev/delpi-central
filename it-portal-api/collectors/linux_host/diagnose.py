"""Diagnóstico read-only do host Linux — seções parciais não derrubam o processo."""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .parsing import (
    filter_host_nics,
    memory_summary_from_meminfo,
    os_summary_from_release,
    parse_df_posix,
    parse_meminfo_kb,
    parse_os_release,
    parse_systemctl_show,
)

DEFAULT_SYSTEMD_ALLOWLIST = (
    "docker.service",
    "containerd.service",
    "ssh.service",
    "sshd.service",
    "cron.service",
    "crond.service",
    "nginx.service",
    "zabbix-agent.service",
    "zabbix-agent2.service",
)

COMMAND_TIMEOUT_SECONDS = 5.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_text(path: Path, *, max_bytes: int = 64_000) -> str | None:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return None


def _run(cmd: list[str], *, timeout: float = COMMAND_TIMEOUT_SECONDS) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout or "", completed.stderr or ""
    except (OSError, subprocess.TimeoutExpired):
        return 127, "", "unavailable"


def collect_identity() -> tuple[dict, str]:
    hostname = socket.gethostname()
    machine_id = _read_text(Path("/etc/machine-id"))
    if machine_id:
        machine_id = machine_id.strip()[:64] or None
    return {"hostname": hostname, "machine_id": machine_id}, "ok"


def collect_os() -> tuple[dict, str]:
    release_raw = _read_text(Path("/etc/os-release")) or ""
    values = parse_os_release(release_raw)
    kernel = platform.release()
    arch = platform.machine()
    summary = os_summary_from_release(values, kernel=kernel, arch=arch)
    status = "ok" if summary.get("name") else "partial"
    # DMI só se legível sem privilégio.
    product = _read_text(Path("/sys/class/dmi/id/product_name"))
    vendor = _read_text(Path("/sys/class/dmi/id/sys_vendor"))
    virt = {
        "type": None,
        "hardware_model": (product or "").strip() or None,
        "vendor": (vendor or "").strip() or None,
    }
    return {"os": summary, "virtualization": virt, "cpu_logical": os.cpu_count()}, status


def collect_memory() -> tuple[dict, str]:
    raw = _read_text(Path("/proc/meminfo"))
    if not raw:
        return {"memory": {}, "swap": {}}, "unavailable"
    mem = memory_summary_from_meminfo(parse_meminfo_kb(raw))
    return {
        "memory": {
            "total_bytes": mem["total_bytes"],
            "available_bytes": mem["available_bytes"],
        },
        "swap": {
            "total_bytes": mem["swap_total_bytes"],
            "free_bytes": mem["swap_free_bytes"],
        },
    }, "ok"


def collect_volumes() -> tuple[dict, str]:
    code, stdout, _ = _run(["df", "-PB1", "-x", "tmpfs", "-x", "devtmpfs", "-x", "overlay"])
    if code != 0 or not stdout.strip():
        code, stdout, _ = _run(["df", "-P"])
        if code != 0 or not stdout.strip():
            return {"volumes": []}, "unavailable"
        # df -P usa blocos de 1K
        volumes = parse_df_posix(stdout)
        for item in volumes:
            item["size_bytes"] *= 1024
            item["used_bytes"] *= 1024
            item["available_bytes"] *= 1024
        return {"volumes": volumes}, "partial" if volumes else "unavailable"
    return {"volumes": parse_df_posix(stdout)}, "ok"


def collect_nics() -> tuple[dict, str]:
    nics: list[dict] = []
    # Prefer sysfs listing + `ip -br addr` when available.
    code, stdout, _ = _run(["ip", "-br", "addr"])
    if code == 0 and stdout.strip():
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0].split("@", 1)[0]
            state = parts[1].lower() if len(parts) > 1 else None
            addresses = [item for item in parts[2:] if ":" in item or "." in item]
            nics.append({"name": name, "addresses": addresses, "state": state})
    else:
        net = Path("/sys/class/net")
        if not net.is_dir():
            return {"host_nics": []}, "unavailable"
        for entry in sorted(net.iterdir()):
            if not entry.is_dir():
                continue
            oper = _read_text(entry / "operstate")
            nics.append(
                {
                    "name": entry.name,
                    "addresses": [],
                    "state": (oper or "").strip() or None,
                }
            )
    filtered = filter_host_nics(nics)
    return {"host_nics": filtered}, "ok" if filtered else "partial"


def collect_systemd(allowlist: tuple[str, ...] = DEFAULT_SYSTEMD_ALLOWLIST) -> tuple[dict, str]:
    services: list[dict] = []
    any_ok = False
    for unit in allowlist:
        code, stdout, _ = _run(
            ["systemctl", "show", unit, "--property=ActiveState,SubState,UnitFileState"]
        )
        if code != 0 or not stdout.strip():
            continue
        parsed = parse_systemctl_show(stdout)
        if not parsed.get("active_state"):
            continue
        any_ok = True
        services.append({"name": unit, **parsed})
    return {"systemd_services": services}, ("ok" if any_ok else "unavailable")


def collect_docker() -> tuple[dict, str]:
    code, version_out, _ = _run(["docker", "version", "--format", "{{.Server.Version}}"])
    if code != 0:
        return {
            "docker_summary": {
                "available": False,
                "unavailable_reason": "docker_cli_unavailable_or_no_permission",
            }
        }, "unavailable"
    code_ps, ps_out, _ = _run(["docker", "ps", "-a", "--format", "{{.Names}}"])
    names = [line.strip() for line in ps_out.splitlines() if line.strip()] if code_ps == 0 else []
    code_info, info_out, _ = _run(
        ["docker", "info", "--format", "{{.Containers}} {{.ContainersRunning}} {{.Images}}"]
    )
    total = running = images = None
    if code_info == 0 and info_out.strip():
        parts = info_out.strip().split()
        if len(parts) >= 3:
            try:
                total, running, images = int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                pass
    return {
        "docker_summary": {
            "available": True,
            "server_version": version_out.strip() or None,
            "containers_total": total,
            "containers_running": running,
            "images": images,
            "container_names_sample": names[:20],
            "unavailable_reason": None,
        }
    }, "ok" if code_ps == 0 else "partial"


SectionCollector = Callable[[], tuple[dict, str]]


def collect_host_snapshot(
    *,
    systemd_allowlist: tuple[str, ...] = DEFAULT_SYSTEMD_ALLOWLIST,
) -> tuple[dict, dict[str, str], str]:
    """Retorna (summary, sections_status, overall_status)."""
    summary: dict = {}
    sections: dict[str, str] = {}

    identity, identity_status = collect_identity()
    summary["identity"] = identity
    sections["identity"] = identity_status

    os_data, os_status = collect_os()
    summary.update(os_data)
    sections["os"] = os_status

    mem_data, mem_status = collect_memory()
    summary.update(mem_data)
    sections["memory"] = mem_status

    vol_data, vol_status = collect_volumes()
    summary.update(vol_data)
    sections["volumes"] = vol_status

    nic_data, nic_status = collect_nics()
    summary.update(nic_data)
    sections["nics"] = nic_status

    svc_data, svc_status = collect_systemd(systemd_allowlist)
    summary.update(svc_data)
    sections["systemd"] = svc_status

    docker_data, docker_status = collect_docker()
    summary.update(docker_data)
    sections["docker"] = docker_status

    statuses = list(sections.values())
    if all(item == "ok" for item in statuses):
        overall = "complete"
    elif all(item in {"unavailable", "failed"} for item in statuses):
        overall = "failed"
    else:
        overall = "partial"
    return summary, sections, overall


def build_observation_payload(
    *,
    run_id: str | None = None,
    observed_at: datetime | None = None,
) -> dict:
    summary, sections, status = collect_host_snapshot()
    hostname = summary.get("identity", {}).get("hostname") or socket.gethostname()
    machine_id = summary.get("identity", {}).get("machine_id")
    return {
        "run_id": run_id or str(uuid.uuid4()),
        "source": "linux_host_collector",
        "schema_version": "1",
        "status": status,
        "observed_at": (observed_at or _now()).isoformat().replace("+00:00", "Z"),
        "host_identity": {"hostname": hostname, "machine_id": machine_id},
        "summary": summary,
        "sections_status": sections,
    }


def diagnose_json() -> str:
    return json.dumps(build_observation_payload(), ensure_ascii=False, indent=2, default=str)
