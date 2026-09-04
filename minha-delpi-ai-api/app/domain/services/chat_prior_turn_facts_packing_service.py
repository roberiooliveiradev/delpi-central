"""Empacota os fatos do turno anterior em um bloco curto de prompt (E2.S3).

Reúne, numa única fonte de verdade, o que o assistente precisa lembrar sem
reler o histórico inteiro: identidade do item em foco (código + descrição),
foco operacional, resumo da última lista (``resultSets``) e um resumo das
capacidades ativas (skills e ferramentas em foco).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_prior_turn_facts_content_service import (
    ChatPriorTurnFactsContentService,
)

_CONTENT = ChatPriorTurnFactsContentService


@dataclass(frozen=True)
class ChatPriorTurnFacts:
    text: str
    sections: tuple[str, ...]
    chars: int
    truncated: bool

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    def as_admin_debug(self) -> dict[str, Any]:
        return {
            "chars": self.chars,
            "sections": list(self.sections),
            "truncated": self.truncated,
        }


class ChatPriorTurnFactsPackingService:
    SECTION_IDENTITY = "identity"
    SECTION_FOCUS = "focus"
    SECTION_LAST_ACTION = "lastAction"
    SECTION_RESULT_SETS = "resultSets"
    SECTION_CAPABILITIES = "capabilities"

    @classmethod
    def build(
        cls,
        snapshot: dict[str, Any] | None,
        *,
        max_chars: int | None = None,
    ) -> ChatPriorTurnFacts:
        snap = snapshot if isinstance(snapshot, dict) else {}
        sections: list[str] = []
        lines: list[str] = []

        identity_lines = cls._identity_lines(snap)

        if identity_lines:
            sections.append(cls.SECTION_IDENTITY)
            lines.extend(identity_lines)

        focus_lines = cls._focus_lines(snap)

        if focus_lines:
            sections.append(cls.SECTION_FOCUS)
            lines.extend(focus_lines)

        last_action_line = cls._last_action_line(snap)

        if last_action_line:
            sections.append(cls.SECTION_LAST_ACTION)
            lines.append(last_action_line)

        result_set_lines = cls._result_set_lines(snap)

        if result_set_lines:
            sections.append(cls.SECTION_RESULT_SETS)
            lines.extend(result_set_lines)

        capability_lines = cls._capability_lines(snap)

        if capability_lines:
            sections.append(cls.SECTION_CAPABILITIES)
            lines.extend(capability_lines)

        if not lines:
            return ChatPriorTurnFacts(text="", sections=(), chars=0, truncated=False)

        heading = _CONTENT.heading("root")
        body = "\n".join(lines)
        text = f"{heading}\n{body}" if heading else body
        truncated = False

        if max_chars is not None and max_chars > 0 and len(text) > max_chars:
            text = cls._clip(text, max_chars)
            truncated = True

        return ChatPriorTurnFacts(
            text=text,
            sections=tuple(sections),
            chars=len(text),
            truncated=truncated,
        )

    @classmethod
    def format_prompt_block(
        cls,
        snapshot: dict[str, Any] | None,
        *,
        max_chars: int | None = None,
    ) -> str:
        return cls.build(snapshot, max_chars=max_chars).text

    # ------------------------------------------------------------- sections

    @classmethod
    def _identity_lines(cls, snapshot: dict[str, Any]) -> list[str]:
        excerpt = snapshot.get("lastResultExcerpt")
        identity = excerpt.get("identityFields") if isinstance(excerpt, dict) else None

        if not isinstance(identity, dict):
            identity = {}

        code = str(identity.get("code") or "").strip()
        description = str(identity.get("description") or "").strip()

        if not code:
            return []

        if description:
            max_description = max(16, _CONTENT.limit_int("maxDescriptionChars", 90))
            line = _CONTENT.line(
                "identityWithDescription",
                code=code,
                description=description[:max_description],
            )
        else:
            line = _CONTENT.line("identityCodeOnly", code=code)

        return [line] if line else []

    @classmethod
    def _focus_lines(cls, snapshot: dict[str, Any]) -> list[str]:
        """Só o foco que **não** vira item de contexto (produto/filial/armazém)."""
        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )

        focus = ChatSnapshotOperationalFocus.get(snapshot)

        if not isinstance(focus, dict) or not focus:
            return []

        labels = _CONTENT.focus_labels()
        lines: list[str] = []

        for key, label in labels.items():
            value = str(focus.get(key) or "").strip()

            if not value:
                continue

            line = _CONTENT.line("focusEntry", label=label, value=value)

            if line:
                lines.append(line)

        return lines

    @classmethod
    def _last_action_line(cls, snapshot: dict[str, Any]) -> str:
        last_action = snapshot.get("lastAction")

        if not isinstance(last_action, dict):
            return ""

        action = str(
            last_action.get("operationId") or last_action.get("name") or ""
        ).strip()

        if not action:
            return ""

        return _CONTENT.line("lastActionLine", action=action)

    @classmethod
    def _result_set_lines(cls, snapshot: dict[str, Any]) -> list[str]:
        result_sets = snapshot.get("resultSets")

        if not isinstance(result_sets, list) or not result_sets:
            return []

        max_sets = max(1, _CONTENT.limit_int("maxResultSets", 2))
        max_items = max(1, _CONTENT.limit_int("maxResultSetItems", 5))
        max_label = max(12, _CONTENT.limit_int("maxLabelChars", 60))
        lines: list[str] = []
        used_sets = 0

        for result_set in result_sets:
            if not isinstance(result_set, dict):
                continue

            items = [
                item for item in result_set.get("items") or [] if isinstance(item, dict)
            ]

            if not items:
                continue

            total = result_set.get("totalCount")
            total_value = total if isinstance(total, int) and total > 0 else len(items)
            heading = _CONTENT.line("resultSetHeading", total=total_value)

            if heading:
                lines.append(heading)

            for item in items[:max_items]:
                code = str(item.get("code") or "").strip()

                if not code:
                    continue

                ordinal = item.get("ordinal") or len(lines)
                label = str(item.get("label") or "").strip()

                if label:
                    line = _CONTENT.line(
                        "resultSetItemWithLabel",
                        ordinal=ordinal,
                        code=code,
                        label=label[:max_label],
                    )
                else:
                    line = _CONTENT.line("resultSetItem", ordinal=ordinal, code=code)

                if line:
                    lines.append(line)

            remaining = total_value - min(len(items), max_items)

            if remaining > 0:
                tail = _CONTENT.line("resultSetTruncated", count=remaining)

                if tail:
                    lines.append(tail)

            used_sets += 1

            if used_sets >= max_sets:
                break

        return lines

    @classmethod
    def _capability_lines(cls, snapshot: dict[str, Any]) -> list[str]:
        capabilities = snapshot.get("sessionCapabilities")

        if not isinstance(capabilities, dict):
            return []

        lines: list[str] = []
        skills = cls._shortlist(
            capabilities.get("skills"),
            limit=max(1, _CONTENT.limit_int("maxSkills", 6)),
        )

        if skills:
            line = _CONTENT.line("skillsLine", skills=", ".join(skills))

            if line:
                lines.append(line)

        tools = cls._shortlist(
            capabilities.get("tools"),
            limit=max(1, _CONTENT.limit_int("maxTools", 6)),
        )

        if tools:
            line = _CONTENT.line("toolsLine", tools=", ".join(tools))

            if line:
                lines.append(line)

        return lines

    @classmethod
    def build_session_capabilities(
        cls,
        *,
        skills: Any = None,
        tool_names: Any = None,
    ) -> dict[str, list[str]]:
        """Resumo enxuto de skills/ferramentas para gravar no snapshot."""
        payload: dict[str, list[str]] = {}
        active_skills = cls._shortlist(
            skills,
            limit=max(1, _CONTENT.limit_int("maxSkills", 6)),
        )

        if active_skills:
            payload["skills"] = active_skills

        tools = cls._shortlist(
            tool_names,
            limit=max(1, _CONTENT.limit_int("maxTools", 6)),
        )

        if tools:
            payload["tools"] = tools

        return payload

    @staticmethod
    def _shortlist(raw: Any, *, limit: int) -> list[str]:
        values: list[str] = []

        if isinstance(raw, dict):
            for key, enabled in raw.items():
                if not enabled:
                    continue

                token = str(key).strip()

                if token and token not in values:
                    values.append(token)
        elif isinstance(raw, (list, tuple, set)):
            for item in raw:
                token = str(item).strip()

                if token and token not in values:
                    values.append(token)

        return values[:limit]

    @classmethod
    def _clip(cls, text: str, max_chars: int) -> str:
        suffix = _CONTENT.truncation_suffix()
        budget = max(1, max_chars - len(suffix))
        clipped = text[:budget].rstrip()

        return f"{clipped}{suffix}"
