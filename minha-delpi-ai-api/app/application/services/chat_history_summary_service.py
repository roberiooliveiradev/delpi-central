import logging
from typing import Any

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_history_summary_content_service import (
    ChatHistorySummaryContentService,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.chat.history")


class ChatHistorySummaryService:
    def __init__(
        self,
        llm_gateway: LlmGatewayPort,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
    ):
        self.llm_gateway = llm_gateway
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )

    def prepare_history(
        self,
        messages,
        *,
        max_messages: int | None = None,
        summary_max_chars: int | None = None,
        memory_snapshot: dict | None = None,
    ) -> tuple[str, list]:
        from app.domain.services.chat_response_mode_context_budget_service import (
            ChatResponseModeContextBudgetService,
        )
        from app.infrastructure.llm.llm_request_context import get_active_config

        budget = None
        try:
            budget = ChatResponseModeContextBudgetService.resolve(
                get_active_config().response_mode
            )
        except Exception:
            budget = None

        keep = max(
            1,
            int(
                max_messages
                or (budget.history_max_messages if budget else None)
                or Settings.CHAT_HISTORY_MAX_MESSAGES
            ),
        )
        summary_cap = max(
            100,
            int(
                summary_max_chars
                or (budget.history_summary_max_chars if budget else None)
                or Settings.CHAT_HISTORY_SUMMARY_MAX_CHARS
            ),
        )
        intelligence = self.intelligence_settings_service.resolve()
        snapshot = memory_snapshot if isinstance(memory_snapshot, dict) else None

        if not intelligence.chat_history_summary_enabled:
            recent = list(messages[-keep:])
            # Compactação desligada: ainda preserva fatos estruturados se houver clip.
            if len(messages) > keep:
                return self.ensure_preserved_facts("", snapshot), recent
            return "", recent

        if len(messages) <= Settings.CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES:
            return "", list(messages[-keep:])

        older = list(messages[:-keep])
        recent = list(messages[-keep:])

        if not older:
            return "", recent

        priority_facts = self.build_preserved_facts_prefix(snapshot)

        try:
            summary = self._summarize(older, priority_facts=priority_facts)
        except Exception as exc:
            logger.warning("Chat history summary skipped: %s", exc)
            return self.ensure_preserved_facts("", snapshot), recent

        if not summary:
            return self.ensure_preserved_facts("", snapshot), recent

        clipped = summary[:summary_cap]

        return self.ensure_preserved_facts(clipped, snapshot), recent

    @classmethod
    def build_preserved_facts_prefix(cls, memory_snapshot: dict | None) -> str:
        if not isinstance(memory_snapshot, dict) or not memory_snapshot:
            return ""

        max_item_chars = ChatHistorySummaryContentService.limit_int(
            "maxItemChars",
            default=160,
        )
        sections: list[str] = []

        corrections = cls._collect_user_corrections(memory_snapshot)
        if corrections:
            label = ChatHistorySummaryContentService.section_label("userCorrections")
            limit = ChatHistorySummaryContentService.limit_int(
                "maxCorrections",
                default=8,
            )
            lines = [
                f"- {cls._clip_item(item, max_item_chars)}"
                for item in corrections[:limit]
            ]
            sections.append(f"{label}:\n" + "\n".join(lines))

        behavior_lines = cls._collect_behavior_lines(memory_snapshot, max_item_chars)
        if behavior_lines:
            label = ChatHistorySummaryContentService.section_label(
                "behaviorInstructions"
            )
            limit = ChatHistorySummaryContentService.limit_int(
                "maxBehaviorItems",
                default=8,
            )
            sections.append(
                f"{label}:\n"
                + "\n".join(f"- {line}" for line in behavior_lines[:limit])
            )

        focus_lines = cls._collect_operational_focus_lines(
            memory_snapshot,
            max_item_chars,
        )
        if focus_lines:
            label = ChatHistorySummaryContentService.section_label("operationalFocus")
            limit = ChatHistorySummaryContentService.limit_int(
                "maxFocusItems",
                default=12,
            )
            sections.append(
                f"{label}:\n" + "\n".join(f"- {line}" for line in focus_lines[:limit])
            )

        if not sections:
            return ""

        header = ChatHistorySummaryContentService.preserved_facts_header()

        return f"{header}\n" + "\n".join(sections)

    @classmethod
    def ensure_preserved_facts(
        cls,
        summary: str | None,
        memory_snapshot: dict | None,
    ) -> str:
        """Garante prefixo estruturado com fatos da working memory no sumário."""

        body = str(summary or "").strip()
        prefix = cls.build_preserved_facts_prefix(memory_snapshot)

        if not prefix:
            return body

        if body and prefix in body:
            return body

        if not body:
            return prefix

        return f"{prefix}\n\n{body}"

    def _summarize(self, messages: list, *, priority_facts: str = "") -> str:
        lines: list[str] = []

        for item in messages:
            role = getattr(item, "role", None) or (
                item.get("role") if isinstance(item, dict) else "unknown"
            )
            content = getattr(item, "content", None) or (
                item.get("content") if isinstance(item, dict) else ""
            )
            normalized = " ".join(str(content or "").split())

            if not normalized:
                continue

            lines.append(f"{role}: {normalized[:500]}")

        if not lines:
            return ""

        conversation = "\n".join(lines[-40:])
        system_parts = [ChatHistorySummaryContentService.system_prompt()]
        priority_instruction = ChatHistorySummaryContentService.priority_instruction()

        if priority_facts and priority_instruction:
            system_parts.append(priority_instruction)

        if priority_facts:
            user_content = ChatHistorySummaryContentService.user_prompt_with_priority(
                conversation=conversation,
                priority_facts=priority_facts,
            )
        else:
            user_content = ChatHistorySummaryContentService.user_prompt(
                conversation=conversation,
            )

        return self.llm_gateway.generate(
            [
                {
                    "role": "system",
                    "content": " ".join(part for part in system_parts if part).strip(),
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ]
        ).strip()

    @classmethod
    def _collect_user_corrections(cls, snapshot: dict) -> list[str]:
        collected: list[str] = []
        seen: set[str] = set()

        def _add(raw: Any) -> None:
            if isinstance(raw, dict):
                token = str(raw.get("content") or raw.get("text") or "").strip()
            else:
                token = str(raw or "").strip()

            if not token or token in seen:
                return

            seen.add(token)
            collected.append(token)

        top_level = snapshot.get("userCorrections")
        if isinstance(top_level, list):
            for item in top_level:
                _add(item)

        state = snapshot.get("conversationState")
        if isinstance(state, dict):
            nested = state.get("userCorrections")
            if isinstance(nested, list):
                for item in nested:
                    _add(item)

        return collected

    @classmethod
    def _collect_behavior_lines(
        cls,
        snapshot: dict,
        max_item_chars: int,
    ) -> list[str]:
        behavior = snapshot.get("behaviorInstructions")

        if not isinstance(behavior, dict) or not behavior:
            return []

        lines: list[str] = []

        for key, value in behavior.items():
            if value in (None, "", {}, []):
                continue

            if isinstance(value, (dict, list)):
                rendered = str(value)
            else:
                rendered = str(value).strip()

            if not rendered:
                continue

            lines.append(
                cls._clip_item(f"{key}={rendered}", max_item_chars),
            )

        return lines

    @classmethod
    def _collect_operational_focus_lines(
        cls,
        snapshot: dict,
        max_item_chars: int,
    ) -> list[str]:
        focus = snapshot.get("operationalFocus")

        if not isinstance(focus, dict) or not focus:
            return []

        lines: list[str] = []

        for key, value in focus.items():
            if value in (None, "", {}, []):
                continue

            if str(key).endswith("Source"):
                continue

            if isinstance(value, (dict, list)):
                rendered = str(value)
            else:
                rendered = str(value).strip()

            if not rendered:
                continue

            lines.append(cls._clip_item(f"{key}={rendered}", max_item_chars))

        return lines

    @staticmethod
    def _clip_item(value: str, max_chars: int) -> str:
        token = " ".join(str(value or "").split())

        if len(token) <= max_chars:
            return token

        return token[: max(1, max_chars - 1)].rstrip() + "…"
