"""Invariante: campos projetáveis do catálogo TV devem existir no contrato de
resposta autoritativo da api-delpi (campos emitidos pelo producer + meta.fields),
a menos que sejam explicitamente classificados como campos de apresentação
pertencentes ao consumidor.

Wave 1 do freeze semântico de `value`: as 8 operações com decisão FIX_CATALOG
no inventário `docs/07-api-delpi/inventory-value-field` não podem anunciar
`value` (nem nomes derivados de operationId que não existem no payload). Cada
campo declarado em `valueFields`/`projectableFields` deve resolver
estruturalmente contra o schema emitido — incluindo caminhos aninhados
(`summary.*`, unwrap de `item`, e caminhos relativos à linha de `seriesField`,
ex.: `metrics.rework_cost_pct`).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTES_PATH = REPO_ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
INVENTORY_PATH = (
    REPO_ROOT
    / "docs"
    / "07-api-delpi"
    / "inventory-value-field"
    / "value_field_consumer_inventory.json"
)

# Campos de meta SI anexados por enrich_dashboard_metric / attach_goal_fields
# (api-delpi dashboard_goals_service._flatten_goal).
_SI_GOAL_FIELDS = {
    "goal",
    "goal_label",
    "goal_value",
    "comparable_goal",
    "reference_goal",
    "target",
    "goal_periodicity",
    "goal_mode",
    "goal_aggregation",
    "goal_period_kind",
    "goal_period_partial",
    "goal_scope_branch",
    "goal_scope_label",
    "goal_scope_hint",
    "scope_type",
    "performance_direction",
    "indicator_id",
    "indicator_name",
    "value_unit",
    "value_prefix",
    "has_goal",
    "start_date",
    "end_date",
}

# Schemas de resposta autoritativos (nível `data` do envelope api-delpi).
# Estrutura: dict = objeto; [dict] = lista cujas linhas têm o schema do dict;
# True = campo escalar/leaf. Construído a partir do código do producer
# (use case + enrichment + meta.fields) — ver inventário para evidências.
RESPONSE_SCHEMAS: dict[str, dict] = {
    # use_case: {branch, start_date, end_date, rol}; enrichment adiciona
    # rol_target_pct + target + campos de meta SI.
    "get_new_business_rol_target_pct": {
        "branch": True,
        "start_date": True,
        "end_date": True,
        "rol": True,
        "rol_target_pct": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    "get_weg_rol_target_pct": {
        "branch": True,
        "start_date": True,
        "end_date": True,
        "rol": True,
        "rol_target_pct": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    # use_case: {ebitda_value, rol, ebitda_over_rol_pct} (+ goal fields).
    "get_financial_ebitda_pct": {
        "ebitda_value": True,
        "rol": True,
        "ebitda_over_rol_pct": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    "get_financial_fixed_cost_pct": {
        "fixed_cost_value": True,
        "rol": True,
        "fixed_cost_over_rol_pct": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    # rota devolve {"item": {...}} — unwrap_operational_data desembrulha item.
    "get_dashboard_department_idd": {
        "item": {
            "department_id": True,
            "department_name": True,
            "score": True,
            "classification": True,
            "contribution": True,
            "variation": True,
            "partial_success": True,
        }
    },
    # use_case: summary{...} + top_products[]; enrichment injeta metas em summary
    # (summary_key="summary").
    "get_supplies_stock_value": {
        "branch": True,
        "location": True,
        "summary": {
            "total_stock_value": True,
            "total_stock_quantity": True,
            "total_records": True,
            "total_products": True,
            "total_locations": True,
            "average_unit_value": True,
            **{k: True for k in _SI_GOAL_FIELDS},
        },
        "by_branch": [{"branch": True}],
        "by_location": [{"location": True}],
        "top_products": [{"product_code": True, "product_name": True}],
    },
    # GetQualityScalarSeriesUseCase.to_dict: {metric, granularity, truncated,
    # points:[{periodo, sort_key, start_date, end_date, metrics:{<metric>}}]}.
    "get_quality_scrap_cost_pct_series": {
        "metric": True,
        "granularity": True,
        "truncated": True,
        "points": [
            {
                "periodo": True,
                "sort_key": True,
                "start_date": True,
                "end_date": True,
                "metrics": {"scrap_cost_pct": True},
            }
        ],
    },
    "get_quality_rework_cost_pct_series": {
        "metric": True,
        "granularity": True,
        "truncated": True,
        "points": [
            {
                "periodo": True,
                "sort_key": True,
                "start_date": True,
                "end_date": True,
                "metrics": {"rework_cost_pct": True},
            }
        ],
    },
    # Sibling scalar das séries — sanity de que o schema cobre irmãos reais.
    # Wave 3 provou via runtime: `value` NÃO é emitido por esta rota
    # (alias era catalog-only; binding resolvia por fallback).
    "get_quality_scrap_cost_pct": {
        "scrap_cost": True,
        "rol": True,
        "scrap_cost_pct": True,
        "occurrences": True,
        "records_without_cost": True,
        "quantity": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    # Parity real: `value` é emitido espelhando o campo primário
    # (attach_quality_kpi_parity / literal no use case).
    "get_kaizen_summary": {
        "total_savings": True,
        "total_kaizens": True,
        "value": True,
        "ideas_goal": {"total_kaizens": True, "value": True},
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    "get_ppm_external_summary": {
        "ppm": True,
        "value": True,
        "total_produzido_un": True,
        "total_produzido_milheiro": True,
        "total_devolvido_un": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    "get_ppm_internal_summary": {
        "ppm": True,
        "value": True,
        "total_produzido_un": True,
        "total_produzido_milheiro": True,
        "total_devolvido_un": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    "get_nonconformity_streak": {
        "current_days_without_nc": True,
        "record_days_without_nc": True,
        "nc_count": True,
        "last_nc_date": True,
        "type": True,
        "branch": True,
        "product_prefix": True,
        "value": True,
    },
    "get_audit_5s_summary": {
        "average_score": True,
        "value": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    # Wave 4 — ops cujo `value` era catalog-only (producer nunca emite):
    # schemas mínimos com o campo semântico canônico.
    "get_sales_conversion_rate": {"sales_conversion_rate_pct": True, "qtd_proposals": True, "qtd_won": True},
    "get_new_business_rol_pct": {"new_business_rol_pct": True, "rol": True},
    "get_new_clients_rol_pct": {"new_clients_rol_pct": True, "rol": True},
    "get_depreciation_pct": {"depreciation_pct": True},
    "get_direct_labor_cost_pct": {"direct_labor_cost_pct": True},
    "get_on_time_delivery_pct": {"on_time_delivery_pct": True},
    "get_overall_equipment_effectiveness_pct": {
        "overall_equipment_effectiveness_pct": True,
    },
    "get_production_cost_pct": {"production_cost_pct": True},
    "get_refugos_scrap_cost_pct": {
        "scrap_cost_pct": True,
        "scrap_cost": True,
        "rol": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
    "get_retrabalhos_rework_cost_pct": {
        "rework_cost_pct": True,
        "rework_cost": True,
        "rol": True,
        **{k: True for k in _SI_GOAL_FIELDS},
    },
}

# Wave 4 — ops cujo `value` era catalog-only: catálogo declara só o campo
# semântico emitido. (op -> campo canônico)
WAVE4_CATALOG_ONLY_CLEANED: dict[str, str] = {
    "get_sales_conversion_rate": "sales_conversion_rate_pct",
    "get_new_business_rol_pct": "new_business_rol_pct",
    "get_new_clients_rol_pct": "new_clients_rol_pct",
    "get_depreciation_pct": "depreciation_pct",
    "get_direct_labor_cost_pct": "direct_labor_cost_pct",
    "get_on_time_delivery_pct": "on_time_delivery_pct",
    "get_overall_equipment_effectiveness_pct": "overall_equipment_effectiveness_pct",
    "get_production_cost_pct": "production_cost_pct",
    "get_refugos_scrap_cost_pct": "scrap_cost_pct",
    "get_retrabalhos_rework_cost_pct": "rework_cost_pct",
}

# `value` segue declarável APENAS onde é campo de domínio legítimo (rankings).
# Wave 6A: parity ops emitiam `value` como alias — agora documentado em
# deprecatedFields, fora de valueFields/projectableFields.
WAVE4_VALUE_STILL_DECLARED = frozenset(
    {
        "get_refugos_rankings",
    }
)

# Wave 2 — SI scalar contract (strategic-indicators-api
# get_dashboard_indicator_metric_use_case): shape compartilhado das 72 rotas
# get_si_indicator_*_{meta,realized}. Meta emite `comparable_goal`/`goal_value`/
# `reference_goal` + alias de compatibilidade `value`; realized emite `value`
# como escalar canônico.
_SI_SCALAR_BASE = {
    "indicator_id": True,
    "source_key": True,
    "name": True,
    "department_id": True,
    "value": True,
    "has_value": True,
    "value_unit": True,
    "value_prefix": True,
    "value_suffix": True,
    "value_decimals": True,
    "partial_success": True,
}
_SI_META_RESPONSE_SCHEMA = {
    **_SI_SCALAR_BASE,
    "comparable_goal": True,
    "goal_value": True,
    "reference_goal": True,
    "goal_label": True,
    "goals": {},
    # Wave 6A: `value` é DEPRECATED_COMPATIBILITY_ALIAS — ainda emitido
    # ("value": comparable_goal), fora do catalogo projetavel.
    "value": True,
}
_SI_REALIZED_RESPONSE_SCHEMA = {
    **_SI_SCALAR_BASE,
    "realized": {},
    "score": True,
}
_SI_META_GOAL_TRIAD = ["comparable_goal", "goal_value", "reference_goal"]


def _si_routes(routes: dict[str, dict], kind: str) -> dict[str, dict]:
    return {
        op: r
        for op, r in routes.items()
        if op.startswith("get_si_indicator_") and op.endswith(f"_{kind}")
    }

# Campos de apresentação pertencentes ao consumidor, classificados
# explicitamente no freeze (ex.: `value` legítimo emitido como alias canônico
# SI realizado — fora do escopo Wave 1). Vazio: nesta wave todo campo declarado
# deve existir no schema de resposta.
CONSUMER_OWNED_PRESENTATION_FIELDS: dict[str, frozenset[str]] = {}

# Nomes legados removidos pelo Wave 1 — nunca devem voltar ao catálogo.
_STALE_FIELD_NAMES = frozenset(
    {
        "value",
        "stockValue",
        "idd",
        "new_business_rol_target_pct",
        "weg_rol_target_pct",
        "financial_ebitda_pct",
        "financial_fixed_cost_pct",
        "quality_scrap_cost_pct_series",
        "quality_rework_cost_pct_series",
    }
)


def _load_routes() -> dict[str, dict]:
    payload = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    return {
        str(r["operationId"]): r
        for r in payload.get("routes") or []
        if isinstance(r, dict) and r.get("operationId")
    }


def _load_fix_catalog_ops() -> set[str]:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return {
        r["operationId"]
        for r in inventory.get("rows") or []
        if r.get("decision") == "FIX_CATALOG"
    }


def _resolve_path(schema: object, parts: list[str]) -> bool:
    """Resolve um caminho pontilhado dentro do schema (`True` = leaf)."""
    node = schema
    for part in parts:
        if isinstance(node, list) and node and isinstance(node[0], dict):
            node = node[0]
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    if isinstance(node, list):
        return bool(node)
    return True


def field_resolves_in_response(field: str, data_schema: dict, series_field: str | None) -> bool:
    """Replica a semântica de resolução do runtime TV:

    - caminho pontilhado a partir da raiz de `data` (ex.: `summary.total`);
    - chave plana sondada dentro de `data.summary` (_extract_scalar_value);
    - chave plana dentro de `data.item` (ponte `unwrap_operational_data`);
    - caminho relativo à linha de `seriesField` (ex.: `metrics.rework_cost_pct`
      em `points[]`) — convenção das rotas de série (vf = campos por ponto).
    """
    parts = [p for p in str(field or "").split(".") if p]
    if not parts:
        return False
    if _resolve_path(data_schema, parts):
        return True
    for probe_key in ("summary", "item"):
        probe = data_schema.get(probe_key)
        if isinstance(probe, dict) and _resolve_path(probe, parts):
            return True
    if series_field:
        rows = data_schema.get(series_field)
        if isinstance(rows, list) and rows and _resolve_path(rows[0], parts):
            return True
    return False


def _declared_fields(route: dict) -> list[str]:
    fields = [str(f) for f in (route.get("valueFields") or [])]
    fields += [
        str(p.get("name"))
        for p in (route.get("projectableFields") or [])
        if isinstance(p, dict) and p.get("name")
    ]
    return fields


def test_fix_catalog_ops_exist_in_inventory_and_catalog() -> None:
    routes = _load_routes()
    fix_ops = _load_fix_catalog_ops()
    assert fix_ops == {
        "get_new_business_rol_target_pct",
        "get_weg_rol_target_pct",
        "get_financial_ebitda_pct",
        "get_financial_fixed_cost_pct",
        "get_dashboard_department_idd",
        "get_supplies_stock_value",
        "get_quality_rework_cost_pct_series",
        "get_quality_scrap_cost_pct_series",
    }
    assert fix_ops <= set(routes)
    assert fix_ops <= set(RESPONSE_SCHEMAS)


def test_fix_catalog_ops_do_not_advertise_stale_fields() -> None:
    routes = _load_routes()
    for op in sorted(_load_fix_catalog_ops()):
        route = routes[op]
        declared = set(_declared_fields(route))
        stale = declared & _STALE_FIELD_NAMES
        assert not stale, f"{op} still advertises nonexistent fields: {stale}"


def test_fix_catalog_fields_resolve_against_response_schema() -> None:
    routes = _load_routes()
    for op in sorted(_load_fix_catalog_ops()):
        route = routes[op]
        schema = RESPONSE_SCHEMAS[op]
        series_field = route.get("seriesField")
        consumer_owned = CONSUMER_OWNED_PRESENTATION_FIELDS.get(op, frozenset())
        declared = [f for f in _declared_fields(route) if f not in consumer_owned]
        assert declared, f"{op} declares no projectable field"
        for field in declared:
            assert field_resolves_in_response(field, schema, series_field), (
                f"{op}: catalog field {field!r} absent from emitted response schema"
            )


def test_quality_loss_series_declare_series_collection_and_nested_metric() -> None:
    routes = _load_routes()
    for op, metric_path in (
        ("get_quality_scrap_cost_pct_series", "metrics.scrap_cost_pct"),
        ("get_quality_rework_cost_pct_series", "metrics.rework_cost_pct"),
    ):
        route = routes[op]
        assert route.get("seriesField") == "points", op
        assert metric_path in (route.get("valueFields") or []), op


def test_resolver_positive_nested_and_row_relative_paths() -> None:
    # nested document path
    assert field_resolves_in_response(
        "total_stock_value", RESPONSE_SCHEMAS["get_supplies_stock_value"], None
    )
    assert field_resolves_in_response(
        "summary.total_stock_value", RESPONSE_SCHEMAS["get_supplies_stock_value"], None
    )
    # item bridge
    assert field_resolves_in_response(
        "score", RESPONSE_SCHEMAS["get_dashboard_department_idd"], None
    )
    # row-relative dotted path under seriesField
    assert field_resolves_in_response(
        "metrics.rework_cost_pct",
        RESPONSE_SCHEMAS["get_quality_rework_cost_pct_series"],
        "points",
    )


def test_resolver_sibling_keeps_legitimate_value() -> None:
    """Irmão (parity real): `value` é emitido espelhando o campo primário."""
    schema = RESPONSE_SCHEMAS["get_nonconformity_streak"]
    assert field_resolves_in_response("value", schema, None)
    assert field_resolves_in_response("current_days_without_nc", schema, None)
    # `value` não existe no payload do scalar de refugo (Wave 3, runtime prod).
    schema_no_value = RESPONSE_SCHEMAS["get_quality_scrap_cost_pct"]
    assert field_resolves_in_response("scrap_cost_pct", schema_no_value, None)
    assert not field_resolves_in_response("value", schema_no_value, None)


def test_resolver_negative_cases() -> None:
    # `value` não existe nos payloads das 8 ops corrigidas
    for op in (
        "get_weg_rol_target_pct",
        "get_dashboard_department_idd",
        "get_supplies_stock_value",
        "get_quality_scrap_cost_pct_series",
    ):
        schema = RESPONSE_SCHEMAS[op]
        series_field = "points" if op.endswith("_series") else None
        assert not field_resolves_in_response("value", schema, series_field), op
    # nomes derivados do operationId que nunca existiram
    assert not field_resolves_in_response(
        "weg_rol_target_pct", RESPONSE_SCHEMAS["get_weg_rol_target_pct"], None
    )
    assert not field_resolves_in_response(
        "stockValue", RESPONSE_SCHEMAS["get_supplies_stock_value"], None
    )
    # path de linha de série não resolve em rota escalar
    assert not field_resolves_in_response(
        "metrics.rework_cost_pct", RESPONSE_SCHEMAS["get_quality_scrap_cost_pct"], None
    )
    # métrica de outra operação não resolve
    assert not field_resolves_in_response(
        "metrics.rework_cost_pct",
        RESPONSE_SCHEMAS["get_quality_scrap_cost_pct_series"],
        "points",
    )


def test_si_meta_routes_project_comparable_goal_not_value() -> None:
    """Wave 2: toda rota get_si_indicator_*_meta prefere a tríade de metas;
    `value` permanece emitido pelo producer como alias, mas não é anunciado."""
    routes = _load_routes()
    metas = _si_routes(routes, "meta")
    assert len(metas) == 36
    for op, route in metas.items():
        declared = _declared_fields(route)
        for field in declared:
            assert field_resolves_in_response(
                field, _SI_META_RESPONSE_SCHEMA, route.get("seriesField")
            ), f"{op}: catalog field {field!r} absent from SI meta response schema"
        assert declared[:3] == _SI_META_GOAL_TRIAD, (
            f"{op}: meta must prefer comparable_goal triad, got {declared[:3]}"
        )
        assert "value" not in declared, f"{op} still advertises value"


def test_si_realized_routes_keep_value_as_canonical() -> None:
    """Sibling guard: realized mantém `value` (escalar canônico do producer)."""
    routes = _load_routes()
    realized = _si_routes(routes, "realized")
    assert len(realized) == 36
    for op, route in realized.items():
        declared = _declared_fields(route)
        assert "value" in declared, f"{op}: realized must keep `value`"
        for field in declared:
            assert field_resolves_in_response(
                field, _SI_REALIZED_RESPONSE_SCHEMA, route.get("seriesField")
            ), f"{op}: catalog field {field!r} absent from SI realized schema"


def test_wave4_catalog_only_value_removed_from_cleaned_ops() -> None:
    """Wave 4: ops cujo `value` era catalog-only (producer não emite, zero
    consumers persistidos) declaram somente o campo semântico."""
    routes = _load_routes()
    assert set(WAVE4_CATALOG_ONLY_CLEANED) <= set(routes)
    for op, semantic in WAVE4_CATALOG_ONLY_CLEANED.items():
        declared = _declared_fields(routes[op])
        assert "value" not in declared, f"{op} still advertises catalog-only value"
        assert semantic in declared, f"{op} lost semantic field {semantic!r}"
        # campo semântico deve existir no schema de resposta do producer
        assert field_resolves_in_response(
            semantic, RESPONSE_SCHEMAS[op], routes[op].get("seriesField")
        ), f"{op}: {semantic!r} absent from emitted response schema"


def test_wave4_emitted_aliases_and_domain_value_keep_declaration() -> None:
    """Keepers: `value` realmente emitido (parity) ou valor de domínio
    legítimo permanece declarado — não removido nesta wave."""
    routes = _load_routes()
    for op in sorted(WAVE4_VALUE_STILL_DECLARED):
        assert "value" in _declared_fields(routes[op]), (
            f"{op}: emitted/legitimate `value` must stay declared"
        )


def test_wave4_heuristic_no_longer_appends_value() -> None:
    """Fonte canônica: infer_value_fields não deve reinjetar `value` em
    operationIds _pct futuros."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen_tv_routes", REPO_ROOT / "scripts" / "generate_tv_data_routes_from_openapi.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fields = mod.infer_value_fields("get_some_new_metric_pct")
    assert "value" not in fields
    assert fields == ["some_new_metric_pct"]


