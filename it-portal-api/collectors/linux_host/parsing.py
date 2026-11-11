"""Parsers puros do coletor Linux — testáveis sem root nem Docker."""

from __future__ import annotations

import re
from typing import Iterable

DOCKER_NIC_PREFIXES = ("docker", "br-", "veth", "cni", "flannel", "cali", "tunl", "virbr")

_OS_RELEASE_RE = re.compile(r'^(?P<key>[A-Z0-9_]+)=(?P<value>.*)$')
_MEMINFO_RE = re.compile(r"^(?P<key>\w+):\s+(?P<value>\d+)\s+kB")
_DF_LINE_RE = re.compile(
    r"^(?P<fs>\S+)\s+(?P<blocks>\d+)\s+(?P<used>\d+)\s+(?P<avail>\d+)\s+"
    r"(?P<pct>\d+)%\s+(?P<mount>\S+)$"
)


def parse_os_release(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = _OS_RELEASE_RE.match(line.strip())
        if not match:
            continue
        raw = match.group("value").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            raw = raw[1:-1]
        values[match.group("key")] = raw
    return values


def os_summary_from_release(values: dict[str, str], *, kernel: str | None, arch: str | None) -> dict:
    name = values.get("NAME") or values.get("ID") or None
    version = values.get("VERSION_ID") or values.get("VERSION") or None
    return {
        "name": name,
        "version": version,
        "pretty_name": values.get("PRETTY_NAME") or None,
        "kernel": kernel,
        "architecture": arch,
    }


def parse_meminfo_kb(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        match = _MEMINFO_RE.match(line)
        if match:
            out[match.group("key")] = int(match.group("value"))
    return out


def memory_summary_from_meminfo(values: dict[str, int]) -> dict:
    total_kb = values.get("MemTotal")
    available_kb = values.get("MemAvailable")
    swap_total_kb = values.get("SwapTotal")
    swap_free_kb = values.get("SwapFree")
    return {
        "total_bytes": None if total_kb is None else total_kb * 1024,
        "available_bytes": None if available_kb is None else available_kb * 1024,
        "swap_total_bytes": None if swap_total_kb is None else swap_total_kb * 1024,
        "swap_free_bytes": None if swap_free_kb is None else swap_free_kb * 1024,
    }


def parse_df_posix(text: str) -> list[dict]:
    volumes: list[dict] = []
    for line in text.splitlines():
        if line.startswith("Filesystem") or not line.strip():
            continue
        match = _DF_LINE_RE.match(line.strip())
        if not match:
            continue
        blocks = int(match.group("blocks"))
        used = int(match.group("used"))
        avail = int(match.group("avail"))
        # df -PB1 → already bytes; df -P → 1024-blocks. Caller chooses flag.
        volumes.append(
            {
                "filesystem": match.group("fs"),
                "mount_point": match.group("mount"),
                "size_bytes": blocks,
                "used_bytes": used,
                "available_bytes": avail,
                "used_percent": float(match.group("pct")),
            }
        )
    return volumes


def is_host_nic(name: str) -> bool:
    lowered = (name or "").strip().lower()
    if not lowered:
        return False
    return not lowered.startswith(DOCKER_NIC_PREFIXES)


def filter_host_nics(nics: Iterable[dict]) -> list[dict]:
    out: list[dict] = []
    for nic in nics:
        name = str(nic.get("name") or "")
        if not is_host_nic(name):
            continue
        out.append(
            {
                "name": name,
                "addresses": list(nic.get("addresses") or [])[:8],
                "state": nic.get("state"),
            }
        )
    return out


def parse_systemctl_show(text: str) -> dict[str, str | None]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return {
        "active_state": values.get("ActiveState"),
        "sub_state": values.get("SubState"),
        "unit_file_state": values.get("UnitFileState"),
    }
