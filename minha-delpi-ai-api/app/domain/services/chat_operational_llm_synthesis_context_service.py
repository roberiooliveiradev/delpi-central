"""Monta bloco compacto de fatos da tool para síntese LLM (evita evasão «preciso acessar»)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)


class ChatOperationalLlmSynthesisContextService:
    @classmethod
    def build_facts_addon(cls, tool_calls: list | None) -> str:
        lines = cls.collect_fact_lines(tool_calls)

        if not lines:
            return ""

        title = ChatOperationalLlmSynthesisContextContentService.title()
        body = "\n".join(f"- {line}" for line in lines)
        block = f"{title}\n{body}".strip()
        max_chars = ChatOperationalLlmSynthesisContextContentService.max_chars()

        if len(block) <= max_chars:
            return f"\n\n{block}"

        trimmed = cls._trim_block(block, max_chars)

        return f"\n\n{trimmed}" if trimmed else ""

    @classmethod
    def collect_fact_lines(cls, tool_calls: list | None) -> list[str]:
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

        if path:
            facts.append(f"Rota consultada: {path}")

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

        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            summary = data_answer.get("summary")

            if isinstance(summary, dict):
                answer = str(summary.get("answer") or "").strip()

                if answer:
                    facts.append(answer)

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

            max_lines = ChatOperationalLlmSynthesisContextContentService.limit_int(
                "maxHumanizedLines",
                6,
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

        for table in cls._iter_table_presentations(metadata):
            table_title = str(table.get("title") or "").strip()
            rows = table.get("rows")

            if not isinstance(rows, list):
                continue

            for row in rows[:max_rows]:
                if not isinstance(row, dict):
                    continue

                parts = [
                    f"{key}: {value}"
                    for key, value in row.items()
                    if str(value or "").strip()
                ]

                if not parts:
                    continue

                prefix = f"{table_title} — " if table_title else ""
                facts.append(f"{prefix}{'; '.join(parts[:4])}")

        facts.extend(cls._facts_from_sql_metadata(metadata))

        return facts

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
