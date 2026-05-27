from app.domain.services.chat_fast_path_service import ChatFastPathService


def test_fast_path_for_greeting():
    assert ChatFastPathService.should_use("olá") is True
    assert ChatFastPathService.should_use("Oi! Tudo bem?") is False
    assert ChatFastPathService.should_use("Oi") is True


def test_fast_path_disabled_with_attachments():
    assert (
        ChatFastPathService.should_use(
            "olá",
            attachment_ids=["att-1"],
        )
        is False
    )


def test_fast_path_not_used_for_knowledge_question():
    assert ChatFastPathService.should_use("qual o estoque do produto 10080014?") is False


def test_fast_path_not_used_for_who_question():
    assert ChatFastPathService.should_use("quem é o arquiteto?") is False
