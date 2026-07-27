"""Aplica projeções de visual (KPI/chart/table) no resolved — pós-cache."""

from __future__ import annotations

from typing import Any


_AGG_FNS = frozenset({"first", "sum", "avg", "min", "max", "count"})


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def aggregate_values(values: list[Any], aggregation: str = "first") -> float | None:
    agg = aggregation if aggregation in _AGG_FNS else "first"
    if agg == "count":
        return float(len(values))
    nums = [n for n in (_as_float(v) for v in values) if n is not None]
    if not nums:
        if agg == "first" and values:
            return _as_float(values[0])
        return None
    if agg == "sum":
        return float(sum(nums))
    if agg == "avg":
        return float(sum(nums) / len(nums))
    if agg == "min":
        return float(min(nums))
    if agg == "max":
        return float(max(nums))
    return float(nums[0])


def _column_values(rows: list[dict[str, Any]], field: str) -> list[Any]:
    return [row.get(field) for row in rows if isinstance(row, dict)]


def _is_auto_baked_field_label(label: str, field: str) -> bool:
    key = (field or "").strip()
    text = (label or "").strip()
    if not key:
        return not text
    return text.lower() == key.lower()


def _lookup_field_label(labels: dict[str, str], field: str) -> str | None:
    key = (field or "").strip()
    if not key:
        return None
    if key in labels:
        return labels[key]
    lower = key.lower()
    for entry_key, value in labels.items():
        if entry_key.lower() == lower:
            return value
    return None


