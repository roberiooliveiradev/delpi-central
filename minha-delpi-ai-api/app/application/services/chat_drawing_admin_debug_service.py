"""Traço de diagnóstico admin para análise de desenhos — Onda 12 / critério adminDebug."""

from __future__ import annotations

from typing import Any


class ChatDrawingAdminDebugService:
    @classmethod
    def build_trace(
        cls,
        *,
        tool_context: dict | None,
        intent_route: dict | None = None,
        workspace_context: dict | None = None,
    ) -> dict[str, Any] | None:
        tool_context = tool_context if isinstance(tool_context, dict) else {}
        intent_route = intent_route if isinstance(intent_route, dict) else {}
        workspace_context = workspace_context if isinstance(workspace_context, dict) else {}

        intent_name = str(intent_route.get("intent") or "").strip()
        drawing_mode = bool(tool_context.get("drawingAnalysisMode"))

        if intent_name != "drawing_analysis" and not drawing_mode:
            return None

        if drawing_mode and intent_name != "drawing_analysis":
            intent_name = "drawing_analysis"

        skills = workspace_context.get("skills") if isinstance(
            workspace_context.get("skills"), dict
        ) else {}
        skill_enabled = bool(skills.get("drawingAnalysis"))

        analysis = tool_context.get("drawingAnalysis")
        analysis = analysis if isinstance(analysis, dict) else {}

        pdf_summary = tool_context.get("drawingPdfExtractSummary")
        pdf_summary = pdf_summary if isinstance(pdf_summary, dict) else {}

        has_pdf = bool(
            analysis.get("hasPdfAttachment")
            or pdf_summary
            or pdf_summary.get("productCode")
        )

        phases: list[dict[str, Any]] = []

        phases.append(
            {
                "id": "intent",
                "label": "Intent desenho",
                "status": "ok",
                "detail": intent_name or "drawing_analysis",
            }
        )

        phases.append(
            {
                "id": "skill",
                "label": "Skill drawing-analysis-delpi",
                "status": "ok" if skill_enabled else "blocked",
                "detail": "habilitada" if skill_enabled else "desabilitada no agente",
            }
        )

        if has_pdf:
            legible = pdf_summary.get("legible")

            if legible is False:
                pdf_status = "warn"
                pdf_detail = str(pdf_summary.get("reason") or "PDF ilegível ou vazio")
            else:
                pdf_status = "ok"
                parts = [
                    f"código={pdf_summary.get('productCode') or analysis.get('productCode') or '—'}",
                    f"rev={pdf_summary.get('revision') or analysis.get('revisionPdf') or '—'}",
                ]

                if pdf_summary.get("componentCount") is not None:
                    parts.append(f"componentes={pdf_summary.get('componentCount')}")

                pdf_detail = ", ".join(parts)

            phases.append(
                {
                    "id": "pdf_extraction",
                    "label": "Extração PDF",
                    "status": pdf_status,
                    "detail": pdf_detail,
                }
            )
        else:
            phases.append(
                {
                    "id": "pdf_extraction",
                    "label": "Extração PDF",
                    "status": "skip",
                    "detail": "Sem PDF anexado neste turno",
                }
            )

        analyser = cls._find_analyser_tool_call(tool_context.get("toolCalls") or [])

        if analyser:
            metadata = analyser.get("metadata") if isinstance(analyser.get("metadata"), dict) else {}
            ok = bool(metadata.get("ok"))
            phases.append(
                {
                    "id": "analyser",
                    "label": "API GET /products/{code}/analyser",
                    "status": "ok" if ok else "error",
                    "detail": cls._format_analyser_detail(metadata, analyser),
                    "path": metadata.get("path"),
                    "statusCode": metadata.get("statusCode"),
                    "actionId": metadata.get("actionId"),
                }
            )
        elif drawing_mode and skill_enabled:
            phases.append(
                {
                    "id": "analyser",
                    "label": "API GET /products/{code}/analyser",
                    "status": "skip",
                    "detail": "Consulta não executada (gate ou resposta direta)",
                }
            )

        if analysis:
            critical = int(analysis.get("criticalErrors") or 0)
            phases.append(
                {
                    "id": "validation",
                    "label": "Validação PDF × API × checklist",
                    "status": "ok",
                    "detail": (
                        f"status={analysis.get('status') or '—'}, "
                        f"críticos={critical}, "
                        f"itens={len(analysis.get('items') or [])}"
                    ),
                    "criticalErrors": critical,
                }
            )
        else:
            phases.append(
                {
                    "id": "validation",
                    "label": "Validação PDF × API × checklist",
                    "status": "skip",
                    "detail": "Relatório estruturado não gerado neste turno",
                }
            )

        export_payload = tool_context.get("drawingAnalysisExport")

        if isinstance(export_payload, dict) and export_payload.get("markdown"):
            phases.append(
                {
                    "id": "report",
                    "label": "Relatório e export",
                    "status": "ok",
                    "detail": str(export_payload.get("filename") or "markdown"),
                }
            )
        elif analysis.get("items"):
            phases.append(
                {
                    "id": "report",
                    "label": "Relatório e export",
                    "status": "warn",
                    "detail": "Análise sem payload de export em metadata",
                }
            )
        else:
            phases.append(
                {
                    "id": "report",
                    "label": "Relatório e export",
                    "status": "skip",
                    "detail": "Sem relatório consolidado",
                }
            )

        return {
            "active": True,
            "phases": phases,
            "summary": {
                "intent": intent_name or "drawing_analysis",
                "skillEnabled": skill_enabled,
                "hasPdfAttachment": has_pdf,
                "productCode": analysis.get("productCode") or pdf_summary.get("productCode"),
                "criticalErrors": analysis.get("criticalErrors"),
                "overallStatus": analysis.get("status"),
            },
        }

    @classmethod
    def extend_pipeline_stages(
        cls,
        stages: list[str] | None,
        trace: dict[str, Any] | None,
    ) -> list[str]:
        merged = list(stages or [])

        if not isinstance(trace, dict) or not trace.get("active"):
            return merged

        for phase in trace.get("phases") or []:
            if not isinstance(phase, dict):
                continue

            phase_id = str(phase.get("id") or "").strip()
            status = str(phase.get("status") or "skip").strip()

            if not phase_id:
                continue

            token = f"drawing:{phase_id}:{status}"

            if token not in merged:
                merged.append(token)

        return merged

    @classmethod
    def _find_analyser_tool_call(cls, tool_calls: list) -> dict[str, Any] | None:
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            path = str(metadata.get("path") or "").lower()

            if "/analyser" in path:
                return tool_call

        return None

    @classmethod
    def _format_analyser_detail(cls, metadata: dict, tool_call: dict) -> str:
        arguments = tool_call.get("arguments") if isinstance(tool_call.get("arguments"), dict) else {}
        code = str(arguments.get("code") or arguments.get("productCode") or "").strip()
        status_code = metadata.get("statusCode")
        parts = []

        if code:
            parts.append(f"código={code}")

        if status_code is not None:
            parts.append(f"HTTP {status_code}")

        if metadata.get("ok"):
            parts.append("OK")
        else:
            parts.append("falha")

        return ", ".join(parts) if parts else "executado"
