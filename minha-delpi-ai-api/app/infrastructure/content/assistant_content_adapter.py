from __future__ import annotations

from typing import Any

from app.domain.ports.assistant_content_port import AssistantContentPort
from app.infrastructure.content.content_service import ContentService


class InfrastructureAssistantContentAdapter(AssistantContentPort):
    def load_bundle(self, bundle: str) -> dict[str, Any]:
        normalized = str(bundle or "").strip().removesuffix(".json")
        return ContentService.load_json(f"assistant/{normalized}")

    def load_personality_playbook(self) -> dict[str, Any]:
        return ContentService.personality_playbook()

    def load_stream(self) -> dict[str, Any]:
        return ContentService.stream()

    def load_skills_catalog(self) -> dict[str, Any]:
        return ContentService.skills_catalog()

    def invalidate_cache(self, bundle: str | None = None) -> None:
        if bundle is None:
            ContentService.clear_cache()
            return

        ContentService.clear_cache()
