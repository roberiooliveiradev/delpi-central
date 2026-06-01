"""Casos de regressão Playbook 08 — pesquisa web confiável (W1–W15)."""

WEB_SEARCH_RESEARCH_CASES = [
    {
        "id": "W1",
        "message": "pesquise na web sobre norma NR-10",
        "expect_web": True,
    },
    {
        "id": "W2",
        "message": "corrija a gramatica deste texto: ola mundo",
        "expect_web": False,
        "text_task_pure": True,
    },
    {
        "id": "W3",
        "message": "qual o estoque do produto 10080001",
        "expect_web": False,
    },
    {
        "id": "W4",
        "message": "pesquise na web manual oficial WEG CFW500",
        "expect_prefer_official": True,
        "expect_site_query": True,
    },
    {
        "id": "W5",
        "message": "pesquise na web noticias recentes sobre WEG 2026",
        "expect_recent_query": True,
    },
    {
        "id": "W6",
        "message": "busque na web datasheet conector industrial",
        "expect_intent": "technical_document_search",
    },
    {
        "id": "W7",
        "message": "pesquise na internet sobre produto xyz inexistente 999",
        "expect_low_confidence_empty": False,
    },
    {
        "id": "W8",
        "message": "pesquise na web sobre heat shrink tubing specifications",
        "expect_english_retry": True,
    },
    {
        "id": "W11",
        "message": "nao pesquise na web, apenas resuma o texto acima",
        "expect_web": False,
        "expect_decline": True,
    },
    {
        "id": "W13",
        "message": "pesquise na web uma pesquisa profunda sobre alternativas ao CFW500",
        "expect_mode": "deep",
        "expect_min_queries": 2,
    },
    {
        "id": "W14",
        "message": "pesquise na web pesquisa rapida o que e IP67",
        "expect_mode": "quick",
    },
    {
        "id": "W15",
        "expect_web": True,
        "message": (
            "pesquise na web se o cliente ABC comprou nosso produto 10080001 "
            "pelo preco interno R$ 12,30"
        ),
        "expect_redacted": True,
        "expect_no_price_in_query": True,
    },
]
