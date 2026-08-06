from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    END_KEYS,
    PERIOD_DAYS_KEY,
    START_KEYS,
)


def _has_value(layer: dict[str, Any], key: str) -> bool:
    value = layer.get(key)
    return value is not None and value != ""


# Aliases de filial Protheus — vazio/all na camada superior limpa herança 01/02.
BRANCH_PARAM_KEYS = frozenset({"branch", "filial", "branch_code", "filial_id"})

# Wire HTTP canônico na api-delpi (enum OpenAPI all|01|02). Aliases PT → all.
BRANCH_SCOPE_WIRE_ALL = "all"


def _is_all_branches_scope(value: Any) -> bool:
    """True = consolidado (all / vazio / aliases PT)."""
    if value is None or value == "":
        return True
    return str(value).strip().lower() in {"all", "todas", "todos"}


def canonical_branch_wire_value(value: Any) -> str | None:
    """Normaliza filial para o wire aceito pela api-delpi (all|01|02).

    Playlists legadas ainda podem gravar ``Todas``; o pattern HTTP da api-delpi
    só aceita ``all`` — devolver None omite o param (equivalente a consolidado).
    """
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if _is_all_branches_scope(raw):
        return BRANCH_SCOPE_WIRE_ALL
    return raw


def resolve_any_branch_value(params: Mapping[str, Any] | None) -> Any:
    """Primeiro valor de filial entre aliases (branch/filial/…)."""
    values = params if isinstance(params, Mapping) else {}
    for key in BRANCH_PARAM_KEYS:
        if key not in values:
            continue
        value = values.get(key)
        if value is None or value == "":
            continue
        if str(value).strip():
            return value
    return None


def schema_branch_param_keys(schema: Mapping[str, Any] | None) -> list[str]:
    """Chaves de filial declaradas no paramSchema da rota (ordem estável)."""
    if not isinstance(schema, Mapping):
        return []
    return [str(key) for key in schema.keys() if str(key) in BRANCH_PARAM_KEYS]


