from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _identity_content() -> dict:
    return ChatAssistantContentService.load_bundle("identity")


@dataclass(frozen=True)
class ChatAgentProfile:
    name: str
    description: str
    system_prompt: str | None
    category: str | None
    metadata: dict
    platform_name: str

    @property
    def has_agent(self) -> bool:
        return bool(self.name)

    @property
    def self_description(self) -> str:
        if self.description:
            return self.description

        if self.system_prompt:
            excerpt = _excerpt_system_prompt(self.system_prompt)

            if excerpt:
                return excerpt

        placeholders = _identity_content().get("placeholders") or {}

        return str(
            placeholders.get("agentDescriptionFallback")
            or "assistente configurado para este tema."
        )


class ChatAgentProfileService:
    @classmethod
    def from_workspace(cls, workspace_context: dict | None) -> ChatAgentProfile:
        workspace = workspace_context or {}
        content = _identity_content()
        agent = workspace.get("agent") or {}
        metadata = agent.get("metadata") if isinstance(agent.get("metadata"), dict) else {}

        name = str(agent.get("name") or "").strip()
        description = str(agent.get("description") or "").strip()
        system_prompt = cls._optional_str(workspace.get("agentPrompt"))
        category = cls._optional_str(agent.get("category"))

        return ChatAgentProfile(
            name=name,
            description=description,
            system_prompt=system_prompt,
            category=category,
            metadata=dict(metadata or {}),
            platform_name=str(content.get("platformName") or "Minha DELPI"),
        )

    @classmethod
    def custom_identity_response(cls, profile: ChatAgentProfile, category: str) -> str | None:
        identity = profile.metadata.get("identity")

        if not isinstance(identity, dict):
            return None

        responses = identity.get("responses")

        if not isinstance(responses, dict):
            return None

        template = str(responses.get(category) or "").strip()

        if not template:
            return None

        return cls.format_template(template, profile)

    @classmethod
    def format_template(cls, template: str, profile: ChatAgentProfile) -> str:
        return template.format(
            platform_name=profile.platform_name,
            agent_name=profile.name,
            agent_description=profile.self_description,
            agent_category=profile.category or "",
        )

    @staticmethod
    def _optional_str(value) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None


def _excerpt_system_prompt(system_prompt: str, *, max_chars: int = 320) -> str:
    text = re.sub(r"\s+", " ", str(system_prompt or "").strip())

    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    clipped = text[:max_chars].rsplit(" ", 1)[0].strip()

    return f"{clipped}…" if clipped else text[:max_chars].strip()
