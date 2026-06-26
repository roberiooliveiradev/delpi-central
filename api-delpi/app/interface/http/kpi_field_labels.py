"""Rótulos PT para meta.fields — rotas KPI/scalar (Playbook 10, consumo no chat)."""

from __future__ import annotations

COMMON_SCALAR_FIELD_LABELS: dict[str, str] = {
    "branch": "Filial",
    "branches": "Filiais",
    "start_date": "Data início",
    "end_date": "Data fim",
    "date_start": "Data início",
    "date_end": "Data fim",
    "end_date_exclusive": "Data fim (exclusiva)",
    "periodo": "Período",
    "period_reference": "Referência do período",
    "granularity": "Granularidade",
    "truncated": "Série truncada",
    "points": "Pontos",
    "sort_key": "Ordenação",
    "summary": "Resumo",
    "value": "Valor",
    "percentage": "Percentual",
    "current": "Atual",
    "previous": "Anterior",
    "target": "Meta",
    "unit": "Unidade",
    "location": "Localização",
    "enabled": "Habilitado",
    "month": "Mês",
    "registros": "Registros",
    "total_records": "Registros",
    "total_items": "Total de itens",
    "total_products": "Produtos distintos",
}

SI_GOAL_FIELD_LABELS: dict[str, str] = {
    "goal_label": "Meta",
    "goal_value": "Valor da meta",
    "goal_periodicity": "Periodicidade da meta",
    "goal_mode": "Modo da meta",
    "goal_scope_branch": "Filial da meta",
    "goal_scope_label": "Escopo da meta",
    "goal_scope_hint": "Observação da meta",
    "comparable_goal": "Meta comparável",
    "has_goal": "Possui meta",
    "performance_direction": "Direção do indicador",
    "indicator_name": "Indicador",
    "indicator_id": "ID do indicador",
    "indicator_code": "Código do indicador",
    "scope_type": "Tipo de escopo",
    "value_unit": "Unidade do valor",
    "value_prefix": "Prefixo do valor",
    "value_suffix": "Sufixo do valor",
    "value_decimals": "Casas decimais",
}

FINANCIAL_ROL_FIELD_LABELS: dict[str, str] = {
    "gross_revenue": "Receita bruta",
    "other_values": "Outros valores",
    "items_without_tes": "Itens sem TES",
    "returns": "Devoluções",
    "discounts": "Descontos",
    "icms": "ICMS",
    "iss": "ISS",
    "pis": "PIS",
    "cofins": "COFINS",
    "ipi_separated": "IPI destacado",
    "rol_taxes": "Impostos sobre ROL",
    "rol": "ROL",
    "rol_with_ipi": "ROL",
    "financial_titles": "Títulos financeiros",
    "financial_balance": "Saldo financeiro",
}

FINANCIAL_EBITDA_FIELD_LABELS: dict[str, str] = {
    "ebitda_value": "EBITDA (valor)",
    "ebitda_over_rol_pct": "EBITDA / ROL (%)",
    "rol_with_ipi": "ROL",
}

FINANCIAL_FIXED_COST_FIELD_LABELS: dict[str, str] = {
    "fixed_cost_value": "Custos fixos (valor)",
    "fixed_cost_over_rol_pct": "Custos fixos / ROL (%)",
}

FINANCIAL_PMR_FIELD_LABELS: dict[str, str] = {
    "pmr_days": "PMR (dias)",
}

SUPPLIES_CPV_FIELD_LABELS: dict[str, str] = {
    "cpv_total": "CPV total",
    "cpv_percentage": "CPV / ROL (%)",
    "cpv_average_monthly": "CPV médio mensal",
    "total_movements": "Total movimentações",
    "average_cost_per_movement": "Custo médio por movimentação",
    "average_cost_per_unit": "Custo médio por unidade",
    "average_unit_value": "Valor médio unitário",
}

SUPPLIES_OTD_FIELD_LABELS: dict[str, str] = {
    "otd_percentage": "OTD (%)",
    "late_percentage": "% atrasos",
}

SUPPLIES_STOCK_VALUE_FIELD_LABELS: dict[str, str] = {
    "total_stock_value": "Valor total de estoque",
    "total_stock_quantity": "Quantidade em estoque",
    "total_locations": "Localizações",
}

SUPPLIES_INVENTORY_TURNOVER_FIELD_LABELS: dict[str, str] = {
    "inventory_turnover_months": "Giro estoque (meses)",
    "inventory_turnover_times": "Giro estoque (vezes)",
    "calculation_mode": "Modo de cálculo",
    "idd_period_valid": "Período IDD válido",
    "strict_idd_period": "Período IDD estrito",
}

SUPPLIES_NEGOTIATION_SAVINGS_FIELD_LABELS: dict[str, str] = {
    "total_savings": "Economia total",
    "savings_amount": "Valor economizado",
}

COMMERCIAL_CONVERSION_FIELD_LABELS: dict[str, str] = {
    "sales_conversion_rate_pct": "Taxa de fechamento (%)",
    "qtd_proposals": "Qtd. propostas",
    "qtd_won": "Qtd. ganhas",
}

