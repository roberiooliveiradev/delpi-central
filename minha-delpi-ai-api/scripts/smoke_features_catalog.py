#!/usr/bin/env python3
"""Smoke — catálogo de funcionalidades (autoajuda Fase 2)."""

from __future__ import annotations

import sys
from unittest.mock import patch

from app.application.services.assistant_capabilities_registry import (
    AssistantCapabilitiesRegistry,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService


def main() -> int:
    failed = 0

    version = AssistantCapabilitiesRegistry.catalog_version()

    if not version:
        print("FAIL catalog version vazio", file=sys.stderr)
        failed += 1
    else:
        print(f"OK catalog version={version}")

    web = AssistantCapabilitiesRegistry.get_feature("web_search")

    if not web or web.get("helpTopicId") != "web":
        print(f"FAIL feature web_search ({web})", file=sys.stderr)
        failed += 1
    else:
        print("OK feature web_search")

    search = AssistantCapabilitiesRegistry.search("lousa")

    if not search or search[0].get("id") != "canvas":
        print(f"FAIL search lousa ({search})", file=sys.stderr)
        failed += 1
    else:
        print("OK search lousa")

    notes = AssistantCapabilitiesRegistry.format_release_notes_answer()

    if not notes:
        print("FAIL release notes vazio", file=sys.stderr)
        failed += 1
    else:
        print("OK release notes")

    with patch(
        "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
        return_value=True,
    ):
        answer = ChatCapabilitiesService.resolve_capability_answer(
            message="o que mudou na última versão?",
            workspace_context={},
            allowed_action_ids=[],
            action_catalog=[],
        )

    if not answer or "novidade" not in answer.lower():
        print(f"FAIL resolve release notes ({answer})", file=sys.stderr)
        failed += 1
    else:
        print("OK resolve «o que mudou?»")

    from uuid import uuid4

    from app.application.services.assistant_capabilities_catalog_generator import (
        AssistantCapabilitiesCatalogGenerator,
    )
    from app.application.services.chat_assistant_catalog_service import (
        ChatAssistantCatalogService,
    )

    generated = AssistantCapabilitiesCatalogGenerator.generate(actions=[])
    drift = AssistantCapabilitiesCatalogGenerator.drift_report(
        on_disk=AssistantCapabilitiesCatalogGenerator.load_catalog(),
        generated=generated,
    )

    if drift:
        print(f"FAIL catalog generator drift: {drift[0]}", file=sys.stderr)
        failed += 1
    else:
        print("OK catalog generator sincronizado (Fase 3)")

    catalog_payload = ChatAssistantCatalogService(agent_repository=None).build_response(
        user_id=uuid4(),
        query="estoque",
        limit=6,
    )

    if not catalog_payload.get("features") or not catalog_payload.get("quickPrompts"):
        print(f"FAIL assistant catalog API shape ({catalog_payload.keys()})", file=sys.stderr)
        failed += 1
    else:
        print("OK assistant catalog service (Fase 4)")

    if failed:
        return 1

    print("Smoke features catalog: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
