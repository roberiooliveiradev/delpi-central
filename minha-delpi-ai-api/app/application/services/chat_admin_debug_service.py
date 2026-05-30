from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ChatAdminDebugLimits:
    max_text_chars: int = 20000
    max_llm_messages: int = 20
    max_json_chars: int = 200000


class ChatAdminDebugService:
    """Monta payload de diagnóstico do turno (RAG, tools, prompt, pipeline).

    O payload é **sempre** persistido em `metadata.adminDebug` para análise interna.
    A **exposição** ao cliente (resposta HTTP/SSE/histórico) depende de permissão admin.
    """

    @staticmethod
    def should_expose_to_client(request) -> bool:
        """True quando a rota autorizou envio do diagnóstico na resposta (usuário admin)."""
        return bool(getattr(request, "admin_debug", False))

    @classmethod
    def payload_for_client(cls, request, payload: dict | None) -> dict | None:
        if payload is None or not cls.should_expose_to_client(request):
            return None
        return payload

    @classmethod
    def build_for_turn(
        cls,
        request,
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
        _ = request  # reservado; persistência não depende de permissão do solicitante

        payload = cls.build(
            workspace_context=workspace_context,
            tool_context=tool_context,
            rag=rag,
            llm_messages=llm_messages,
            history_summary=history_summary,
            operational_optimize=operational_optimize,
            analysis_mode=analysis_mode,
            fast_path=fast_path,
            skip_rag=skip_rag,
            limits=limits,
        )
        payload["recordedAt"] = datetime.now(timezone.utc).isoformat()
        return payload

    @staticmethod
    def attach_to_assistant_metadata(
        metadata: dict,
        admin_debug_payload: dict | None,
        intelligence_metadata: dict | None = None,
    ) -> None:
        if admin_debug_payload is None:
            return

        if intelligence_metadata:
            admin_debug_payload["intelligence"] = ChatAdminDebugService._compact_intelligence(
                intelligence_metadata
            )

        metadata["adminDebug"] = admin_debug_payload

    @staticmethod
    def _compact_intelligence(intelligence_metadata: dict) -> dict:
        payload: dict[str, Any] = {}

        for key in (
            "timings",
            "pipeline",
            "nativeToolCalling",
            "agentic",
            "toolCount",
            "ragSourceCount",
            "topRagScore",
        ):
            value = intelligence_metadata.get(key)

            if value is not None:
                payload[key] = value

        return payload

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

        rag_sources = rag.get("sources") or []
        rag_context_raw = str(rag.get("context") or "")
        rag_debug: dict[str, Any] = {
            "sources": rag_sources,
            "ragContextText": rag_context_text,
        }
        if rag_context_raw.strip() and not rag_sources:
            rag_debug["sourcesNote"] = (
                "Fontes globais/admin não são expostas ao cliente; o texto do RAG "
                "ainda foi injetado no prompt."
            )

        payload = {
            "workspace": {
                "agentId": workspace_context.get("agentId"),
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
            "rag": rag_debug,
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