# Wave 5 — aliases camelCase catalog-only: producers api-delpi nunca emitem
# otdPct/oeePct; zero consumers persistidos/codigo. (op -> alias -> canonico)
WAVE5_CAMELCASE_ALIASES: dict[str, tuple[str, str]] = {
    "get_on_time_delivery_pct": ("otdPct", "on_time_delivery_pct"),
    "get_overall_equipment_effectiveness_pct": (
        "oeePct",
        "overall_equipment_effectiveness_pct",
    ),
}


def test_wave5_camelcase_aliases_removed_from_catalog() -> None:
    """Wave 5: aliases camelCase stale (otdPct/oeePct) nao sao mais declarados;
    campo semantico permanece e resolve no schema emitido."""
    routes = _load_routes()
    for op, (alias, semantic) in WAVE5_CAMELCASE_ALIASES.items():
        declared = _declared_fields(routes[op])
        assert alias not in declared, f"{op} still advertises catalog-only {alias}"
        assert semantic in declared, f"{op} lost semantic field {semantic!r}"
        projectable = {f["name"] for f in routes[op].get("projectableFields") or []}
        assert alias not in projectable, f"{op}: {alias} still projectable"
        assert semantic in projectable, f"{op}: {semantic} not projectable"
        assert field_resolves_in_response(
            semantic, RESPONSE_SCHEMAS[op], routes[op].get("seriesField")
        ), f"{op}: {semantic!r} absent from emitted response schema"


