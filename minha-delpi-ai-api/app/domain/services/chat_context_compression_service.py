"""Compactação de contexto conversacional — Playbook memória e contexto (Fase 4)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_conversation_summarizer_service import (
    ChatConversationSummarizerService,
)


class ChatContextCompressionService:
    """Compressão estruturada e por prioridade para o bloco de memória no prompt."""

    MAX_PROMPT_CHARS = 1200
    STRATEGY_STRUCTURED_PRIORITY = "structured_priority"
    STRATEGY_EXTRACTIVE = "extractive"
    STRATEGY_HIERARCHICAL = "hierarchical"

    @classmethod
    def should_compress(cls, previous_messages: list[Any] | None) -> bool:
        return ChatConversationSummarizerService.should_summarize(previous_messages)

    @classmethod
    def apply_to_snapshot(
        cls,
        snapshot: dict,
        *,
        previous_messages: list[Any] | None,
        message: str | None = None,
    ) -> dict:
        result = dict(snapshot)

        if not cls.should_compress(previous_messages):
            return result

        force = bool(result.get("preferencesTopicChanged"))
        summary = ChatConversationSummarizerService.build(
            previous_messages=previous_messages,
            snapshot=result,
            force_refresh=force,
        )

        if not summary:
            return result

        compressed = cls.compress(
            summary,
            previous_messages=previous_messages,
            snapshot=result,
            current_message=message,
        )
        result["conversationSummary"] = summary
        result["compressedContext"] = compressed
        return result

    @classmethod
    def compress(
        cls,
        summary: dict[str, Any],
        *,
        previous_messages: list[Any] | None = None,
        snapshot: dict | None = None,
        current_message: str | None = None,
    ) -> dict[str, Any]:
        structured = cls._structured_payload(summary, snapshot)
        extractive = cls._extractive_snippets(previous_messages, max_items=4)
        priority_block = cls._priority_block(summary, snapshot)
        prompt_text = cls._build_prompt_text(
            summary,
            priority_block=priority_block,
            extractive=extractive,
            current_message=current_message,
        )

        return {
            "strategy": cls.STRATEGY_HIERARCHICAL
            if len(previous_messages or []) >= 20
            else cls.STRATEGY_STRUCTURED_PRIORITY,
            "structured": structured,
            "extractiveSnippets": extractive,
            "priorityBlock": priority_block,
            "promptText": prompt_text[: cls.MAX_PROMPT_CHARS],
            "charBudget": cls.MAX_PROMPT_CHARS,
            "messageCount": len(previous_messages or []),
        }

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        compressed = (snapshot or {}).get("compressedContext")

        if isinstance(compressed, dict) and compressed.get("promptText"):
            return "Resumo da conversa (compactado):\n" + str(compressed["promptText"]).strip()

        summary = (snapshot or {}).get("conversationSummary")

        if not isinstance(summary, dict):
            return None

        lines = ChatConversationSummarizerService.format_types_for_prompt(summary)

        if not lines:
            return None

        return "Resumo da conversa:\n" + "\n".join(f"- {line}" for line in lines)

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        summary = (snapshot or {}).get("conversationSummary") or {}
        compressed = (snapshot or {}).get("compressedContext") or {}

        return {
            "summaryLoaded": bool(summary.get("summary")),
            "compressionStrategy": compressed.get("strategy"),
            "entitiesCount": len(summary.get("entities") or []),
            "decisionsCount": len(summary.get("decisions") or []),
            "pendingCount": len(summary.get("pending") or []),
            "promptChars": len(str(compressed.get("promptText") or "")),
            "messageCount": summary.get("messageCount"),
        }

    @classmethod
    def _structured_payload(
        cls,
        summary: dict[str, Any],
        snapshot: dict | None,
    ) -> dict[str, Any]:
        snap = snapshot or {}
        state = snap.get("conversationState") or {}

        return {
            "summary": summary.get("summary"),
            "entities": summary.get("entities") or [],
            "decisions": summary.get("decisions") or [],
            "pending": summary.get("pending") or [],
            "operational": summary.get("operational"),
            "activeTopic": state.get("activeTopic"),
            "activeTaskType": (state.get("activeTask") or {}).get("type")
            if isinstance(state.get("activeTask"), dict)
            else None,
        }

    @classmethod
    def _priority_block(cls, summary: dict[str, Any], snapshot: dict | None) -> str:
        lines: list[str] = []
        snap = snapshot or {}

        for item in summary.get("decisions") or []:
            lines.append(f"[decisão] {item}")

        for item in summary.get("pending") or []:
            lines.append(f"[pendência] {item}")

        prefs = snap.get("preferencesApplied") or []

        for pref in prefs[:6]:
            lines.append(f"[preferência] {pref}")

        corrections = (snap.get("conversationState") or {}).get("userCorrections") or []

        if corrections:
            last = corrections[-1]

            if isinstance(last, dict) and last.get("content"):
                lines.append(f"[correção] {last['content']}")

        for entity in summary.get("entities") or []:
            lines.append(f"[entidade] {entity}")

        return "\n".join(lines[:14])

    @classmethod
    def _extractive_snippets(
        cls,
        previous_messages: list[Any] | None,
        *,
        max_items: int,
    ) -> list[str]:
        snippets: list[str] = []

        for item in (previous_messages or [])[-24:]:
            role = ChatConversationSummarizerService._message_role(item)
            content = ChatConversationSummarizerService._message_content(item).strip()

            if not content or role not in ("user", "assistant"):
                continue

            normalized = " ".join(content.split())

            if len(normalized) < 12:
                continue

            prefix = "Usuário" if role == "user" else "Assistente"
            snippets.append(f"{prefix}: {normalized[:220]}")

        return snippets[-max_items:]

    @classmethod
    def _build_prompt_text(
        cls,
        summary: dict[str, Any],
        *,
        priority_block: str,
        extractive: list[str],
        current_message: str | None,
    ) -> str:
        parts: list[str] = []
        main = str(summary.get("summary") or "").strip()

        if main:
            parts.append(main)

        if priority_block:
            parts.append(priority_block)

        if extractive:
            parts.append("Trechos recentes:\n" + "\n".join(extractive))

        resume = str(summary.get("resumeHint") or "").strip()

        if resume:
            parts.append(resume)

        if current_message and len(str(current_message).strip()) > 4:
            parts.append(f"Mensagem atual: {str(current_message).strip()[:200]}")

        return "\n\n".join(part for part in parts if part).strip()
