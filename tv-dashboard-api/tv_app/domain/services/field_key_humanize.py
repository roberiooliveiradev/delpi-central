"""Humanização centralizada de chaves snake_case → rótulo PT (TV / enrichment).

Espelho de ``plugins/tv-dashboard-presentation/src/fieldKeyHumanize.ts``.
Preferir mapa de chave completa; senão traduz tokens (`_` = espaço).
"""

from __future__ import annotations

FIELD_KEY_LABELS: dict[str, str] = {
    "month": "Mês",
    "periodo": "Período",
    "value": "Valor",
    "total": "Total",
    "gross_savings_month": "Economia bruta (mês)",
    "gross_costs_month": "Custos brutos (mês)",
    "gross_investment_month": "Investimento bruto (mês)",
    "gross_recurring_investment_month": "Invest. recorrente (mês)",
    "shared_resource_cost_month": "Custo recurso compartilhado (mês)",
    "investment_total_month": "Investimento total (mês)",
    "net_savings_month": "Economia líquida (mês)",
    "implemented_solutions_count": "Soluções ativas",
    "solutions_started_in_period_count": "Soluções iniciadas no período",
    "total_investment_in_period": "Investimento total",
    "total_gross_costs_until_now": "Investimento total",
    "total_gross_savings_in_period": "Economia bruta",
    "total_hours_saved_until_now": "Horas economizadas",
    "total_net_savings_until_now": "Economia líquida",
    "average_roi": "ROI médio",
    "accumulated_net_savings_until_now": "Economia líquida acumulada",
    "economia_bruta": "Economia bruta",
    "investimento": "Investimento",
    "economia_liquida": "Economia líquida",
    "horas_economizadas": "Horas economizadas",
}

FIELD_TOKEN_LABELS: dict[str, str] = {
    "month": "mês",
    "months": "meses",
    "year": "ano",
    "years": "anos",
    "day": "dia",
    "days": "dias",
    "week": "semana",
    "period": "período",
    "periodo": "período",
    "date": "data",
    "start": "início",
    "end": "fim",
    "from": "de",
    "to": "até",
    "gross": "bruto",
    "net": "líquido",
    "savings": "economia",
    "saving": "economia",
    "costs": "custos",
    "cost": "custo",
    "investment": "investimento",
    "investments": "investimentos",
    "recurring": "recorrente",
    "shared": "compartilhado",
    "resource": "recurso",
    "resources": "recursos",
    "hours": "horas",
    "hour": "hora",
    "saved": "economizadas",
    "total": "total",
    "average": "média",
    "avg": "média",
    "mean": "média",
    "count": "quantidade",
    "quantity": "quantidade",
    "qty": "qtd.",
    "amount": "valor",
    "value": "valor",
    "values": "valores",
    "rate": "taxa",
    "pct": "%",
    "percent": "%",
    "percentage": "%",
    "roi": "ROI",
    "branch": "filial",
    "filial": "filial",
    "sector": "setor",
    "department": "departamento",
    "product": "produto",
    "item": "item",
    "code": "código",
    "name": "nome",
    "description": "descrição",
    "status": "status",
    "active": "ativas",
    "started": "iniciadas",
    "solutions": "soluções",
    "solution": "solução",
    "implemented": "implementadas",
    "in": "no",
    "until": "até",
    "now": "agora",
    "accumulated": "acumulada",
}


def is_weak_field_label(field: str, label: str | None) -> bool:
    key = str(field or "").strip()
    text = str(label or "").strip()
    if not key:
        return not text
    if not text:
        return True
    if text == key:
        return True
    spaced = key.replace("_", " ")
    if text == spaced:
        return True
    if text.lower() == spaced.lower():
        return True
    if text.lower() == key.lower():
        return True
    return False


def humanize_field_key(field: str) -> str:
    key = str(field or "").strip()
    if not key:
        return ""
    lower = key.lower()
    curated = FIELD_KEY_LABELS.get(lower)
    if curated:
        return curated
    tokens = [part for part in lower.split("_") if part]
    if not tokens:
        return key
    if len(tokens) == 1:
        single = FIELD_TOKEN_LABELS.get(tokens[0], tokens[0])
        return single[:1].upper() + single[1:] if single else single
    translated = [FIELD_TOKEN_LABELS.get(token, token) for token in tokens]
    joined = " ".join(translated)
    return joined[:1].upper() + joined[1:] if joined else joined