def test_wave5_unrelated_camelcase_fields_unaffected() -> None:
    """Negative: `otdPct` em ops de serie supplies/producao e campo de dominio
    legitimo dentro das linhas (seriesField points) — nunca declarado como
    scalar projectable — e o cleanup nao pode removê-lo nem quebrar a serie."""
    routes = _load_routes()
    series = routes["get_production_otd_series"]
    assert series.get("seriesField") == "points"
    # contrato series-only: nenhum scalar declarado; `otdPct` vive em points[]
    # (campo de dominio legitimo do producer) e nunca foi alias top-level
    assert _declared_fields(series) == []


# Wave 6A — DEPRECATED_COMPATIBILITY_ALIAS: `value` ainda emitido pelos
# producers, documentado em deprecatedFields, fora de valueFields/
# projectableFields. Sem remocao fisica nesta wave.
WAVE6A_PARITY_DEPRECATION: dict[str, str] = {
    "get_kaizen_summary": "total_savings",
    "get_ppm_external_summary": "ppm",
    "get_ppm_internal_summary": "ppm",
    "get_audit_5s_summary": "average_score",
    "get_nonconformity_streak": "current_days_without_nc",
}


def _deprecated_names(route: dict) -> dict[str, dict]:
    return {
        str(item.get("name")): item
        for item in route.get("deprecatedFields") or []
        if isinstance(item, dict) and item.get("name")
    }