def _normalize_field_labels(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    canonical_by_lower: dict[str, str] = {}
    for key, value in raw.items():
        field = str(key or "").strip()
        if not field or not isinstance(value, str):
            continue
        if not value.strip():
            continue
        lower = field.lower()
        previous = canonical_by_lower.get(lower)
        if previous and previous != field:
            out.pop(previous, None)
        canonical_by_lower[lower] = field
        out[field] = value
    return out


def apply_field_labels_to_resolved(
    resolved: dict[str, Any],
    field_labels: Any,
) -> dict[str, Any]:
    """
    Reaplica rótulos do registro da fonte (fieldLabels) em table/kpi/chart.
    Chaves das rows e valores não mudam — só display.
    """
    if not isinstance(resolved, dict):
        return resolved
    labels = _normalize_field_labels(field_labels)
    if not labels:
        return resolved

    next_resolved = dict(resolved)
    changed = False

    table = resolved.get("table")
    if isinstance(table, dict):
        columns = table.get("columns")
        if isinstance(columns, list) and columns:
            next_cols: list[dict[str, Any]] = []
            cols_changed = False
            for col in columns:
                if not isinstance(col, dict):
                    next_cols.append(col)
                    continue
                key = str(col.get("key") or "").strip()
                override = _lookup_field_label(labels, key)
                if override and override != str(col.get("label") or ""):
                    cols_changed = True
                    next_cols.append({**col, "label": override})
                else:
                    next_cols.append(col)
            if cols_changed:
                changed = True
                next_resolved["table"] = {**table, "columns": next_cols}

    metrics = resolved.get("kpiMetrics")
    if isinstance(metrics, list) and metrics:
        next_metrics: list[dict[str, Any]] = []
        metrics_changed = False
        for metric in metrics:
            if not isinstance(metric, dict):
                next_metrics.append(metric)
                continue
            field = str(metric.get("field") or "").strip()
            override = _lookup_field_label(labels, field)
            if override and override != str(metric.get("label") or ""):
                metrics_changed = True
                next_metrics.append({**metric, "label": override})
            else:
                next_metrics.append(metric)
        if metrics_changed:
            changed = True
            next_resolved["kpiMetrics"] = next_metrics
            kpi = next_resolved.get("kpi")
            if isinstance(kpi, dict) and next_metrics:
                primary = next_metrics[0]
                primary_field = str(primary.get("field") or "")
                primary_override = _lookup_field_label(labels, primary_field)
                if primary_override:
                    next_resolved["kpi"] = {**kpi, "label": primary_override}

    chart = resolved.get("chart")
    if isinstance(chart, dict):
        series = chart.get("series")
        if isinstance(series, list) and series:
            next_series: list[dict[str, Any]] = []
            series_changed = False
            for entry in series:
                if not isinstance(entry, dict):
                    next_series.append(entry)
                    continue
                field = str(entry.get("field") or "").strip()
                override = _lookup_field_label(labels, field) if field else None
                if field and override and override != str(entry.get("name") or ""):
                    series_changed = True
                    next_series.append({**entry, "name": override})
                else:
                    next_series.append(entry)
            if series_changed:
                changed = True
                next_resolved["chart"] = {**chart, "series": next_series}

    return next_resolved if changed else resolved


def apply_view_projection_to_resolved(resolved: dict[str, Any], block: dict[str, Any]) -> dict[str, Any]:
    """
    Aplica kpiProjection / chartProjection / tableProjection do bloco visual.
    Idempotente o suficiente para o cliente detectar `serverProjectionApplied`.
    """
    if not isinstance(resolved, dict):
        return resolved
    next_resolved = dict(resolved)
    block_type = str(block.get("type") or "")
    rows_raw = (resolved.get("table") or {}).get("rows") if isinstance(resolved.get("table"), dict) else None
    rows = [r for r in (rows_raw or []) if isinstance(r, dict)]
    applied = False

    if block_type == "kpi_view":
        projection = block.get("kpiProjection")
        metrics_cfg = projection.get("metrics") if isinstance(projection, dict) else None
        if isinstance(metrics_cfg, list) and metrics_cfg:
            existing = {
                str(m.get("field") or ""): m
                for m in (resolved.get("kpiMetrics") or [])
                if isinstance(m, dict) and m.get("field")
            }
            out_metrics: list[dict[str, Any]] = []
            for item in metrics_cfg:
                if not isinstance(item, dict):
                    continue
                if item.get("visible") is False:
                    continue
                field = str(item.get("field") or "").strip()
                if not field:
                    continue
                agg = str(item.get("aggregation") or "first")
                base = existing.get(field) or {}
                value: Any = base.get("value")
                if rows and agg != "first":
                    value = aggregate_values(_column_values(rows, field), agg)
                elif rows and value is None:
                    value = aggregate_values(_column_values(rows, field), "first")
                proj_label = str(item.get("label") or "")
                base_label = str(base.get("label") or "")
                if proj_label.strip() and not _is_auto_baked_field_label(proj_label, field):
                    label = proj_label
                elif base_label.strip():
                    label = base_label
                else:
                    label = field
                out_metrics.append({"field": field, "label": label, "value": value})
            if out_metrics:
                next_resolved["kpiMetrics"] = out_metrics
                primary = out_metrics[0]
                next_resolved["kpi"] = {"value": primary.get("value"), "label": primary.get("label")}
                applied = True

    if block_type == "table_view":
        projection = block.get("tableProjection")
        columns_cfg = projection.get("columns") if isinstance(projection, dict) else None
        table = resolved.get("table") if isinstance(resolved.get("table"), dict) else {}
        if isinstance(columns_cfg, list) and columns_cfg and isinstance(table, dict):
            visible = [c for c in columns_cfg if isinstance(c, dict) and c.get("visible") is not False]
            if visible:
                keys = [str(c.get("key") or "").strip() for c in visible if str(c.get("key") or "").strip()]
                old_label_by = {
                    str(c.get("key") or ""): str(c.get("label") or c.get("key") or "")
                    for c in (table.get("columns") if isinstance(table.get("columns"), list) else [])
                    if isinstance(c, dict) and c.get("key")
                }
                next_cols = []
                for col in visible:
                    key = str(col.get("key") or "").strip()
                    if not key:
                        continue
                    proj_label = str(col.get("label") or "")
                    base_label = old_label_by.get(key) or ""
                    if proj_label.strip() and not _is_auto_baked_field_label(proj_label, key):
                        label = proj_label
                    elif base_label.strip():
                        label = base_label
                    else:
                        label = key
                    next_cols.append({"key": key, "label": label})
                next_rows = []
                for row in rows:
                    next_rows.append({k: row.get(k) for k in keys if k in row})
                next_resolved["table"] = {"rows": next_rows, "columns": next_cols}
                applied = True

    if block_type == "chart_view":
        projection = block.get("chartProjection")
        chart_type = str(block.get("chartType") or "line").strip() or "line"
        if isinstance(projection, dict) and rows:
            series_cfg = projection.get("series") if isinstance(projection.get("series"), list) else []
            category = str(projection.get("categoryField") or "").strip()
            # Sem série explícita + categoria + pizza/rosca → contagem por grupo.
            if not series_cfg and category and chart_type in _COUNT_DEFAULT_CHART_TYPES:
                series_cfg = [
                    {
                        "field": category,
                        "aggregation": "count",
                        "label": "Contagem",
                    }
                ]
            if series_cfg:
                series_out = _build_chart_series(
                    rows=rows,
                    category=category,
                    series_cfg=series_cfg,
                    chart_type=chart_type,
                )
                if series_out:
                    next_resolved["chart"] = {
                        "points": series_out[0]["points"],
                        "chartType": chart_type,
                        "series": series_out,
                    }
                    applied = True

    if applied:
        next_resolved["serverProjectionApplied"] = True
    return next_resolved


# Tipos alinhados a chartDataPolicy.ts (rowMode: groupByCategory).
_GROUP_BY_CHART_TYPES = frozenset(
    {
        "bar",
        "stacked_bar",
        "pie",
        "doughnut",
        "radar",
        "combo",
        "waterfall",
        "funnel",
    }
)
_COUNT_DEFAULT_CHART_TYPES = frozenset({"pie", "doughnut"})


def _series_display_name(item: dict[str, Any], field: str) -> str:
    proj_label = str(item.get("label") or "")
    if proj_label.strip() and not _is_auto_baked_field_label(proj_label, field):
        return proj_label
    return field


def _aggregate_group_rows(
    group_rows: list[dict[str, Any]],
    field: str,
    aggregation: str,
    *,
    count_fallback: bool,
) -> float | None:
    agg = aggregation if aggregation in _AGG_FNS else "first"
    if agg == "count":
        return float(len(group_rows))
    values = _column_values(group_rows, field)
    nums = [n for n in (_as_float(v) for v in values) if n is not None]
    if nums:
        return aggregate_values(nums, agg)
    # Pizza/rosca: medida ausente → conta linhas do grupo (paridade com viewProjection.ts).
    if count_fallback:
        return float(len(group_rows))
    if agg == "first" and values:
        return _as_float(values[0])
    return None


def _build_chart_series(
    *,
    rows: list[dict[str, Any]],
    category: str,
    series_cfg: list[Any],
    chart_type: str,
) -> list[dict[str, Any]]:
    count_fallback = chart_type in _COUNT_DEFAULT_CHART_TYPES
    default_agg = "count" if count_fallback else "first"
    group_by = bool(category) and chart_type in _GROUP_BY_CHART_TYPES

    if group_by:
        groups: dict[str, list[dict[str, Any]]] = {}
        order: list[str] = []
        for row in rows:
            raw = row.get(category)
            key = "(vazio)" if raw is None or raw == "" else str(raw)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(row)

        series_out: list[dict[str, Any]] = []
        for item in series_cfg:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "").strip()
            if not field:
                continue
            agg = str(item.get("aggregation") or default_agg)
            points = [
                {
                    "label": key,
                    "value": _aggregate_group_rows(
                        groups[key],
                        field,
                        agg,
                        count_fallback=count_fallback,
                    ),
                }
                for key in order
            ]
            series_out.append(
                {
                    "name": _series_display_name(item, field),
                    "field": field,
                    "color": item.get("color"),
                    "points": points,
                }
            )
        return series_out

    categories = [
        str(row.get(category)) if category and row.get(category) is not None else str(idx + 1)
        for idx, row in enumerate(rows)
    ]
    series_out = []
    for item in series_cfg:
        if not isinstance(item, dict):
            continue
        field = str(item.get("field") or "").strip()
        if not field:
            continue
        agg = str(item.get("aggregation") or default_agg)
        points = []
        for idx, row in enumerate(rows):
            if agg == "count":
                value: float | None = 1.0
            else:
                value = aggregate_values([row.get(field)], agg)
                if value is None and count_fallback:
                    value = 1.0
            points.append({"label": categories[idx], "value": value})
        series_out.append(
            {
                "name": _series_display_name(item, field),
                "field": field,
                "color": item.get("color"),
                "points": points,
            }
        )
    return series_out
