"""Normalize and protect explicit table_view visual projection."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

# Part kinds supported by plugin-ui ConfigurablePresentationTable / TablePartRef.
# rowEven/rowOdd drive banded-row fills (CSS vars); body/footer remain unsupported.
_ALLOWED_TABLE_PART_KINDS = frozenset(
    {"frame", "title", "header", "headerCell", "row", "cell", "rowEven", "rowOdd"}
)

# Synonyms that are NOT implemented — reject, do not ignore.
_UNSUPPORTED_TABLE_PART_KINDS = frozenset({"body", "footer"})


def column_field_key(column: Mapping[str, Any] | None) -> str:
    if not isinstance(column, Mapping):
        return ""
    return str(column.get("key") or column.get("field") or "").strip()


def has_explicit_table_columns(block: Mapping[str, Any] | None) -> bool:
    if not isinstance(block, Mapping):
        return False
    proj = block.get("tableProjection")
    if not isinstance(proj, Mapping):
        return False
    columns = proj.get("columns")
    if not isinstance(columns, list) or not columns:
        return False
    return any(column_field_key(col) for col in columns if isinstance(col, Mapping))


def normalize_table_projection_columns(
    columns: Sequence[Any] | None,
) -> list[dict[str, Any]]:
    """Canonicalize columns: always set ``key`` (MFE/runtime), keep label/format."""
    out: list[dict[str, Any]] = []
    if not isinstance(columns, list):
        return out
    for raw in columns:
        if not isinstance(raw, dict):
            continue
        key = column_field_key(raw)
        if not key:
            continue
        col = dict(raw)
        col["key"] = key
        # Keep ``field`` as alias for older GPT payloads; key is authoritative.
        if not str(col.get("field") or "").strip():
            col["field"] = key
        out.append(col)
    return out


def normalize_block_table_projection(block: dict[str, Any]) -> dict[str, Any]:
    """In-place safe normalize of tableProjection on a block dict; returns block."""
    proj = block.get("tableProjection")
    if not isinstance(proj, dict):
        return block
    columns = proj.get("columns")
    if not isinstance(columns, list):
        return block
    normalized = normalize_table_projection_columns(columns)
    next_proj = dict(proj)
    next_proj["columns"] = normalized
    block["tableProjection"] = next_proj
    return block


def validate_table_parts(table_parts: Any) -> list[str]:
    """Return error tokens for unsupported tableParts keys (empty = ok)."""
    if table_parts is None:
        return []
    if not isinstance(table_parts, dict):
        return ["tableParts"]
    errors: list[str] = []
    for raw_key in table_parts.keys():
        key = str(raw_key or "").strip()
        if not key:
            continue
        kind = key.split(":", 1)[0].strip()
        if kind in _UNSUPPORTED_TABLE_PART_KINDS:
            errors.append(f"tableParts.{kind}")
            continue
        if kind not in _ALLOWED_TABLE_PART_KINDS:
            errors.append(f"tableParts.{kind}")
    return errors


def explicit_column_keys(block: Mapping[str, Any] | None) -> list[str]:
    if not has_explicit_table_columns(block):
        return []
    proj = block.get("tableProjection") if isinstance(block, Mapping) else None
    columns = proj.get("columns") if isinstance(proj, Mapping) else None
    if not isinstance(columns, list):
        return []
    return [
        column_field_key(col)
        for col in columns
        if isinstance(col, Mapping) and column_field_key(col)
    ]


def compare_explicit_block_intent(
    *,
    intent_block: Mapping[str, Any],
    actual_block: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Semantic diff for caller-authoritative fields (frame + tableProjection)."""
    diffs: list[dict[str, Any]] = []
    block_id = str(intent_block.get("id") or "").strip() or "?"
    if not isinstance(actual_block, Mapping):
        diffs.append(
            {
                "path": f"blocks.{block_id}",
                "expected": "present",
                "actual": None,
            }
        )
        return diffs

    intent_type = str(intent_block.get("type") or "").strip()
    actual_type = str(actual_block.get("type") or "").strip()
    if intent_type and intent_type != actual_type:
        diffs.append(
            {
                "path": f"blocks.{block_id}.type",
                "expected": intent_type,
                "actual": actual_type,
            }
        )

    intent_frame = intent_block.get("frame")
    if isinstance(intent_frame, dict) and intent_frame:
        actual_frame = (
            actual_block.get("frame")
            if isinstance(actual_block.get("frame"), dict)
            else {}
        )
        for axis in ("x", "y", "w", "h"):
            if axis not in intent_frame:
                continue
            try:
                want = float(intent_frame[axis])
                got = float(actual_frame.get(axis)) if axis in actual_frame else None
            except (TypeError, ValueError):
                want = intent_frame.get(axis)
                got = actual_frame.get(axis)
            if got is None or abs(float(want) - float(got)) > 0.051:
                diffs.append(
                    {
                        "path": f"blocks.{block_id}.frame.{axis}",
                        "expected": want,
                        "actual": got,
                    }
                )

    if has_explicit_table_columns(intent_block):
        want_keys = explicit_column_keys(intent_block)
        got_keys = explicit_column_keys(actual_block)
        if want_keys != got_keys:
            diffs.append(
                {
                    "path": f"blocks.{block_id}.tableProjection.columns",
                    "expected": want_keys,
                    "actual": got_keys,
                }
            )
        else:
            # Labels / valueFormat must survive when provided.
            intent_cols = normalize_table_projection_columns(
                (intent_block.get("tableProjection") or {}).get("columns")  # type: ignore[union-attr]
            )
            actual_cols = normalize_table_projection_columns(
                (actual_block.get("tableProjection") or {}).get("columns")  # type: ignore[union-attr]
                if isinstance(actual_block.get("tableProjection"), dict)
                else []
            )
            by_key = {column_field_key(c): c for c in actual_cols}
            for col in intent_cols:
                key = column_field_key(col)
                got = by_key.get(key) or {}
                want_label = str(col.get("label") or "").strip()
                if want_label and str(got.get("label") or "").strip() != want_label:
                    diffs.append(
                        {
                            "path": f"blocks.{block_id}.tableProjection.columns.{key}.label",
                            "expected": want_label,
                            "actual": got.get("label"),
                        }
                    )
                want_fmt = str(col.get("valueFormat") or "").strip()
                if want_fmt and str(got.get("valueFormat") or "").strip() != want_fmt:
                    diffs.append(
                        {
                            "path": (
                                f"blocks.{block_id}.tableProjection.columns.{key}.valueFormat"
                            ),
                            "expected": want_fmt,
                            "actual": got.get("valueFormat"),
                        }
                    )

    intent_ds = str(intent_block.get("dataSourceId") or "").strip()
    if intent_ds:
        got_ds = str(actual_block.get("dataSourceId") or "").strip()
        if intent_ds != got_ds:
            diffs.append(
                {
                    "path": f"blocks.{block_id}.dataSourceId",
                    "expected": intent_ds,
                    "actual": got_ds or None,
                }
            )

    return diffs


def collect_upsert_block_intents(ops: list[Any] | None) -> list[dict[str, Any]]:
    """Blocks from upsert_block ops that carry authoritative visual fields."""
    intents: list[dict[str, Any]] = []
    for raw in ops or []:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("op") or "").strip() != "upsert_block":
            continue
        block = raw.get("block")
        if not isinstance(block, dict):
            continue
        has_frame = isinstance(block.get("frame"), dict) and bool(block.get("frame"))
        has_proj = has_explicit_table_columns(block)
        has_ds = bool(str(block.get("dataSourceId") or "").strip())
        if not (has_frame or has_proj or has_ds):
            continue
        intents.append(dict(block))
    return intents
