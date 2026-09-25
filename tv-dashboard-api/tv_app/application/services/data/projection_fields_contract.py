"""Contrato único de campos projetáveis (result + contexto de filtro efetivo).

Fonte de verdade para preview metadata, editor dropdown e validação de mutation.
Sem regras por operationId.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

ORIGIN_RESULT = "result"
ORIGIN_DISCOVERED = "discovered"
ORIGIN_EFFECTIVE_FILTER = "effective_filter"

CONTEXT_START = "filter.start_date"
CONTEXT_END = "filter.end_date"
CONTEXT_RANGE_LABEL = "filter.date_range_label"

_DATE_PARAM_PAIRS: tuple[tuple[str, str], ...] = (
    ("start_date", "end_date"),
    ("date_start", "date_end"),
    ("date_from", "date_to"),
)

_STATIC_CONTEXT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "name": CONTEXT_START,
        "type": "date",
        "semanticType": "date",
        "nullable": True,
        "projectable": True,
        "origin": ORIGIN_EFFECTIVE_FILTER,
        "label": "Início do filtro",
    },
    {
        "name": CONTEXT_END,
        "type": "date",
        "semanticType": "date",
        "nullable": True,
        "projectable": True,
        "origin": ORIGIN_EFFECTIVE_FILTER,
        "label": "Fim do filtro",
    },
    {
        "name": CONTEXT_RANGE_LABEL,
        "type": "string",
        "semanticType": "text",
        "nullable": True,
        "projectable": True,
        "origin": ORIGIN_EFFECTIVE_FILTER,
        "label": "Período do filtro",
    },
)


def supported_context_field_names() -> frozenset[str]:
    return frozenset(spec["name"] for spec in _STATIC_CONTEXT_SPECS)


def _has_value(params: dict[str, Any], key: str) -> bool:
    value = params.get(key)
    return value is not None and str(value).strip() != ""


def _iso_date_token(raw: Any) -> str | None:
    text = str(raw or "").strip()
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


def _format_date_pt_br(iso: str) -> str:
    try:
        parsed = date.fromisoformat(iso[:10])
    except ValueError:
        return iso
    return parsed.strftime("%d/%m/%Y")


def _effective_date_pair(params: dict[str, Any]) -> tuple[str | None, str | None]:
    for start_key, end_key in _DATE_PARAM_PAIRS:
        if _has_value(params, start_key) or _has_value(params, end_key):
            start = _iso_date_token(params.get(start_key)) if _has_value(params, start_key) else None
            end = _iso_date_token(params.get(end_key)) if _has_value(params, end_key) else None
            return start, end
    return None, None


def _field_descriptor(
    *,
    name: str,
    type_: str = "string",
    nullable: bool = True,
    projectable: bool = True,
    semantic_type: str | None = None,
    origin: str = ORIGIN_RESULT,
    label: str | None = None,
) -> dict[str, Any]:
    key = str(name or "").strip()
    out: dict[str, Any] = {
        "name": key,
        "type": str(type_ or "string").strip() or "string",
        "nullable": bool(nullable),
        "projectable": bool(projectable),
        "origin": origin,
    }
    if semantic_type:
        out["semanticType"] = str(semantic_type).strip()
    if label and str(label).strip():
        out["label"] = str(label).strip()
    return out


def _semantic_from_type_hint(raw: Any) -> str | None:
    token = str(raw or "").strip().lower()
    if not token:
        return None
    aliases = {
        "currency": "currency",
        "money": "currency",
        "percent": "percent",
        "percentage": "percent",
        "date": "date",
        "datetime": "date",
        "number": "number",
        "integer": "number",
        "float": "number",
        "text": "text",
        "string": "text",
    }
    return aliases.get(token, token)


def _type_from_semantic(semantic: str | None, fallback: str = "string") -> str:
    if semantic in {"currency", "percent", "number"}:
        return "number"
    if semantic == "date":
        return "date"
    if semantic == "text":
        return "string"
    return fallback


def projectable_fields_from_legacy(
    *,
    value_fields: list[Any] | None = None,
    value_field_types: dict[str, Any] | None = None,
    value_field_labels: dict[str, Any] | None = None,
    existing: list[Any] | None = None,
    origin: str = ORIGIN_RESULT,
) -> list[dict[str, Any]]:
    """Monta projectableFields a partir de valueFields/types/labels ou lista já estruturada."""
    by_name: dict[str, dict[str, Any]] = {}

    if isinstance(existing, list):
        for item in existing:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            semantic = _semantic_from_type_hint(item.get("semanticType") or item.get("type"))
            by_name[name] = _field_descriptor(
                name=name,
                type_=str(item.get("type") or _type_from_semantic(semantic)),
                nullable=bool(item.get("nullable", True)),
                projectable=bool(item.get("projectable", True)),
                semantic_type=semantic,
                origin=str(item.get("origin") or origin),
                label=str(item.get("label") or "").strip() or None,
            )

    types = value_field_types if isinstance(value_field_types, dict) else {}
    labels = value_field_labels if isinstance(value_field_labels, dict) else {}
    for raw in value_fields or []:
        name = str(raw or "").strip()
        if not name:
            continue
        type_hint = types.get(name)
        semantic = _semantic_from_type_hint(type_hint)
        label = labels.get(name)
        if name in by_name:
            current = by_name[name]
            if semantic and not current.get("semanticType"):
                current["semanticType"] = semantic
                current["type"] = _type_from_semantic(semantic, current.get("type") or "string")
            if label and not current.get("label"):
                current["label"] = str(label).strip()
            continue
        by_name[name] = _field_descriptor(
            name=name,
            type_=_type_from_semantic(semantic),
            semantic_type=semantic,
            origin=origin,
            label=str(label).strip() if label else None,
        )

    return list(by_name.values())


def normalize_route_projectable_fields(route: dict[str, Any]) -> dict[str, Any]:
    """Garante projectableFields no catálogo e espelha valueFields (alias de transição)."""
    if not isinstance(route, dict):
        return route
    merged = dict(route)
    fields = projectable_fields_from_legacy(
        value_fields=merged.get("valueFields") if isinstance(merged.get("valueFields"), list) else None,
        value_field_types=(
            merged.get("valueFieldTypes")
            if isinstance(merged.get("valueFieldTypes"), dict)
            else None
        ),
        value_field_labels=(
            merged.get("valueFieldLabels")
            if isinstance(merged.get("valueFieldLabels"), dict)
            else None
        ),
        existing=(
            merged.get("projectableFields")
            if isinstance(merged.get("projectableFields"), list)
            else None
        ),
        origin=ORIGIN_RESULT,
    )
    if fields:
        merged["projectableFields"] = fields
        names = [item["name"] for item in fields if item.get("projectable", True)]
        if names:
            existing_vf = [
                str(item).strip()
                for item in (merged.get("valueFields") or [])
                if str(item).strip()
            ]
            # Alias: union preservando ordem (projectable primeiro, depois extras legados).
            ordered: list[str] = []
            seen: set[str] = set()
            for name in names + existing_vf:
                if name in seen:
                    continue
                seen.add(name)
                ordered.append(name)
            merged["valueFields"] = ordered
    return merged


def build_context_fields(
    effective_params: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Campos virtuais do filtro efetivo (playlist → slide → fonte → sessão)."""
    params = effective_params if isinstance(effective_params, dict) else {}
    start, end = _effective_date_pair(params)
    values: dict[str, Any] = {}

    if start:
        values[CONTEXT_START] = start
    if end:
        values[CONTEXT_END] = end
    if start and end:
        values[CONTEXT_RANGE_LABEL] = f"{_format_date_pt_br(start)} – {_format_date_pt_br(end)}"
    elif start:
        values[CONTEXT_RANGE_LABEL] = _format_date_pt_br(start)
    elif end:
        values[CONTEXT_RANGE_LABEL] = _format_date_pt_br(end)

    if not values:
        return [], {}

    # Specs estáticos sempre que houver período efetivo (dropdown + validação alinhados).
    fields = [dict(spec) for spec in _STATIC_CONTEXT_SPECS]
    return fields, values