def _si_meta_ops(routes: dict) -> list[str]:
    return sorted(
        op
        for op in routes
        if op.startswith("get_si_indicator_") and op.endswith("_meta")
    )


def test_wave6a_deprecated_alias_target_set_is_exactly_42() -> None:
    """41 ops × `value` (36 SI meta + 5 parity) + 1 nested ideas_goal.value = 42
    sites DEPRECATED_COMPATIBILITY_ALIAS documentados no catálogo."""
    routes = _load_routes()
    meta_ops = _si_meta_ops(routes)
    assert len(meta_ops) == 36
    sites = 0
    for op in [*meta_ops, *WAVE6A_PARITY_DEPRECATION]:
        dep = _deprecated_names(routes[op])
        assert "value" in dep, f"{op} missing deprecated `value` entry"
        assert dep["value"]["status"] == "DEPRECATED_COMPATIBILITY_ALIAS"
        sites += 1
    nested = _deprecated_names(routes["get_kaizen_summary"])
    assert nested["ideas_goal.value"]["replacement"] == "ideas_goal.total_kaizens"
    sites += 1
    assert sites == 42


def test_wave6a_canonical_replacement_declared_for_every_alias() -> None:
    """Toda entrada deprecatedFields tem `replacement` semântico que permanece
    declarado/projetável na rota."""
    routes = _load_routes()
    for op in [*_si_meta_ops(routes), *WAVE6A_PARITY_DEPRECATION]:
        dep = _deprecated_names(routes[op])
        for name, entry in dep.items():
            replacement = entry.get("replacement")
            assert replacement, f"{op}:{name} missing replacement"
            if "." in replacement:
                # nested path (ideas_goal.value): bloco raiz deve existir no
                # payload emitido — nao e campo top-level projetavel.
                root = replacement.split(".", 1)[0]
                assert field_resolves_in_response(
                    root, RESPONSE_SCHEMAS[op], routes[op].get("seriesField")
                ), f"{op}: nested replacement root {root!r} not emitted"
            else:
                assert replacement in _declared_fields(routes[op]), (
                    f"{op}: replacement {replacement!r} not declared"
                )


