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

    actions: list[dict] = []

    try:
        actions = AssistantCapabilitiesCatalogGenerator.load_actions_from_database()
    except Exception as exc:
        print(f"WARN actions DB indisponível no smoke: {exc}", file=sys.stderr)

    generated = AssistantCapabilitiesCatalogGenerator.generate(actions=actions)
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

    if not catalog_payload.get("contextualHighlights"):
        print("FAIL catalog contextualHighlights vazio", file=sys.stderr)
        failed += 1
    else:
        print("OK catalog contextualHighlights (Fase 5)")

    if not catalog_payload.get("features") or not catalog_payload.get("quickPrompts"):
        print(f"FAIL assistant catalog API shape ({catalog_payload.keys()})", file=sys.stderr)
        failed += 1
    else:
        print("OK assistant catalog service (Fase 4)")

    onboarding = catalog_payload.get("onboarding") or {}

    if not onboarding.get("starterCards") or len(onboarding.get("tourSteps") or []) < 5:
        print(f"FAIL onboarding payload ({onboarding.keys()})", file=sys.stderr)
        failed += 1
    else:
        print("OK catalog onboarding (Playbook 10)")

    profiles = onboarding.get("profiles") or []

    if len(profiles) < 5:
        print(f"FAIL onboarding profiles ({len(profiles)})", file=sys.stderr)
        failed += 1
    else:
        print("OK catalog onboarding profiles")

    commercial = ChatAssistantCatalogService(agent_repository=None).build_response(
        user_id=uuid4(),
        onboarding_profile_id="commercial",
        limit=6,
    )
    commercial_cards = (commercial.get("onboarding") or {}).get("starterCards") or []

    if not commercial_cards or not any("venda" in str(card.get("query") or "").lower() for card in commercial_cards):
        print("FAIL onboarding profile commercial cards", file=sys.stderr)
        failed += 1
    else:
        print("OK onboarding profileId=commercial")

    import subprocess
    import sys as _sys

    identity_check = subprocess.run(
        [_sys.executable, "scripts/check_identity_catalog_alignment.py"],
        cwd=None,
        capture_output=True,
        text=True,
    )

    if identity_check.returncode != 0:
        print(
            identity_check.stderr.strip() or identity_check.stdout.strip(),
            file=_sys.stderr,
        )
        failed += 1
    else:
        print("OK identity ↔ catálogo")

    if failed:
        return 1

    print("Smoke features catalog: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
