from app.domain.services.chat_text_context_resolver_service import ChatTextContextResolverService


def test_extract_inline_after_colon():
    ctx = ChatTextContextResolverService.resolve("corrija: o produto esta bloqueado")

    assert ctx["hasInlineText"] is True
    assert "bloqueado" in (ctx.get("inlineText") or "")


def test_references_previous_message():
    ctx = ChatTextContextResolverService.resolve(
        "resuma a resposta anterior",
        previous_messages=[{"role": "assistant", "content": "Texto longo da resposta."}],
    )

    assert ctx["referencesPrevious"] is True
    assert ctx.get("priorSnippet")
