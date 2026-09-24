"""Compact projections for TÉO GPT Actions / MCP READ responses (≤ ~100 KiB)."""

from __future__ import annotations

import json
from typing import Any, Mapping

GPT_ACTIONS_RESPONSE_MAX_BYTES = 100 * 1024

_SEARCH_ITEM_CAP = 40
_EXCERPT_CHARS = 800


def utf8_size(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))


def ascii_utf8_size(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=True, default=str).encode("utf-8"))


def actions_response_sizes(payload: Any) -> dict[str, int]:
    return {
        "unicode": utf8_size(payload),
        "ascii": ascii_utf8_size(payload),
        "envelopeAscii": ascii_utf8_size({"success": True, "data": payload}),
    }


def _truncate_str(value: Any, *, max_chars: int = _EXCERPT_CHARS) -> Any:
    if not isinstance(value, str):
        return value
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1] + "…"


def project_search_records(payload: Mapping[str, Any]) -> dict[str, Any]:
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    total = payload.get("total", len(items))
    truncated = len(items) > _SEARCH_ITEM_CAP
    slim: list[Any] = []
    for item in items[:_SEARCH_ITEM_CAP]:
        if not isinstance(item, dict):
            slim.append(item)
            continue
        row = dict(item)
        for heavy in (
            "conteudo",
            "content_md",
            "content",
            "body",
            "markdown",
            "transcript",
            "nodes",
            "edges",
            "raw",
        ):
            if heavy in row and isinstance(row[heavy], (str, dict, list)):
                if isinstance(row[heavy], str):
                    row[heavy] = _truncate_str(row[heavy], max_chars=240)
                else:
                    row[f"{heavy}_omitted"] = True
                    row.pop(heavy, None)
        slim.append(row)
    out = {"total": total, "items": slim}
    if truncated:
        out["truncated"] = True
        out["returned"] = len(slim)
    return out


def project_get_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"value": payload}
    out = dict(payload)
    for heavy in ("conteudo", "content_md", "content", "body", "markdown", "transcript"):
        if heavy in out and isinstance(out[heavy], str):
            raw = out[heavy]
            if len(raw) > _EXCERPT_CHARS:
                out[f"{heavy}_excerpt"] = raw[:_EXCERPT_CHARS]
                out[f"{heavy}_truncated"] = True
                out[f"{heavy}_chars"] = len(raw)
                out.pop(heavy, None)
    # Diagram / WBS graphs — keep counts, drop full graph if huge
    for graph_key in ("nodes", "edges", "tree", "items"):
        val = out.get(graph_key)
        if isinstance(val, list) and len(json.dumps(val, default=str)) > 20_000:
            out[f"{graph_key}_count"] = len(val)
            out[f"{graph_key}_omitted"] = True
            out.pop(graph_key, None)
    return out


def project_catalog(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Keep indexes; drop bulky duplicated prose from guides when over budget."""
    out = dict(payload)
    guide = out.get("registration_guide")
    if isinstance(guide, dict):
        # Keep structure but drop long example blobs if present
        slim_guide = dict(guide)
        for drop in ("examples", "long_examples", "sample_payloads"):
            slim_guide.pop(drop, None)
        # Cap entity_schemas descriptions indirectly by keeping keys only when huge
        schemas = slim_guide.get("entity_schemas")
        if isinstance(schemas, dict) and ascii_utf8_size(schemas) > 40_000:
            slim_guide["entity_schemas"] = {
                k: (
                    {"fields": sorted(v.keys())[:40]}
                    if isinstance(v, dict)
                    else v
                )
                for k, v in schemas.items()
            }
            slim_guide["entity_schemas_compacted"] = True
        out["registration_guide"] = slim_guide

    diagram = out.get("diagram_catalog")
    if isinstance(diagram, dict) and ascii_utf8_size(diagram) > 25_000:
        out["diagram_catalog"] = {
            "node_types": list(diagram.get("node_types") or diagram.get("nodes") or [])[
                :80
            ],
            "edge_types": list(diagram.get("edge_types") or diagram.get("edges") or [])[
                :40
            ],
            "compacted": True,
        }

    surface = out.get("capability_surface")
    if isinstance(surface, dict):
        directives = surface.get("agent_directives")
        if isinstance(directives, dict):
            # Already compacted by intelligence service; ensure size bound
            if ascii_utf8_size(directives) > 35_000:
                surface = dict(surface)
                surface["agent_directives"] = {
                    "version": directives.get("version"),
                    "authority": directives.get("authority"),
                    "write_flow": directives.get("write_flow"),
                    "execution_posture": directives.get("execution_posture"),
                    "actions_runtime": directives.get("actions_runtime"),
                    "modes": directives.get("modes"),
                    "flows_index": sorted((directives.get("flows") or {}).keys())
                    if isinstance(directives.get("flows"), dict)
                    else [],
                    "compacted": True,
                }
                out["capability_surface"] = surface

    sizes = actions_response_sizes(out)
    if sizes["envelopeAscii"] > GPT_ACTIONS_RESPONSE_MAX_BYTES:
        # Last resort: drop familias/agrupadores lists and keep indexes
        out.pop("familias_processo", None)
        out.pop("agrupadores_ferramenta", None)
        out["catalog_budget_trimmed"] = True
    return out


def ensure_budget(payload: Any) -> Any:
    """Return payload if under budget; otherwise raise ValueError for callers to project."""
    sizes = actions_response_sizes(payload)
    if sizes["envelopeAscii"] <= GPT_ACTIONS_RESPONSE_MAX_BYTES:
        return payload
    raise ValueError(
        f"Actions response over budget: envelopeAscii={sizes['envelopeAscii']}"
    )
