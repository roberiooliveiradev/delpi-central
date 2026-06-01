from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_web_search_source_follow_up_service import (
    ChatWebSearchSourceFollowUpService,
)


def test_list_sources_request_detected():
    assert ChatWebSearchSourceFollowUpService.is_list_sources_request(
        "liste os links das fontes da pesquisa web acima"
    )


def test_build_list_links_from_recent_web_search():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "webSearchResearch": {
                    "searchStatus": "success",
                    "query": "delpi conexoes eletricas",
                    "sourceCount": 2,
                    "sites": [
                        {
                            "title": "Delpi Conexões Elétricas",
                            "url": "https://delpi.com.br/delpi-conexoes-eletricas/",
                        },
                        {
                            "title": "Delpi",
                            "url": "https://delpi.com.br/",
                        },
                    ],
                },
                "sources": [
                    {
                        "title": "Delpi Conexões Elétricas",
                        "sourceRef": "https://delpi.com.br/delpi-conexoes-eletricas/",
                        "sourceType": "web",
                    },
                ],
            },
        },
    ]

    answer = ChatWebSearchSourceFollowUpService.build_list_links_answer(
        "liste os links das fontes da pesquisa web acima",
        history,
    )

    assert answer is not None
    assert "delpi.com.br/delpi-conexoes-eletricas" in answer
    assert "1." in answer


def test_data_reference_without_tool_allows_web_follow_up():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "webSearchResearch": {
                    "searchStatus": "success",
                    "sourceCount": 1,
                },
            },
        },
    ]

    assert not ChatAnalysisIntentService.is_data_reference_without_tool_data(
        "liste os links das fontes da pesquisa web acima",
        history,
    )


def test_summarize_from_web_snippets():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "webSearchResearch": {
                    "searchStatus": "success",
                    "query": "motor weg",
                    "sourceCount": 1,
                    "sites": [{"title": "WEG", "url": "https://weg.net/", "isOfficial": True}],
                },
                "toolCalls": [
                    {
                        "name": "web_search",
                        "data": {
                            "searchStatus": "success",
                            "results": [
                                {
                                    "title": "Catálogo WEG",
                                    "url": "https://weg.net/cat",
                                    "snippet": "Motor trifásico 5 CV, tensão 380 V.",
                                },
                            ],
                        },
                    },
                ],
            },
        },
    ]

    answer = ChatWebSearchSourceFollowUpService.build_summarize_answer(
        "resuma em tópicos os resultados da pesquisa web sobre motor weg",
        history,
    )

    assert answer is not None
    assert "Motor trifásico" in answer or "5 CV" in answer


def test_compare_sources_requires_two_snippets():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "webSearchResearch": {"searchStatus": "success", "query": "delpi"},
                "toolCalls": [
                    {
                        "name": "web_search",
                        "data": {
                            "searchStatus": "success",
                            "results": [
                                {
                                    "title": "A",
                                    "url": "https://a.example/",
                                    "snippet": "Dado A 10 mm.",
                                },
                                {
                                    "title": "B",
                                    "url": "https://b.example/",
                                    "snippet": "Dado B 20 mm.",
                                },
                            ],
                        },
                    },
                ],
            },
        },
    ]

    answer = ChatWebSearchSourceFollowUpService.build_compare_sources_answer(
        "compare as fontes da pesquisa web sobre delpi e destaque divergências",
        history,
    )

    assert answer is not None
    assert "Comparação" in answer


def test_blocks_external_when_web_follow_up():
    history = [
        {
            "role": "assistant",
            "metadata": {"webSearchResearch": {"searchStatus": "success", "sourceCount": 1}},
        },
    ]

    assert ChatWebSearchSourceFollowUpService.blocks_external_action_selection(
        "resuma em tópicos os resultados da pesquisa web sobre delpi",
        history,
    )


def test_phone_in_web_summary_is_not_product_code():
    text = "Contato (47) 3370-5502 — Jaraguá do Sul SC"

    assert ChatProductQueryIntentService.extract_product_code(text) is None