def project_branch_params_onto_route_schema(
    params: Mapping[str, Any] | None,
    schema: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Projeta filial de qualquer alias para a(s) chave(s) do schema da rota.

    Programação/tela/dados mistos gravam ``branch``; rotas como ``/refugos/*``
    só expõem ``filial`` no OpenAPI. Sem projeção o gateway emitia ``branch=01``
    (via always_allow) e a api-delpi ignorava — consolidado indevido.
    """
    out = dict(params) if isinstance(params, Mapping) else {}
    targets = schema_branch_param_keys(schema)
    if not targets:
        return out
    wire = canonical_branch_wire_value(resolve_any_branch_value(out))
    _clear_branch_aliases(out)
    if wire is None:
        return out
    for key in targets:
        out[key] = wire
    return out


def _clear_branch_aliases(target: dict[str, Any]) -> None:
    for key in BRANCH_PARAM_KEYS:
        target.pop(key, None)


def _layer_has_any_dates(layer: dict[str, Any]) -> bool:
    return any(_has_value(layer, key) for key in (*START_KEYS, *END_KEYS))


def _clear_date_keys(target: dict[str, Any]) -> None:
    for key in (*START_KEYS, *END_KEYS):
        target.pop(key, None)


def _normalize_preset(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def input_overrides_period_intent(input_overrides: dict[str, Any] | None) -> bool:
    """True se a camada de input/runtime fixa período (datas ou periodDays)."""
    if not isinstance(input_overrides, dict):
        return False
    if _has_value(input_overrides, PERIOD_DAYS_KEY):
        return True
    return any(_has_value(input_overrides, key) for key in (*START_KEYS, *END_KEYS))


def reconcile_merged_params_after_input(
    merged: dict[str, Any],
    *,
    input_overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    """Input/runtime vence preset relativo e periodDays/datas da fonte.

    Sem isso, `dateRangePreset: this_month` em dataBinding.params recalcula o mês
    inteiro e ignora filtro interativo (Data fim / Período dias).
    """
    if not input_overrides_period_intent(input_overrides):
        return merged
    out = dict(merged)
    overrides = input_overrides if isinstance(input_overrides, dict) else {}
    out.pop(DATE_RANGE_PRESET_KEY, None)
    has_explicit_dates = any(_has_value(overrides, key) for key in (*START_KEYS, *END_KEYS))
    has_period_days = _has_value(overrides, PERIOD_DAYS_KEY)
    if has_explicit_dates and not has_period_days:
        # Datas do filtro não podem ser recalculadas por periodDays da fonte.
        out.pop(PERIOD_DAYS_KEY, None)
    if has_period_days and not has_explicit_dates:
        # last_n a partir do input: remove datas concretas herdadas da fonte.
        for key in (*START_KEYS, *END_KEYS):
            if not _has_value(overrides, key):
                out.pop(key, None)
    return out


def _is_relative_date_range_preset(value: Any) -> bool:
    preset = _normalize_preset(value)
    return bool(preset) and preset != "custom"


def _strip_competence_for_relative_preset(merged: dict[str, Any]) -> None:
    """Preset relativo (ex.: previous_month) vence competence SI herdada.

    A UI grava `competence: \"\"` na camada editada, mas o merge ignora vazio e
    a competence da fonte/tela permanece — o SI então prioriza competence e
    ignora o mês do preset. Ver regressão TV «Mês passado» + IDD.
    """
    if _is_relative_date_range_preset(merged.get(DATE_RANGE_PRESET_KEY)):
        merged.pop("competence", None)


def _apply_period_layer(merged: dict[str, Any], layer: dict[str, Any]) -> None:
    """Aplica intenção de período da camada sem vazar datas stale das camadas inferiores.

    - Preset relativo → descarta datas e competence herdadas (o gateway recalcula).
    - `custom` sem datas na camada → descarta datas herdadas (evita 0026 + custom do bloco).
    - `custom` com datas na camada → datas da camada prevalecem no loop normal.
    """
    if DATE_RANGE_PRESET_KEY not in layer:
        return
    raw = layer.get(DATE_RANGE_PRESET_KEY)
    if raw is None or raw == "":
        return
    preset = _normalize_preset(raw)
    if not preset:
        return
    if preset == "custom":
        if not _layer_has_any_dates(layer):
            _clear_date_keys(merged)
        return
    # Relativo (this_month, previous_month, last_7_days, …)
    _clear_date_keys(merged)
    merged.pop("competence", None)
    if preset != "last_n_days" and not _has_value(layer, PERIOD_DAYS_KEY):
        merged.pop(PERIOD_DAYS_KEY, None)


def merge_data_params(
    *,
    playlist_defaults: dict[str, Any] | None,
    slide_filters: dict[str, Any] | None,
    block_params: dict[str, Any] | None,
    input_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """programação → tela → dados (bloco) → input (maior precedência ganha)."""
    merged: dict[str, Any] = {}
    for layer in (playlist_defaults, slide_filters, block_params, input_overrides):
        if not isinstance(layer, dict):
            continue
        _apply_period_layer(merged, layer)
        for key, value in layer.items():
            key_str = str(key)
            # Filial vazia limpa herança; all/Todas grava wire canônico ``all``.
            if key_str in BRANCH_PARAM_KEYS and _is_all_branches_scope(value):
                _clear_branch_aliases(merged)
                wire = canonical_branch_wire_value(value)
                if wire is not None:
                    merged[key_str] = wire
                continue
            if value is None or value == "":
                continue
            merged[key_str] = value
    out = reconcile_merged_params_after_input(merged, input_overrides=input_overrides)
    # Camada inferior pode repor competence depois do pop no preset da camada
    # superior (ex.: fonte com competence + input previous_month).
    _strip_competence_for_relative_preset(out)
    return out


def param_inherited_from_slide(
    key: str,
    *,
    slide_filters: dict[str, Any] | None,
    block_params: dict[str, Any] | None,
) -> bool:
    slide = slide_filters if isinstance(slide_filters, dict) else {}
    block = block_params if isinstance(block_params, dict) else {}
    return key in slide and key not in block