def test_wave6a_deprecated_alias_not_projectable() -> None:
    """Alias deprecated não é preferido: fora de valueFields e projectableFields."""
    routes = _load_routes()
    for op in [*_si_meta_ops(routes), *WAVE6A_PARITY_DEPRECATION]:
        dep_names = set(_deprecated_names(routes[op]))
        declared = set(_declared_fields(routes[op]))
        projectable = {f["name"] for f in routes[op].get("projectableFields") or []}
        assert not (dep_names & declared), f"{op}: deprecated name still declared"
        assert not (dep_names & projectable), f"{op}: deprecated name still projectable"
        assert "value" not in (routes[op].get("valueFields") or [])


def test_wave6a_deprecated_alias_still_emitted_by_producer() -> None:
    """Wave 6A não remove emissão: `value` segue presente no schema de resposta
    emitido (meta triad + parity ops)."""
    routes = _load_routes()
    for op in _si_meta_ops(routes):
        assert field_resolves_in_response(
            "value", _SI_META_RESPONSE_SCHEMA, routes[op].get("seriesField")
        ), f"{op}: emitted `value` alias absent from producer schema"
    for op in WAVE6A_PARITY_DEPRECATION:
        assert field_resolves_in_response(
            "value", RESPONSE_SCHEMAS[op], routes[op].get("seriesField")
        ), f"{op}: emitted `value` alias absent from producer schema"


