from app.domain.services.chat_attachment_content_service import (
    ChatAttachmentContentService,
)


def test_welcome_block_loads_from_attachments_json():
    block = ChatAttachmentContentService.welcome_block()

    assert block.get("title") == "Arquivo recebido."
    assert "resumo" in (block.get("bullets") or [])


def test_canvas_clarification_uses_content_templates():
    answer = ChatAttachmentContentService.clarification_answer(
        ["a última resposta", "a tabela"],
    )

    assert "lousa" in answer.lower()
    assert "última resposta" in answer


def test_follow_up_queries_mapped():
    queries = ChatAttachmentContentService.follow_up_queries()

    assert queries.get("Resumir") == "resuma o conteúdo do arquivo anexado"
