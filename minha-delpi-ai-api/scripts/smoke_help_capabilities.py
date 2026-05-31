#!/usr/bin/env python3
"""Smoke — autoajuda Fase 1 (respostas «como uso X?» e chips de exploração)."""

from __future__ import annotations

import sys
from unittest.mock import patch

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_help_follow_up_service import ChatHelpFollowUpService


def main() -> int:
    failed = 0

    cases = (
        ("como faço pesquisa na web?", "web"),
        ("como uso a lousa?", "canvas"),
        ("como faço para gerar gráfico?", "chart"),
        ("como anexo arquivo?", "attachment"),
        ("como escolho um agente?", "agent"),
    )

    for message, expected_topic in cases:
        topic = ChatCapabilitiesService.classify_help_topic(message)

        with patch(
            "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
            return_value=True,
        ):
            answer = ChatCapabilitiesService.build_feature_answer(
                message=message,
                workspace_context={"agent": None},
                allowed_action_ids=[],
                action_catalog=[],
            )

        if topic != expected_topic:
            print(f"FAIL topic {message!r}: esperado {expected_topic}, obteve {topic}", file=sys.stderr)
            failed += 1
            continue

        if not answer:
            print(f"FAIL answer ausente para {message!r}", file=sys.stderr)
            failed += 1
            continue

        metadata: dict = {}
        ChatHelpFollowUpService.attach_to_assistant_metadata(metadata, message=message)

        if not metadata.get("helpFollowUpSuggestions"):
            print(f"FAIL chips ausentes para {message!r}", file=sys.stderr)
            failed += 1
            continue

        print(f"OK {expected_topic}: resposta + {len(metadata['helpFollowUpSuggestions'])} chips")

    general = ChatCapabilitiesService.is_capabilities_question("o que você pode fazer?")
    metadata_general: dict = {}
    ChatHelpFollowUpService.attach_to_assistant_metadata(
        metadata_general,
        message="o que você pode fazer?",
    )

    if not general or not metadata_general.get("helpFollowUpSuggestions"):
        print("FAIL chips gerais para «o que você pode fazer?»", file=sys.stderr)
        failed += 1
    else:
        print("OK geral: chips de exploração")

    from app.application.services.assistant_capabilities_catalog_validator import (
        AssistantCapabilitiesCatalogValidator,
    )

    catalog_errors = AssistantCapabilitiesCatalogValidator.validate()

    if catalog_errors:
        print(f"FAIL catalog validator: {catalog_errors[0]}", file=sys.stderr)
        failed += 1
    else:
        print("OK catalog validator")

    if failed:
        return 1

    print("Smoke help capabilities: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
