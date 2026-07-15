"""Defaults canônicos de parâmetros TV antes do fetch à api-delpi.

Garante que preview/smoke/blocos sem formulário completo ainda enviem
obrigatórios convencionais (filial, schema.default, período) nos nomes certos.
"""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    PERIOD_DAYS_KEY,
    find_date_range_keys,
    read_date_range_values,
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


def _branch_default_for_route(route: Mapping[str, Any]) -> str:
    path = str(route.get("path") or "").strip()
    for prefix, value in _BRANCH_DEFAULT_BY_PATH_PREFIX:
        if path.startswith(prefix):
            return value
    return CONVENIENT_REQUIRED_DEFAULTS["branch"]


def _convenient_default(key: str, route: Mapping[str, Any]) -> str | None:
    if key == "branch":
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
    `periodDays` / `dateRangePreset` do catálogo só entram se ainda não houver datas.
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
        if _has_value(merged, key):
            continue
        default = spec.get("default")
        if default is not None and default != "":
            merged[str(key)] = default
            continue
        if not spec.get("optional", True) and key in CONVENIENT_REQUIRED_DEFAULTS:
            convenient = _convenient_default(key, route_map)
            if convenient is not None:
                merged[str(key)] = convenient

    pair = find_date_range_keys(schema) or find_date_range_keys(route_map.get("dateRangeKeys"))
    if pair:
        start_key, end_key = pair
        alias_start, alias_end = read_date_range_values(merged, start_key, end_key)
        has_period_intent = _has_value(merged, DATE_RANGE_PRESET_KEY) or _has_value(
            merged, PERIOD_DAYS_KEY
        )
        if not alias_start and not alias_end and not has_period_intent:
            period_default = catalog_defaults.get(PERIOD_DAYS_KEY)
            merged[PERIOD_DAYS_KEY] = int(period_default) if period_default not in (None, "") else 30

    return merged
