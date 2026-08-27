"""Defaults canônicos de parâmetros TV antes do fetch à api-delpi.

Garante que preview/smoke/blocos sem formulário completo ainda enviem
obrigatórios convencionais (filial, schema.default, período) nos nomes certos.

Filtros **opcionais** nunca são inventados no wire nem no bloco Dados:
«Não definido aqui» omite o param; a api-delpi aplica o default do Query.
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


def is_optional_param_spec(spec: Mapping[str, Any] | None) -> bool:
    """True = filtro omitível na UI («Não definido aqui»). Ausência de optional = opcional."""
    if not isinstance(spec, Mapping):
        return True
    return bool(spec.get("optional", True))


def should_apply_schema_default(key: str, spec: Mapping[str, Any]) -> bool:
    """Defaults de catálogo/OpenAPI só para params **obrigatórios**.

    Filtro opcional (qualquer tipo: enum, bool, string, int) permanece vazio no
    bloco/wire — a api-delpi aplica o default do Query quando o param é omitido.
    """
    default = spec.get("default")
    if default is None or default == "":
        return False
    if key in _NO_SCHEMA_DEFAULT_KEYS or key in _CATALOG_PERIOD_KEYS:
        return False
    if is_optional_param_spec(spec):
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

    Params **opcionais** no paramSchema nunca vêm de defaultParams/schema — vale para
    todas as rotas (group_by, granularity, sort, only_positive, status, …).
    """
    route_map = route if isinstance(route, Mapping) else {}
    schema = route_map.get("paramSchema") if isinstance(route_map.get("paramSchema"), dict) else {}
    catalog_defaults = (
        route_map.get("defaultParams") if isinstance(route_map.get("defaultParams"), dict) else {}
    )

    merged: dict[str, Any] = {}
    for key, value in catalog_defaults.items():
        key_str = str(key)
        if key_str in _CATALOG_PERIOD_KEYS:
            continue
        if value is None or value == "":
            continue
        spec = schema.get(key_str) if isinstance(schema.get(key_str), dict) else None
        # Chave conhecida como opcional no schema → não forçar (todas as rotas).
        if isinstance(spec, dict) and is_optional_param_spec(spec):
            continue
        merged[key_str] = value

    if isinstance(params, Mapping):
        for key, value in params.items():
            if value is None or value == "":
                continue
            merged[str(key)] = value

    for key, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        if key in _CATALOG_PERIOD_KEYS:
            continue
        if _has_value(merged, key):
            continue
        if should_apply_schema_default(key, spec):
            merged[str(key)] = spec.get("default")
            continue
        if not is_optional_param_spec(spec) and key in CONVENIENT_REQUIRED_DEFAULTS:
            convenient = _convenient_default(key, route_map)
            if convenient is not None:
                merged[str(key)] = convenient

    return merged


def schema_param_default(route: Mapping[str, Any] | None, param_name: str) -> str | None:
    """Default declarativo do paramSchema (contrato OpenAPI / FastAPI Query).

    Usado na apresentação (ex.: tableFieldsByParam) quando o wire omitiu o param
    — espelha o default que a api-delpi aplicaria, sem gravar no bloco Dados.
    """
    if not isinstance(route, Mapping):
        return None
    schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    spec = schema.get(param_name) if isinstance(schema.get(param_name), dict) else {}
    if not isinstance(spec, dict):
        return None
    raw = spec.get("default")
    if raw is None or raw == "":
        return None
    text = str(raw).strip()
    return text or None
