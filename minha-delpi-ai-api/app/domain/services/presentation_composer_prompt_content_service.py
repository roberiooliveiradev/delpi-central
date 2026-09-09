"""Loader JSON `presentation_composer_prompts` — system/repair/knobs do Spec composer."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "presentation_composer_prompts"

_DEFAULT_SYSTEM = (
    "You propose a PresentationSpec JSON for analytics visualization. "
    "Use only candidate field keys provided. Never invent fields, hex colors, "
    "CSS, or JavaScript. Respond with JSON only."
)
_DEFAULT_REPAIR = (
    "Previous JSON was invalid. Fix it. Errors: {errors}. Previous output:\n{previous}"
)


class PresentationComposerPromptContentService:
    @classmethod
    def system_prompt(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "systemPrompt", default=_DEFAULT_SYSTEM)
            or _DEFAULT_SYSTEM
        ).strip()

    @classmethod
    def repair_prompt(cls, *, errors: list[str], previous: str) -> str:
        import json

        template = str(
            ChatAssistantContentService.get(
                _BUNDLE, "repairPromptTemplate", default=_DEFAULT_REPAIR
            )
            or _DEFAULT_REPAIR
        )
        return template.format(
            errors=json.dumps(errors, ensure_ascii=False),
            previous=str(previous or "")[:2000],
        )

    @classmethod
    def allowed_palette_families(cls) -> list[str]:
        values = ChatAssistantContentService.list(_BUNDLE, "allowedPaletteFamilies")
        return [str(item).strip() for item in values if str(item or "").strip()]

    @classmethod
    def rules(cls) -> list[str]:
        values = ChatAssistantContentService.list(_BUNDLE, "rules")
        return [str(item).strip() for item in values if str(item or "").strip()]

    @classmethod
    def knobs_by_view(cls) -> dict[str, list[str]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "knobsByView")
        if not isinstance(node, dict):
            return {}
        payload: dict[str, list[str]] = {}
        for key, value in node.items():
            if isinstance(value, list):
                payload[str(key)] = [str(item) for item in value if str(item or "").strip()]
        return payload

    @classmethod
    def prompt_contract_keys(cls) -> set[str]:
        """Keys expected in FakeLlm / snapshot tests."""
        return {
            "systemPrompt",
            "repairPromptTemplate",
            "allowedPaletteFamilies",
            "rules",
            "knobsByView",
            "allowedViews",
        }
