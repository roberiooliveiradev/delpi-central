"""Parâmetros do GET /products/{code}/analyser em turnos de análise de desenho."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService


class ChatDrawingAnalyserParameterService:
    FULL_VIEW = "full"

    @classmethod
    def requires_full_view(
        cls,
        *,
        drawing_analysis_mode: bool = False,
        message: str | None = None,
        attachment_ids: list | None = None,
    ) -> bool:
        if drawing_analysis_mode:
            return True

        return ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=attachment_ids,
        )

    @classmethod
    def apply_to_parameters(
        cls,
        parameters: dict[str, Any] | None,
        *,
        action: dict | None,
        drawing_analysis_mode: bool = False,
        message: str | None = None,
        attachment_ids: list | None = None,
    ) -> dict[str, Any]:
        merged = dict(parameters or {})
        path = str((action or {}).get("path") or "")

        if not cls.requires_full_view(
            drawing_analysis_mode=drawing_analysis_mode,
            message=message,
            attachment_ids=attachment_ids,
        ):
            return merged

        if "/analyser" not in path.lower():
            return merged

        schema_names = {
            str(parameter.get("name"))
            for parameter in ((action or {}).get("parametersSchema") or [])
            if parameter.get("name")
        }

        if not schema_names or "view" in schema_names:
            merged["view"] = cls.FULL_VIEW

        return merged

    @classmethod
    def apply_to_tool_call(
        cls,
        tool_call: dict[str, Any] | None,
        *,
        action: dict | None,
        drawing_analysis_mode: bool = False,
        message: str | None = None,
        attachment_ids: list | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(tool_call, dict):
            return tool_call

        arguments = tool_call.get("arguments")

        if not isinstance(arguments, dict):
            return tool_call

        parameters = arguments.get("parameters")

        if not isinstance(parameters, dict):
            return tool_call

        return {
            **tool_call,
            "arguments": {
                **arguments,
                "parameters": cls.apply_to_parameters(
                    parameters,
                    action=action,
                    drawing_analysis_mode=drawing_analysis_mode,
                    message=message,
                    attachment_ids=attachment_ids,
                ),
            },
        }
