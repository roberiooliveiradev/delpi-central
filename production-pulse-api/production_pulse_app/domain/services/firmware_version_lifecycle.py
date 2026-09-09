from __future__ import annotations

from typing import Any


def firmware_lifecycle_state(row: dict[str, Any]) -> str:
    if row.get("archived_at") is not None:
        return "archived"
    if row.get("published_at") is not None:
        return "published"
    return "draft"


def has_source(row: dict[str, Any]) -> bool:
    return bool((row.get("source_text") or "").strip())


def has_artifact(row: dict[str, Any]) -> bool:
    return bool(row.get("artifact_path") and row.get("artifact_sha256"))


def can_edit_source(row: dict[str, Any]) -> bool:
    return firmware_lifecycle_state(row) == "draft"


def can_attach_artifact(row: dict[str, Any]) -> bool:
    return firmware_lifecycle_state(row) == "draft"


def can_publish(row: dict[str, Any]) -> bool:
    return firmware_lifecycle_state(row) == "draft" and has_artifact(row)


def can_edit_metadata(row: dict[str, Any]) -> bool:
    return firmware_lifecycle_state(row) in {"draft", "published"}


MAX_SOURCE_TEXT_BYTES = 256 * 1024


def validate_source_text(source_text: str | None) -> str | None:
    if source_text is None:
        return None
    normalized = source_text.replace("\r\n", "\n")
    if not normalized.strip():
        return None
    size = len(normalized.encode("utf-8"))
    if size > MAX_SOURCE_TEXT_BYTES:
        raise ValueError("firmwareSourceTooLarge")
    return normalized
