from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatAdminDebugLimits:
    max_text_chars: int = 20000
    max_llm_messages: int = 20
    max_json_chars: int = 200000


class ChatAdminDebugService:
    """Monta payload de diagnóstico para admins.

    Importante: este payload pode conter contexto amplo (RAG, tools, prompt).
    Deve ser exposto apenas quando o backend determinar que o usuário é admin.
    """

    @classmethod
    def build(
        cls,
        *,
        workspace_context: dict,
        tool_context: dict,
        rag: dict,
        llm_messages: list[dict],
        history_summary: str,
        operational_optimize: bool,
        analysis_mode: bool,
        fast_path: bool,
        skip_rag: bool,
        limits: ChatAdminDebugLimits | None = None,
    ) -> dict:
        limits = limits or ChatAdminDebugLimits()

        tool_context_text = cls._truncate_text(str(tool_context.get("context") or ""), limits)
        rag_context_text = cls._truncate_text(str(rag.get("context") or ""), limits)

        compact_llm_messages: list[dict] = []
        for msg in (llm_messages or [])[: limits.max_llm_messages]:
            if not isinstance(msg, dict):
                continue
            compact_llm_messages.append(
                {
                    "role": msg.get("role"),
                    "name": msg.get("name"),
                    "content": cls._truncate_text(str(msg.get("content") or ""), limits),
                }
            )

        payload = {
            "workspace": {
                "agentKey": workspace_context.get("agentKey"),
                "agent": workspace_context.get("agent"),
                "project": workspace_context.get("project"),
                "skills": workspace_context.get("skills"),
                "specialization": workspace_context.get("specialization"),
                "actionsEnabled": workspace_context.get("actionsEnabled"),
                "actionProviderKeys": workspace_context.get("actionProviderKeys"),
                "allowedActionIdsCount": len(workspace_context.get("allowedActionIds") or []),
            },
            "pipeline": {
                "operationalOptimize": bool(operational_optimize),
                "analysisMode": bool(analysis_mode),
                "fastPath": bool(fast_path),
                "skipRag": bool(skip_rag),
                "historySummary": cls._truncate_text(str(history_summary or ""), limits),
            },
            "tooling": {
                "toolCalls": tool_context.get("toolCalls") or [],
                "selectedExternalAction": tool_context.get("selectedExternalAction"),
                "toolContextText": tool_context_text,
            },
            "rag": {
                "sources": rag.get("sources") or [],
                "ragContextText": rag_context_text,
            },
            "llm": {
                "messages": compact_llm_messages,
            },
        }

        # Evita explodir a resposta com payload gigante acidental.
        serialized = json.dumps(payload, ensure_ascii=False, default=str)
        if len(serialized) > limits.max_json_chars:
            payload["warning"] = (
                "adminDebug truncado por limite de tamanho; reduza contexto para inspecionar."
            )
            # Remove o mais pesado primeiro
            payload["llm"]["messages"] = []
            payload["tooling"]["toolContextText"] = cls._truncate_text(
                payload["tooling"]["toolContextText"], ChatAdminDebugLimits(max_text_chars=4000)
            )
            payload["rag"]["ragContextText"] = cls._truncate_text(
                payload["rag"]["ragContextText"], ChatAdminDebugLimits(max_text_chars=4000)
            )

        return payload

    @staticmethod
    def _truncate_text(text: str, limits: ChatAdminDebugLimits) -> str:
        value = str(text or "")
        if len(value) <= limits.max_text_chars:
            return value
        return value[: limits.max_text_chars].rstrip() + "\n…(truncado)"

