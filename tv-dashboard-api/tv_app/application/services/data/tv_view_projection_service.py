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


_METRIC_DUMP_ROW_KEYS = frozenset({"metric", "field", "value", "label", "indicador"})
_PAYLOAD_LIST_KEYS = (
    "leadByLevel",
    "levelData",
    "statusData",
    "ranking",
    "serie",
    "series",
    "points",
    "items",
    "rows",
    "records",
    "results",
    "history",
    "flow",
    "branches",
)


def _is_metric_summary_rows(rows: list[dict[str, Any]]) -> bool:
    """Table dump of kpiMetrics (metric/field/value) — not a categorical chart frame."""
    if not rows:
        return False
    sample = rows[: min(12, len(rows))]
    keys: set[str] = set()
    for row in sample:
        keys.update(str(k) for k in row.keys())
    if not keys:
        return False
    if keys <= _METRIC_DUMP_ROW_KEYS and "field" in keys and "value" in keys:
        return True
    if keys == {"campo", "valor"}:
        return True
    return False


def _rows_cover_projection_fields(
    rows: list[dict[str, Any]],
    *,
    category: str,
    series_fields: list[str],
) -> bool:
    if not rows or _is_metric_summary_rows(rows):
        return False
    keys: set[str] = set()
    for row in rows[: min(20, len(rows))]:
        keys.update(str(k) for k in row.keys())
    needed = [f for f in [category, *series_fields] if f]
    if not needed:
        return True
    return any(field in keys for field in needed)


def _list_rows_from_payload_node(node: Any) -> list[dict[str, Any]]:
    if isinstance(node, list):
        return [row for row in node if isinstance(row, dict)]
    if isinstance(node, dict):
        for nested_key in ("items", "rows"):
            nested = node.get(nested_key)
            if isinstance(nested, list):
                return [row for row in nested if isinstance(row, dict)]
    return []


def _alternate_rows_from_resolved_data(
    resolved: dict[str, Any],
    *,
    category: str,
    series_fields: list[str],
) -> list[dict[str, Any]]:
    """Find business list rows (e.g. leadByLevel) matching chart encoding fields."""
    data = resolved.get("data")
    if data is None:
        return []
    from tv_app.application.services.series_points_extractor import unwrap_operational_data

    payload = unwrap_operational_data(data)
    candidates: list[list[dict[str, Any]]] = []
    if isinstance(payload, list):
        candidates.append([row for row in payload if isinstance(row, dict)])
    elif isinstance(payload, dict):
        for key in _PAYLOAD_LIST_KEYS:
            rows = _list_rows_from_payload_node(payload.get(key))
            if rows:
                candidates.append(rows)
        # Nested summary envelopes occasionally wrap lists one level deeper.
        for value in payload.values():
            if isinstance(value, dict):
                for key in _PAYLOAD_LIST_KEYS:
                    rows = _list_rows_from_payload_node(value.get(key))
                    if rows:
                        candidates.append(rows)

    needed = [f for f in [category, *series_fields] if f]
    best: list[dict[str, Any]] = []
    best_score = -1
    for rows in candidates:
        if not rows:
            continue
        keys = set()
        for row in rows[: min(20, len(rows))]:
            keys.update(str(k) for k in row.keys())
        score = sum(1 for field in needed if field in keys) if needed else 1
        if score > best_score:
            best_score = score
            best = rows
    if needed and best_score <= 0:
        return []
    return best


def _chart_series_from_selected_metrics(
    resolved: dict[str, Any],
    series_cfg: list[Any],
    chart_type: str,
) -> list[dict[str, Any]]:
    """Selected-only slices from kpiMetrics when no categorical frame exists."""
    metrics = {
        str(m.get("field") or ""): m
        for m in (resolved.get("kpiMetrics") or [])
        if isinstance(m, dict) and m.get("field")
    }
    series_out: list[dict[str, Any]] = []
    for item in series_cfg:
        if not isinstance(item, dict):
            continue
        field = str(item.get("field") or "").strip()
        if not field:
            continue
        metric = metrics.get(field)
        if not metric:
            continue
        value = aggregate_values([metric.get("value")], str(item.get("aggregation") or "first"))
        if value is None and metric.get("value") not in (None, ""):
            # Non-numeric scalar still paints as single point when finite-coercion fails later.
            raw = metric.get("value")
            try:
                value = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
        if value is None:
            continue
        name = _series_display_name(item, field)
        # Prefer authored series label; fall back to metric business label for the point.
        point_label = name or str(metric.get("label") or field)
        series_out.append(
            {
                "name": name,
                "field": field,
                "color": item.get("color"),
                "points": [{"label": point_label, "value": value}],
            }
        )
    if not series_out:
        return []
    # Multi-measure without category → bar-like points (selected metrics only).
    if len(series_out) > 1 and chart_type in {"line", "area"}:
        chart_type_out = "bar"
    else:
        chart_type_out = chart_type
    # Caller sets chartType; keep series list as encoding.
    _ = chart_type_out
    return series_out


