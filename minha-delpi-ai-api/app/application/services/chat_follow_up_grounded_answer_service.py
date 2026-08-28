"""Respostas grounded de follow-up: challenge, clarify_slot e ack pós-revise."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


class ChatFollowUpGroundedAnswerService:
    @classmethod
    def build_challenge_answer(
        cls,
        *,
        workspace_context: dict | None = None,
        tool_context: dict | None = None,
    ) -> str | None:
        excerpt = cls._resolve_excerpt(workspace_context, tool_context)
        if not isinstance(excerpt, dict) or not excerpt:
            return None

        title = str(excerpt.get("title") or "").strip() or (
            ChatTurnGroundingContentService.last_result_heading()
        )
        preview = str(excerpt.get("preview") or "").strip()
        instruction = ChatFollowUpTurnContentService.challenge_faithfulness_instruction()
        last_action = cls._resolve_last_action(workspace_context)
        params = (
            last_action.get("params")
            if isinstance(last_action, dict) and isinstance(last_action.get("params"), dict)
            else {}
        )

        parts: list[str] = [
            f"Sobre o último resultado (**{title}**), sua observação faz sentido analisar assim:"
        ]

        if preview:
            parts.append(preview[:800])

        branch = str(params.get("branch") or "").strip()
        start = str(params.get("start_date") or "").strip()
        end = str(params.get("end_date") or "").strip()

        if not branch or branch.lower() in {"all", "todas"}:
            parts.append(
                "Os valores acima parecem **consolidados** (sem filtro de uma única filial). "
                "Por isso um número de unidade pode coincidir com o total se a consulta não "
                "estiver filtrada — ou se só houver movimento em uma filial no período."
            )
        else:
            parts.append(
                f"A última consulta já estava filtrada pela filial **{branch}**."
            )

        if start and end:
            parts.append(f"Período da última consulta: {start} a {end}.")

        if instruction:
            # Não ecoar a instrução interna; só reforça o tom no template.
            parts.append(
                "Posso consultar só uma filial ou comparar filiais neste período — diga como prefere."
            )

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def build_clarify_answer(
        cls,
        *,
        workspace_context: dict | None = None,
        tool_context: dict | None = None,
    ) -> str | None:
        slot = cls._resolve_clarify_slot(workspace_context, tool_context) or "branch"
        prompt = ChatFollowUpTurnContentService.clarify_slot_prompt(slot)
        return prompt or None

    @classmethod
    def build_revise_ack(
        cls,
        *,
        parameters: dict[str, Any] | None = None,
        last_action: dict[str, Any] | None = None,
    ) -> str | None:
        params = dict(parameters or {})
        if not params and isinstance(last_action, dict):
            raw = last_action.get("params")
            if isinstance(raw, dict):
                params = dict(raw)

        parts: list[str] = []
        branch = str(params.get("branch") or "").strip()
        if branch and branch.lower() not in {"all", "todas"}:
            parts.append(ChatFollowUpTurnContentService.revise_ack_branch(branch))

        start = str(params.get("start_date") or "").strip()
        end = str(params.get("end_date") or "").strip()
        if start and end:
            parts.append(
                ChatFollowUpTurnContentService.revise_ack_period(start=start, end=end)
            )

        return " ".join(parts).strip() or None

    @classmethod
    def challenge_suggestion_items(cls) -> list[dict[str, str]]:
        return ChatFollowUpTurnContentService.challenge_suggestions()

    @classmethod
    def inject_challenge_prompt_context(
        cls,
        tool_context: dict | None,
        *,
        workspace_context: dict | None = None,
    ) -> dict:
        updated = dict(tool_context or {})
        excerpt = cls._resolve_excerpt(workspace_context, updated)
        instruction = ChatFollowUpTurnContentService.challenge_faithfulness_instruction()
        blocks: list[str] = []

        if instruction:
            blocks.append(instruction)

        if isinstance(excerpt, dict) and excerpt:
            excerpt_block = ChatTurnGroundingContentService.format_excerpt_prompt_block(
                excerpt
            )
            if excerpt_block:
                blocks.append(excerpt_block)

        last_action = cls._resolve_last_action(workspace_context)
        if isinstance(last_action, dict) and last_action:
            params = last_action.get("params") if isinstance(last_action.get("params"), dict) else {}
            blocks.append(
                "Parâmetros da última consulta: "
                + ", ".join(f"{k}={v}" for k, v in params.items() if v not in (None, ""))
            )

        if blocks:
            existing = str(updated.get("analysisContext") or "").strip()
            joined = "\n\n".join(blocks)
            updated["analysisContext"] = (
                f"{existing}\n\n{joined}".strip() if existing else joined
            )
            updated["groundedNarrate"] = True
            updated["followUpChallenge"] = True

        suggestions = cls.challenge_suggestion_items()
        if suggestions:
            updated["followUpSuggestions"] = suggestions

        return updated

    @classmethod
    def _resolve_clarify_slot(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> str | None:
        for source in (tool_context, workspace_context):
            if not isinstance(source, dict):
                continue
            turn = source.get("turnGrounding")
            if not isinstance(turn, dict):
                continue
            follow_up = turn.get("followUp")
            if isinstance(follow_up, dict) and follow_up.get("clarifySlot"):
                return str(follow_up.get("clarifySlot")).strip() or None
        return None

    @classmethod
    def _resolve_excerpt(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> dict[str, Any] | None:
        for source in (tool_context, workspace_context):
            if not isinstance(source, dict):
                continue
            turn = source.get("turnGrounding")
            if isinstance(turn, dict):
                excerpt = turn.get("excerpt")
                if isinstance(excerpt, dict) and excerpt:
                    return excerpt
            working = source.get("workingMemory")
            if isinstance(working, dict):
                excerpt = working.get("lastResultExcerpt")
                if isinstance(excerpt, dict) and excerpt:
                    return excerpt
        return None

    @classmethod
    def _resolve_last_action(
        cls,
        workspace_context: dict | None,
    ) -> dict[str, Any] | None:
        workspace = workspace_context if isinstance(workspace_context, dict) else {}
        working = workspace.get("workingMemory")
        if isinstance(working, dict) and isinstance(working.get("lastAction"), dict):
            return working.get("lastAction")
        return None
