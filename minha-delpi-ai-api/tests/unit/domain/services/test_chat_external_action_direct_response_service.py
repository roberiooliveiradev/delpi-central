from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)


def test_should_skip_rag_when_external_action_ran():
    assert ChatExternalActionDirectResponseService.should_skip_rag(
        {"skipRag": True, "directAnswer": None}
    )


def test_resolve_answer_returns_trimmed_text():
    answer = ChatExternalActionDirectResponseService.resolve_answer(
        {"directAnswer": "  Produto 10080055: cabo.  "}
    )

    assert answer == "Produto 10080055: cabo."


def test_iter_stream_chunks_splits_paragraphs():
    chunks = list(
        ChatExternalActionDirectResponseService.iter_stream_chunks(
            "Título\n\nLinha 1\n\nLinha 2"
        )
    )

    assert chunks == ["Título", "\n\n", "Linha 1", "\n\n", "Linha 2"]
