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
    section = _limits_section().get("pollIntervalSeconds")
    return section if isinstance(section, dict) else {}


def poll_interval_min(*, default: float = 0.5) -> float:
    raw = _poll_interval_limits().get("min")
    if isinstance(raw, (int, float)):
        return float(raw)
    return default


def poll_interval_max(*, default: float = 300.0) -> float:
    raw = _poll_interval_limits().get("max")
    if isinstance(raw, (int, float)):
        return float(raw)
    return default


def name_max_length(*, default: int = 120) -> int:
    raw = _limits_section().get("nameMaxLength")
    if isinstance(raw, int) and raw > 0:
        return raw
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
    "ipv4_pattern",
    "load_device_validation_content",
    "matches_ipv4",
    "name_max_length",
    "poll_interval_max",
    "poll_interval_min",
    "valid_branches",
]
