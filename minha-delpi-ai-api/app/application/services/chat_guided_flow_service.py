"""Fluxos guiados com passos e chips — Playbook interatividade, Fase 5."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _capabilities_content() -> dict[str, Any]:
    return ContentService.load_json("assistant/capabilities")


_GUIDE_REQUEST_TERMS = (
    "como consult",
    "como faço",
    "como faco",
    "como uso",
    "como usar",
    "passo a passo",
    "me guie",
    "me guia",
    "fluxo guiado",
    "tutorial",
    "por onde comeco",
    "por onde começo",
    "primeiros passos",
)


_FLOW_TOPIC_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("stock", ("estoque", "saldo", "armazem", "armazém")),
    ("product", ("produto", "ficha", "cadastro", "codigo", "código")),
    ("suppliers", ("fornecedor", "fornecedores")),
    ("sales", ("venda", "vendas", "ov", "ordem de venda", "faturamento")),
    ("purchases", ("compra", "compras")),
    ("lmp", ("lmp", "lmps", "lista de material")),
    ("attachment", ("anexo", "anexar", "arquivo", "pdf")),
    ("indicators", ("indicador", "kpi", "rol", "ebitda", "ppm")),
    ("web", ("pesquisa na web", "pesquisar na web", "internet")),
)


class ChatGuidedFlowService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        workspace_context: dict | None = None,
    ) -> None:
        if ChatCapabilitiesService.is_capabilities_question(message):
            cards = cls.build_capability_cards(workspace_context=workspace_context)

            if cards:
                metadata["guidedFlowCards"] = cards

        flow = cls.build_for_message(message)

        if not flow:
            return

        metadata["guidedFlow"] = flow

        suggestions = cls._step_suggestions(flow)

        if suggestions:
            metadata["guidedFlowSuggestions"] = suggestions

    @classmethod
    def is_guided_flow_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > 200:
            return False

        if any(term in normalized for term in _GUIDE_REQUEST_TERMS):
            return True

        if ChatCapabilitiesService.is_capability_inquiry(message):
            return True

        return False

    @classmethod
    def detect_flow_id(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        best_id: str | None = None
        best_score = 0

        for flow_id, markers in _FLOW_TOPIC_MARKERS:
            score = sum(1 for marker in markers if marker in normalized)

            if score > best_score:
                best_score = score
                best_id = flow_id

        if best_id:
            return best_id

        topic = ChatCapabilitiesService.classify_help_topic(message)

        topic_map = {
            "web": "web",
            "canvas": "product",
            "chart": "indicators",
            "attachment": "attachment",
            "agent": "product",
        }

        return topic_map.get(topic or "")

    @classmethod
    def build_for_message(cls, message: str) -> dict[str, Any] | None:
        if not cls.is_guided_flow_request(message):
            return None

        flow_id = cls.detect_flow_id(message)

        if not flow_id:
            return None

        return cls.build_flow(flow_id)

    @classmethod
    def build_flow(cls, flow_id: str) -> dict[str, Any] | None:
        flows = _capabilities_content().get("guidedFlows") or {}
        raw = flows.get(flow_id)

        if not isinstance(raw, dict):
            return None

        title = str(raw.get("title") or "").strip()

        if not title:
            return None

        steps = cls._normalize_steps(raw.get("steps"))

        if not steps:
            return None

        return {
            "id": str(raw.get("id") or flow_id).strip() or flow_id,
            "title": title,
            "intro": str(raw.get("intro") or "").strip() or None,
            "steps": steps,
        }

    @classmethod
    def build_capability_cards(
        cls,
        *,
        workspace_context: dict | None = None,
    ) -> list[dict[str, Any]]:
        interactive = _capabilities_content().get("interactive") or {}
        cards = interactive.get("cards")

        if not isinstance(cards, list):
            return []

        from app.application.services.chat_workspace_agent_activation_service import (
            ChatWorkspaceAgentActivationService,
        )

        operational_enabled = ChatWorkspaceAgentActivationService.operational_tools_enabled(
            workspace_context,
        )
        operational_flow_ids = {
            str(item).strip().lower()
            for item in (interactive.get("operationalCardFlowIds") or [])
            if str(item or "").strip()
        }

        result: list[dict[str, Any]] = []

        for card in cards:
            if not isinstance(card, dict):
                continue

            flow_id = str(card.get("flowId") or "").strip().lower()

            if not operational_enabled and flow_id in operational_flow_ids:
                continue

            title = str(card.get("title") or "").strip()

            if not title:
                continue

            suggestions = []

            for item in card.get("suggestions") or []:
                if not isinstance(item, dict):
                    continue

                label = str(item.get("label") or "").strip()
                query = str(item.get("query") or "").strip()

                if label and query:
                    suggestions.append({"label": label, "query": query})

            result.append(
                {
                    "title": title,
                    "description": str(card.get("description") or "").strip() or None,
                    "flowId": str(card.get("flowId") or "").strip() or None,
                    "suggestions": suggestions,
                }
            )

        return result

    @classmethod
    def _normalize_steps(cls, raw_steps: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_steps, list):
            return []

        steps: list[dict[str, Any]] = []

        for index, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue

            text = str(step.get("text") or "").strip()

            if not text:
                continue

            suggestion = None
            raw_suggestion = step.get("suggestion")

            if isinstance(raw_suggestion, dict):
                label = str(raw_suggestion.get("label") or "").strip()
                query = str(raw_suggestion.get("query") or "").strip()

                if label and query:
                    suggestion = {"label": label, "query": query}

            steps.append(
                {
                    "order": int(step.get("order") or index),
                    "text": text,
                    "suggestion": suggestion,
                }
            )

        return steps

    @classmethod
    def _step_suggestions(cls, flow: dict[str, Any]) -> list[dict[str, str]]:
        suggestions: list[dict[str, str]] = []

        for step in flow.get("steps") or []:
            if not isinstance(step, dict):
                continue

            raw = step.get("suggestion")

            if not isinstance(raw, dict):
                continue

            label = str(raw.get("label") or "").strip()
            query = str(raw.get("query") or "").strip()

            if label and query:
                suggestions.append({"label": label, "query": query})

        return suggestions
