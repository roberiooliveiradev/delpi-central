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


def tv_dashboard_setting_int(key: str, default: int) -> int:
    block_cfg = _load_settings().get("comunicadoDataBlocks") or {}
    if key == "comunicadoDataBlocksMaxPerSlide":
        try:
            return max(1, int(block_cfg.get("maxPerSlide") or default))
        except (TypeError, ValueError):
            return default
    try:
        return int(_load_settings().get(key, default))
    except (TypeError, ValueError):
        return default


def presentation_setting_int(key: str, default: int) -> int:
    presentation = _load_content().get("presentation") or {}
    try:
        return int(presentation.get(key, default))
    except (TypeError, ValueError):
        return default


def trend_direction_label(direction: str | None) -> str:
    presentation = _load_content().get("presentation") or {}
    labels = presentation.get("trendDirectionLabels") or {}
    if not isinstance(labels, dict):
        return "—"
    normalized = str(direction or "stable").strip().lower()
    return str(labels.get(normalized) or labels.get("stable") or "—")


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


def ui_content_bundle() -> dict[str, Any]:
    return dict(_load_content())


def media_setting_int(key: str, default: int) -> int:
    media = _load_settings().get("mediaUpload") or {}
    try:
        return int(media.get(key, default))
    except (TypeError, ValueError):
        return default


def media_setting_mime_ext(media_kind: str) -> dict[str, str]:
    media = _load_settings().get("mediaUpload") or {}
    if media_kind == "video":
        raw = media.get("videoMimeExtensions") or {}
    else:
        raw = media.get("imageMimeExtensions") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).lower(): str(v) for k, v in raw.items()}