def build_projectable_fields(
    route: dict[str, Any] | None,
    *,
    discovered_names: list[str] | None = None,
    meta_fields: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Campos de resultado: declarados do catálogo + descobertos (nunca remove declarados)."""
    normalized = normalize_route_projectable_fields(dict(route or {}))
    declared = list(normalized.get("projectableFields") or [])
    by_name = {
        str(item.get("name") or "").strip(): dict(item)
        for item in declared
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }

    labels = meta_fields if isinstance(meta_fields, dict) else {}
    for name, label in labels.items():
        key = str(name or "").strip()
        if not key:
            continue
        if key in by_name:
            if label and not by_name[key].get("label"):
                by_name[key]["label"] = str(label).strip()
            continue
        # meta.fields da api-delpi: declara campo de resultado com rótulo.
        by_name[key] = _field_descriptor(
            name=key,
            origin=ORIGIN_RESULT,
            label=str(label).strip() if label else None,
        )

    for raw in discovered_names or []:
        key = str(raw or "").strip()
        if not key or key in by_name:
            continue
        by_name[key] = _field_descriptor(name=key, origin=ORIGIN_DISCOVERED)

    return list(by_name.values())


def allowed_projection_field_names(
    route: dict[str, Any] | None = None,
    *,
    fields: list[dict[str, Any]] | None = None,
    context_fields: list[dict[str, Any]] | None = None,
    include_static_context: bool = True,
) -> list[str]:
    """Allowlist única para editor e mutation validator."""
    names: list[str] = []
    seen: set[str] = set()

    def push(name: str) -> None:
        key = str(name or "").strip()
        if not key or key in seen:
            return
        seen.add(key)
        names.append(key)

    for item in fields or []:
        if isinstance(item, dict) and item.get("projectable", True):
            push(str(item.get("name") or ""))

    if fields is None and isinstance(route, dict):
        for item in build_projectable_fields(route):
            if item.get("projectable", True):
                push(item["name"])
        for raw in route.get("valueFields") or []:
            push(str(raw))

    for item in context_fields or []:
        if isinstance(item, dict) and item.get("projectable", True):
            push(str(item.get("name") or ""))

    if include_static_context:
        for name in supported_context_field_names():
            push(name)

    return names


def collect_projection_field_refs(block: dict[str, Any]) -> list[str]:
    """Extrai textProjection.field e contentRuns[].dataRef.field não vazios."""
    if not isinstance(block, dict):
        return []
    refs: list[str] = []
    seen: set[str] = set()

    def push(raw: Any) -> None:
        key = str(raw or "").strip()
        if not key or key in seen:
            return
        seen.add(key)
        refs.append(key)

    projection = block.get("textProjection")
    if isinstance(projection, dict):
        push(projection.get("field"))

    runs = block.get("contentRuns")
    if isinstance(runs, list):
        for run in runs:
            if not isinstance(run, dict):
                continue
            data_ref = run.get("dataRef")
            if isinstance(data_ref, dict):
                push(data_ref.get("field"))

    cells = block.get("cells")
    if isinstance(cells, list):
        for row in cells:
            if not isinstance(row, list):
                continue
            for cell in row:
                if not isinstance(cell, dict):
                    continue
                data_ref = cell.get("dataRef")
                if isinstance(data_ref, dict):
                    push(data_ref.get("field"))

    return refs


def collect_view_projection_field_refs(block: dict[str, Any]) -> list[str]:
    """Campos referenciados por kpiProjection/chartProjection/tableProjection."""
    if not isinstance(block, dict):
        return []
    refs: list[str] = []
    seen: set[str] = set()

    def push(raw: Any) -> None:
        key = str(raw or "").strip()
        if not key or key in seen:
            return
        seen.add(key)
        refs.append(key)

    kpi = block.get("kpiProjection")
    if isinstance(kpi, dict):
        push(kpi.get("valueField"))
        push(kpi.get("field"))
        push(kpi.get("goalField"))
        for metric in kpi.get("metrics") or []:
            if isinstance(metric, dict):
                push(metric.get("field"))

    chart = block.get("chartProjection")
    if isinstance(chart, dict):
        push(chart.get("xField"))
        push(chart.get("yField"))
        push(chart.get("categoryField"))
        push(chart.get("seriesField"))
        push(chart.get("goalField"))
        for series in chart.get("series") or []:
            if isinstance(series, dict):
                push(series.get("field"))

    table = block.get("tableProjection")
    if isinstance(table, dict):
        for col in table.get("columns") or []:
            if isinstance(col, dict):
                push(col.get("key"))
                push(col.get("field"))

    return refs


def collect_source_consumer_field_refs(
    blocks: list[Any],
    source_id: str,
) -> dict[str, list[str]]:
    """``{block_id: [fields]}`` de todos os consumers vinculados a ``source_id``.

    Cobre textProjection/contentRuns/canvas cells (``dataRef.field``) e as
    projeções de view (kpi/chart/table). Células de canvas_table com
    ``dataSourceId`` próprio são atribuídas à fonte correta.
    """
    target = str(source_id or "").strip()
    out: dict[str, list[str]] = {}
    if not target or not isinstance(blocks, list):
        return out
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("id") or "").strip()
        refs: list[str] = []
        if str(block.get("type") or "") == "canvas_table":
            default_source = str(block.get("dataSourceId") or "").strip()
            cells = block.get("cells")
            if isinstance(cells, list):
                for row in cells:
                    if not isinstance(row, list):
                        continue
                    for cell in row:
                        if not isinstance(cell, dict):
                            continue
                        cell_source = (
                            str(cell.get("dataSourceId") or "").strip() or default_source
                        )
                        if cell_source != target:
                            continue
                        data_ref = cell.get("dataRef")
                        if isinstance(data_ref, dict):
                            field = str(data_ref.get("field") or "").strip()
                            if field and field not in refs:
                                refs.append(field)
        elif str(block.get("dataSourceId") or "").strip() == target:
            refs = list(collect_projection_field_refs(block))
            for field in collect_view_projection_field_refs(block):
                if field not in refs:
                    refs.append(field)
        if refs:
            out[block_id or "?"] = refs
    return out


def validate_block_projection_fields(
    block: dict[str, Any],
    *,
    route: dict[str, Any] | None = None,
    fields: list[dict[str, Any]] | None = None,
    context_fields: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Retorna erro tipado INVALID_PROJECTION_FIELD ou None se ok.

    Campos vazios não são validados (UX de link ainda pode sugerir default).
    """
    refs = collect_projection_field_refs(block)
    if not refs:
        return None
    allowed = allowed_projection_field_names(
        route,
        fields=fields,
        context_fields=context_fields,
        include_static_context=True,
    )
    allowed_set = set(allowed)
    # Sem catálogo de result fields ainda: só context fields são estritos.
    # Se a rota declara projectable/valueFields, todos os refs devem estar na allowlist.
    route_declares = bool(
        (isinstance(route, dict) and (route.get("projectableFields") or route.get("valueFields")))
        or fields
    )
    invalid: list[str] = []
    for ref in refs:
        if ref in allowed_set:
            continue
        if ref.startswith("filter."):
            invalid.append(ref)
            continue
        if route_declares:
            invalid.append(ref)
    if not invalid:
        return None
    return {
        "code": "INVALID_PROJECTION_FIELD",
        "message": (
            "Campo de projeção inválido: "
            + ", ".join(invalid)
            + ". Use um dos campos permitidos."
        ),
        "invalidFields": invalid,
        "allowedFields": allowed,
    }


def attach_projection_metadata(
    resolved: dict[str, Any],
    *,
    route: dict[str, Any] | None,
    effective_params: dict[str, Any] | None,
    discovered_names: list[str] | None = None,
) -> dict[str, Any]:
    """Anexa fields / contextFields / contextValues no resolved (preview/runtime)."""
    if not isinstance(resolved, dict):
        return resolved
    meta = resolved.get("meta") if isinstance(resolved.get("meta"), dict) else {}
    meta_fields = meta.get("fields") if isinstance(meta.get("fields"), dict) else None
    fields = build_projectable_fields(
        route,
        discovered_names=discovered_names,
        meta_fields=meta_fields,
    )
    context_fields, context_values = build_context_fields(effective_params)
    out = dict(resolved)
    if fields:
        out["fields"] = fields
        out["projectableFields"] = fields
    if context_fields:
        out["contextFields"] = context_fields
    if context_values:
        out["contextValues"] = context_values
    return out


def discover_names_from_resolved(resolved: dict[str, Any] | None) -> list[str]:
    """Nomes já materializados no resolved (kpiMetrics/table) — origem discovered."""
    if not isinstance(resolved, dict):
        return []
    names: list[str] = []
    seen: set[str] = set()

    def push(raw: Any) -> None:
        key = str(raw or "").strip()
        if not key or key in seen:
            return
        seen.add(key)
        names.append(key)

    for metric in resolved.get("kpiMetrics") or []:
        if isinstance(metric, dict):
            push(metric.get("field"))
    table = resolved.get("table")
    if isinstance(table, dict):
        for col in table.get("columns") or []:
            if isinstance(col, dict):
                push(col.get("key") or col.get("field"))
        rows = table.get("rows")
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            for key in rows[0].keys():
                push(key)
    kpi = resolved.get("kpi")
    if isinstance(kpi, dict) and (kpi.get("value") is not None or kpi.get("label")):
        push("value")
    return names
