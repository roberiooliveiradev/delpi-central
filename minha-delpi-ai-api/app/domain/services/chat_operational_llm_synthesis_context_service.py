"""Monta bloco compacto de fatos da tool para síntese LLM (evita evasão «preciso acessar»)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)


class ChatOperationalLlmSynthesisContextService:
    @classmethod
    def build_facts_addon(
        cls,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        lines = cls.collect_fact_lines(tool_calls, response_mode=response_mode)

        if not lines:
            return ""

        title = ChatOperationalLlmSynthesisContextContentService.title()
        body = "\n".join(f"- {line}" for line in lines)
        block = f"{title}\n{body}".strip()
        max_chars = cls._resolve_max_chars(response_mode)

        if len(block) <= max_chars:
            result = f"\n\n{block}"
        else:
            trimmed = cls._trim_block(block, max_chars)
            result = f"\n\n{trimmed}" if trimmed else ""

        if cls._should_append_prose_rules(tool_calls, response_mode):
            panel_rule = ChatOperationalLlmSynthesisContextContentService.prose_panel_rule()

            if panel_rule and cls._tool_calls_use_prose_panel(tool_calls):
                result = f"{result}\n\n{panel_rule}" if result else f"\n\n{panel_rule}"

            fidelity_rule = ChatOperationalLlmSynthesisContextContentService.factual_fidelity_rule()

            if fidelity_rule and cls._tool_calls_use_prose_panel(tool_calls):
                result = f"{result}\n\n{fidelity_rule}" if result else f"\n\n{fidelity_rule}"

        return result

    @classmethod
    def _resolve_max_chars(cls, response_mode: str | None) -> int:
        from app.domain.services.chat_response_mode_content_service import (
            ChatResponseModeContentService,
        )
        from app.domain.services.chat_response_mode_service import ChatResponseModeService

        if ChatResponseModeService.normalize(response_mode) == "fast":
            fast_cap = ChatResponseModeContentService.fast_llm_max_facts_chars()

            if fast_cap is not None:
                return fast_cap

        if ChatResponseModeService.normalize(response_mode) == "normal":
            normal_cap = ChatResponseModeContentService.normal_llm_max_facts_chars()

            if normal_cap is not None:
                return normal_cap

        return ChatOperationalLlmSynthesisContextContentService.max_chars()

    @classmethod
    def _should_append_prose_rules(
        cls,
        tool_calls: list | None,
        response_mode: str | None,
    ) -> bool:
        from app.domain.services.chat_response_mode_content_service import (
            ChatResponseModeContentService,
        )
        from app.domain.services.chat_response_mode_service import ChatResponseModeService

        if (
            ChatResponseModeService.normalize(response_mode) == "fast"
            and ChatResponseModeContentService.fast_llm_skip_prose_panel_rules()
        ):
            return False

        if (
            ChatResponseModeService.normalize(response_mode) == "normal"
            and ChatResponseModeContentService.normal_llm_skip_prose_panel_rules()
        ):
            return False

        return True

    @classmethod
    def collect_fact_lines(
        cls,
        tool_calls: list | None,
        *,
        response_mode: str | None = None,
    ) -> list[str]:
        if not isinstance(tool_calls, list):
            return []

        lines: list[str] = []

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            if not metadata.get("ok"):
                if ChatOperationalLlmSynthesisContextContentService.include_failed_tools():
                    cls._append_unique_lines(
                        lines,
                        cls._facts_from_error_metadata(metadata),
                    )

                continue

            cls._append_unique_lines(lines, cls._facts_from_metadata(metadata))

        return lines

    @classmethod
    def _facts_from_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        facts: list[str] = []
        path = str(metadata.get("path") or "").strip()

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        decoupled = ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(metadata)

        product_code = cls._product_code_from_path(path)

        if product_code:
            facts.append(f"Produto consultado: {product_code}")

        if path:
            facts.append(f"Rota consultada: {path}")

        cls._append_unique_lines(facts, cls._facts_from_api_sections(metadata))

        coverage = metadata.get("dataCoverageNotice")

        if isinstance(coverage, dict):
            message = str(coverage.get("message") or "").strip()

            if message:
                facts.append(message)

        pagination = metadata.get("pagination")

        if isinstance(pagination, dict):
            if pagination.get("is_complete") is False:
                facts.append("Resultado parcial — lista truncada pelo limite da consulta.")

            total = pagination.get("total")

            if total not in (None, ""):
                facts.append(f"Total de registros: {total}")

        data_commentary = metadata.get("dataCommentary")

        if isinstance(data_commentary, dict):
            narrative = str(data_commentary.get("narrativeInsight") or "").strip()

            if narrative:
                facts.append(narrative)

            for key in ("attention", "analysis"):
                items = data_commentary.get(key)

                if not isinstance(items, list):
                    continue

                limit = ChatOperationalLlmSynthesisContextContentService.limit_int(
                    f"max{key.capitalize()}",
                    4 if key == "attention" else 3,
                )

                for item in items[:limit]:
                    text = cls._stringify(item)

                    if text:
                        facts.append(text)

        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            summary = data_answer.get("summary")
            skip_summary_answer = decoupled and cls._should_skip_summary_answer(metadata)

            if isinstance(summary, dict) and not skip_summary_answer:
                answer = str(summary.get("answer") or "").strip()

                if answer:
                    facts.append(answer)

            if isinstance(summary, dict):
                for key in ("attention", "analysis"):
                    items = summary.get(key)

                    if not isinstance(items, list):
                        continue

                    for item in items[:3]:
                        text = cls._stringify(item)

                        if text:
                            facts.append(text)

            for key in ("highlights", "limitations"):
                items = data_answer.get(key)

                if not isinstance(items, list):
                    continue

                limit = ChatOperationalLlmSynthesisContextContentService.limit_int(
                    f"max{key.capitalize()}",
                    4 if key == "highlights" else 2,
                )

                for item in items[:limit]:
                    text = cls._stringify(item)

                    if text:
                        facts.append(text)

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        effective_humanized = ChatPresentationProseDeliveryService.resolve_effective_humanized_summary(
            metadata,
        )

        if isinstance(effective_humanized, dict):
            title = str(effective_humanized.get("titulo") or "").strip()

            if title:
                facts.append(title)

            max_lines_key = (
                "maxHumanizedLinesWhenDecoupled" if decoupled else "maxHumanizedLines"
            )
            max_lines = ChatOperationalLlmSynthesisContextContentService.limit_int(
                max_lines_key,
                2 if decoupled else 3,
            )

            for line in ChatPresentationProseDeliveryService.resolve_humanized_lines_for_facts(
                metadata,
            )[:max_lines]:
                text = str(line or "").strip()

                if text:
                    facts.append(text.lstrip("- ").strip())

        kpi = metadata.get("kpiPresentation")

        if isinstance(kpi, dict):
            for metric in (kpi.get("metrics") or [])[:4]:
                if not isinstance(metric, dict):
                    continue

                label = str(metric.get("label") or metric.get("name") or "").strip()
                value = str(metric.get("value") or metric.get("formattedValue") or "").strip()

                if label and value:
                    facts.append(f"{label}: {value}")

        max_rows = ChatOperationalLlmSynthesisContextContentService.limit_int("maxTableRows", 4)

        skip_table_rows = (
            decoupled
            and ChatOperationalLlmSynthesisContextContentService.skip_table_rows_when_decoupled()
        )

        if not skip_table_rows:
            for table in cls._iter_table_presentations(metadata):
                table_title = str(table.get("title") or "").strip()
                role = str(table.get("role") or "").strip().casefold()
                rows = table.get("rows")

                if not isinstance(rows, list):
                    continue

                row_limit = max_rows

                if role == "profile":
                    row_limit = ChatOperationalLlmSynthesisContextContentService.limit_int(
                        "maxProfileTableRowsWhenDecoupled" if decoupled else "maxProfileTableRows",
                        0 if decoupled else 12,
                    )

                if row_limit <= 0:
                    continue

                for row in rows[:row_limit]:
                    if not isinstance(row, dict):
                        continue

                    line = cls._format_table_row_fact(row)

                    if not line:
                        continue

                    prefix = f"{table_title} — " if table_title else ""
                    facts.append(f"{prefix}{line}")

        facts.extend(cls._facts_from_sql_metadata(metadata))

        return facts

    @classmethod
    def _product_code_from_path(cls, path: str) -> str:
        import re

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        match = re.search(r"/products/(\d{4,})/", str(path or ""))

        if not match:
            return ""

        return ChatProductQueryIntentService.normalize_product_code(match.group(1))

    @classmethod
    def _should_skip_summary_answer(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        if not ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(metadata):
            return False

        if ChatOperationalLlmSynthesisContextContentService.skip_summary_answer_when_decoupled():
            return True

        path = str(metadata.get("path") or "").lower()

        if "/analyser" in path or "/profile" in path:
            return True

        for table in cls._iter_table_presentations(metadata):
            role = str(table.get("role") or "").strip().casefold()

            if role == "profile":
                return True

        return False

    @classmethod
    def _facts_from_api_sections(cls, metadata: dict[str, Any]) -> list[str]:
        facts: list[str] = []
        api_meta = metadata.get("apiDelpiResponseMeta")

        if not isinstance(api_meta, dict):
            return facts

        for section in api_meta.get("sections") or []:
            if not isinstance(section, dict):
                continue

            label = str(section.get("label") or section.get("key") or section.get("name") or "").strip()
            count = section.get("itemCount", section.get("count"))

            if not label or count in (None, ""):
                continue

            try:
                numeric = int(count)
            except (TypeError, ValueError):
                facts.append(f"{label}: {count}")
                continue

            if numeric == 0:
                facts.append(f"{label}: nenhum registro (0)")
            else:
                facts.append(f"{label}: {numeric} registro(s)")

        return facts

    @classmethod
    def _format_table_row_fact(cls, row: dict[str, Any]) -> str:
        campo = str(row.get("campo") or row.get("field") or "").strip()
        valor = row.get("valor", row.get("value"))

        if campo and str(valor or "").strip():
            return f"{campo}: {valor}"

        parts = [
            f"{key}: {value}"
            for key, value in row.items()
            if str(value or "").strip()
        ]

        return "; ".join(parts[:4]) if parts else ""

    @classmethod
    def _iter_table_presentations(cls, metadata: dict[str, Any]):
        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for presentation in bulk:
                if isinstance(presentation, dict):
                    yield presentation

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict) and str(presentation.get("type") or "") == "table":
            yield presentation

    @classmethod
    def _facts_from_sql_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        rows = cls._extract_sql_rows(metadata)
        path = str(metadata.get("path") or "").lower()
        is_sql = "/data/sql" in path or "sql" in str(metadata.get("actionId") or "").lower()

        if not rows and not is_sql:
            return []

        facts: list[str] = []
        max_rows = ChatOperationalLlmSynthesisContextContentService.limit_int("maxSqlRows", 5)

        for row in rows[:max_rows]:
            parts = [
                f"{key}: {value}"
                for key, value in row.items()
                if str(value or "").strip()
            ]

            if parts:
                facts.append("; ".join(parts[:5]))

        return facts

    @classmethod
    def _extract_sql_rows(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []

        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            sources.append(humanized)

        archive = metadata.get("templateProseArchive")

        if isinstance(archive, dict):
            archived = archive.get("humanizedSummary")

            if isinstance(archived, dict):
                sources.append(archived)

        for source in sources:
            sql_rows = source.get("sqlRows")

            if isinstance(sql_rows, list):
                rows.extend(row for row in sql_rows if isinstance(row, dict))

        return rows

    @classmethod
    def _facts_from_error_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        facts: list[str] = []
        path = str(metadata.get("path") or "").strip()

        if path:
            facts.append(f"Consulta com falha: {path}")

        status_code = metadata.get("statusCode")

        if status_code not in (None, ""):
            facts.append(f"HTTP {status_code}")

        for key in ("message", "error", "reason"):
            text = str(metadata.get(key) or "").strip()

            if text:
                facts.append(text)
                break

        preview = str(metadata.get("responsePreview") or "").strip()

        if preview and preview not in facts:
            facts.append(preview[:400])

        return facts

    @classmethod
    def _stringify(cls, value: Any) -> str:
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, dict):
            text = str(value.get("text") or value.get("label") or value.get("summary") or "").strip()

            if text:
                return text

            title = str(value.get("title") or "").strip()
            detail = str(value.get("detail") or value.get("value") or "").strip()

            if title and detail:
                return f"{title}: {detail}"

            if title:
                return title

        return str(value or "").strip()

    @classmethod
    def _append_unique_lines(cls, target: list[str], additions: list[str]) -> None:
        seen = {cls._normalize_key(line) for line in target}

        for line in additions:
            text = str(line or "").strip()

            if not text:
                continue

            key = cls._normalize_key(text)

            if key in seen:
                continue

            seen.add(key)
            target.append(text)

    @classmethod
    def _normalize_key(cls, text: str) -> str:
        return " ".join(str(text or "").lower().split())

    @classmethod
    def _tool_calls_use_prose_panel(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(
                metadata,
            ):
                return True

        return False

    @classmethod
    def _trim_block(cls, block: str, max_chars: int) -> str:
        lines = block.splitlines()

        if not lines:
            return ""

        kept = [lines[0]]
        size = len(lines[0])

        for line in lines[1:]:
            candidate = size + 1 + len(line)

            if candidate > max_chars:
                break

            kept.append(line)
            size = candidate

        return "\n".join(kept).strip()
