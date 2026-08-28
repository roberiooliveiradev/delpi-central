"""Adapter LLM para classificação residual de follow-up (enum only)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.ports.follow_up_turn_classifier_port import FollowUpTurnClassifierPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)


class InfrastructureFollowUpTurnClassifierAdapter(FollowUpTurnClassifierPort):
    def __init__(self, llm_gateway: LlmGatewayPort) -> None:
        self._llm = llm_gateway

    def classify(
        self,
        message: str,
        last_action_summary: dict[str, Any] | None = None,
    ) -> str | None:
        summary = "{}"
        if isinstance(last_action_summary, dict) and last_action_summary:
            parts = [
                f"{key}={last_action_summary.get(key)}"
                for key in ("path", "name", "operationId", "apiRouteDomain")
                if last_action_summary.get(key)
            ]
            params = last_action_summary.get("params")
            if isinstance(params, dict) and params:
                parts.append(f"params={params}")
            summary = "; ".join(parts) or "{}"

        system = ChatFollowUpTurnContentService.classifier_prompt_system()
        user = ChatFollowUpTurnContentService.classifier_prompt_user(
            message=message,
            last_action_summary=summary,
        )
        if not system or not user:
            return None

        raw = self._llm.generate(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        text = str(raw or "").strip().lower()
        if not text:
            return None

        # Primeira linha / token que bata no catálogo.
        allowed = ChatFollowUpTurnContentService.classifier_labels()
        first = re.split(r"[\s,;]+", text)[0].strip(" .\"'`")
        if first in allowed:
            return first
        for label in allowed:
            if label in text:
                return label
        return None
