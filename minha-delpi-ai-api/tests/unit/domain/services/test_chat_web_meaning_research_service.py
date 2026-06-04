from app.domain.services.chat_web_meaning_research_service import (
    ChatWebMeaningResearchService,
)


def test_eligible_public_term():
    assert ChatWebMeaningResearchService.is_eligible("PKCE") is True
    assert ChatWebMeaningResearchService.is_eligible("CFW500") is True


def test_not_eligible_internal_code():
    assert ChatWebMeaningResearchService.is_eligible("10080001") is False


def test_not_eligible_when_message_sensitive():
    # mensagem com PII/operacional bloqueia a pesquisa web
    assert (
        ChatWebMeaningResearchService.is_eligible(
            "PKCE", message="qual o preço do cliente X?"
        )
        is False
    )


def test_build_query():
    assert ChatWebMeaningResearchService.build_query("PKCE") == "o que significa PKCE"


def test_permission_prompt_mentions_term():
    prompt = ChatWebMeaningResearchService.build_permission_prompt("PKCE")
    assert "PKCE" in prompt
    assert "públicas" in prompt
