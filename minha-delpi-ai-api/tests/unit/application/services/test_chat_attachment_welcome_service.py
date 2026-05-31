from app.application.services.chat_attachment_welcome_service import (
    ChatAttachmentWelcomeService,
)


def test_should_welcome_empty_message_with_attachments():
    assert ChatAttachmentWelcomeService.should_welcome(
        "",
        attachment_ids=["uuid"],
    )


def test_should_welcome_handoff_phrase():
    assert ChatAttachmentWelcomeService.should_welcome(
        "segue o anexo",
        attachment_ids=["uuid"],
    )


def test_should_not_welcome_without_attachments():
    assert not ChatAttachmentWelcomeService.should_welcome(
        "segue o anexo",
        attachment_ids=None,
    )


def test_should_not_welcome_operational_question():
    assert not ChatAttachmentWelcomeService.should_welcome(
        "qual o estoque do produto 10080001?",
        attachment_ids=["uuid"],
    )


def test_build_direct_answer_lists_filename():
    answer = ChatAttachmentWelcomeService.build_direct_answer(
        attachments=[{"original_filename": "relatorio.pdf"}],
    )

    assert answer
    assert "Arquivo recebido" in answer
    assert "relatorio.pdf" in answer