def test_wave6a_canonical_value_contracts_untouched() -> None:
    """Negative: SI realized `value` (canonico), rankings items[].value
    (dominio) e shapes de apresentacao nao sao marcados deprecated."""
    routes = _load_routes()
    realized = [
        op
        for op in routes
        if op.startswith("get_si_indicator_") and op.endswith("_realized")
    ]
    assert len(realized) == 36
    for op in realized:
        assert "value" in _declared_fields(routes[op])
        assert "value" not in _deprecated_names(routes[op])
    assert "value" in _declared_fields(routes["get_refugos_rankings"])
    assert "value" not in _deprecated_names(routes["get_refugos_rankings"])


def test_wave6a_generator_strips_deprecated_from_projectables() -> None:
    """Guard do gerador: campo em deprecatedFields nunca ressurge como
    projectable/valueField, mesmo herdado do catalogo antigo."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen_tv_routes", REPO_ROOT / "scripts" / "generate_tv_data_routes_from_openapi.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    route = mod.normalize_projectable_fields_on_route(
        {
            "valueFields": ["canonical_pct", "value"],
            "projectableFields": [
                {"name": "canonical_pct", "type": "number"},
                {"name": "value", "type": "number"},
            ],
            "deprecatedFields": [
                {
                    "name": "value",
                    "replacement": "canonical_pct",
                    "status": "DEPRECATED_COMPATIBILITY_ALIAS",
                }
            ],
        }
    )
    assert [f["name"] for f in route["projectableFields"]] == ["canonical_pct"]
    assert route["valueFields"] == ["canonical_pct"]


def test_wave6a_deprecation_ledger_matches_catalog() -> None:
    """Ledger governado (docs/.../value_alias_deprecation_ledger.json) cobre
    exatamente os 42 sites deprecated do catalogo, com replacement coerente."""
    ledger_path = (
        REPO_ROOT
        / "docs"
        / "07-api-delpi"
        / "inventory-value-field"
        / "value_alias_deprecation_ledger.json"
    )
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    routes = _load_routes()

    # total de sites: operationCount (familias agrupadas) ou 1 por entrada
    total_sites = sum(int(e.get("operationCount", 1)) for e in ledger["entries"])
    assert total_sites == 42

    # entradas por-operationId batem com deprecatedFields do catalogo
    for entry in ledger["entries"]:
        op = entry.get("operationId")
        if not op:
            continue  # familia SI meta validada abaixo
        dep = _deprecated_names(routes[op])
        assert entry["alias"] in dep, f"{op}: ledger alias not in catalog"
        assert dep[entry["alias"]]["replacement"] == entry["canonicalReplacement"]

    # familia meta: 36 ops x value -> comparable_goal
    meta_entry = next(
        e for e in ledger["entries"] if e.get("operationFamily") == "get_si_indicator_*_meta"
    )
    assert meta_entry["operationCount"] == 36
    assert meta_entry["canonicalReplacement"] == "comparable_goal"
    for op in _si_meta_ops(routes):
        dep = _deprecated_names(routes[op])
        assert dep["value"]["replacement"] == "comparable_goal"
