"""Formatação de metadata e contexto de external actions — Fase 3C lote 10."""

from __future__ import annotations

import json

from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.infrastructure.config.settings import Settings


class ChatToolContextExternalActionFormatter:
    def __init__(self, presenter: ExternalActionResultPresenter) -> None:
        self._presenter = presenter

    def _attach_request_sql(self, data, arguments=None, metadata=None):
        from app.domain.services.external_actions.external_action_sql_capability_service import (
            ExternalActionSqlCapabilityService,
        )

        return ExternalActionSqlCapabilityService.attach_request_sql_to_data(
            data,
            arguments=arguments,
            metadata=metadata,
        )

    def _build_safe_tool_metadata(
            self,
            tool_name: str,
            metadata: dict | None,
            data,
        ) -> dict:
            safe_metadata = dict(metadata or {})

            if tool_name == "execute_external_action":
                safe_metadata["responsePreview"] = self._build_response_preview(data)
                path = str(safe_metadata.get("path") or "")
                attached_data = self._attach_request_sql(data, None, safe_metadata)
                operational_root = self._presenter._unwrap_data(attached_data)

                if isinstance(operational_root, dict):
                    from app.domain.services.chat_operational_commentary_enrichment_service import (
                        ChatOperationalCommentaryEnrichmentService,
                    )

                    ChatOperationalCommentaryEnrichmentService.enrich_metadata(
                        safe_metadata,
                        data=operational_root,
                        format_quantity=lambda value, field_key=None: self._presenter._format_field_value(
                            str(field_key or "available_quantity"),
                            value,
                        ),
                    )

                humanized = self._presenter.present(
                    attached_data,
                    path=path,
                )

                if isinstance(humanized, dict):
                    linhas = [
                        str(line).strip()
                        for line in (humanized.get("linhas") or [])
                        if str(line or "").strip()
                    ]
                    decision = safe_metadata.get("presentationDecision")

                    if (
                        isinstance(decision, dict)
                        and str(decision.get("selected") or "").strip().lower() == "kpi"
                        and linhas
                    ):
                        titulo = str(humanized.get("titulo") or "").strip()
                        linhas = [
                            titulo or "Indicadores disponíveis no painel de KPIs.",
                        ]

                    if humanized.get("titulo") or linhas:
                        titulo = str(humanized.get("titulo") or "").strip()

                        if titulo == "Lista de LMPs" and (
                            "eficiencia-fabril" in path.lower()
                            or "eficiencia_fabril" in path.lower()
                        ):
                            titulo = "Eficiência fabril"

                        safe_metadata["humanizedSummary"] = {
                            "titulo": titulo,
                            "linhas": linhas,
                        }
                        self._merge_data_commentary_into_humanized_summary(safe_metadata)

            return safe_metadata

    @staticmethod
    def _merge_data_commentary_into_humanized_summary(metadata: dict) -> None:
        from app.domain.services.chat_humanized_data_response_service import (
            ChatHumanizedDataResponseService,
        )

        commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(metadata)
        humanized = metadata.get("humanizedSummary")

        if not isinstance(commentary, dict) or not isinstance(humanized, dict):
            return

        lines = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]
        extras = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]
        summary = str(commentary.get("summary") or "").strip()

        if summary and summary not in extras:
            extras.insert(0, summary)

        narrative = str(commentary.get("narrativeInsight") or "").strip()

        if narrative and narrative not in extras:
            extras.insert(0, narrative)

        for line in extras:
            if line not in lines:
                lines.append(line)

        if lines:
            humanized["linhas"] = lines[:12]

    def _build_response_preview(
        self,
        data,
        max_chars: int | None = None,
    ) -> str:
        limit = (
            max_chars
            if max_chars is not None
            else Settings.CHAT_TOOL_RESPONSE_PREVIEW_MAX_CHARS
        )

        if data is None:
            return ""

        try:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            text = str(data)

        if len(text) <= limit:
            return text

        return f"{text[:limit]}\n…"

    def _format_tool_context(
            self,
            name: str,
            reason: str | None,
            data,
            metadata: dict | None,
            arguments: dict | None = None,
            *,
            message: str | None = None,
        ) -> str:
            if name == "execute_external_action":
                meta = dict(metadata or {})

                if message and not meta.get("currentMessage"):
                    meta["currentMessage"] = message

                return self._format_external_action_context(
                    reason=reason,
                    data=data,
                    metadata=meta,
                    arguments=arguments,
                )

            payload = {
                "tool": name,
                "reason": reason,
                "metadata": metadata or {},
                "authorizedResult": data,
            }

            return (
                f"[Ferramenta autorizada: {name}]\n"
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
            )

    def _format_external_action_context(
            self,
            reason: str | None,
            data,
            metadata: dict,
            arguments: dict | None = None,
        ) -> str:
            status_code = metadata.get("statusCode")
            ok = metadata.get("ok")
            action_id = metadata.get("actionId")
            path = metadata.get("path")
            provider = metadata.get("provider")

            if metadata.get("sqlSchemaPrefetch"):
                from app.domain.services.chat_advanced_sql_specialist_service import (
                    ChatAdvancedSqlSpecialistService,
                )

                humanized = ChatAdvancedSqlSpecialistService.compact_schema_prefetch_context(
                    message=str((metadata or {}).get("currentMessage") or ""),
                    data=data,
                    metadata=metadata,
                )
                payload = {
                    "tool": "execute_external_action",
                    "reason": reason,
                    "provider": provider,
                    "actionId": action_id,
                    "path": path,
                    "statusCode": status_code,
                    "ok": ok,
                    "sqlSchemaPrefetch": True,
                    "humanizedSummary": humanized,
                }

                return (
                    "[Contexto interno — metadados Protheus para elaborar SQL; não exibir catálogo ao usuário]\n"
                    f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
                )

            humanized = self._presenter.present(
                self._attach_request_sql(data, arguments, metadata),
                path=path or "",
            )

            linhas = list(humanized.get("linhas") or [])
            coverage = metadata.get("dataCoverageNotice")

            if isinstance(coverage, dict) and coverage.get("message"):
                linhas.append(str(coverage["message"]))

            titulo = str(humanized.get("titulo") or "").strip()
            path_text = str(path or "").lower()

            if titulo == "Lista de LMPs" and (
                "eficiencia-fabril" in path_text or "eficiencia_fabril" in path_text
            ):
                titulo = "Eficiência fabril"

            from app.domain.services.chat_humanized_data_response_service import (
                ChatHumanizedDataResponseService,
            )

            data_answer = metadata.get("dataAnswer")
            data_commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(
                metadata
            )

            payload = {
                "tool": "execute_external_action",
                "reason": reason,
                "provider": provider,
                "actionId": action_id,
                "path": path,
                "statusCode": status_code,
                "ok": ok,
                "humanizedSummary": {
                    "titulo": titulo,
                    "linhas": linhas,
                },
            }

            if isinstance(data_answer, dict) and data_answer.get("summary"):
                payload["dataAnswer"] = data_answer

            if isinstance(data_commentary, dict) and (
                data_commentary.get("highlights")
                or data_commentary.get("attention")
                or data_commentary.get("narrativeInsight")
                or data_commentary.get("summary")
            ):
                payload["dataCommentary"] = data_commentary

            from app.domain.services.chat_assistant_content_service import (
                ChatAssistantContentService,
            )

            commentary_rule = ChatAssistantContentService.get(
                "data_interpretation",
                "toolContextCommentaryRule",
                default="",
            )

            return (
                "[Ferramenta autorizada: execute_external_action]\n"
                "A API externa/interna foi consultada com o token autorizado do usuário.\n"
                f"Provider: {provider}\n"
                f"Action: {action_id}\n"
                f"Path: {path}\n"
                f"Status HTTP: {status_code}\n"
                f"Sucesso: {ok}\n"
                "Regra obrigatória: responda ao usuário em português natural, sem mostrar JSON bruto.\n"
                "Use o resumo humanizado como fonte principal.\n"
                f"{commentary_rule}\n"
                "Se precisar de algum dado técnico, use apenas o resumo técnico compacto.\n"
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
            )
