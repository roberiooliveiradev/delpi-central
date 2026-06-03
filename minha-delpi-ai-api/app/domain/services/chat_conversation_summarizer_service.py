"""Resumos estruturados de conversa — Playbook memória e contexto (Fase 4)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatConversationSummarizerService:
    """Resumo extrativo/estruturado (sem LLM) para economizar contexto no prompt."""

    TRIGGER_MESSAGE_COUNT = 10
    _DECISION_RE = re.compile(
        r"\b(?:daqui\s+pra\s+frente|de\s+agora\s+em\s+diante|sempre\s+use|"
        r"prefiro\s+que|não\s+use\s+mais|nao\s+use\s+mais)\b",
        re.IGNORECASE,
    )
    _PENDING_RE = re.compile(
        r"\b(?:falta|pendente|ainda\s+preciso|depois\s+disso|pr[oó]ximo\s+passo)\b",
        re.IGNORECASE,
    )

    @classmethod
    def should_summarize(cls, previous_messages: list[Any] | None) -> bool:
        return len(previous_messages or []) >= cls.TRIGGER_MESSAGE_COUNT

    @classmethod
    def load_from_previous_messages(cls, previous_messages: list[Any] | None) -> dict[str, Any]:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "assistant":
                continue

            metadata = cls._message_metadata(item)
            snapshot = metadata.get("contextSnapshot")

            if not isinstance(snapshot, dict):
                continue

            summary = snapshot.get("conversationSummary")

            if isinstance(summary, dict) and summary.get("summary"):
                return dict(summary)

        return {}

    @classmethod
    def build(
        cls,
        *,
        previous_messages: list[Any] | None,
        snapshot: dict | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        if not cls.should_summarize(previous_messages):
            return {}

        prior = {} if force_refresh else cls.load_from_previous_messages(previous_messages)
        snap = snapshot or {}

        entities = cls._collect_entities(previous_messages, snap)
        decisions = cls._collect_decisions(previous_messages, snap)
        pending = cls._collect_pending(previous_messages, snap)
        operational = cls._build_operational_line(previous_messages, snap)
        short = cls._build_short_summary(previous_messages, snap, operational)
        resume_hint = cls._build_resume_hint(snap)

        merged_decisions = list(
            dict.fromkeys((prior.get("decisions") or []) + decisions)
        )[-12:]
        merged_pending = list(dict.fromkeys((prior.get("pending") or []) + pending))[-8:]
        merged_entities = list(
            dict.fromkeys((prior.get("entities") or []) + entities)
        )[-16:]

        summary_text = short

        if prior.get("summary") and not force_refresh and not snap.get("preferencesTopicChanged"):
            summary_text = cls._merge_summary_text(prior.get("summary"), short)

        return {
            "summary": summary_text[:800],
            "short": summary_text[:400],
            "operational": operational[:500] if operational else None,
            "entities": merged_entities,
            "decisions": merged_decisions,
            "pending": merged_pending,
            "technical": cls._build_technical_notes(previous_messages, snap),
            "resumeHint": resume_hint,
            "messageCount": len(previous_messages or []),
            "version": int(prior.get("version") or 0) + (1 if force_refresh else 0) or 1,
        }

    @classmethod
    def format_types_for_prompt(cls, summary: dict[str, Any] | None) -> list[str]:
        if not summary:
            return []

        lines: list[str] = []
        text = str(summary.get("summary") or "").strip()

        if text:
            lines.append(text)

        operational = str(summary.get("operational") or "").strip()

        if operational and operational not in text:
            lines.append(f"Operacional: {operational}")

        decisions = summary.get("decisions") or []

        if decisions:
            lines.append("Decisões: " + "; ".join(str(d) for d in decisions[:6]))

        pending = summary.get("pending") or []

        if pending:
            lines.append("Pendências: " + "; ".join(str(p) for p in pending[:5]))

        entities = summary.get("entities") or []

        if entities:
            lines.append("Entidades: " + ", ".join(str(e) for e in entities[:10]))

        resume = str(summary.get("resumeHint") or "").strip()

        if resume:
            lines.append(f"Retomada: {resume}")

        technical = str(summary.get("technical") or "").strip()

        if technical:
            lines.append(f"Técnico: {technical}")

        return lines

    @classmethod
    def _collect_entities(
        cls,
        previous_messages: list[Any] | None,
        snapshot: dict,
    ) -> list[str]:
        found: list[str] = []
        entities = dict(snapshot.get("lastEntities") or {})
        active = snapshot.get("activeEntities") or {}

        if isinstance(active, dict):
            entities.update({k: v for k, v in active.items() if v})

        if entities.get("productCode"):
            found.append(f"produto {entities['productCode']}")

        if entities.get("branch"):
            found.append(f"filial {entities['branch']}")

        if entities.get("period"):
            found.append(f"período {entities['period']}")

        codes = ChatAnalysisIntentService.extract_all_product_codes(
            *[cls._message_content(m) for m in (previous_messages or [])[-20:]],
        )

        for code in codes[:5]:
            label = f"produto {code}"

            if label not in found:
                found.append(label)

        code = ChatProductQueryIntentService.extract_last_product_code_from_messages(
            previous_messages,
        )

        if code:
            label = f"produto {code}"

            if label not in found:
                found.append(label)

        return found

    @classmethod
    def _collect_decisions(
        cls,
        previous_messages: list[Any] | None,
        snapshot: dict,
    ) -> list[str]:
        decisions: list[str] = []
        prefs = snapshot.get("userPreferences") or {}

        if isinstance(prefs, dict):
            for key, value in prefs.items():
                if value and key not in ("revoked", "topicChanged"):
                    decisions.append(f"preferência {key}")

        state = snapshot.get("conversationState") or {}

        for item in state.get("userCorrections") or []:
            if isinstance(item, dict) and item.get("content"):
                decisions.append(str(item["content"])[:120])

        for item in (previous_messages or [])[-16:]:
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item)

            if cls._DECISION_RE.search(content):
                decisions.append(content.strip()[:160])

        return list(dict.fromkeys(decisions))[-8:]

    @classmethod
    def _collect_pending(
        cls,
        previous_messages: list[Any] | None,
        snapshot: dict,
    ) -> list[str]:
        pending: list[str] = []
        state = snapshot.get("conversationState") or {}
        task = state.get("activeTask")

        if isinstance(task, dict):
            objective = str(task.get("objective") or task.get("label") or "").strip()

            if objective and str(task.get("status") or "") != "completed":
                pending.append(objective[:160])

            for item in task.get("pending") or []:
                if item:
                    pending.append(str(item)[:120])

        for paused in state.get("taskStack") or []:
            if not isinstance(paused, dict):
                continue

            label = str(paused.get("label") or paused.get("type") or "").strip()

            if label:
                pending.append(f"tarefa pausada: {label}")

        for item in (previous_messages or [])[-12:]:
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item)

            if cls._PENDING_RE.search(content):
                pending.append(content.strip()[:140])

        return list(dict.fromkeys(pending))[-6:]

    @classmethod
    def _build_operational_line(
        cls,
        previous_messages: list[Any] | None,
        snapshot: dict,
    ) -> str:
        parts: list[str] = []
        last_action = snapshot.get("lastAction")

        if isinstance(last_action, dict) and last_action.get("name"):
            params = last_action.get("params") or {}
            hint = ", ".join(f"{k}={v}" for k, v in params.items() if v)
            label = last_action["name"]

            if hint:
                parts.append(f"última consulta {label} ({hint})")
            else:
                parts.append(f"última consulta {label}")

        presentation = snapshot.get("lastPresentation")

        if isinstance(presentation, dict) and presentation.get("type"):
            parts.append(f"apresentação {presentation['type']}")

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)

            if cls._message_role(item) != "assistant":
                continue

            tool_calls = metadata.get("toolCalls") or []

            if not isinstance(tool_calls, list):
                continue

            for tool_call in tool_calls:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").strip()

                if path:
                    parts.append(f"ferramenta {path}")
                    break

            if parts:
                break

        return "; ".join(parts)

    @classmethod
    def _build_short_summary(
        cls,
        previous_messages: list[Any] | None,
        snapshot: dict,
        operational: str,
    ) -> str:
        state = snapshot.get("conversationState") or {}
        topic = str(state.get("activeTopic") or "").strip()
        task = state.get("activeTask")
        user_topics: list[str] = []

        for item in (previous_messages or [])[-8:]:
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item).strip()

            if content and len(content) > 8:
                user_topics.append(content[:100])

        parts: list[str] = []

        if topic:
            parts.append(f"Assunto: {topic}.")

        if isinstance(task, dict):
            label = str(task.get("label") or task.get("type") or "").strip()

            if label:
                parts.append(f"Tarefa: {label}.")

        if user_topics:
            parts.append(f"Pedidos recentes: {' → '.join(user_topics[-3:])}.")

        if operational:
            parts.append(operational)

        return " ".join(parts).strip() or "Conversa longa com contexto operacional ativo."

    @classmethod
    def _build_resume_hint(cls, snapshot: dict) -> str | None:
        state = snapshot.get("conversationState") or {}
        task = state.get("activeTask")

        if not isinstance(task, dict):
            return None

        objective = str(task.get("objective") or "").strip()
        label = str(task.get("label") or "").strip()

        if objective:
            return f"Continuar {label or 'tarefa'}: {objective[:200]}"

        if label:
            return f"Continuar {label}"

        return None

    @classmethod
    def _build_technical_notes(
        cls,
        previous_messages: list[Any] | None,
        snapshot: dict,
    ) -> str | None:
        hints = snapshot.get("referenceHints") or {}

        if isinstance(hints, dict) and hints.get("lastSqlSnippet"):
            return f"SQL recente: {str(hints['lastSqlSnippet'])[:200]}"

        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item)

            if re.search(r"\b(?:select|insert|update)\b", content, re.IGNORECASE):
                return f"SQL mencionado: {content[:180]}"

        return None

    @classmethod
    def _merge_summary_text(cls, prior: str, fresh: str) -> str:
        prior_norm = str(prior or "").strip()
        fresh_norm = str(fresh or "").strip()

        if not prior_norm:
            return fresh_norm

        if fresh_norm in prior_norm:
            return prior_norm

        return f"{prior_norm} {fresh_norm}"[:800]

    @staticmethod
    def _message_content(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    @staticmethod
    def _message_role(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @staticmethod
    def _message_metadata(message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}
