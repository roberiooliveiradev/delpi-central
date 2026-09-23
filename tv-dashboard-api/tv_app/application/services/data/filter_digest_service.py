"""Compact filter layering digest for VISTA (programação → tela → fonte)."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.comunicado_data_params_service import (
    BRANCH_PARAM_KEYS,
    resolve_any_branch_value,
)
from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    PERIOD_DAYS_KEY,
)

_RELAYER_KEYS = frozenset(
    {
        "branch",
        "filial",
        "branch_code",
        "filial_id",
        DATE_RANGE_PRESET_KEY,
        PERIOD_DAYS_KEY,
        "competence",
    }
)


def _source_params(block: Mapping[str, Any]) -> dict[str, Any]:
    binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
    params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
    return dict(params)


def _normalized_relayer_value(key: str, value: Any) -> Any:
    if key in BRANCH_PARAM_KEYS:
        return resolve_any_branch_value({key: value})
    if isinstance(value, str):
        return value.strip()
    return value


def _collect_sources(native_config: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(native_config, dict):
        return []
    blocks = native_config.get("blocks")
    if not isinstance(blocks, list):
        return []
    out: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if str(block.get("type") or "") != "data_source":
            continue
        params = _source_params(block)
        out.append(
            {
                "blockId": str(block.get("id") or ""),
                "params": params,
            }
        )
    return out


def _duplicate_shared_keys(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keys with the same normalized value on every non-empty source."""
    if len(sources) < 2:
        return []
    duplicates: list[dict[str, Any]] = []
    for key in _RELAYER_KEYS:
        values: list[Any] = []
        for src in sources:
            params = src.get("params") if isinstance(src.get("params"), dict) else {}
            if key in params and params.get(key) not in (None, ""):
                values.append(_normalized_relayer_value(key, params.get(key)))
            elif key in BRANCH_PARAM_KEYS:
                branch = resolve_any_branch_value(params)
                if branch not in (None, ""):
                    values.append(_normalized_relayer_value("branch", branch))
        if len(values) < 2:
            continue
        if len(set(str(v) for v in values)) == 1:
            duplicates.append({"key": key, "value": values[0], "sourceCount": len(sources)})
    return duplicates


def _wrong_layer_hints(
    sources: list[dict[str, Any]],
    *,
    programming_defaults: Mapping[str, Any],
    slide_filters: Mapping[str, Any],
) -> list[str]:
    hints: list[str] = []
    if len(sources) < 2:
        return hints
    for key in (DATE_RANGE_PRESET_KEY, PERIOD_DAYS_KEY, "branch"):
        present = 0
        for src in sources:
            params = src.get("params") if isinstance(src.get("params"), dict) else {}
            if key in (DATE_RANGE_PRESET_KEY, PERIOD_DAYS_KEY):
                if params.get(key) not in (None, ""):
                    present += 1
            elif resolve_any_branch_value(params) not in (None, ""):
                present += 1
        if present >= 2:
            in_prog = key in programming_defaults and programming_defaults.get(key) not in (
                None,
                "",
            )
            in_slide = key in slide_filters and slide_filters.get(key) not in (None, "")
            if not in_prog and not in_slide:
                hints.append(f"shared_{key}_on_sources")
    return hints


class FilterDigestService:
    """Projects typed filter layering without executing data fetches."""

    @classmethod
    def digest_slide(
        cls,
        native_config: Mapping[str, Any] | None,
        *,
        slide_id: str | None = None,
        title: str | None = None,
        programming_defaults: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        cfg = native_config if isinstance(native_config, dict) else {}
        prog = dict(programming_defaults) if isinstance(programming_defaults, dict) else {}
        slide_filters = cfg.get("dataFilters") if isinstance(cfg.get("dataFilters"), dict) else {}
        sources = _collect_sources(cfg)
        return {
            "slideId": slide_id,
            "title": title,
            "programmingDefaults": prog,
            "dataFilters": dict(slide_filters),
            "sources": sources,
            "duplicates": _duplicate_shared_keys(sources),
            "wrongLayerHints": _wrong_layer_hints(
                sources,
                programming_defaults=prog,
                slide_filters=slide_filters,
            ),
        }

    @classmethod
    def digest_playlist(
        cls,
        *,
        programming_defaults: Mapping[str, Any] | None,
        slides: list[Any] | None,
    ) -> dict[str, Any]:
        prog = dict(programming_defaults) if isinstance(programming_defaults, dict) else {}
        per_slide: list[dict[str, Any]] = []
        aggregate_wrong: list[str] = []
        for slide in slides or []:
            if not isinstance(slide, dict):
                continue
            native = slide.get("nativeConfig") if isinstance(slide.get("nativeConfig"), dict) else {}
            entry = cls.digest_slide(
                native,
                slide_id=str(slide.get("id") or "") or None,
                title=str(slide.get("title") or "") or None,
                programming_defaults=prog,
            )
            per_slide.append(entry)
            for hint in entry.get("wrongLayerHints") or []:
                if hint not in aggregate_wrong:
                    aggregate_wrong.append(str(hint))
        return {
            "programmingDefaults": prog,
            "slides": per_slide,
            "wrongLayerHints": aggregate_wrong,
        }
