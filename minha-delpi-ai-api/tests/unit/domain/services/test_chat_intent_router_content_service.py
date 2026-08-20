"""Loader canônico intent_router — padrões e limites."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_assistant_content_service import (
    invalidate_assistant_content_cache,
)
from app.domain.services.chat_intent_router_content_service import (
    ChatIntentRouterContentService,
)

configure_domain_infrastructure_ports()
invalidate_assistant_content_cache("intent_router")
ChatIntentRouterContentService.invalidate_cache()


def test_short_context_reply_patterns_compile():
    patterns = ChatIntentRouterContentService.short_context_reply_patterns()
    assert patterns
    assert any(p.fullmatch("filial 02") for p in patterns)
    assert any(p.fullmatch("10080055") for p in patterns)


def test_short_context_reply_max_chars_from_json():
    assert ChatIntentRouterContentService.limit_int("shortContextReplyMaxChars", 0) == 48
