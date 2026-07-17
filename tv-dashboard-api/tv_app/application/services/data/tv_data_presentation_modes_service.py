from __future__ import annotations

from tv_app.application.services.tv_data_route_catalog_service import DATA_BLOCK_TYPES

_DISPLAY_MODES = frozenset({"kpi", "line_chart", "bar_chart", "table", "auto", "chart"})

_BLOCK_TYPE_FOR_MODE: dict[str, str] = {
    "kpi": "data_kpi",
    "table": "data_table",
    "line_chart": "data_chart",
    "bar_chart": "data_chart",
    "chart": "data_chart",
}

_SHAPE_DEFAULT_MODES: dict[str, list[str]] = {
    "scalar": ["kpi", "auto"],
    "list": ["table", "auto"],
    "playbook_report": ["kpi", "line_chart", "table", "auto"],
    "paged_list": ["table", "auto"],
    "hierarchy": ["table", "auto"],
    "composite_analysis": ["kpi", "line_chart", "table", "auto"],
}


def normalize_display_mode(value: str | None) -> str:
    token = str(value or "kpi").strip().lower()
    if token == "chart":
        return "line_chart"
    if token == "auto":
        return "auto"
    return token if token in _DISPLAY_MODES else "kpi"


def block_type_for_display_mode(display_mode: str) -> str:
    return _BLOCK_TYPE_FOR_MODE.get(normalize_display_mode(display_mode), "data_kpi")


def suggested_display_modes(
    *,
    allowed_display_modes: list[str] | None,
    meta_shape: str | None = None,
) -> list[str]:
    allowed = [str(mode).strip() for mode in (allowed_display_modes or []) if str(mode).strip()]
    if allowed:
        return allowed
    shape = str(meta_shape or "scalar").strip().lower()
    return list(_SHAPE_DEFAULT_MODES.get(shape, ["kpi", "table", "line_chart"]))


def validate_display_mode(
    display_mode: str | None,
    *,
    allowed_display_modes: list[str] | None,
) -> None:
    del allowed_display_modes
    mode = normalize_display_mode(display_mode)
    if mode == "auto":
        return
    if mode not in _DISPLAY_MODES:
        raise ValueError(f"Formato de apresentação inválido: {mode}")


def validate_block_type_for_binding(
    block_type: str,
    display_mode: str | None,
) -> None:
    if block_type in {"data_source", "data_metric"}:
        return
    if block_type not in DATA_BLOCK_TYPES:
        raise ValueError("Tipo de bloco de dados inválido.")
    expected = block_type_for_display_mode(display_mode or "kpi")
    mode = normalize_display_mode(display_mode)
    if mode == "auto":
        return
    if block_type != expected and not (block_type == "data_metric" and mode == "auto"):
        raise ValueError("Tipo de bloco incompatível com o formato de apresentação selecionado.")
