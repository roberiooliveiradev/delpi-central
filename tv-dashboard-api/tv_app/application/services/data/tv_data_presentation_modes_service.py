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
    "playbook_report": ["kpi", "line_chart", "table", "auto"],
    "paged_list": ["table", "auto"],
    "hierarchy": ["table", "auto"],
    "composite_analysis": ["kpi", "line_chart", "table", "auto"],
}


def normalize_display_mode(value: str | None) -> str:
    token = str(value or "auto").strip().lower()
    if token == "chart":
        return "line_chart"
    return token if token in _DISPLAY_MODES else "auto"


def block_type_for_display_mode(display_mode: str) -> str:
    return _BLOCK_TYPE_FOR_MODE.get(normalize_display_mode(display_mode), "data_metric")


def suggested_display_modes(
    *,
    allowed_display_modes: list[str] | None,
    meta_shape: str | None = None,
) -> list[str]:
    allowed = [str(mode).strip() for mode in (allowed_display_modes or []) if str(mode).strip()]
    if allowed:
        return allowed
    shape = str(meta_shape or "scalar").strip().lower()
    return list(_SHAPE_DEFAULT_MODES.get(shape, ["auto", "kpi", "table"]))


def validate_display_mode(
    display_mode: str | None,
    *,
    allowed_display_modes: list[str] | None,
) -> None:
    mode = normalize_display_mode(display_mode)
    allowed = suggested_display_modes(allowed_display_modes=allowed_display_modes)
    if mode != "auto" and mode not in allowed:
        raise ValueError(f"Formato de apresentação não permitido: {mode}")


def validate_block_type_for_binding(
    block_type: str,
    display_mode: str | None,
) -> None:
    if block_type not in DATA_BLOCK_TYPES:
        raise ValueError("Tipo de bloco de dados inválido.")
    expected = block_type_for_display_mode(display_mode or "auto")
    mode = normalize_display_mode(display_mode)
    if mode == "auto":
        return
    if block_type != expected and not (block_type == "data_metric" and mode == "auto"):
        raise ValueError("Tipo de bloco incompatível com o formato de apresentação selecionado.")
