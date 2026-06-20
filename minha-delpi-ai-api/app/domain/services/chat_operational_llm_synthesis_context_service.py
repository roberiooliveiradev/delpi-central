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

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            cls._append_unique_lines(lines, cls._facts_from_metadata(metadata))

        return lines

    @classmethod
    def _facts_from_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        facts: list[str] = []
        path = str(metadata.get("path") or "").strip()

        if path:
            facts.append(f"Rota consultada: {path}")

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

        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            title = str(humanized.get("titulo") or "").strip()

            if title:
                facts.append(title)

            archived = metadata.get("templateProseArchive")

            if isinstance(archived, dict):
                archived_humanized = archived.get("humanizedSummary")

                if isinstance(archived_humanized, dict):
                    humanized = archived_humanized

            max_lines = ChatOperationalLlmSynthesisContextContentService.limit_int(
                "maxHumanizedLines",
                6,
            )

            for line in (humanized.get("linhas") or [])[:max_lines]:
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

        for table in metadata.get("tablePresentations") or []:
            if not isinstance(table, dict):
                continue

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
