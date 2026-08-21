"""Modo canônico do turno — decide se consome prior, pergunta slot, tools ou LLM."""

from __future__ import annotations

from typing import Any


class ChatTurnModeService:
    CONSUME_PRIOR = "consume_prior"
    ASK_SLOT = "ask_slot"
    EXECUTE_TOOLS = "execute_tools"
    LLM_NARRATE = "llm_narrate"

    @classmethod
    def resolve(
        cls,
        *,
        message: str | None = None,
        tool_context: dict | None = None,
        direct_answer: str | None = None,
        pipeline_stages: list[str] | None = None,
        tool_calls: list | None = None,
    ) -> str:
        del message
        context = tool_context if isinstance(tool_context, dict) else {}
        answer = str(direct_answer or context.get("directAnswer") or "").strip()
        stages = {str(stage).strip() for stage in (pipeline_stages or []) if str(stage).strip()}

        if answer and (
            context.get("drawingAnalysisMode")
            or "drawing_analysis" in stages
            or "drawing_report_adjustment" in stages
        ):
            return cls.CONSUME_PRIOR

        if cls._looks_like_ask_slot(answer=answer, tool_calls=tool_calls, stages=stages):
            return cls.ASK_SLOT

        if cls._has_pending_or_successful_tools(tool_calls) or "tools" in stages:
            if answer and cls._all_tool_calls_failed_validation(tool_calls):
                return cls.ASK_SLOT

            return cls.EXECUTE_TOOLS

        if answer and stages.intersection(
            {
                "small_talk",
                "utility_direct",
                "meta_direct_answer",
                "platform_direct_answer",
                "common_chat_operational_guidance",
                "unclear_request",
            }
        ):
            return cls.CONSUME_PRIOR

        if answer and not tool_calls:
            return cls.CONSUME_PRIOR

        return cls.LLM_NARRATE

    @classmethod
    def should_skip_llm(cls, mode: str) -> bool:
        return mode in {cls.CONSUME_PRIOR, cls.ASK_SLOT}

    @classmethod
    def should_skip_agentic(cls, mode: str) -> bool:
        return mode in {cls.CONSUME_PRIOR, cls.ASK_SLOT}

    @classmethod
    def _looks_like_ask_slot(
        cls,
        *,
        answer: str,
        tool_calls: list | None,
        stages: set[str],
    ) -> bool:
        if "operational_parameter" in stages:
            return True

        if cls._all_tool_calls_failed_validation(tool_calls):
            return True

        lowered = answer.casefold()

        return any(
            token in lowered
            for token in (
                "informe o código",
                "preciso do código",
                "parâmetro obrigatório",
                "falta o parâmetro",
            )
        )

    @classmethod
    def _all_tool_calls_failed_validation(cls, tool_calls: list | None) -> bool:
        calls = [call for call in (tool_calls or []) if isinstance(call, dict)]

        if not calls:
            return False

        saw_external = False

        for call in calls:
            if str(call.get("name") or "") != "execute_external_action":
                continue

            saw_external = True
            metadata = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}

            if metadata.get("ok"):
                return False

            kind = str(metadata.get("errorKind") or "").strip()

            if kind not in {
                "missing_required_parameter",
                "missing_path_parameter",
                "unknown_parameter",
            }:
                return False

        return saw_external

    @classmethod
    def _has_pending_or_successful_tools(cls, tool_calls: list | None) -> bool:
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            if str(call.get("name") or "") == "execute_external_action":
                return True

        return False
