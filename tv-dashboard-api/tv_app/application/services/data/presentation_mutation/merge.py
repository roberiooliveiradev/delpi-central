"""Deep-merge helpers for PresentationMutation nested dict patches.

Partial patches must not wipe sibling nested keys (e.g. style.color when only
fontSize/fontWeight are sent). Explicit ``None`` clears a key.
"""

from __future__ import annotations

from typing import Any

# Nested object keys on a slide block that merge deeply on upsert.
BLOCK_DEEP_MERGE_KEYS = frozenset(
    {
        "style",
        "frame",
        "dataBinding",
        "dataTransform",
        "fieldLabels",
        "kpiParts",
        "chartParts",
        "tableParts",
        "kpiOptions",
        "chartOptions",
        "tableOptions",
        "kpiProjection",
        "chartProjection",
        "tableProjection",
        "textProjection",
        "input",
        "imageCrop",
        "animations",
    }
)

# Top-level nativeConfig keys that are dicts and should deep-merge on patch.
NATIVE_DEEP_MERGE_KEYS = frozenset(
    {
        "background",
        "dataFilters",
        "groupTransforms",
        "speakerNotes",  # if ever dict-shaped; strings replace wholesale below
    }
)


def deep_merge_dicts(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Merge ``patch`` onto ``base``. Nested dicts merge recursively; ``None`` deletes."""
    out = dict(base)
    for key, value in patch.items():
        if value is None:
            out.pop(key, None)
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge_dicts(out[key], value)
        else:
            out[key] = value
    return out


def merge_block_patch(existing: dict[str, Any], cleaned: dict[str, Any]) -> dict[str, Any]:
    """Top-level shallow merge with deep merge for known nested block keys."""
    merged = dict(existing)
    for key, value in cleaned.items():
        if value is None:
            merged.pop(key, None)
            continue
        if key in BLOCK_DEEP_MERGE_KEYS and isinstance(value, dict):
            prior = merged.get(key) if isinstance(merged.get(key), dict) else {}
            merged[key] = deep_merge_dicts(prior, value)
        else:
            merged[key] = value
    return merged


def merge_data_binding(
    existing_binding: dict[str, Any] | None,
    patch_binding: dict[str, Any],
) -> dict[str, Any]:
    """Merge dataBinding so partial upserts keep refreshSec / selected fields / etc."""
    base = existing_binding if isinstance(existing_binding, dict) else {}
    return deep_merge_dicts(base, patch_binding)


def merge_native_config_key(cfg: dict[str, Any], key: str, value: Any) -> None:
    """Apply one patch_native_config key onto cfg with deep merge for dict values."""
    if value is None:
        cfg.pop(key, None)
        return
    if (
        key in NATIVE_DEEP_MERGE_KEYS
        and isinstance(value, dict)
        and isinstance(cfg.get(key), dict)
    ):
        cfg[key] = deep_merge_dicts(cfg[key], value)
    else:
        cfg[key] = value
