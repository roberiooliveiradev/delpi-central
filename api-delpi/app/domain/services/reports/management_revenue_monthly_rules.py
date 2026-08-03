"""Constantes e formatação — Relatório Gerencial (faturamento mensal)."""

from __future__ import annotations

from typing import Any

PROVIDER_KEY = "management_revenue_monthly"
PROVIDER_DISPLAY_NAME = "Relatório Gerencial — Faturamento"
DEFAULT_CUSTOMER_LIMIT = 20
TITLE = "Relatório Gerencial"
SECTION_FATURAMENTO = "Faturamento"

POSITIVE_COLOR = "#15803D"
NEGATIVE_COLOR = "#B91C1C"
NEUTRAL_COLOR = "#64748B"

# Departamentos SI (mesmo conjunto dos dashboards / FULL_MEASUREMENT).
SI_DEPARTMENT_IDS: tuple[str, ...] = (
    "commercial",
    "engineering",
    "financial",
    "hr",
    "production",
    "quality",
    "supplies",
)
SI_DEPARTMENT_LABELS_PT: dict[str, str] = {
    "engineering": "Engenharia",
    "production": "Produção",
    "commercial": "Comercial",
    "quality": "Qualidade",
    "hr": "RH",
    "financial": "Financeiro",
    "supplies": "Suprimentos",
}

# Triângulos preenchidos (Unicode) — legíveis em Outlook/Gmail.
_ARROW_UP = "▲"
_ARROW_DOWN = "▼"
_ARROW_FLAT = "●"


def format_brl(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    formatted = f"{number:,.2f}"
    # 1,234,567.89 → 1.234.567,89
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_brl_mi(value: Any, *, digits: int = 1) -> str:
    """Formata valor absoluto em milhões (ex.: R$ 24,8 mi)."""
    try:
        number = float(value or 0) / 1_000_000.0
    except (TypeError, ValueError):
        number = 0.0
    text = f"{number:.{digits}f}".replace(".", ",")
    if digits > 0 and text.endswith("," + ("0" * digits)):
        text = text.split(",")[0]
    return f"R$ {text} mi"


def format_pct(value: Any) -> str:
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.2f}%".replace(".", ",")


def format_pct_html(value: Any) -> str:
    if value is None:
        return f'<span style="color:{NEUTRAL_COLOR};">—</span>'
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f'<span style="color:{NEUTRAL_COLOR};">—</span>'
    if number > 0:
        color = POSITIVE_COLOR
    elif number < 0:
        color = NEGATIVE_COLOR
    else:
        color = NEUTRAL_COLOR
    return (
        f'<span style="color:{color};font-weight:700;">{format_pct(number)}</span>'
    )


def trend_arrow_html(value: Any) -> str:
    """Seta preenchida: ▲ alta / ▼ queda / ● neutro — cor conforme o sinal."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number > 0:
        arrow, color = _ARROW_UP, POSITIVE_COLOR
    elif number < 0:
        arrow, color = _ARROW_DOWN, NEGATIVE_COLOR
    else:
        arrow, color = _ARROW_FLAT, NEUTRAL_COLOR
    return (
        f'<span style="color:{color};font-weight:700;font-size:13px;'
        f'line-height:1;">{arrow}</span>'
    )


def format_delta_brl_html(value: Any) -> str:
    """Valor Δ em R$ com cor semântica (sem sinal duplicado além do número)."""
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    if number > 0:
        color = POSITIVE_COLOR
    elif number < 0:
        color = NEGATIVE_COLOR
    else:
        color = NEUTRAL_COLOR
    return (
        f'<span style="color:{color};font-weight:600;">{format_brl(number)}</span>'
    )


def parse_as_of_date(raw: Any) -> str | None:
    """Retorna YYYY-MM-DD ou None."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    raise ValueError("asOfDate deve estar no formato YYYY-MM-DD.")


def parse_customer_limit(raw: Any) -> int:
    if raw is None or raw == "":
        return DEFAULT_CUSTOMER_LIMIT
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("customerLimit inválido.") from exc
    if value < 1 or value > 100:
        raise ValueError("customerLimit deve estar entre 1 e 100.")
    return value
