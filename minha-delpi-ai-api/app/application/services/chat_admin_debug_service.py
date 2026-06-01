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
    def resolve_client_admin_debug(
        cls,
        request,
        *,
        build_payload: dict | None,
        assistant_metadata: dict | None,
    ) -> dict | None:
        """Mescla diagnóstico do turno com memória/assertividade gravados após o attach."""
        if not cls.should_expose_to_client(request):
            return None

        merged: dict[str, Any] = dict(build_payload or {})
        admin_debug = (assistant_metadata or {}).get("adminDebug")

        if isinstance(admin_debug, dict):
            for key in (
                "memory",
                "contextAssertiveness",
                "intelligence",
                "trustSignals",
                "textCorrectionMetrics",
                "textCorrectionTask",
                "textCorrectionQuality",
                "textCorrectionPreferences",
                "textCorrectionCanvasUpdate",
                "sessionMemoryMetrics",
            ):
                value = admin_debug.get(key)

                if value is not None:
                    merged[key] = value

            pipeline = admin_debug.get("pipeline")

            if isinstance(pipeline, dict) and pipeline.get("textCorrectionMode") is not None:
                merged.setdefault("pipeline", {})
                if isinstance(merged["pipeline"], dict):
                    merged["pipeline"]["textCorrectionMode"] = pipeline["textCorrectionMode"]

        return merged or None

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
        intent_route: dict | None = None,
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
            intent_route=intent_route,
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

        trust_signals = metadata.get("trustSignals")

        if isinstance(trust_signals, list) and trust_signals:
            admin_debug_payload["trustSignals"] = trust_signals

        metadata["adminDebug"] = admin_debug_payload

    @staticmethod
    def sync_text_correction_trace(metadata: dict) -> None:
        """Replica métricas de correção textual no adminDebug após attach tardio."""
        admin_debug = metadata.get("adminDebug")

        if not isinstance(admin_debug, dict):
            return

        correction_metrics = metadata.get("textCorrectionMetrics")

        if isinstance(correction_metrics, dict):
            admin_debug["textCorrectionMetrics"] = correction_metrics

        text_task = metadata.get("textTask")

        if isinstance(text_task, dict) and text_task.get("type") == "correction":
            admin_debug["textCorrectionTask"] = {
                "subtype": text_task.get("subtype"),
                "source": text_task.get("source"),
                "deliverFinalOnly": text_task.get("deliverFinalOnly"),
                "preserveStyle": text_task.get("preserveStyle"),
            }

        quality = metadata.get("textCorrectionQuality")

        if isinstance(quality, dict):
            admin_debug["textCorrectionQuality"] = quality

        preferences = metadata.get("textCorrectionPreferences")

        if isinstance(preferences, dict):
            admin_debug["textCorrectionPreferences"] = preferences


        session_metrics = metadata.get("sessionMemoryMetrics")

        if isinstance(session_metrics, dict):
            admin_debug["sessionMemoryMetrics"] = session_metrics

        canvas_update = metadata.get("textCorrectionCanvasUpdate")

        if isinstance(canvas_update, dict):
            admin_debug["textCorrectionCanvasUpdate"] = canvas_update

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
        intent_route: dict | None = None,
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

        memory_block = None
        working_memory = workspace_context.get("workingMemory")

        if isinstance(working_memory, dict):
            from app.domain.services.chat_working_memory_service import (
                ChatWorkingMemoryService,
            )

            memory_block = ChatWorkingMemoryService.compact_for_admin_debug(working_memory)

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
                "textCorrectionMode": bool(workspace_context.get("textCorrectionMode")),
                "historySummary": cls._truncate_text(str(history_summary or ""), limits),
            },
            "intentRoute": intent_route if isinstance(intent_route, dict) else None,
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

        if memory_block is not None:
            payload["memory"] = memory_block

        from app.application.services.chat_drawing_admin_debug_service import (
            ChatDrawingAdminDebugService,
        )

        drawing_trace = ChatDrawingAdminDebugService.build_trace(
            tool_context=tool_context,
            intent_route=intent_route,
            workspace_context=workspace_context,
        )

        if drawing_trace:
            payload["drawingAnalysisTrace"] = drawing_trace
            payload["pipeline"]["drawingAnalysisMode"] = True
            payload["pipeline"]["drawingStages"] = [
                f"drawing:{phase.get('id')}:{phase.get('status')}"
                for phase in (drawing_trace.get("phases") or [])
                if isinstance(phase, dict) and phase.get("id")
            ]

            from app.application.services.chat_drawing_metrics_service import (
                ChatDrawingMetricsService,
            )

            drawing_payload = tool_context.get("drawingAnalysis")

            if isinstance(drawing_payload, dict):
                payload["drawingAnalysisMetrics"] = ChatDrawingMetricsService.build_snapshot(
                    drawing_payload,
                    report_exported=bool(
                        isinstance(tool_context.get("drawingAnalysisExport"), dict)
                        and tool_context["drawingAnalysisExport"].get("markdown")
                    ),
                    analyser_ok=ChatDrawingMetricsService.resolve_analyser_ok(tool_context),
                )

        from app.application.services.chat_document_vision_metrics_service import (
            ChatDocumentVisionMetricsService,
        )

        vision_payload = tool_context.get("documentVision")

        if isinstance(vision_payload, dict) and vision_payload:
            summary = tool_context.get("drawingPdfExtractSummary")
            char_count = None
            legible = None
            vision_context = "attachment"

            if isinstance(summary, dict):
                char_count = int(summary.get("charCount") or 0) or None
                legible = summary.get("legible")
                vision_context = "drawing"

            if char_count is None:
                char_count = int(vision_payload.get("charCount") or 0) or None

            if legible is None:
                legible = vision_payload.get("legible")

            payload["documentVisionMetrics"] = ChatDocumentVisionMetricsService.build_snapshot(
                vision_payload,
                char_count=char_count,
                legible=legible,
                context=vision_context,
            )
            title_block = vision_payload.get("titleBlock")
            title_fields = {}

            if isinstance(title_block, dict):
                fields = title_block.get("fields")

                if isinstance(fields, dict):
                    title_fields = fields

            payload["documentVisionTrace"] = {
                "engine": vision_payload.get("engine"),
                "stages": vision_payload.get("stages"),
                "legibilityScore": vision_payload.get("legibilityScore"),
                "durationMs": vision_payload.get("durationMs"),
                "charCount": char_count,
                "bomRowCount": vision_payload.get("bomRowCount"),
                "tableCount": vision_payload.get("tableCount")
                or (
                    len(vision_payload.get("tables") or [])
                    if isinstance(vision_payload.get("tables"), list)
                    else None
                ),
                "hasTitleBlock": bool(title_block),
                "titleBlockCode": title_fields.get("code"),
                "titleBlockRev": title_fields.get("rev"),
                "context": vision_context,
            }
            payload["pipeline"]["documentVision"] = True

        from app.domain.services.chat_web_search_admin_metrics_service import (
            ChatWebSearchAdminMetricsService,
        )

        web_search_debug = ChatWebSearchAdminMetricsService.build_admin_debug_web_search(
            tool_context=tool_context,
        )

        if web_search_debug:
            payload["webSearch"] = web_search_debug
            payload["pipeline"]["webSearch"] = True

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

