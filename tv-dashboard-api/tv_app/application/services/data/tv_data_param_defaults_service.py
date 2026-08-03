"""Defaults canônicos de parâmetros TV antes do fetch à api-delpi.

Garante que preview/smoke/blocos sem formulário completo ainda enviem
obrigatórios convencionais (filial, schema.default, período) nos nomes certos.
"""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    PERIOD_DAYS_KEY,
)

# Valores seguros para campos obrigatórios recorrentes quando ausentes.
# Buscas exigem ≥3 chars na api-delpi; agendamento usa filial SC/ES (não 01/02).
CONVENIENT_REQUIRED_DEFAULTS: dict[str, str] = {
    "branch": "01",
    "filial": "01",
    "branch_code": "01",
    "q": "pac",
    "description": "codigo",
}

_BRANCH_DEFAULT_BY_PATH_PREFIX: tuple[tuple[str, str], ...] = (
    ("/scheduling/", "SC"),
)

# Não mesclar cegamente: forçaria recalcular o intervalo e apagaria data parcial do usuário.
_CATALOG_PERIOD_KEYS = frozenset({PERIOD_DAYS_KEY, DATE_RANGE_PRESET_KEY})

# Select de identidade/filtro: nunca inventar valor (ex.: department_id → commercial).
_NO_SCHEMA_DEFAULT_KEYS = frozenset({"department_id"})


def should_apply_schema_default(key: str, spec: Mapping[str, Any]) -> bool:
    """Defaults de catálogo/OpenAPI só quando não sabotam «Limpar filtro» em selects."""
    default = spec.get("default")
    if default is None or default == "":
        return False
    if key in _NO_SCHEMA_DEFAULT_KEYS or key in _CATALOG_PERIOD_KEYS:
        return False
    enum = spec.get("enum")
    # Select opcional: limpar deve permanecer vazio (não reverter para Todos/comercial/…).
    if enum and bool(spec.get("optional", True)):
        return False
    return True


def _branch_default_for_route(route: Mapping[str, Any]) -> str:
    path = str(route.get("path") or "").strip()
    for prefix, value in _BRANCH_DEFAULT_BY_PATH_PREFIX:
        if path.startswith(prefix):
            return value
    schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    for key in ("branch", "filial"):
        branch_spec = schema.get(key) if isinstance(schema.get(key), dict) else {}
        enum_values = branch_spec.get("enum") if isinstance(branch_spec, dict) else None
        if isinstance(enum_values, list) and "all" in [str(v) for v in enum_values]:
            return "all"
    return CONVENIENT_REQUIRED_DEFAULTS["branch"]


def _convenient_default(key: str, route: Mapping[str, Any]) -> str | None:
    if key in {"branch", "filial"}:
        return _branch_default_for_route(route)
    return CONVENIENT_REQUIRED_DEFAULTS.get(key)


def _has_value(params: Mapping[str, Any], key: str) -> bool:
    value = params.get(key)
    return value is not None and value != ""


def apply_catalog_param_defaults(
    params: Mapping[str, Any] | None,
    route: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Mescla defaultParams do catálogo + defaults do schema + convenções de obrigatórios.

    Ordem (mais específico ganha): convenient/schema ← route.defaultParams ← params.
    `periodDays` / `dateRangePreset` nunca são injetados automaticamente (nem via
    defaultParams do catálogo nem schema.default) — só entram nos params do caller.
    """
    route_map = route if isinstance(route, Mapping) else {}
    schema = route_map.get("paramSchema") if isinstance(route_map.get("paramSchema"), dict) else {}
    catalog_defaults = (
        route_map.get("defaultParams") if isinstance(route_map.get("defaultParams"), dict) else {}
    )

    merged: dict[str, Any] = {}
    for key, value in catalog_defaults.items():
        if key in _CATALOG_PERIOD_KEYS:
            continue
        if value is None or value == "":
            continue
        merged[str(key)] = value

    if isinstance(params, Mapping):
        for key, value in params.items():
            if value is None or value == "":
                continue
            merged[str(key)] = value

    for key, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        if key in _CATALOG_PERIOD_KEYS:
            # periodDays/dateRangePreset: nunca default mágico via schema — só params do caller.
            continue
        if _has_value(merged, key):
            continue
        if should_apply_schema_default(key, spec):
            merged[str(key)] = spec.get("default")
            continue
        if not spec.get("optional", True) and key in CONVENIENT_REQUIRED_DEFAULTS:
            convenient = _convenient_default(key, route_map)
            if convenient is not None:
                merged[str(key)] = convenient

    # Sem datas/preset/periodDays explícitos → não injeta janela (histórico completo).
    return merged
