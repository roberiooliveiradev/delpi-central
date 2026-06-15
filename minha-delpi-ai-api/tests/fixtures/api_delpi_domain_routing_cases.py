"""Casos de roteamento api-delpi agrupados por domínio — mock sem HTTP à API real.

Fonte: docs/roadmap/api-delpi-chat-intelligence-audit.md (tabela de regressão).
"""

from __future__ import annotations

from tests.fixtures.chat_intelligence_regression_cases import SELECTION_CASES

# Mensagens de auditoria por domínio (ordem estável para relatório do smoke).
AUDIT_DOMAIN_MESSAGES: dict[str, list[str]] = {
    "products": [
        "liste produtos do grupo MP",
        "resumo do produto 10080047",
        "ficha completa do produto 10080047",
        "faturamento do produto 10080047",
        "estoque do produto 10080047",
    ],
    "engineering": [
        "kpis do painel de LMPs",
        "processos do transforma mais",
    ],
    "supplies": [
        "qual o valor total de estoque",
        "qual o CPV da filial 01 no último mês",
        "mostre o OTD de compras",
    ],
    "sales": [
        "listar ordens de venda da semana",
    ],
    "commercial": [
        "taxa de conversão de vendas",
    ],
    "financial": [
        "qual o ebitda do último trimestre",
        "pmr da filial 02",
    ],
    "production": [
        "oee da produção",
        "dashboard eficiencia fabril com resultado mod",
    ],
    "quality": [
        "resumo de kaizens do mês",
    ],
    "system": [
        "colunas da tabela SB1",
        "qual a tabela de produtos?",
    ],
}

_CASE_BY_MESSAGE = {case["message"]: case for case in SELECTION_CASES}


def build_domain_routing_cases() -> list[dict]:
    cases: list[dict] = []

    for domain, messages in AUDIT_DOMAIN_MESSAGES.items():
        for message in messages:
            base = _CASE_BY_MESSAGE.get(message)

            if base is None:
                raise KeyError(
                    f"Caso de seleção ausente para domínio {domain!r}: {message!r}"
                )

            cases.append({**base, "domain": domain})

    return cases


DOMAIN_ROUTING_CASES: list[dict] = build_domain_routing_cases()
