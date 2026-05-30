#!/usr/bin/env python3
"""Smoke local: detecção e início da resposta para frases de capacidades."""

from app.application.services.chat_capabilities_service import ChatCapabilitiesService

PHRASES = (
    "o que vc faz?",
    "o que vc é capaz de fazer?",
    "o que você pode fazer?",
    "ajuda",
)

COMMON = {"agent": None, "agentId": None}
AGENT = {
    "agent": {"name": "Especialista em Produtos"},
    "agentId": "11111111-1111-4111-8111-111111111111",
}


def main() -> None:
    catalog = [
        {
            "actionId": "act.stock",
            "method": "GET",
            "path": "/api/v1/products/{code}/stock",
            "summary": "Estoque",
        },
    ]

    for label, ctx, allowed in (
        ("CHAT COMUM", COMMON, []),
        ("AGENTE", AGENT, ["act.stock"]),
    ):
        print(f"\n=== {label} ===")
        for phrase in PHRASES:
            ok = ChatCapabilitiesService.is_capabilities_question(phrase)
            print(f"  [{('OK' if ok else 'FALHA')}] {phrase!r}")
            if not ok:
                continue
            text = ChatCapabilitiesService.build_direct_answer(
                workspace_context=ctx,
                allowed_action_ids=allowed,
                action_catalog=catalog if allowed else [],
            )
            print(f"       -> {text.splitlines()[0]}")


if __name__ == "__main__":
    main()
