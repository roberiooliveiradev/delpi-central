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


def test_source_citation_templates_from_json():
    single = ChatAttachmentContentService.source_citation_single(
        filename="contrato.pdf",
    )
    multiple = ChatAttachmentContentService.source_citation_multiple(
        filenames="a.pdf, b.pdf",
    )

    assert "**contrato.pdf**" in single
    assert "**a.pdf, b.pdf**" in multiple


def test_canvas_responses_load_from_attachments_json():
    disabled = ChatAttachmentContentService.canvas_text("disabled")

    assert "lousa" in disabled.lower()
    assert "não está habilitada" in disabled.lower()

    copied = ChatAttachmentContentService.canvas_text(
        "simpleCopySuccess",
        title="Perfil",
    )

    assert "«Perfil»" in copied
    assert ChatAttachmentContentService.canvas_default_title() == "Conteúdo do chat"
