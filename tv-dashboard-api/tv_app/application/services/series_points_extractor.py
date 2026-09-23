"""Extrai pontos {label, value} de envelopes api-delpi (séries OEE/OTD/PPM)."""

from __future__ import annotations

from typing import Any

_ENVELOPE_META_KEYS = frozenset({"meta", "success", "message", "errors", "error"})


def _first_non_null(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Retorna o primeiro campo presente e não nulo, preservando 0, False e string vazia.

    `or` não pode ser usado aqui: zero é um dado operacional válido.
    """
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def unwrap_operational_data(data: Any) -> Any:
    """Normaliza payload api-delpi (envelope `{ success, data }` ou business data)."""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return data

    if data.get("success") is not None and "data" in data:
        inner = data.get("data")
        if isinstance(inner, (dict, list)):
            data = inner
            if isinstance(data, list):
                return data

    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            other_keys = [
                key
                for key in data.keys()
                if key not in _ENVELOPE_META_KEYS and key != "data"
            ]
            if not other_keys or all(
                data.get(key) in (None, "", [], {}) for key in other_keys
            ):
                data = inner

    # Ponte dashboard SI: `{ "item": { idd, indicators, … } }` (único payload útil).
    if isinstance(data, dict):
        item = data.get("item")
        if isinstance(item, dict):
            other_keys = [
                key
                for key in data.keys()
                if key not in _ENVELOPE_META_KEYS and key != "item"
            ]
            if not other_keys or all(
                data.get(key) in (None, "", [], {}) for key in other_keys
            ):
                return item

    return data


def envelope_data(envelope: dict[str, Any] | Any) -> dict[str, Any]:
    unwrapped = unwrap_operational_data(envelope)
    return unwrapped if isinstance(unwrapped, dict) else {}


def extract_series_points(
    data: Any,
    series_field: str | None = None,
    *,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    """Converte lista `points`/`series`/`serie`/`ranking` do payload em pontos de gráfico TV.

    Quando `data` já é uma lista tabular (ex.: saída de uma transformação M sobre a série),
    ela é a própria série canônica — os pontos vêm direto das linhas, sem procurar chaves.
    """
    data = unwrap_operational_data(data)
    raw: list[Any] | None = None
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        candidates: list[str] = []
        if series_field and str(series_field).strip():
            candidates.append(str(series_field).strip())
        for key in ("points", "series", "serie", "ranking", "levelData", "statusData", "leadByLevel"):
            if key not in candidates:
                candidates.append(key)
        for key in candidates:
            value = data.get(key)
            if isinstance(value, list) and value:
                raw = value
                break
    if not isinstance(raw, list):
        return []
    branch_code = str(branch).strip() if branch else ""
    points: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        label = _first_non_null(
            row,
            (
                "label",
                "bucket",
                "periodo",
                "competencia",
                "date",
                "name",
                "centro_custo",
                "fornecedor",
                "level",
                "status",
            ),
        )
        value = row.get("value")
        if value is None:
            value = _first_non_null(row, ("total", "qty", "quantidade", "count"))
        if value is None and branch_code:
            branch_key = branch_code.zfill(2)
            value = _first_non_null(
                row,
                (
                    f"oee_filial_{branch_key}",
                    f"otd_filial_{branch_key}",
                    f"oee_pct_filial_{branch_key}",
                    f"ppm_filial_{branch_key}",
                ),
            )
        if value is None:
            value = _first_non_null(
                row,
                (
                    "economia_bruta",
                    "investimento",
                    "investimento_total_mes",
                    "economia_liquida",
                    "economia_liquida_mes",
                ),
            )
        if value is None:
            for field_key, field_value in row.items():
                if not isinstance(field_key, str) or field_value is None:
                    continue
                if field_key.startswith(("oee_", "otd_", "ppm_")) and field_key not in {
                    "oee_pct",
                    "otd_pct",
                }:
                    value = field_value
                    break
        points.append({"label": label, "value": value})
    return points


_WIDE_LABEL_KEYS = frozenset(
    {
        "label",
        "bucket",
        "periodo",
        "competencia",
        "date",
        "name",
        "granularity",
    }
)
_WIDE_METRIC_PREFIXES = (
    "conversion_",
    "oee_",
    "otd_",
    "ppm_",
    "qtd_",
)


def wide_metric_fields(row: dict[str, Any]) -> list[str]:
    """Numeric metric columns that must not collapse into a single points[].value."""
    fields: list[str] = []
    for key, value in row.items():
        if not isinstance(key, str) or key in _WIDE_LABEL_KEYS:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if key.startswith(_WIDE_METRIC_PREFIXES) or key.endswith("_pct"):
            fields.append(key)
    return fields


def chart_series_from_rows(rows: list[Any]) -> dict[str, Any] | None:
    """Project a wide table into chart.series. None when fewer than 2 metrics."""
    typed = [row for row in rows if isinstance(row, dict)]
    if not typed:
        return None
    fields = wide_metric_fields(typed[0])
    if len(fields) < 2:
        return None
    series: list[dict[str, Any]] = []
    for field in fields:
        points: list[dict[str, Any]] = []
        values: list[Any] = []
        for row in typed:
            label = _first_non_null(
                row,
                ("label", "bucket", "periodo", "competencia", "date", "name"),
            )
            value = row.get(field)
            values.append(value)
            points.append({"label": label, "value": value})
        series.append({"field": field, "values": values, "points": points})
    return {"series": series}


def rows_from_operational_payload(data: Any) -> list[dict[str, Any]]:
    unwrapped = unwrap_operational_data(data)
    if isinstance(unwrapped, list):
        return [row for row in unwrapped if isinstance(row, dict)]
    if isinstance(unwrapped, dict):
        for key in ("points", "series", "rows", "items"):
            raw = unwrapped.get(key)
            if isinstance(raw, list) and raw and isinstance(raw[0], dict):
                return [row for row in raw if isinstance(row, dict)]
    return []


def envelope_meta(envelope: dict[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        return {}
    meta = envelope.get("meta")
    return meta if isinstance(meta, dict) else {}


def response_fields_from_meta(
    meta: dict[str, Any],
) -> dict[str, str] | list[dict[str, Any]]:
    """
    Extrai rótulos de ``meta.fields`` do envelope api-delpi.

    Formato canônico: dict ``{campo: rótulo PT}``.
    Legado: lista ``[{key|name, label|title}, ...]``.
    """
    fields = meta.get("fields")
    if isinstance(fields, dict):
        out: dict[str, str] = {}
        for key, label in fields.items():
            field = str(key).strip()
            if not field:
                continue
            if isinstance(label, dict):
                text = str(label.get("label") or label.get("title") or "").strip()
            elif isinstance(label, (list, tuple)):
                text = ""
            else:
                text = str(label or "").strip()
            if text:
                out[field] = text
        return out
    if isinstance(fields, list):
        return [field for field in fields if isinstance(field, dict)]
    return {}
