from __future__ import annotations

import hashlib
import json
from typing import Any

from tv_app.application.services.branch_policy_service import validate_data_route_branch
from tv_app.application.services.comunicado_data_params_service import merge_data_params
from tv_app.application.services.comunicado_input_filters_service import (
    collect_input_filter_contributions,
    merge_filter_layers,
)
from tv_app.application.services.data.tv_data_fetch_error_service import resolve_data_fetch_error
from tv_app.application.services.data.m_query.m_phase7_quality_service import (
    SafeTelemetry,
    profile_table,
    reset_phase7_caches,
)
from tv_app.application.services.data.tv_data_presentation_modes_service import normalize_display_mode
from tv_app.application.services.data.m_query.m_query_dependency_service import (
    MQueryDependencyService,
)
from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_to_payload,
    apply_data_transform_to_payload_result,
    coerce_payload_to_table,
    normalize_data_transform,
)
from tv_app.application.services.data.tv_view_projection_service import (
    apply_view_projection_to_resolved,
)
from tv_app.application.services.native_screen_cache_service import (
    native_data_cache_ttl_seconds,
)
from tv_app.application.services.tv_dashboard_content_service import (
    m_query_setting,
    message,
    tv_dashboard_setting_int,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    DATA_BLOCK_TYPES,
    DATA_VIEW_BLOCK_TYPES,
    TEXT_DATA_BOUND_BLOCK_TYPES,
    TvDataRouteCatalogService,
)
from tv_app.infrastructure.cache.ttl_cache import TtlCache
from tv_app.infrastructure.gateways.delpi_operational_gateway import DelpiOperationalGateway
from tv_app.application.services.series_points_extractor import (
    extract_series_points,
    unwrap_operational_data,
)

_data_block_cache = TtlCache[dict[str, Any]](ttl_seconds=native_data_cache_ttl_seconds())

# Sem maxRows explícito: série diária (~3 meses) cabe no scroll do bloco; não truncar em 5
# (gráfico recebe a série inteira — tabela deve acompanhar).
_DEFAULT_TABLE_MAX_ROWS = 90
# Séries longas (ex.: «este ano» diário): tabela acompanha o gráfico com todos os pontos.
_DEFAULT_SERIES_TABLE_MAX_ROWS = 366


def _apply_incremental_pagination_defaults(
    params: dict[str, Any],
    route: dict[str, Any] | None,
) -> dict[str, Any]:
    schema = route.get("paramSchema") if isinstance(route, dict) else None
    if not isinstance(schema, dict) or "page" not in schema or "page_size" not in schema:
        return params
    page_size = max(1, tv_dashboard_setting_int("tableIncrementalPageSize", 30))
    return {
        **params,
        "page": params.get("page") or 1,
        "page_size": params.get("page_size") or page_size,
    }


def _resolve_table_max_rows(binding: dict[str, Any], route_info: dict[str, Any]) -> int:
    if binding.get("maxRows") is not None:
        return max(1, int(binding["maxRows"]))
    constraints = route_info.get("tvConstraints")
    if isinstance(constraints, dict) and constraints.get("maxRows") is not None:
        return max(1, int(constraints["maxRows"]))
    # Rota de série: tabela traz todos os pontos da API (acompanha o gráfico), sem cap de 90.
    if str(route_info.get("seriesField") or "").strip():
        return _DEFAULT_SERIES_TABLE_MAX_ROWS
    return _DEFAULT_TABLE_MAX_ROWS


