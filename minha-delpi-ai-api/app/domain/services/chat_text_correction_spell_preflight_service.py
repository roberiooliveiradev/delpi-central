"""Preflight LanguageTool — filtra issues e monta bloco de prompt para correção textual."""

from __future__ import annotations

import re
from typing import Any

from app.domain.ports.text_correction_spell_check_port import TextCorrectionSpellCheckIssue
from app.domain.services.chat_text_correction_spell_check_service import (
    ChatTextCorrectionSpellCheckService,
)
from app.domain.services.chat_text_correction_spell_content_service import (
    ChatTextCorrectionSpellContentService,
)


class ChatTextCorrectionSpellPreflightService:
    @classmethod
    def run(
        cls,
        *,
        source_text: str | None,
        preserved_codes: list[str] | None = None,
    ) -> dict[str, Any] | None:
        text = str(source_text or "").strip()

        if not text or not ChatTextCorrectionSpellCheckService.is_enabled():
            return None

        min_len = ChatTextCorrectionSpellContentService.limit_int("minSourceLength", 8)
        max_len = ChatTextCorrectionSpellContentService.limit_int("maxSourceLength", 8000)

        if len(text) < min_len or len(text) > max_len:
            return None

        raw_issues = ChatTextCorrectionSpellCheckService.check(text)

        if not raw_issues:
            return {
                "used": False,
                "issueCount": 0,
                "filteredIssueCount": 0,
                "engine": ChatTextCorrectionSpellContentService.metrics_engine_label(),
                "promptBlock": "",
            }

        filtered = cls._filter_issues(
            text,
            raw_issues,
            preserved_codes=preserved_codes or [],
        )
        prompt_block = cls._build_prompt_block(text, filtered)

        return {
            "used": bool(filtered),
            "issueCount": len(raw_issues),
            "filteredIssueCount": len(filtered),
            "engine": ChatTextCorrectionSpellContentService.metrics_engine_label(),
            "promptBlock": prompt_block,
        }

    @classmethod
    def _filter_issues(
        cls,
        text: str,
        issues: list[TextCorrectionSpellCheckIssue],
        *,
        preserved_codes: list[str],
    ) -> list[TextCorrectionSpellCheckIssue]:
        ignored_rules = ChatTextCorrectionSpellContentService.ignored_rule_ids()
        ignored_categories = ChatTextCorrectionSpellContentService.ignored_categories()
        protected_patterns = ChatTextCorrectionSpellContentService.protected_patterns()
        max_issues = ChatTextCorrectionSpellContentService.limit_int("maxIssuesInPrompt", 12)

        filtered: list[TextCorrectionSpellCheckIssue] = []

        for issue in issues:
            if len(filtered) >= max_issues:
                break

            offset = int(issue.get("offset", -1))
            length = int(issue.get("length", 0))
            rule_id = str(issue.get("ruleId") or "").strip()
            category = str(issue.get("category") or "").strip()

            if offset < 0 or length <= 0 or offset + length > len(text):
                continue

            if rule_id and rule_id in ignored_rules:
                continue

            if category and category in ignored_categories:
                continue

            fragment = text[offset : offset + length]

            if cls._fragment_is_protected(fragment, protected_patterns):
                continue

            if cls._overlaps_preserved_code(text, offset, length, preserved_codes):
                continue

            filtered.append(issue)

        return filtered

    @staticmethod
    def _fragment_is_protected(
        fragment: str,
        patterns: tuple[re.Pattern[str], ...],
    ) -> bool:
        cleaned = str(fragment or "").strip()

        if not cleaned:
            return True

        return any(pattern.search(cleaned) for pattern in patterns)

    @staticmethod
    def _overlaps_preserved_code(
        text: str,
        offset: int,
        length: int,
        preserved_codes: list[str],
    ) -> bool:
        fragment = text[offset : offset + length]

        for code in preserved_codes:
            token = str(code or "").strip()

            if not token:
                continue

            if token in fragment or fragment in token:
                return True

            start = text.find(token)

            while start >= 0:
                end = start + len(token)

                if offset < end and offset + length > start:
                    return True

                start = text.find(token, start + 1)

        return False

    @classmethod
    def _build_prompt_block(
        cls,
        text: str,
        issues: list[TextCorrectionSpellCheckIssue],
    ) -> str:
        if not issues:
            return ""

        preview_len = ChatTextCorrectionSpellContentService.limit_int(
            "fragmentPreviewLength",
            80,
        )
        max_replacements = ChatTextCorrectionSpellContentService.limit_int(
            "maxReplacementPreview",
            3,
        )
        lines = [ChatTextCorrectionSpellContentService.prompt_text("header")]

        for issue in issues:
            offset = int(issue.get("offset", 0))
            length = int(issue.get("length", 0))
            fragment = text[offset : offset + length]

            if len(fragment) > preview_len:
                fragment = f"{fragment[: preview_len - 1]}…"

            replacements = [
                str(item).strip()
                for item in (issue.get("replacements") or [])
                if str(item).strip()
            ][:max_replacements]
            suggestions = ""

            if replacements:
                suggestions = (
                    ChatTextCorrectionSpellContentService.prompt_text("suggestionsPrefix")
                    + ChatTextCorrectionSpellContentService.prompt_text(
                        "suggestionsSeparator",
                        default=", ",
                    ).join(replacements)
                )

            line = ChatTextCorrectionSpellContentService.format(
                "issueLine",
                fragment=fragment,
                message=str(issue.get("message") or "").strip(),
                suggestions=suggestions,
            )

            if line:
                lines.append(line)

        footer = ChatTextCorrectionSpellContentService.prompt_text("footer")

        if footer:
            lines.append(footer)

        return "\n".join(line for line in lines if line.strip())
