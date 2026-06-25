"""Vocabulário e padrões — refinamento operacional."""

from __future__ import annotations

import re

class ChatOperationalRefinementVocabulary:
    FILTER_TERMS = (
        "filtre",
        "filtro",
        "filtrar",
        "filtra ",
        "mostre só",
        "mostre so",
        "só a filial",
        "so a filial",
        "apenas filial",
        "somente filial",
        "somente a filial",
        "restrinja",
        "restringe",
        "limitar a filial",
        "limita a filial",
    )
    BRANCH_RE = re.compile(
        r"\b(?:filial|fil\.?)\s*[_-]?\s*(\d{1,2})\b",
        re.IGNORECASE,
    )
    WAREHOUSE_RE = re.compile(
        r"\b(?:armaz[eé]m|arm\.?|deposito|depósito)\s*[_-]?\s*(\d{1,3})\b",
        re.IGNORECASE,
    )
    PAGINATED_PATH_FRAGMENTS = (
        "/parents",
        "/structure",
        "/search",
        "/stock",
        "/purchases",
        "/inspection",
        "/guide",
        "/dashboard",
        "/items",
        "/columns",
        "/system/tables",
    )
    NEXT_PAGE_TERMS = (
        "proxima pagina",
        "proxima pag",
        "seguinte pagina",
        "pagina seguinte",
        "next page",
    )
    PREV_PAGE_TERMS = (
        "pagina anterior",
        "pagina previa",
        "pagina prev",
        "previous page",
        "voltar pagina",
        "pagina de tras",
    )
    DEPTH_INCREASE_TERMS = (
        "mais niveis",
        "aprofundar",
        "ampliar niveis",
        "aumentar profundidade",
        "aumente a profundidade",
        "todos os niveis",
        "ver mais niveis",
        "expandir niveis",
        "max depth",
        "max_depth",
    )
    MAX_DEPTH_RE = re.compile(
        r"\b(?:max[_-]?depth|profundidade|niveis)\s*(?:para\s+)?(\d{1,3})\b",
        re.IGNORECASE,
    )
    MORE_RESULTS_TERMS = (
        "mais registros",
        "mais linhas",
        "mais resultados",
        "mais itens",
        "ver mais",
        "mostrar mais",
        "traga mais",
        "exiba mais",
    )
    PAGE_SIZE_PATTERNS = (
        re.compile(
            r"\b(?:aumente|aumenta|mostre|traga|exiba|liste|coloque|mude|altere|"
            r"passar?|colocar?)\s+(?:para\s+)?(\d{1,4})\s*"
            r"(?:linhas?|registros?|itens?|resultados?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:aumente|aumenta)\s+(?:o\s+)?(?:page[_-]?size|tamanho\s+da\s+pagina|"
            r"tamanho\s+da\s+página)\s+(?:para\s+)?(\d{1,4})\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bpage[_-]?size\s*[=:]?\s*(\d{1,4})\b", re.IGNORECASE),
        re.compile(
            r"\b(\d{1,4})\s*(?:linhas?|registros?|itens?|resultados?)\b",
            re.IGNORECASE,
        ),
    )
    PAGE_NUMBER_RE = re.compile(r"\bp[aá]gina\s*(\d+)\b", re.IGNORECASE)
    STOCK_RESET_TERMS = (
        "completo de novo",
        "estoque completo",
        "completo novamente",
        "tudo de novo",
        "todas as filiais",
        "todas filiais",
        "todas as filial",
        "sem filtro",
        "sem filial",
        "remova o filtro",
        "remover filtro",
        "tire o filtro",
        "mostre completo",
        "mostra completo",
        "visao completa",
        "visão completa",
    )
