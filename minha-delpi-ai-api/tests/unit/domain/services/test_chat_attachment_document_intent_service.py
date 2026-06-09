from app.domain.services.chat_attachment_document_intent_service import (
    ChatAttachmentDocumentIntentService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService


def test_is_document_content_question_boleto_style():
    assert ChatAttachmentDocumentIntentService.is_document_content_question(
        "o que esta escrito no arquivo?"
    )


def test_is_image_describe_question():
    assert ChatAttachmentDocumentIntentService.is_image_describe_question(
        "descreva a imagem anexada"
    )
    assert ChatAttachmentDocumentIntentService.is_document_content_question(
        "o que tem na foto anexada?"
    )


def test_is_document_content_question_negative_operational():
    assert not ChatAttachmentDocumentIntentService.is_document_content_question(
        "qual o estoque do produto 10080001?"
    )


def test_classify_attachment_document_with_attachment_ids():
    route = ChatIntentRouterService.classify(
        "o que esta escrito no arquivo?",
        attachment_ids=["att-1"],
    )

    assert route.intent == "attachment_task"
    assert "attachment_document" in route.flags
    assert route.requires_tool is False
    assert route.requires_rag is True


def test_resolve_executed_attachment_document_beats_empty_tools_stage():
    route = ChatIntentRouterService.resolve_executed(
        message="o que esta escrito no arquivo?",
        pipeline_stages=[
            "ingress",
            "attachment_document",
            "post_tool",
            "rag",
        ],
        tool_calls=[],
        attachment_ids=["att-1"],
    )

    assert route.intent == "attachment_document"
    assert "stage:attachment_document" in route.flags