COMMERCIAL_SALES_ORDER_OTD_FIELD_LABELS: dict[str, str] = {
    "sales_order_otd_pct": "OTD pedidos (%)",
    "total_lines": "Total de linhas",
    "on_time_lines": "Linhas no prazo",
    "late_lines": "Linhas atrasadas",
}

COMMERCIAL_ROL_FIELD_LABELS: dict[str, str] = {
    "total_rol": "ROL total",
    "new_business_rol": "ROL novos negócios",
    "new_business_rol_pct": "% ROL novos negócios",
    "new_clients_rol": "ROL clientes novos",
    "new_clients_rol_pct": "% ROL clientes novos",
    "weg_rol": "ROL WEG",
    "rol_target_pct": "% meta ROL",
    "rol_matrix": "ROL matriz",
    "rol_branch": "ROL filial",
    "total_new_clients": "Total clientes novos",
    "monthly_average": "Média mensal",
    "qtd_months": "Qtd. meses",
}

PRODUCTION_OEE_FIELD_LABELS: dict[str, str] = {
    "overall_equipment_effectiveness_pct": "OEE (%)",
    "oee_pct": "OEE (%)",
    "oee_filial_01": "OEE filial 01",
    "oee_filial_02": "OEE filial 02",
    "total_appointments": "Apontamentos",
    "valid_appointments": "Apontamentos válidos",
    "outlier_appointments": "Apontamentos fora da faixa",
    "outlier_percentage": "% fora da faixa",
}

PRODUCTION_OTD_FIELD_LABELS: dict[str, str] = {
    "on_time_delivery_pct": "OTD produção (%)",
    "otd_filial_01": "OTD filial 01",
    "otd_filial_02": "OTD filial 02",
    "late_percentage": "% atrasos",
    "total_ops_finished": "OPs finalizadas",
    "on_time_ops": "OPs no prazo",
    "late_ops": "OPs em atraso",
}

PRODUCTION_COST_FIELD_LABELS: dict[str, str] = {
    "direct_labor_cost_pct": "MOD direta / ROL (%)",
    "production_cost_pct": "Custo produção / ROL (%)",
    "depreciation_pct": "Depreciação / ROL (%)",
}

QUALITY_PPM_FIELD_LABELS: dict[str, str] = {
    "ppm": "PPM",
    "total_devolvido_un": "Total devolvido (un.)",
    "total_produzido_un": "Total produzido (un.)",
    "total_produzido_milheiro": "Total produzido (milheiro)",
    "registered_date": "Data de registro",
    "returned_quantity_original": "Qtd. devolvida (original)",
}

QUALITY_PRODUCED_QUANTITY_FIELD_LABELS: dict[str, str] = {
    "branch": "Filial",
    "product_code": "Código do produto",
    "product_type": "Tipo do produto",
    "description": "Descrição",
    "unit": "Unidade",
    "produced_milheiro": "Produzido (milheiro)",
    "produced_un": "Produzido (un.)",
    "orders_count": "Ordens de produção",
    "total_produced_milheiro": "Total produzido (milheiro)",
    "total_produced_un": "Total produzido (un.)",
    "products": "Produtos filtrados",
    "date_start": "Data inicial",
    "date_end": "Data final",
    "branches": "Filiais",
    "by_product": "Totais por produto",
    "items": "Detalhe por filial e produto",
}

QUALITY_KAIZEN_FIELD_LABELS: dict[str, str] = {
    "total_kaizens": "Total kaizens",
    "average_score": "Nota média",
    "annual_savings": "Economia projetada por ano",
}

QUALITY_KAIZEN_DETAIL_FIELD_LABELS: dict[str, str] = {
    **COMMON_SCALAR_FIELD_LABELS,
    "title": "Título",
    "date_implemented": "Data de implementação",
    "status": "Status",
    "accountable": "Responsável",
    "sector": "Setor",
    "investment": "Investimento",
    "daily_savings": "Economia por dia",
    "annual_savings": "Economia projetada por ano",
    "seconds_per_occurrence": "Segundos por ocorrência",
    "occurrences_per_day": "Ocorrências por dia",
    "hourly_cost": "Custo hora",
    "hours_saved_per_day": "Horas poupadas por dia",
}

QUALITY_AUDIT_5S_FIELD_LABELS: dict[str, str] = {
    "average_score": "Nota média 5S",
    "list_audits": "Auditorias",
}

HR_FIELD_LABELS: dict[str, str] = {
    "internal_satisfaction_pct": "Satisfação interna (%)",
    "absenteeism_pct": "Absenteísmo (%)",
    "turnover_pct": "Turnover (%)",
    "training_hours_per_collaborator": "Horas treinamento/colaborador",
    "active_pdi_count": "PDIs ativos",
    "active_pdi_pct": "% PDIs ativos",
    "total_pdis": "Total de PDIs",
    "performance_reviews_completion_pct": "Avaliações concluídas (%)",
    "completion_pct": "% conclusão",
    "completed_reviews": "Avaliações concluídas",
    "total_reviews": "Total avaliações",
    "measurement_date": "Data da medição",
}