def _resolve_chart_rows_for_projection(
    resolved: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    category: str,
    series_cfg: list[Any],
) -> list[dict[str, Any]]:
    series_fields = [
        str(item.get("field") or "").strip()
        for item in series_cfg
        if isinstance(item, dict) and str(item.get("field") or "").strip()
    ]
    if _rows_cover_projection_fields(rows, category=category, series_fields=series_fields):
        return rows
    alt = _alternate_rows_from_resolved_data(
        resolved, category=category, series_fields=series_fields
    )
    if _rows_cover_projection_fields(alt, category=category, series_fields=series_fields):
        return alt
    # Metric dump / unrelated frame must not drive category encoding.
    if _is_metric_summary_rows(rows):
        return []
    return rows


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
                usable_rows = rows if not _is_metric_summary_rows(rows) else []
                if usable_rows and agg != "first":
                    value = aggregate_values(_column_values(usable_rows, field), agg)
                elif usable_rows and value is None:
                    value = aggregate_values(_column_values(usable_rows, field), "first")
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
                old_label_by = {
                    str(c.get("key") or ""): str(c.get("label") or c.get("key") or "")
                    for c in (table.get("columns") if isinstance(table.get("columns"), list) else [])
                    if isinstance(c, dict) and c.get("key")
                }
                next_cols: list[dict[str, Any]] = []
                for col in visible:
                    key = str(col.get("key") or col.get("field") or "").strip()
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
                    next_col: dict[str, Any] = {"key": key, "label": label}
                    value_format = str(col.get("valueFormat") or "").strip()
                    if value_format:
                        next_col["valueFormat"] = value_format
                    next_cols.append(next_col)
                keys = [str(c.get("key") or "").strip() for c in next_cols if c.get("key")]
                next_rows = []
                for row in rows:
                    next_rows.append({k: row.get(k) for k in keys if k in row})
                next_resolved["table"] = {"rows": next_rows, "columns": next_cols}
                applied = True

    if block_type == "chart_view":
        projection = block.get("chartProjection")
        chart_type = str(block.get("chartType") or "line").strip() or "line"
        if isinstance(projection, dict):
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
            chart_rows = _resolve_chart_rows_for_projection(
                resolved,
                rows,
                category=category,
                series_cfg=series_cfg if isinstance(series_cfg, list) else [],
            )
            series_out: list[dict[str, Any]] = []
            if chart_rows and series_cfg:
                series_out = _build_chart_series(
                    rows=chart_rows,
                    category=category,
                    series_cfg=series_cfg,
                    chart_type=chart_type,
                    max_categories=_resolve_max_categories(projection, chart_type),
                )
            elif series_cfg and not category:
                # Encoding escolhe medidas sem dimensão → selected metrics only.
                series_out = _chart_series_from_selected_metrics(
                    resolved, series_cfg, chart_type
                )
            if series_out:
                effective_type = chart_type
                if len(series_out) > 1 and chart_type in {"line", "area"} and not category:
                    effective_type = "bar"
                next_chart: dict[str, Any] = {
                    "points": series_out[0]["points"],
                    "chartType": effective_type,
                    "series": series_out,
                }
                projected_goal = _resolve_projected_goal(chart_rows or rows, projection)
                if projected_goal is not None:
                    next_chart["projectedGoal"] = projected_goal
                next_resolved["chart"] = next_chart
                applied = True
            elif series_cfg or category:
                # Projection intent must never keep source kpiMetrics dump as chart.
                next_resolved["chart"] = {
                    "points": [],
                    "chartType": chart_type,
                    "series": [],
                }
                applied = True

    if applied:
        next_resolved["serverProjectionApplied"] = True

    # Visual weekend filter (presentation-only; never sent as query). Bake here so
    # MFE does not re-project chart points when serverProjectionApplied.
    before_chart = next_resolved.get("chart")
    next_resolved = _apply_exclude_weekends_if_needed(next_resolved)
    if next_resolved.get("chart") is not before_chart:
        next_resolved["serverProjectionApplied"] = True
    return next_resolved


def _truthy_param(value: Any) -> bool:
    if value is True or value == 1:
        return True
    text = str(value or "").strip().lower()
    return text in {"true", "1", "yes", "on", "sim"}


def _is_daily_granularity(value: Any) -> bool:
    raw = str(value or "").strip().lower()
    return raw in {"day", "daily", "dia"}


def _parse_category_point_date(label: Any) -> tuple[int, int, int] | None:
    text = str(label or "").strip()
    if not text:
        return None
    import re

    iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", text)
    if iso:
        return int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
    br = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$", text)
    if br:
        day = int(br.group(1))
        month = int(br.group(2))
        year = int(br.group(3))
        if year < 100:
            year += 1900 if year >= 70 else 2000
        return year, month, day
    return None


