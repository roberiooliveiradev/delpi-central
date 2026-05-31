"""Heurísticas de seleção para KPIs departamentais (comercial, financeiro, produção, RH, qualidade)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@dataclass(frozen=True)
class DepartmentKpiMatch:
    path_token: str
    domain_prefix: str
    reason: str
    operation_hint: str = ""


class ChatDepartmentKpiIntentService:
    """Mapeia perguntas em português para tokens de path da api-delpi (sem código de produto)."""

    _RULES: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], str], ...] = (
        # Comercial
        (
            "/commercial/",
            "closing-rate",
            ("taxa de convers", "closing rate", "conversao de venda", "fechamento de venda"),
            ("suprimentos", "compra"),
            "taxa de conversão comercial",
        ),
        (
            "/commercial/",
            "sales-order-otd",
            ("otd de pedido", "otd de venda", "otd comercial", "pedido de venda no prazo"),
            ("suprimentos", "compra", "producao"),
            "OTD de pedidos de venda (comercial)",
        ),
        (
            "/commercial/",
            "rol/series",
            ("serie de rol", "série de rol", "rol no tempo", "evolucao do rol"),
            (),
            "série temporal de ROL comercial",
        ),
        (
            "/commercial/",
            "new-clients-average",
            ("media de novos clientes", "média de novos clientes", "novos clientes media"),
            (),
            "média de novos clientes",
        ),
        (
            "/commercial/",
            "new-clients-rol-pct",
            ("rol de clientes novos", "clientes novos rol"),
            ("novos negocios",),
            "percentual ROL de clientes novos",
        ),
        (
            "/commercial/",
            "new-business-rol-pct",
            ("rol de novos negocios", "rol de novos negócios", "novos negocios rol"),
            (),
            "percentual ROL de novos negócios",
        ),
        (
            "/commercial/",
            "head_office_rol_target",
            ("meta rol matriz", "rol matriz", "meta da matriz"),
            ("filial",),
            "meta percentual ROL matriz",
        ),
        (
            "/commercial/",
            "branch_rol_target",
            ("meta rol filial", "rol filial meta"),
            ("matriz",),
            "meta percentual ROL da filial",
        ),
        # Financeiro
        (
            "/financial/",
            "ebitda",
            ("ebitda",),
            ("comercial",),
            "EBITDA percentual",
        ),
        (
            "/financial/",
            "fixed_cost",
            ("custo fixo", "custos fixos"),
            (),
            "custo fixo percentual",
        ),
        (
            "/financial/",
            "pmr",
            ("pmr", "prazo medio de recebimento", "prazo médio de recebimento"),
            ("suprimentos",),
            "PMR (prazo médio de recebimento)",
        ),
        (
            "/financial/",
            "/financial/rol",
            (
                "rol financeiro",
                "indicador rol financeiro",
                "rol do mes",
                "rol de ",
                "qual o rol",
                "quanto foi o rol",
                " qual rol",
                " o rol",
            ),
            (
                "serie",
                "série",
                "series",
                "evolucao",
                "evolução",
                "clientes novos",
                "conversao",
                "conversão",
                "novos negocios",
                "novos negócios",
                "meta rol",
                "rol matriz",
                "rol filial",
                "rolamento",
            ),
            "ROL (receita operacional líquida)",
        ),
        # Produção
        (
            "/production/",
            "overall_equipment",
            ("oee", "eficiencia de equipamento", "eficiência de equipamento"),
            (),
            "OEE (eficiência global dos equipamentos)",
        ),
        (
            "/production/",
            "direct_labor",
            ("mao de obra direta", "mão de obra direta", "custo direto de mao", "custo direto de mão"),
            (),
            "custo direto de mão de obra",
        ),
        (
            "/production/",
            "production_cost",
            ("custo de producao", "custo de produção"),
            ("mao de obra", "mão de obra"),
            "custo de produção percentual",
        ),
        (
            "/production/",
            "depreciation",
            ("depreciacao", "depreciação"),
            (),
            "depreciação percentual sobre ROL",
        ),
        (
            "/production/",
            "on_time_delivery",
            ("otd de producao", "otd de produção", "entrega no prazo producao", "entrega no prazo produção"),
            ("comercial", "compra", "suprimentos"),
            "OTD de produção",
        ),
        # RH
        (
            "/hr/",
            "branches",
            ("filiais rh", "filial rh", "lista de filiais rh", "filiais de rh"),
            ("snapshot", "pdi", "avaliacao", "avaliação"),
            "filiais de RH",
        ),
        (
            "/hr/",
            "active-pdi",
            ("pdi ativo", "pdis ativos", "plano de desenvolvimento"),
            (),
            "quantidade de PDIs ativos",
        ),
        (
            "/hr/",
            "performance-reviews",
            ("avaliacao de desempenho", "avaliação de desempenho", "avaliacoes rh", "avaliações rh"),
            (),
            "conclusão de avaliações de desempenho",
        ),
        (
            "/hr/",
            "snapshot",
            ("snapshot rh", "indicadores de rh", "headcount", "turnover rh", "painel rh"),
            ("pdi", "avaliacao"),
            "snapshot de RH",
        ),
        # Qualidade
        (
            "/quality/",
            "branches",
            ("filiais qualidade", "filial qualidade", "lista de filiais qualidade"),
            ("kaizen", "ppm", "5s", "nao conformidade", "não conformidade"),
            "filiais de qualidade",
        ),
        (
            "/quality/",
            "kaizens",
            ("kaizen",),
            (),
            "resumo de kaizens",
        ),
        (
            "/quality/",
            "audit-5s",
            ("auditoria 5s", "audit 5s", "5s"),
            (
                "nc ",
                "nao conformidade",
                "não conformidade",
                "areas",
                "áreas",
                "candidatas",
                "operacional",
                "postgresql",
            ),
            "resumo de auditoria 5S",
        ),
        (
            "/quality/",
            "ppm/internal",
            ("ppm interno", "ppm interna"),
            ("externo", "externa"),
            "PPM interno",
        ),
        (
            "/quality/",
            "ppm/external",
            ("ppm externo", "ppm externa"),
            ("interno", "interna"),
            "PPM externo",
        ),
        (
            "/quality/",
            "nonconformities/series",
            ("serie de nao conformidade", "série de não conformidade", "evolucao de nc", "evolução de nc"),
            (),
            "série temporal de não conformidades",
        ),
        (
            "/quality/",
            "nonconformities",
            ("nao conformidade", "não conformidade", "nao-conformidade", "listar nc"),
            ("serie", "série", "kaizen", "ppm", "5s", "auditoria 5s", "audit 5s"),
            "não conformidades",
        ),
        (
            "/quality/audit-5s/",
            "audits",
            ("auditorias 5s", "auditoria 5s operacional", "listar auditorias 5s"),
            ("resumo", "summary", "nc totvs"),
            "auditorias operacionais 5S (PostgreSQL)",
        ),
        (
            "/quality/audit-5s/",
            "nonconformities",
            (
                "nc 5s",
                "nao conformidade 5s",
                "não conformidade 5s",
                "nc da auditoria 5s",
                "nc operacional 5s",
            ),
            ("totvs", "protheus", "serie", "série", "ppm", "kaizen"),
            "NC operacionais da auditoria 5S (PostgreSQL)",
        ),
        (
            "/quality/audit-5s/",
            "areas",
            ("areas 5s", "áreas 5s", "areas da auditoria 5s"),
            (),
            "áreas da auditoria 5S",
        ),
        (
            "/quality/audit-5s/",
            "nc-candidates",
            ("candidatas a nc 5s", "nc candidatas 5s", "candidatas nao conformidade 5s"),
            (),
            "respostas candidatas a NC na auditoria 5S",
        ),
        # Sistema (metadados)
        (
            "/system/",
            "tables/search",
            (
                "buscar tabela",
                "pesquisar tabela",
                "qual tabela",
                "qual a tabela",
                "tabelas do protheus",
                "metadado de tabela",
            ),
            ("coluna",),
            "busca de tabelas do Protheus",
        ),
        (
            "/system/",
            "columns/search",
            ("buscar coluna", "pesquisar coluna", "colunas da tabela"),
            (),
            "busca de colunas",
        ),
    )

    @classmethod
    def resolve(cls, message: str) -> DepartmentKpiMatch | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        if cls._has_product_code(normalized):
            return None

        if cls._looks_like_supplies_domain(normalized):
            return None

        best: DepartmentKpiMatch | None = None
        best_score = 0

        for domain_prefix, path_token, keywords, excludes, label in cls._RULES:
            if any(exclude in normalized for exclude in excludes):
                continue

            score = sum(2 for keyword in keywords if keyword in normalized)

            if score <= 0:
                continue

            if "otd" in normalized and "/supplies/" in domain_prefix:
                continue

            if score > best_score:
                best_score = score
                best = DepartmentKpiMatch(
                    path_token=path_token,
                    domain_prefix=domain_prefix,
                    reason=f"A pergunta solicita {label}.",
                    operation_hint=label,
                )

        return best

    @classmethod
    def _has_product_code(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        return bool(ChatProductQueryIntentService.extract_product_code(normalized))

    @classmethod
    def _looks_like_supplies_domain(cls, normalized: str) -> bool:
        supplies_terms = (
            "cpv",
            "giro de estoque",
            "idd",
            "inventory-turnover",
            "valor total de estoque",
            "estoque da empresa",
            "estoque total",
        )

        if any(term in normalized for term in supplies_terms):
            return True

        if "otd" in normalized and any(
            term in normalized for term in ("compra", "fornecedor", "suprimentos")
        ):
            return True

        return False
