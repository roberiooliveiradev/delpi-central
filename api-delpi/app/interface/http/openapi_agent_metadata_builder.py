"""Metadados OpenAPI derivados de route_contract_registry — vocabulário generalista."""

from __future__ import annotations

import re

from app.interface.http.openapi_agent_metadata import agent_route
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS, RouteContract

_DOMAIN_LABELS: dict[str, str] = {
    "/commercial/": "Comercial",
    "/financial/": "Financeiro",
    "/production/": "Produção",
    "/hr/": "Recursos Humanos",
    "/quality/": "Qualidade",
    "/supplies/": "Suprimentos",
    "/engineering/": "Engenharia",
    "/products/": "Produto",
    "/sales/": "Vendas",
    "/purchases/": "Compras",
    "/inspecoes-entrada/": "Inspeções de entrada",
    "/pedidos-venda-abertos/": "Pedidos de venda em aberto",
    "/propostas-comerciais/": "Propostas comerciais",
    "/system/": "Sistema",
}

_ENTITY_LABELS: dict[str, str] = {
    "commercial_rol_target": "meta percentual ROL comercial",
    "commercial_rol_series": "série temporal de ROL comercial",
    "production_order_detail": "detalhe de ordem de produção por OP",
    "open_sales_order": "pedidos de venda em aberto",
    "open_production_order": "OPs abertas (pedidos de venda)",
    "commercial_proposal_document": "proposta comercial interna (PDF/Totvs)",
    "commercial_proposal": "propostas comerciais",
    "sales_conversion_rate": "taxa de fechamento comercial",
    "new_clients_average": "média de novos clientes",
    "sales_order_otd": "OTD de pedidos de venda",
    "sales_order_otd_panel": "Painel OTD de pedidos de venda",
    "sales_order_otd_series": "Série temporal OTD de pedidos de venda",
    "sales_order_otd_line": "Detalhe de linha OTD de pedido de venda",
    "new_business_rol_pct": "percentual ROL de novos negócios",
    "new_clients_rol_pct": "percentual ROL de clientes novos",
    "financial_rol": "ROL financeiro",
    "financial_ebitda_pct": "EBITDA percentual",
    "financial_fixed_cost_pct": "custo fixo percentual",
    "financial_pmr": "prazo médio de recebimento (PMR)",
    "hr_snapshot": "snapshot de RH",
    "hr_branch": "filiais de RH",
    "hr_active_pdi_count": "PDIs ativos",
    "hr_performance_reviews_completion": "conclusão de avaliações de desempenho",
    "direct_labor_cost_pct": "custo direto de mão de obra",
    "production_cost_pct": "custo de produção percentual",
    "depreciation_pct": "depreciação percentual",
    "refugos_custo_x_rol": "custo de refugo sobre ROL",
    "retrabalho_custo_x_rol": "custo de retrabalho sobre ROL",
    "overall_equipment_effectiveness": "OEE (eficiência global dos equipamentos)",
    "production_otd": "OTD de produção",
    "supplies_safety_stock_detail": (
        "detalhe de estoque de segurança com cobertura de compras, "
        "empenhos e extrato projetado de saldo"
    ),
    "supplies_safety_stock_supplier": (
        "fornecedores vinculados ao produto com última compra"
    ),
    "supplies_safety_stock_supplier_price_history": (
        "histórico de preço unitário do produto com um fornecedor"
    ),
    "supplies_safety_stock_item": "itens de estoque de segurança",
    "supplies_safety_stock_summary": "resumo de estoque de segurança",
    "supplies_safety_stock_filters": "filtros de estoque de segurança",
    "supplies_safety_stock_consumption_analysis_summary": (
        "resumo da análise de consumo versus estoque de segurança sugerido"
    ),
    "supplies_safety_stock_consumption_analysis_item": (
        "itens da análise de consumo e estoque de segurança sugerido"
    ),
    "supplies_safety_stock_consumption_analysis_detail": (
        "detalhe da análise de consumo com série mensal e memória de cálculo"
    ),
}

_SHAPE_SUMMARY_PREFIX: dict[str, str] = {
    "scalar": "Indicador",
    "paged_list": "Lista paginada",
    "hierarchy": "Hierarquia",
    "product_snapshot": "Ficha",
    "composite_analysis": "Análise consolidada",
    "playbook_report": "Relatório operacional",
    "list": "Lista",
}


class OpenApiAgentMetadataBuilder:
    @classmethod
    def from_contract(cls, operation_id: str, *, path: str = "") -> dict:
        contract = ROUTE_CONTRACTS.get(str(operation_id or "").strip())

        if contract is None:
            raise KeyError(f"operationId sem contrato: {operation_id!r}")

        label = cls.entity_label(contract.entity)
        summary = cls.summary_for(contract, label)
        description = cls.description_for(contract, label, path=path)

        return agent_route(
            summary=summary,
            description=description,
            operation_id=str(operation_id).strip(),
        )

    @classmethod
    def entity_label(cls, entity: str) -> str:
        key = str(entity or "").strip()

        if not key:
            return "consulta operacional"

        if key in _ENTITY_LABELS:
            return _ENTITY_LABELS[key]

        return cls._humanize_entity(key)

    @classmethod
    def summary_for(cls, contract: RouteContract, label: str) -> str:
        prefix = _SHAPE_SUMMARY_PREFIX.get(contract.shape, "Consulta")

        if contract.shape == "scalar" and "meta" in label:
            return f"{prefix} — {label.capitalize()}"

        return f"{prefix} — {label.capitalize()}"

    @classmethod
    def description_for(cls, contract: RouteContract, label: str, *, path: str) -> str:
        domain = cls._domain_label(path)
        shape_hint = cls._shape_hint(contract.shape)
        parts = [
            f"Retorna {label} via API DELPI.",
            shape_hint,
        ]

        if domain:
            parts.append(f"Domínio: {domain}.")

        parts.append(
            "Filtros comuns: filial (branch), date_start/date_end ou start_date/end_date quando aplicável."
        )

        if contract.shape == "paged_list":
            parts.append("Suporta paginação (page, page_size).")

        return " ".join(parts)

    @staticmethod
    def _domain_label(path: str) -> str:
        lowered = str(path or "").lower()

        for prefix, label in _DOMAIN_LABELS.items():
            if lowered.startswith(prefix):
                return label

        return ""

    @staticmethod
    def _shape_hint(shape: str) -> str:
        hints = {
            "scalar": "Indicador agregado ou KPI pontual.",
            "paged_list": "Lista paginada de registros.",
            "hierarchy": "Estrutura hierárquica (BOM, pais, árvore).",
            "product_snapshot": "Snapshot cadastral ou operacional de um item.",
            "composite_analysis": "Visão consolidada com múltiplas seções.",
            "playbook_report": "Relatório operacional do playbook (REST, sem SQL).",
            "list": "Lista de itens sem paginação obrigatória.",
        }

        return hints.get(shape, "Resposta estruturada para consumo no chat.")

    @staticmethod
    def _humanize_entity(entity: str) -> str:
        tokens = re.split(r"[_\s]+", entity.strip().lower())
        acronyms = {
            "rol": "ROL",
            "otd": "OTD",
            "oee": "OEE",
            "pmr": "PMR",
            "pdi": "PDI",
            "lmp": "LMP",
            "nc": "NC",
            "hr": "RH",
            "cpv": "CPV",
            "kpi": "KPI",
            "mp": "MP",
            "pa": "PA",
        }
        words: list[str] = []

        for token in tokens:
            if not token:
                continue

            words.append(acronyms.get(token, token))

        phrase = " ".join(words)

        return phrase or entity.replace("_", " ")