def _is_weekend_ymd(ymd: tuple[int, int, int]) -> bool:
    from datetime import date

    try:
        return date(ymd[0], ymd[1], ymd[2]).weekday() >= 5
    except ValueError:
        return False


def _filter_points_excluding_weekends(points: list[Any]) -> list[Any]:
    out: list[Any] = []
    for point in points:
        if not isinstance(point, dict):
            out.append(point)
            continue
        ymd = _parse_category_point_date(point.get("label"))
        if ymd is None or not _is_weekend_ymd(ymd):
            out.append(point)
    return out


def _apply_exclude_weekends_if_needed(resolved: dict[str, Any]) -> dict[str, Any]:
    view = resolved.get("viewFilterParams")
    if not isinstance(view, dict):
        return resolved
    if not _truthy_param(view.get("excludeWeekends")):
        return resolved
    gran = view.get("granularity")
    if gran is not None and str(gran).strip() != "" and not _is_daily_granularity(gran):
        return resolved
    chart = resolved.get("chart")
    if not isinstance(chart, dict):
        return resolved
    next_chart = dict(chart)
    series = chart.get("series")
    if isinstance(series, list) and series:
        next_series = []
        for item in series:
            if not isinstance(item, dict):
                next_series.append(item)
                continue
            points = item.get("points")
            next_item = dict(item)
            if isinstance(points, list):
                next_item["points"] = _filter_points_excluding_weekends(points)
            next_series.append(next_item)
        next_chart["series"] = next_series
        if next_series and isinstance(next_series[0], dict):
            next_chart["points"] = list(next_series[0].get("points") or [])
    else:
        points = chart.get("points")
        if isinstance(points, list):
            next_chart["points"] = _filter_points_excluding_weekends(points)
    return {**resolved, "chart": next_chart}


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


# Soft caps alinhados a chartDataPolicy.ts (maxCategories).
_DEFAULT_MAX_CATEGORIES: dict[str, int] = {
    "pie": 8,
    "doughnut": 8,
    "funnel": 12,
    "bar": 24,
    "stacked_bar": 24,
    "horizontal_bar": 24,
}


def _resolve_max_categories(projection: dict[str, Any], chart_type: str) -> int | None:
    raw = projection.get("maxCategories")
    if raw is None:
        return _DEFAULT_MAX_CATEGORIES.get(chart_type)
    if raw is False or raw == 0 or raw == "0":
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_CATEGORIES.get(chart_type)
    if n <= 0:
        return None
    return max(1, n)


def _resolve_projected_goal(rows: list[dict[str, Any]], projection: dict[str, Any]) -> float | None:
    field = str(projection.get("goalField") or "").strip()
    if not field or not rows:
        return None
    agg = str(projection.get("goalAggregation") or "first")
    values = _column_values(rows, field)
    nums = [n for n in (_as_float(v) for v in values) if n is not None]
    if not nums and values:
        # first of raw when non-numeric — rare for goals
        first = _as_float(values[0])
        return first
    if not nums:
        return None
    return aggregate_values(nums, agg if agg in _AGG_FNS else "first")


def _collapse_categories_to_max(
    groups: dict[str, list[dict[str, Any]]],
    order: list[str],
    max_categories: int | None,
) -> list[str]:
    if max_categories is None or len(order) <= max_categories:
        return order
    ranked = sorted(order, key=lambda key: len(groups.get(key) or []), reverse=True)
    keep = set(ranked[: max_categories - 1])
    others: list[dict[str, Any]] = []
    next_order: list[str] = []
    for key in order:
        if key in keep:
            next_order.append(key)
            continue
        others.extend(groups.pop(key, []))
    if others:
        groups["Outros"] = others
        next_order.append("Outros")
    return next_order


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
    max_categories: int | None = None,
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

        order = _collapse_categories_to_max(groups, order, max_categories)

        # Funnel: sort by first series value descending (parity with viewProjection.ts).
        if chart_type == "funnel" and series_cfg:
            first = series_cfg[0] if isinstance(series_cfg[0], dict) else None
            if isinstance(first, dict) and str(first.get("field") or "").strip():
                field0 = str(first.get("field") or "").strip()
                agg0 = str(first.get("aggregation") or default_agg)

                def _funnel_key(key: str) -> float:
                    val = _aggregate_group_rows(
                        groups.get(key) or [],
                        field0,
                        agg0,
                        count_fallback=count_fallback,
                    )
                    return float(val or 0)

                order = sorted(order, key=_funnel_key, reverse=True)

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

    categories: list[str] = []
    for idx, row in enumerate(rows):
        if category and row.get(category) is not None:
            categories.append(str(row.get(category)))
        else:
            categories.append(str(idx + 1))
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
