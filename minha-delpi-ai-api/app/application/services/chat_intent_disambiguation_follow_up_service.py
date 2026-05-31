"""Chips de desambiguação de roteamento na resposta do assistente — Playbook 02."""

from __future__ import annotations

from typing import Any


class ChatIntentDisambiguationFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        suggestions: list[dict[str, str]] | None,
    ) -> None:
        if not isinstance(metadata, dict) or not suggestions:
            return

        metadata["routingDisambiguationSuggestions"] = list(suggestions)
