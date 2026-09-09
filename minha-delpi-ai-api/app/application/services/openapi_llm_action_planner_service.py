"""Planner LLM estruturado OpenAPI-first — escolhe só entre top-K do catálogo.

Sempre ativo no stack OpenAPI-first (mesmo gateway de prosa/chat). Fail-soft:
erro/parse inválido → ``None`` e o planner determinístico assume.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)

logger = logging.getLogger("minha-delpi-ai-api.openapi.planner")


class OpenApiLlmActionPlannerService:
    """Adapter ``(message, slim_catalog) -> plan dict`` para ``PlanExternalActionsService``."""

    def __init__(self, llm_gateway: LlmGatewayPort | None) -> None:
        self.llm_gateway = llm_gateway

    @classmethod
    def from_stack(cls) -> OpenApiLlmActionPlannerService | None:
        """Wire canônico: sempre usa ``make_llm_gateway()`` (prosa/chat)."""
        try:
            from app.composition.llm_composer import make_llm_gateway

            return cls(make_llm_gateway())
        except Exception:
            logger.exception("openapi_llm_planner_gateway_unavailable")
            return None

    def __call__(
        self,
        message: str,
        slim_catalog: list[dict[str, Any]],
        *,
        conversation_context: str = "",
        candidate_set_id: str = "",
        repair: bool = False,
    ) -> dict[str, Any] | None:
        if self.llm_gateway is None or not slim_catalog:
            return None
        try:
            payload = self._generate(
                message,
                slim_catalog,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
                repair=repair,
            )
        except Exception:
            logger.exception("openapi_llm_planner_failed")
            return None
        if not isinstance(payload, dict):
            if repair:
                return None
            return self.__call__(
                message,
                slim_catalog,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
                repair=True,
            )
        if "steps" not in payload and "clarify" not in payload and "mode" not in payload:
            if repair:
                return None
            return self.__call__(
                message,
                slim_catalog,
                conversation_context=conversation_context,
                candidate_set_id=candidate_set_id,
                repair=True,
            )
        return payload

    def _generate(
        self,
        message: str,
        slim_catalog: list[dict[str, Any]],
        *,
        conversation_context: str = "",
        candidate_set_id: str = "",
        repair: bool = False,
    ) -> dict[str, Any] | None:
        system = OpenApiToolRoutingContentService.get(
            "planner",
            "llmSystemPrompt",
            default=(
                "You are an OpenAPI action planner. Choose only actionId values from the "
                "provided catalog. Return JSON with keys steps and optional clarify. "
                "Never invent paths, URLs or actionIds."
            ),
        )
        user_template = OpenApiToolRoutingContentService.get(
            "planner",
            "llmUserTemplate",
            default=(
                "Message:\n{message}\n\nConversation context:\n{conversation_context}\n\n"
                "Catalog JSON:\n{catalog}\n\nCandidate set: {candidate_set_id}\n\nSchema:\n{schema}"
            ),
        )
        schema = OpenApiToolRoutingContentService.get_node("planner", "schema") or {}
        user = str(user_template).format(
            message=message,
            catalog=json.dumps(slim_catalog, ensure_ascii=False),
            schema=json.dumps(schema, ensure_ascii=False),
            conversation_context=conversation_context or "(none)",
            candidate_set_id=candidate_set_id or "",
        )
        if repair:
            user = (
                user
                + "\n\nReturn ONLY valid JSON matching the schema. No markdown, no commentary."
            )
        raw = self.llm_gateway.generate(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        return self._extract_json(raw)

    @classmethod
    def _extract_json(cls, raw: str) -> dict[str, Any] | None:
        text = str(raw or "").strip()
        if not text:
            return None
        try:
            payload = json.loads(text)
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            return None
