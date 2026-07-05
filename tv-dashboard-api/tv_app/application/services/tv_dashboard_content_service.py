from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_dashboard_content.json"
SETTINGS_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_dashboard_settings.json"


@lru_cache(maxsize=1)
def _load_content() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_settings() -> dict[str, Any]:
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def message(key: str, default: str = "") -> str:
    messages = _load_content().get("messages") or {}
    return str(messages.get(key) or default or key)


def presentation_setting_int(key: str, default: int) -> int:
    presentation = _load_content().get("presentation") or {}
    try:
        return int(presentation.get(key, default))
    except (TypeError, ValueError):
        return default


def heartbeat_interval_sec() -> int:
    heartbeat = _load_settings().get("presentationHeartbeat") or {}
    try:
        return int(heartbeat.get("intervalSec") or 60)
    except (TypeError, ValueError):
        return 60


def allowed_branches() -> list[str]:
    policy = _load_settings().get("branchPolicy") or {}
    raw = policy.get("allowedBranches") or []
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def branch_rejection_message() -> str:
    policy = _load_settings().get("branchPolicy") or {}
    return str(policy.get("rejectionMessage") or message("branchNotAllowed"))