def _build_data_cache_key(
    *,
    operation_id: str,
    params: dict[str, Any],
    authorization: str | None,
    user: Any | None = None,
    service_context: str | None = None,
) -> str:
    permissions = sorted(
        {
            str(permission).strip()
            for permission in (getattr(user, "permissions", None) or [])
            if str(permission).strip()
        }
    )
    identity = next(
        (
            str(value).strip()
            for value in (
                getattr(user, "sub", None),
                getattr(user, "id", None),
                getattr(user, "user_id", None),
                getattr(user, "email", None),
                getattr(user, "username", None),
            )
            if value is not None and str(value).strip()
        ),
        "",
    )
    principal = {
        "kind": "user" if authorization or user is not None else "service",
        "identity": identity,
        "permissions": permissions,
        "isSuperadmin": bool(getattr(user, "is_superadmin", False)),
        "serviceContext": str(service_context or "tv-dashboard").strip(),
        # Fallback opaco quando o modelo HTTP não expõe subject; nunca serializa o token.
        "credentialDigest": hashlib.sha256(authorization.encode("utf-8")).hexdigest()
        if authorization and not identity
        else "",
    }
    auth_fingerprint = hashlib.sha256(
        json.dumps(principal, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return json.dumps(
        {
            "operationId": operation_id,
            "params": params,
            "authorizationFingerprint": f"sha256:{auth_fingerprint}",
        },
        sort_keys=True,
        default=str,
    )


def _catalog_value_fields(route_info: dict[str, Any]) -> list[str]:
    raw = route_info.get("valueFields") or []
    return [str(field).strip() for field in raw if str(field).strip()]


def _value_field_labels(route_info: dict[str, Any]) -> dict[str, str]:
    raw = route_info.get("valueFieldLabels")
    if not isinstance(raw, dict):
        return {}
    return {
        str(key).strip(): str(label).strip()
        for key, label in raw.items()
        if str(key).strip() and str(label).strip()
    }


def _humanize_value_field(field: str, labels: dict[str, str]) -> str:
    if field in labels:
        return labels[field]
    return field.replace("_", " ").strip()


def _binding_selected_fields(binding: dict[str, Any]) -> list[str] | None:
    """None = todas as métricas; lista = filtro (ordem preservada)."""
    selected = binding.get("selectedValueFields")
    if isinstance(selected, list):
        fields = [str(item).strip() for item in selected if str(item).strip()]
        if fields:
            return fields
    override = binding.get("valueField")
    if override is not None and str(override).strip():
        return [str(override).strip()]
    return None


def _value_fields_for_binding(route_info: dict[str, Any], binding: dict[str, Any]) -> list[str]:
    """Compat: lista efetiva para scalar único (seleção ou catálogo)."""
    selected = _binding_selected_fields(binding)
    if selected is not None:
        return selected
    return _catalog_value_fields(route_info)


def _iter_scalar_candidate_keys(value_fields: list[Any]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for field in value_fields:
        key = str(field).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        keys.append(key)
    for fallback in ("value", "total", "pct", "percentage"):
        if fallback not in seen:
            seen.add(fallback)
            keys.append(fallback)
    return keys


# Campos de paginação/cobertura — não são KPI de negócio (ex.: playbook_report.summary).
_KPI_META_FIELD_KEYS = frozenset(
    {
        "total_records",
        "totalrecords",
        "page",
        "page_size",
        "pagesize",
        "offset",
        "limit",
        "returned",
        "is_complete",
        "iscomplete",
        "branch_filter_applied",
        "consolidated_across_branches",
    }
)


def _is_kpi_meta_field(key: str) -> bool:
    key_l = key.lower().replace("-", "_")
    if key_l in _KPI_META_FIELD_KEYS:
        return True
    if key_l.endswith("_applied") or key_l.startswith("is_"):
        return True
    return False


def _first_numeric_like_field(payload: dict[str, Any]) -> Any:
    """Fallback quando o catálogo não declara valueFields (ex.: campos *_pct no payload)."""
    preferred: list[tuple[int, str, Any]] = []
    for key, value in payload.items():
        if value is None or isinstance(value, (dict, list, bool)):
            continue
        if not isinstance(key, str) or _is_kpi_meta_field(key):
            continue
        key_l = key.lower()
        rank = 3
        if key_l.endswith("_pct") or key_l.endswith("_percentage") or key_l.endswith("pct"):
            rank = 0
        elif key_l in {"value", "total"}:
            rank = 1
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            rank = 2
        else:
            continue
        preferred.append((rank, key, value))
    if not preferred:
        return None
    preferred.sort(key=lambda item: (item[0], item[1]))
    return preferred[0][2]


def _discover_numeric_field_keys(payload: dict[str, Any]) -> list[str]:
    preferred: list[tuple[int, str]] = []
    for key, value in payload.items():
        if value is None or isinstance(value, (dict, list, bool)):
            continue
        if not isinstance(key, str) or _is_kpi_meta_field(key):
            continue
        key_l = key.lower()
        rank = 3
        if key_l.endswith("_pct") or key_l.endswith("_percentage") or key_l.endswith("pct"):
            rank = 0
        elif key_l in {"value", "total"}:
            rank = 1
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            rank = 2
        else:
            continue
        preferred.append((rank, key))
    preferred.sort(key=lambda item: (item[0], item[1]))
    return [key for _, key in preferred]


def _scalar_payloads(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    payloads: list[dict[str, Any]] = []
    summary = data.get("summary")
    if isinstance(summary, dict):
        payloads.append(summary)
    payloads.append(data)
    return payloads


def _lookup_scalar_field(data: Any, field: str) -> Any:
    for payload in _scalar_payloads(data):
        if field in payload and payload[field] is not None:
            return payload[field]
    return None


def _discover_candidates(data: Any) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for payload in _scalar_payloads(data):
        for key in _discover_numeric_field_keys(payload):
            if key not in seen:
                seen.add(key)
                candidates.append(key)
    return candidates


def _metrics_from_candidates(
    data: Any,
    candidates: list[str],
    labels: dict[str, str],
) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for field in candidates:
        value = _lookup_scalar_field(data, field)
        if value is None or isinstance(value, (dict, list, bool)):
            continue
        metrics.append(
            {
                "field": field,
                "value": value,
                "label": _humanize_value_field(field, labels),
            }
        )
    return metrics


def _list_count_metric(
    data: Any,
    *,
    route_info: dict[str, Any],
    labels: dict[str, str],
) -> dict[str, Any] | None:
    """Playbook/listagem sem escalar de negócio: KPI = quantidade de registros."""
    if not isinstance(data, dict):
        return None
    # Série temporal: KPI é o último ponto (tratado adiante), nunca a contagem de pontos.
    if isinstance(route_info, dict) and str(route_info.get("seriesField") or "").strip():
        return None
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    total = summary.get("total_records")
    if isinstance(total, bool) or not isinstance(total, (int, float)):
        rows = _list_from_data(data, route_info.get("tableFields") if isinstance(route_info, dict) else None)
        if not rows:
            return None
        total = len(rows)
    count_label = labels.get("total_records") or message("dataListCountLabel", "Quantidade")
    return {
        "field": "total_records",
        "value": total,
        "label": count_label,
    }


def _extract_kpi_metrics(
    data: Any,
    *,
    route_info: dict[str, Any],
    binding: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extrai métricas escalares; se valueFields do catálogo erram o payload, cai na discovery."""
    labels = _value_field_labels(route_info)
    catalog = _catalog_value_fields(route_info)
    metrics = _metrics_from_candidates(data, catalog, labels) if catalog else []
    if not metrics:
        metrics = _metrics_from_candidates(data, _discover_candidates(data), labels)
    if not metrics:
        count_metric = _list_count_metric(data, route_info=route_info, labels=labels)
        if count_metric is not None:
            metrics = [count_metric]

    selected = _binding_selected_fields(binding)
    if selected is None:
        return metrics
    wanted = {field: index for index, field in enumerate(selected)}
    filtered = [metric for metric in metrics if metric["field"] in wanted]
    filtered.sort(key=lambda metric: wanted.get(str(metric["field"]), 999))
    if filtered:
        return filtered
    # Seleção pediu campo inexistente no payload (ex.: coluna de linha) — mantém contagem.
    if len(metrics) == 1 and metrics[0].get("field") == "total_records":
        return metrics
    return filtered


def _extract_scalar_value(data: Any, value_fields: list[Any]) -> Any:
    if not isinstance(data, dict):
        return None
    keys = _iter_scalar_candidate_keys(value_fields)
    summary = data.get("summary")
    if isinstance(summary, dict):
        for key in keys:
            if key in summary and summary[key] is not None:
                return summary[key]
        if not value_fields:
            fallback = _first_numeric_like_field(summary)
            if fallback is not None:
                return fallback
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    if not value_fields:
        return _first_numeric_like_field(data)
    return None


def _extract_series(
    data: Any,
    series_field: str | None,
    *,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    return extract_series_points(data, series_field, branch=branch)

_TABLE_LIST_KEYS = (
    "items",
    "top_products",
    "branches",
    "ranking",
    "serie",
    "series",
    "points",
    "levelData",
    "statusData",
    "leadByLevel",
    "suites",
    "routes",
    "centros_custo",
    "fornecedores",
    "valores",
    "records",
    "results",
    "rows",
    "entries",
    "flow",
    "history",
    "transitions",
)

_SKIP_GENERIC_LIST_KEYS = frozenset(
    {
        "meta",
        "summary",
        "pagination",
        "success",
        "message",
        "errors",
        "error",
    }
)


def _list_from_data(data: Any, table_field: str | None) -> list[Any]:
    """Extrai linhas para tabela: lista bare, `items`/`tableField` e chaves list comuns."""
    data = unwrap_operational_data(data)
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    keys: list[str] = []
    if table_field and str(table_field).strip():
        keys.append(str(table_field).strip())
    for key in _TABLE_LIST_KEYS:
        if key not in keys:
            keys.append(key)

    for key in keys:
        raw = data.get(key)
        if isinstance(raw, list) and raw:
            return raw

    for key, raw in data.items():
        if key in _SKIP_GENERIC_LIST_KEYS:
            continue
        if isinstance(raw, list) and raw:
            return raw

    return []


def _build_table_columns(meta: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    fields = meta.get("fields")
    if isinstance(fields, list):
        columns: list[dict[str, str]] = []
        for field in fields:
            if not isinstance(field, dict):
                continue
            key = str(field.get("key") or field.get("name") or "").strip()
            if not key:
                continue
            columns.append(
                {
                    "key": key,
                    "label": str(field.get("label") or field.get("title") or key),
                }
            )
        if columns:
            return columns
    if rows:
        return [{"key": str(key), "label": str(key)} for key in rows[0].keys()]
    return []


def _series_to_table_rows(
    data: Any,
    series_field: str | None,
    *,
    branch: str | None = None,
    max_rows: int,
    value_label: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Converte pontos de série temporal em linhas tabulares (ex.: OTD/OEE)."""
    points = _extract_series(data, series_field, branch=branch)
    rows: list[dict[str, Any]] = []
    for point in points[:max_rows]:
        # Só as chaves declaradas nas colunas (periodo/value): evitar `label` duplicando
        # a coluna Período na derivação de colunas do frontend (união das chaves da linha).
        rows.append(
            {
                "periodo": point.get("label"),
                "value": point.get("value"),
            }
        )
    if not rows:
        return [], []
    columns = [
        {"key": "periodo", "label": "Período"},
        {"key": "value", "label": value_label or "Valor"},
    ]
    return rows, columns


def _scalar_object_as_table_rows(
    data: Any,
    *,
    max_rows: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Objeto só com escalares (health, inspector) → tabela campo/valor para preview TV."""
    data = unwrap_operational_data(data)
    if not isinstance(data, dict):
        return [], []
    rows: list[dict[str, Any]] = []
    for key, value in data.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, (dict, list)) or value is None or value == "":
            continue
        if _is_kpi_meta_field(key):
            continue
        rows.append({"campo": key, "valor": value})
        if len(rows) >= max_rows:
            break
    if not rows:
        return [], []
    columns = [
        {"key": "campo", "label": "Campo"},
        {"key": "valor", "label": "Valor"},
    ]
    return rows, columns


def _extract_table_rows(
    data: Any,
    table_field: str | None,
    max_rows: int,
    *,
    meta: dict[str, Any] | None = None,
    series_field: str | None = None,
    branch: str | None = None,
    value_label: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    # Rotas de série (seriesField no catálogo) têm a série como fonte canônica: normaliza
    # os pontos (label/valor por filial) antes do caminho de lista genérico e nunca vaza
    # metadados internos (granularity, truncated, sort_key…) como colunas ou campo/valor.
    # Exceção: quando os dados já são uma lista tabular (ex.: saída de uma transformação M
    # sobre a série), eles já são a tabela canônica — usa o caminho de lista genérico e não
    # tenta reextrair a série (que não existe mais na lista) e zerar a apresentação.
    already_tabular = isinstance(unwrap_operational_data(data), list)
    if series_field and str(series_field).strip() and not already_tabular:
        series_rows, series_columns = _series_to_table_rows(
            data,
            series_field,
            branch=branch,
            max_rows=max_rows,
            value_label=value_label,
        )
        return series_rows, series_columns

    raw_rows = _list_from_data(data, table_field)
    rows: list[dict[str, Any]] = []
    for row in raw_rows[:max_rows]:
        if isinstance(row, dict):
            rows.append(dict(row))
        elif isinstance(row, (str, int, float, bool)):
            rows.append({"value": row})
    columns = _build_table_columns(meta or {}, rows)
    if rows:
        return rows, columns

    series_rows, series_columns = _series_to_table_rows(
        data,
        series_field,
        branch=branch,
        max_rows=max_rows,
        value_label=value_label,
    )
    if series_rows:
        return series_rows, series_columns

    return _scalar_object_as_table_rows(data, max_rows=max_rows)


def _source_table_for_route(
    data: Any,
    route_info: dict[str, Any] | None,
    *,
    branch: str | None = None,
) -> dict[str, Any] | None:
    """Tabela-fonte canônica (`Fonte`) para transformações M.

    Rotas de série usam a série normalizada (periodo/value), a mesma que alimenta
    gráfico/tabela — nunca o fallback escalar campo/valor, que vazaria metadados
    internos (granularity, truncated) como se fossem os dados. Fora de séries,
    retorna None e o executor cai no coerce genérico do payload.
    """
    series_field = route_info.get("seriesField") if isinstance(route_info, dict) else None
    if not (series_field and str(series_field).strip()):
        return None
    points = _extract_series(data, series_field, branch=branch)
    return {
        "columns": ["periodo", "value"],
        "rows": [
            {"periodo": point.get("label"), "value": point.get("value")} for point in points
        ],
    }


def _scalar_as_chart_points(value: Any, label: str | None = None) -> list[dict[str, Any]]:
    if value is None:
        return []
    return [{"label": label, "value": value}]


def _rows_have_numeric_cells(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        if not isinstance(row, dict):
            continue
        for value in row.values():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                return True
    return False


def _meaningful_kpi_metrics(
    data: Any,
    *,
    route_info: dict[str, Any],
    binding: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = _extract_kpi_metrics(data, route_info=route_info, binding=binding)
    return [metric for metric in metrics if metric.get("field") != "total_records"]


def _infer_auto_display_mode(
    data: Any,
    route_info: dict[str, Any],
    meta: dict[str, Any],
    *,
    binding: dict[str, Any] | None = None,
) -> str:
    shape = str(meta.get("shape") or route_info.get("metaShape") or "scalar").lower()
    table_field = route_info.get("tableFields")
    binding_payload = binding if isinstance(binding, dict) else {}

    if shape in {"list", "paged_list", "hierarchy"} and _list_from_data(data, table_field):
        return "table"

    if route_info.get("tableFields") or shape == "paged_list":
        return "table"

    rows, _ = _extract_table_rows(
        data,
        table_field,
        5,
        meta=meta,
        series_field=route_info.get("seriesField"),
    )
    if rows:
        if not _meaningful_kpi_metrics(data, route_info=route_info, binding=binding_payload):
            return "table"
        if len(rows) > 1 and not _rows_have_numeric_cells(rows):
            return "table"

    if route_info.get("seriesField") or shape in {"playbook_report", "composite_analysis"}:
        points = _extract_series(data, route_info.get("seriesField"))
        if points:
            return "line_chart"
    return "kpi"


class ComunicadoDataEnrichmentService:
    """Resolve blocos data_* via api-delpi (allowlist + merge de filtros)."""

    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        gateway: DelpiOperationalGateway | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._gateway = gateway or DelpiOperationalGateway(catalog=self._catalog)

    def enrich_blocks(
        self,
        blocks: list[dict[str, Any]],
        *,
        cfg: dict[str, Any],
        authorization: str | None = None,
        playlist_defaults: dict[str, Any] | None = None,
        user: Any | None = None,
        force_refresh: bool = False,
        filter_overrides: dict[str, Any] | None = None,
        target_step_name: str | None = None,
        target_source_id: str | None = None,
        preview_options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        slide_filters = cfg.get("dataFilters") if isinstance(cfg.get("dataFilters"), dict) else {}
        # Preview isola um data_source em `blocks`, mas inputs vivem no slide (`cfg.blocks`).
        context_blocks = self._filter_context_blocks(blocks, cfg)
        schema_by_source_id: dict[str, dict[str, Any]] = {}
        slide_schemas: list[dict[str, Any]] = []
        for block in context_blocks:
            if str(block.get("type") or "") not in DATA_BLOCK_TYPES:
                continue
            binding = block.get("dataBinding")
            if not isinstance(binding, dict):
                continue
            operation_id = str(binding.get("operationId") or "").strip()
            route = self._catalog.get_route(operation_id) if operation_id else None
            schema = (
                route.get("paramSchema")
                if isinstance(route, dict) and isinstance(route.get("paramSchema"), dict)
                else {}
            )
            source_id = str(block.get("id") or "")
            if source_id:
                schema_by_source_id[source_id] = schema
            if schema:
                slide_schemas.append(schema)

        contributions = collect_input_filter_contributions(
            context_blocks,
            runtime_overrides=filter_overrides,
            schema_by_source_id=schema_by_source_id,
            slide_schemas=slide_schemas,
        )
        slide_input_contrib = (
            contributions.get("slide") if isinstance(contributions.get("slide"), dict) else {}
        )
        by_source = (
            contributions.get("bySourceId")
            if isinstance(contributions.get("bySourceId"), dict)
            else {}
        )

        graph = MQueryDependencyService().resolve(
            blocks,
            target_step_by_source={
                str(target_source_id or ""): target_step_name
            }
            if target_source_id and target_step_name
            else None,
        )
        if not graph.valid:
            first = next(
                item for item in graph.diagnostics if item.get("severity") == "error"
            )
            raise ValueError(str(first.get("message") or "Consulta M inválida."))
        query_bindings = graph.bindings()
        graph_nodes = {node.source_id: node for node in graph.nodes}

        # Autoriza toda consulta do DAG antes do primeiro fetch. Uma irmã não autorizada
        # jamais entra no ambiente de execução da consulta dependente.
        for source_id in graph.ordered_source_ids:
            node = graph_nodes[source_id]
            binding = node.block.get("dataBinding")
            operation_id = (
                str(binding.get("operationId") or "").strip()
                if isinstance(binding, dict)
                else ""
            )
            if not operation_id:
                continue
            route = self._catalog.get_route(operation_id)
            if not self._catalog.is_allowed(operation_id) or route is None:
                raise ValueError("Fonte de dados indisponível.")
            block_params = (
                binding.get("params")
                if isinstance(binding, dict) and isinstance(binding.get("params"), dict)
                else {}
            )
            source_contrib = (
                by_source.get(source_id)
                if isinstance(by_source.get(source_id), dict)
                else {}
            )
            merged = merge_data_params(
                playlist_defaults=playlist_defaults,
                slide_filters=slide_filters,
                block_params=block_params,
                input_overrides=merge_filter_layers(slide_input_contrib, source_contrib),
            )
            validate_data_route_branch(route, merged, user=user)

        # Dedupe in-request: mesmas operationId+params ⇒ um fetch nesta montagem.
        request_memo: dict[str, dict[str, Any]] = {}
        enrich_kwargs: dict[str, Any] = {
            "slide_filters": slide_filters,
            "playlist_defaults": playlist_defaults,
            "authorization": authorization,
            "user": user,
            "force_refresh": force_refresh,
            "request_memo": request_memo,
        }
        enriched: list[dict[str, Any]] = []
        source_blocks = {
            str(block.get("id") or ""): block
            for block in blocks
            if isinstance(block, dict) and str(block.get("type") or "") in DATA_BLOCK_TYPES
        }
        ordered_blocks = [
            source_blocks[source_id]
            for source_id in graph.ordered_source_ids
            if source_id in source_blocks
        ] + [
            block
            for block in blocks
            if not isinstance(block, dict)
            or str(block.get("id") or "") not in set(graph.ordered_source_ids)
        ]
        query_tables: dict[str, dict[str, Any]] = {}
        for block in ordered_blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type in DATA_BLOCK_TYPES:
                source_id = str(block.get("id") or "")
                source_contrib = by_source.get(source_id) if isinstance(by_source.get(source_id), dict) else {}
                # Inputs/runtime acima de dataBinding.params (preset relativo da fonte).
                input_overrides = merge_filter_layers(slide_input_contrib, source_contrib)
                enriched.append(
                    self._enrich_data_block(
                        block,
                        input_overrides=input_overrides,
                        sibling_tables=query_tables,
                        query_bindings=query_bindings,
                        target_step_name=(
                            target_step_name
                            if source_id == str(target_source_id or "")
                            else None
                        ),
                        preview_options=preview_options,
                        **enrich_kwargs,
                    )
                )
                resolved = enriched[-1].get("resolved")
                query_table = (
                    resolved.pop("_queryTable", None)
                    if isinstance(resolved, dict)
                    else None
                )
                if isinstance(query_table, dict):
                    query_tables[source_id] = query_table
                    node = graph_nodes.get(source_id)
                    if node is not None:
                        query_tables[node.query_name] = query_table
                continue
            if block_type in DATA_VIEW_BLOCK_TYPES:
                enriched.append(dict(block))
                continue
            if block_type == "input":
                enriched.append(
                    self._decorate_input_block(
                        block,
                        schema_by_source_id=schema_by_source_id,
                        slide_schemas=slide_schemas,
                    )
                )
                continue
            enriched.append(block)

        # Compatibilidade v1: o merge legado ainda endereça sourceId.
        sibling_tables = self._build_sibling_tables(enriched)
        if sibling_tables and any(self._transform_needs_siblings(block) for block in enriched):
            re_enriched: list[dict[str, Any]] = []
            for block in enriched:
                if not isinstance(block, dict) or not self._transform_needs_siblings(block):
                    re_enriched.append(block)
                    continue
                source_id = str(block.get("id") or "")
                source_contrib = by_source.get(source_id) if isinstance(by_source.get(source_id), dict) else {}
                input_overrides = merge_filter_layers(slide_input_contrib, source_contrib)
                siblings = {key: value for key, value in sibling_tables.items() if key != source_id}
                re_enriched.append(
                    self._enrich_data_block(
                        block,
                        input_overrides=input_overrides,
                        sibling_tables=siblings,
                        query_bindings=query_bindings,
                        **enrich_kwargs,
                    )
                )
            enriched = re_enriched
        by_id = {
            str(block.get("id") or ""): block
            for block in enriched
            if isinstance(block, dict) and str(block.get("id") or "")
        }
        restored = [
            by_id.get(str(block.get("id") or ""), block)
            if isinstance(block, dict)
            else block
            for block in blocks
        ]
        return self._link_view_blocks_to_sources(restored)

    @staticmethod
    def _transform_needs_siblings(block: dict[str, Any]) -> bool:
        if str(block.get("type") or "") != "data_source":
            return False
        normalized = normalize_data_transform(block.get("dataTransform"))
        steps = normalized.get("steps") if normalized else None
        if not steps:
            return False
        return any(str(step.get("op") or "") == "merge" for step in steps if isinstance(step, dict))

    @staticmethod
    def _build_sibling_tables(blocks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        tables: dict[str, dict[str, Any]] = {}
        for block in blocks:
            if not isinstance(block, dict) or str(block.get("type") or "") != "data_source":
                continue
            source_id = str(block.get("id") or "").strip()
            resolved = block.get("resolved")
            if not source_id or not isinstance(resolved, dict):
                continue
            data = resolved.get("data")
            _, _, table = apply_data_transform_to_payload(data, block.get("dataTransform"))
            if table is None:
                table = coerce_payload_to_table(data)
            if table is not None:
                tables[source_id] = table
        return tables

    @staticmethod
    def _filter_context_blocks(
        blocks: list[dict[str, Any]],
        cfg: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Blocos do slide para contribuições de input; fallback = lista enriquecida."""
        cfg_blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else None
        if cfg_blocks:
            return [block for block in cfg_blocks if isinstance(block, dict)]
        return [block for block in blocks if isinstance(block, dict)]

    def _decorate_input_block(
        self,
        block: dict[str, Any],
        *,
        schema_by_source_id: dict[str, dict[str, Any]],
        slide_schemas: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Anexa resolvedField (snapshot do paramSchema) para UI do kiosk sem catálogo no cliente."""
        from tv_app.application.services.comunicado_input_filters_service import (
            resolve_input_param_schema_field,
            resolve_input_target_scope,
        )

        result = dict(block)
        input_cfg = dict(block.get("input")) if isinstance(block.get("input"), dict) else {}
        param_key = str(input_cfg.get("paramKey") or "").strip()
        scope = resolve_input_target_scope(input_cfg)
        if scope == "slide":
            # Já só entra schema non-empty em slide_schemas; reforça filtro.
            schemas = [schema for schema in slide_schemas if isinstance(schema, dict) and schema]
        else:
            ids = [
                str(item).strip()
                for item in (input_cfg.get("targetSourceIds") or [])
                if str(item).strip()
            ]
            # Paridade editor: schemas vazios não entram na interseção.
            schemas = [
                schema_by_source_id[sid]
                for sid in ids
                if sid in schema_by_source_id
                and isinstance(schema_by_source_id[sid], dict)
                and schema_by_source_id[sid]
            ]
        field = resolve_input_param_schema_field(param_key, schemas) if param_key else None
        if field:
            input_cfg["resolvedField"] = field
            input_cfg["paramAvailable"] = True
        elif param_key:
            # paramKey ligado mas schema ausente no catálogo/enrich — libera controle texto
            # (UI kiosk não fica em "Parâmetro indisponível" por assimetria de schemas).
            label = str(input_cfg.get("label") or "").strip() or param_key
            input_cfg["resolvedField"] = {"type": "string", "label": label}
            input_cfg["paramAvailable"] = True
        else:
            input_cfg["paramAvailable"] = False
            input_cfg.pop("resolvedField", None)
        result["input"] = input_cfg
        return result

    @staticmethod
    def _link_view_blocks_to_sources(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        source_resolved: dict[str, dict[str, Any]] = {}
        for block in blocks:
            if str(block.get("type") or "") == "data_source":
                resolved = block.get("resolved")
                if isinstance(resolved, dict):
                    source_resolved[str(block.get("id") or "")] = resolved
        if not source_resolved:
            return blocks
        linked: list[dict[str, Any]] = []
        for block in blocks:
            block_type = str(block.get("type") or "")
            if block_type not in DATA_VIEW_BLOCK_TYPES and block_type not in TEXT_DATA_BOUND_BLOCK_TYPES:
                linked.append(block)
                continue
            source_id = str(block.get("dataSourceId") or "").strip()
            if not source_id or source_id not in source_resolved:
                linked.append(block)
                continue
            merged = dict(block)
            if block_type in DATA_VIEW_BLOCK_TYPES:
                merged["resolved"] = apply_view_projection_to_resolved(
                    source_resolved[source_id],
                    block,
                )
            else:
                merged["resolved"] = dict(source_resolved[source_id])
                merged["serverTextProjectionApplied"] = True
            linked.append(merged)
        return linked

    def _resolve_presentation(
        self,
        *,
        display_mode: str,
        data: Any,
        route_info: dict[str, Any],
        meta: dict[str, Any],
        binding: dict[str, Any],
        merged_params: dict[str, Any],
        label: str | None,
    ) -> dict[str, Any]:
        mode = normalize_display_mode(display_mode)
        if mode == "auto":
            mode = _infer_auto_display_mode(
                data,
                route_info,
                meta,
                binding=binding,
            )

        value_fields = _value_fields_for_binding(route_info, binding)
        metrics = _extract_kpi_metrics(data, route_info=route_info, binding=binding)
        branch = merged_params.get("branch")
        branch_str = str(branch).strip() if branch else None
        max_rows = _resolve_table_max_rows(binding, route_info)

        if mode == "kpi":
            primary = metrics[0] if metrics else None
            scalar = primary["value"] if primary else _extract_scalar_value(data, value_fields)
            if scalar is None:
                points = _extract_series(data, route_info.get("seriesField"), branch=branch_str)
                if points:
                    scalar = points[-1].get("value")
            kpi_label = primary["label"] if primary else label
            resolved: dict[str, Any] = {
                "kpi": {"value": scalar, "label": kpi_label},
                "kpiMetrics": metrics,
            }
            # Relatório com lista: anexa tabela para preview/TV poderem cair no ranking
            # quando o summary só tem metadados ou o KPI summary não cobre o conteúdo.
            rows, columns = _extract_table_rows(
                data,
                route_info.get("tableFields"),
                max_rows,
                meta=meta,
                series_field=route_info.get("seriesField"),
                branch=branch_str,
                value_label=label,
            )
            if rows:
                resolved["table"] = {"rows": rows, "columns": columns}
            return resolved

        if mode in {"line_chart", "bar_chart"}:
            points = _extract_series(data, route_info.get("seriesField"), branch=branch_str)
            if not points:
                if len(metrics) > 1:
                    points = [
                        {"label": metric["label"], "value": metric["value"]} for metric in metrics
                    ]
                else:
                    scalar = (
                        metrics[0]["value"]
                        if metrics
                        else _extract_scalar_value(data, value_fields)
                    )
                    points = _scalar_as_chart_points(scalar, label)
            chart_type = "bar" if mode == "bar_chart" or len(metrics) > 1 else "line"
            if mode == "line_chart" and len(metrics) <= 1:
                chart_type = "line"
            return {
                "chart": {"points": points, "chartType": chart_type},
                "kpiMetrics": metrics,
            }

        rows, columns = _extract_table_rows(
            data,
            route_info.get("tableFields"),
            max_rows,
            meta=meta,
            series_field=route_info.get("seriesField"),
            branch=branch_str,
            value_label=label,
        )
        if not rows:
            if metrics:
                rows = [
                    {
                        "metric": metric["label"],
                        "field": metric["field"],
                        "value": metric["value"],
                    }
                    for metric in metrics
                ]
                columns = [
                    {"key": "metric", "label": "Indicador"},
                    {"key": "value", "label": "Valor"},
                ]
            else:
                scalar = _extract_scalar_value(data, value_fields)
                if scalar is not None:
                    row: dict[str, Any] = {}
                    field_key = value_fields[0] if value_fields else "value"
                    row[field_key] = scalar
                    if label:
                        row["label"] = label
                    rows = [row]
                    columns = _build_table_columns(meta, rows)
        return {
            "table": {"rows": rows, "columns": columns},
            "kpiMetrics": metrics,
        }

    def _enrich_data_block(
        self,
        block: dict[str, Any],
        *,
        slide_filters: dict[str, Any],
        playlist_defaults: dict[str, Any] | None,
        authorization: str | None,
        user: Any | None,
        force_refresh: bool = False,
        request_memo: dict[str, dict[str, Any]] | None = None,
        input_overrides: dict[str, Any] | None = None,
        sibling_tables: dict[str, dict[str, Any]] | None = None,
        query_bindings: tuple[dict[str, Any], ...] = (),
        target_step_name: str | None = None,
        preview_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = dict(block)
        binding = block.get("dataBinding")
        if not isinstance(binding, dict):
            result["resolved"] = {"error": message("dataIndicatorUnavailable", "Indicador indisponível")}
            return result

        operation_id = str(binding.get("operationId") or "").strip()
        if not self._catalog.is_allowed(operation_id):
            result["resolved"] = {"error": message("dataIndicatorUnavailable", "Indicador indisponível")}
            return result

        block_params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
        merged_params = merge_data_params(
            playlist_defaults=playlist_defaults,
            slide_filters=slide_filters,
            block_params=block_params,
            input_overrides=input_overrides,
        )
        merged_params = _apply_incremental_pagination_defaults(
            merged_params,
            self._catalog.get_route(operation_id),
        )

        route = self._catalog.get_route(operation_id)
        try:
            validate_data_route_branch(route, merged_params, user=user)
        except ValueError as exc:
            result["resolved"] = {"error": str(exc)}
            return result

        try:
            payload = self._fetch_cached(
                operation_id,
                merged_params,
                authorization,
                user=user,
                service_context="user-preview" if user is not None else "presentation-service",
                force_refresh=force_refresh,
                request_memo=request_memo,
            )
        except Exception as exc:  # noqa: BLE001
            result["resolved"] = resolve_data_fetch_error(exc)
            return result

        route_info = payload.get("route") or {}
        cache_hit = bool(payload.get("_tvCacheHit"))
        data = payload.get("data")
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        display_mode = str(binding.get("displayMode") or "kpi")
        block_type = str(block.get("type") or "")

        presentation_data = data
        server_transform_applied = False
        transform_metadata: dict[str, Any] | None = None
        transform_result: dict[str, Any] | None = None
        if block_type == "data_source":
            options = preview_options if isinstance(preview_options, dict) else {}
            deadline_ms = min(
                max(1, int(options.get("deadlineMs") or m_query_setting("previewDeadlineMaxMs", 3000))),
                int(m_query_setting("previewDeadlineMaxMs", 3000)),
            )
            branch = merged_params.get("branch") if isinstance(merged_params, dict) else None
            branch_str = str(branch).strip() if branch else None
            transform_result = apply_data_transform_to_payload_result(
                data,
                block.get("dataTransform"),
                sibling_tables=sibling_tables,
                query_bindings=query_bindings,
                target_step_name=target_step_name,
                culture=str(m_query_setting("defaultCulture", "pt-BR")),
                deadline_ms=deadline_ms,
                source_table=_source_table_for_route(data, route_info, branch=branch_str),
            )
            transformed = transform_result["data"]
            server_transform_applied = bool(transform_result["applied"])
            transform_metadata = transform_result["transform"]
            if server_transform_applied:
                presentation_data = transformed
            elif transform_result.get("failed"):
                presentation_data = []

        resolved: dict[str, Any] = {
            "meta": meta,
            "data": data,
            "error": None,
            "displayMode": normalize_display_mode(display_mode),
            "label": binding.get("label") or route_info.get("label"),
        }
        if server_transform_applied:
            resolved["serverTransformApplied"] = True
        if transform_metadata and transform_metadata.get("version") is not None:
            resolved["dataTransform"] = transform_metadata
        if isinstance(transform_result, dict) and transform_result.get("failed"):
            errors = transform_result.get("runtimeErrors") or {}
            sample = errors.get("sample") if isinstance(errors, dict) else None
            first_error = sample[0] if isinstance(sample, list) and sample else {}
            resolved["error"] = str(
                first_error.get("message") or "A transformação M falhou."
            )

        if block_type == "data_source":
            for mode in ("kpi", "line_chart", "table"):
                resolved.update(
                    self._resolve_presentation(
                        display_mode=mode,
                        data=presentation_data,
                        route_info=route_info,
                        meta=meta,
                        binding=binding,
                        merged_params=merged_params,
                        label=resolved.get("label"),
                    )
                )
            query_table = (
                None
                if isinstance(transform_result, dict) and transform_result.get("failed")
                else (
                    transform_result.get("table")
                    if isinstance(transform_result, dict)
                    else coerce_payload_to_table(data)
                )
            )
            if isinstance(query_table, dict):
                resolved["_queryTable"] = query_table
            if (
                isinstance(transform_result, dict)
                and transform_metadata
                and transform_metadata.get("version") == 2
            ):
                max_rows = min(
                    max(1, int(options.get("maxRows") or m_query_setting("maxPreviewRows", 200))),
                    int(m_query_setting("maxPreviewRows", 200)),
                )
                max_columns = int(m_query_setting("maxPreviewColumns", 200))
                columns = list(query_table.get("columns") or [])[:max_columns] if isinstance(query_table, dict) else []
                available_rows = len(query_table.get("rows") or []) if isinstance(query_table, dict) else 0
                max_cells = int(m_query_setting("maxPreviewCells", 40000))
                max_rows_by_cells = max(1, max_cells // max(1, len(columns)))
                returned_rows = min(max_rows, max_rows_by_cells, available_rows)
                rows = [
                    {column: row.get(column) for column in columns}
                    for row in (query_table.get("rows") or [])[:returned_rows]
                ] if isinstance(query_table, dict) else []
                resolved["query"] = {
                    "profile": "m-delpi-v1",
                    "scriptHash": transform_result.get("scriptHash"),
                    "selectedStepName": transform_result.get("selectedStepName"),
                    "diagnostics": transform_metadata.get("diagnostics") or [],
                    "runtimeErrors": transform_result.get("runtimeErrors")
                    or {"count": 0, "sample": []},
                    "executionMs": int(transform_result.get("executionMs") or 0),
                    "stepMetrics": transform_result.get("stepMetrics") or [],
                    "explainPlan": (
                        transform_result.get("explainPlan")
                        if bool(m_query_setting("explainPlanEnabled", False))
                        else None
                    ),
                    "cacheHit": cache_hit,
                }
                resolved["preview"] = {
                    "columns": [
                        item
                        for item in (transform_result.get("schema") or [])
                        if isinstance(item, dict) and item.get("key") in columns
                    ],
                    # Schema imutável da Fonte, anterior a rename/remove/select.
                    # O compilador semântico não pode reutilizar `columns`, que
                    # representa a saída da etapa selecionada.
                    "sourceColumns": transform_result.get("sourceSchema") or [],
                    "rows": rows,
                    "returnedRows": returned_rows,
                    "availableRows": available_rows,
                    "truncated": returned_rows < available_rows
                    or (
                        isinstance(query_table, dict)
                        and len(columns) < len(query_table.get("columns") or [])
                    ),
                    "isSample": returned_rows < available_rows,
                }
                try:
                    column_profile = profile_table(
                        query_table,
                        requested=bool(options.get("includeColumnProfile")),
                        deadline_ms=deadline_ms,
                    )
                except TimeoutError:
                    resolved["query"]["profiling"] = {
                        "status": "timeout",
                        "code": "m.profile_timeout",
                    }
                else:
                    if column_profile is not None:
                        resolved["preview"]["columnProfile"] = column_profile
                        resolved["query"]["profiling"] = {"status": "completed"}
                SafeTelemetry(
                    "m.preview.completed",
                    int(transform_result.get("executionMs") or 0),
                    "source-hit" if cache_hit else "source-miss",
                    rows=returned_rows,
                    columns=len(columns),
                    errors=int(
                        (transform_result.get("runtimeErrors") or {}).get("count", 0)
                    ),
                    artifact_hash=str(transform_result.get("scriptHash") or ""),
                ).emit()
        else:
            resolved.update(
                self._resolve_presentation(
                    display_mode=display_mode,
                    data=data,
                    route_info=route_info,
                    meta=meta,
                    binding=binding,
                    merged_params=merged_params,
                    label=resolved.get("label"),
                )
            )

        result["resolved"] = resolved
        return result

    def _fetch_cached(
        self,
        operation_id: str,
        params: dict[str, Any],
        authorization: str | None,
        *,
        user: Any | None = None,
        service_context: str | None = None,
        force_refresh: bool = False,
        request_memo: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        cache_key = _build_data_cache_key(
            operation_id=operation_id,
            params=params,
            authorization=authorization,
            user=user,
            service_context=service_context,
        )
        if request_memo is not None and cache_key in request_memo:
            return {**request_memo[cache_key], "_tvCacheHit": True}
        if not force_refresh:
            cached = _data_block_cache.get(cache_key)
            if cached is not None:
                if request_memo is not None:
                    request_memo[cache_key] = cached
                return {**cached, "_tvCacheHit": True}
        payload = self._gateway.fetch_by_operation_id(
            operation_id,
            params=params,
            authorization=authorization,
        )
        if not payload.get("error"):
            _data_block_cache.set(cache_key, payload)
        if request_memo is not None:
            request_memo[cache_key] = payload
        return payload


def reset_comunicado_data_block_cache() -> None:
    _data_block_cache.invalidate_all()
    reset_phase7_caches()