ENGINEERING_LMP_FIELD_LABELS: dict[str, str] = {
    "total_lmps": "Total de LMPs",
    "percent_dentro_prazo": "% no prazo",
    "avg_lead_time": "Lead time médio",
    "nivel": "Nível",
    "dias_uteis_sla": "Dias úteis SLA",
    "sla_minutos": "SLA (min)",
    "engineering_status": "Status engenharia",
    "engineering_total_minutes": "Minutos engenharia",
    "data_limite": "Data limite",
    "lead_time_util": "Lead time útil",
    "qtd_pi": "Qtd. PI",
}

ENGINEERING_TRANSFORMA_MAIS_FIELD_LABELS: dict[str, str] = {
    "implemented_solutions_count": "Soluções implementadas",
    "total_net_savings_until_now": "Economia líquida acumulada",
    "total_hours_saved_until_now": "Horas economizadas acumuladas",
    "total_gross_costs_until_now": "Custos brutos acumulados",
    "total_gross_savings_in_period": "Economia bruta no período",
    "average_roi": "ROI médio",
    "gross_savings_month": "Economia bruta (mês)",
    "gross_costs_month": "Custos brutos (mês)",
    "gross_investment_month": "Investimento bruto (mês)",
    "gross_recurring_investment_month": "Invest. recorrente (mês)",
    "shared_resource_cost_month": "Custo recurso compartilhado (mês)",
    "net_savings_month": "Economia líquida (mês)",
    "accumulated_net_savings_until_now": "Economia líquida acumulada (período)",
}


def merge_kpi_field_labels(*bundles: dict[str, str] | None) -> dict[str, str]:
    merged: dict[str, str] = {}

    for bundle in bundles:
        if bundle:
            merged.update(bundle)

    return merged


ENGINEERING_LMP_DETAIL_FIELD_LABELS: dict[str, str] = merge_kpi_field_labels(
    COMMON_SCALAR_FIELD_LABELS,
    ENGINEERING_LMP_FIELD_LABELS,
    {
        "sale_number": "Nº proposta",
        "sale_description": "Descrição",
        "listing_kind": "Tipo listagem",
        "status": "Status classificação",
        "start_date": "Data início",
        "end_date": "Data fim",
        "branch": "Filial",
        "costumer_code": "Código cliente",
        "costumer_store": "Loja cliente",
        "costumer_name": "Cliente",
        "seller_code": "Código vendedor",
        "seller_name": "Vendedor",
        "qtd_engineering_entries": "Entradas engenharia",
        "qtd_engineering_closed": "Encerramentos engenharia",
        "qtd_advanced_from_engineering": "Avanços engenharia",
        "qtd_returned_from_engineering": "Retornos engenharia",
        "list_products": "Produtos",
    },
)


def kpi_fields(*bundles: dict[str, str] | None) -> dict[str, str]:
    """Rótulos comuns + metas SI + bundles específicos da rota."""
    return merge_kpi_field_labels(
        COMMON_SCALAR_FIELD_LABELS,
        SI_GOAL_FIELD_LABELS,
        *bundles,
    )


_FIELD_FORMAT_TOKENS: dict[str, tuple[str, ...]] = {
    "currency": (
        "revenue",
        "receita",
        "rol",
        "cost",
        "custo",
        "price",
        "preco",
        "saving",
        "economia",
        "investment",
        "balance",
        "saldo",
        "icms",
        "pis",
        "cofins",
        "iss",
        "ipi",
        "discount",
        "desconto",
        "return",
        "devolv",
        "tax",
        "imposto",
        "valor",
        "amount",
        "ebitda_value",
        "fixed_cost",
        "cpv_total",
        "stock_value",
        "savings",
        "depreciation",
    ),
    "percent": (
        "_pct",
        "_percent",
        "percentage",
        "taxa",
        "rate",
        "margem",
        "margin",
        "otd",
        "giro",
        "eficiencia",
        "yield",
        "turnover",
        "absenteeism",
        "satisfaction",
        "completion",
    ),
    "date": (
        "_date",
        "date_start",
        "date_end",
        "start_date",
        "end_date",
        "registered_date",
        "measurement_date",
        "data_limite",
    ),
    "quantity": (
        "qtd",
        "qty",
        "quantity",
        "_count",
        "_lines",
        "_months",
        "registros",
        "points",
        "kaizens",
        "reviews",
        "pdis",
        "lmps",
        "proposals",
        "movements",
        "hours_saved",
        "solutions",
    ),
    "days": (
        "_days",
        "pmr_days",
        "lead_time",
        "dias_uteis",
    ),
}


def infer_field_format(key: str) -> str | None:
    lowered = str(key or "").strip().lower()

    if not lowered:
        return None

    for field_format, tokens in _FIELD_FORMAT_TOKENS.items():
        if any(token in lowered for token in tokens):
            return field_format

    return None


def infer_scalar_field_formats(fields: dict[str, str] | None) -> dict[str, str]:
    if not fields:
        return {}

    inferred: dict[str, str] = {}

    for key in fields:
        field_format = infer_field_format(key)

        if field_format:
            inferred[key] = field_format

    return inferred
