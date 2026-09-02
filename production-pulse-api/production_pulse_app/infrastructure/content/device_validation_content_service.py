from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "device_validation_content.json"


@lru_cache(maxsize=1)
def load_device_validation_content() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def _limits_section() -> dict[str, Any]:
    section = load_device_validation_content().get("limits")
    return section if isinstance(section, dict) else {}


def _poll_interval_limits() -> dict[str, Any]:
    section = _limits_section().get("pollIntervalMs")
    return section if isinstance(section, dict) else {}


def poll_interval_min(*, default: int = 1) -> int:
    raw = _poll_interval_limits().get("min")
    if isinstance(raw, (int, float)):
        return int(raw)
    return default


def poll_interval_max(*, default: int = 300_000) -> int:
    raw = _poll_interval_limits().get("max")
    if isinstance(raw, (int, float)):
        return int(raw)
    return default


def poll_interval_default(*, default: int = 30_000) -> int:
    raw = _poll_interval_limits().get("default")
    if isinstance(raw, (int, float)):
        return int(raw)
    return default


def live_ui_refresh_min_ms(*, default: int = 50) -> int:
    section = _limits_section().get("liveUiRefreshMs")
    if not isinstance(section, dict):
        return default
    raw = section.get("min")
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    return default


def scheduler_tick_ms(*, default: int = 100) -> int:
    section = _limits_section().get("schedulerTickMs")
    if not isinstance(section, dict):
        return default
    raw = section.get("default")
    if isinstance(raw, (int, float)):
        return max(10, int(raw))
    return default


def _online_grace_section() -> dict[str, Any]:
    section = _limits_section().get("onlineGraceMs")
    return section if isinstance(section, dict) else {}


def online_grace_multiplier(*, default: int = 2) -> int:
    raw = _online_grace_section().get("multiplier")
    if isinstance(raw, (int, float)) and int(raw) >= 1:
        return int(raw)
    return default


def online_grace_min_ms(*, default: int = 2_000) -> int:
    raw = _online_grace_section().get("min")
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    return default


def online_grace_max_ms(*, default: int = 600_000) -> int:
    raw = _online_grace_section().get("max")
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    return default


def name_max_length(*, default: int = 120) -> int:
    raw = _limits_section().get("nameMaxLength")
    if isinstance(raw, int) and raw > 0:
        return raw
    return default


def _counter_set_limits() -> dict[str, Any]:
    section = _limits_section().get("counterSet")
    return section if isinstance(section, dict) else {}


def counter_set_min(*, default: int = 0) -> int:
    raw = _counter_set_limits().get("min")
    if isinstance(raw, (int, float)):
        return int(raw)
    return default


def counter_set_max(*, default: int = 2_147_483_647) -> int:
    raw = _counter_set_limits().get("max")
    if isinstance(raw, (int, float)):
        return int(raw)
    return default


def valid_branches() -> frozenset[str]:
    raw = load_device_validation_content().get("validBranches")
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(str(branch).strip() for branch in raw if str(branch).strip())


@lru_cache(maxsize=1)
def ipv4_pattern() -> re.Pattern[str]:
    patterns = load_device_validation_content().get("patterns")
    raw = patterns.get("ipv4") if isinstance(patterns, dict) else None
    if isinstance(raw, str) and raw.strip():
        return re.compile(raw.strip())
    return re.compile(
        r"^(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)$"
    )


def matches_ipv4(value: str) -> bool:
    return bool(ipv4_pattern().fullmatch((value or "").strip()))


__all__ = [
    "counter_set_max",
    "counter_set_min",
    "ipv4_pattern",
    "live_ui_refresh_min_ms",
    "load_device_validation_content",
    "matches_ipv4",
    "name_max_length",
    "online_grace_max_ms",
    "online_grace_min_ms",
    "online_grace_multiplier",
    "poll_interval_default",
    "poll_interval_max",
    "poll_interval_min",
    "scheduler_tick_ms",
    "valid_branches",
]
