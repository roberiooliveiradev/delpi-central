"""Ingresso, canvas, histórico e think pré-tool — Fase 3C lote 21."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


@dataclass(frozen=True)
class ChatTurnPreparationIngressResult:
    canvas_action: Any
    canvas_open_payload: Any | None
    canvas_operational_update: bool
    attachment_ids: Any
    allowed_action_ids: list[str]
    operational_optimize: bool
    analysis_mode: bool
    text_task_category: str | None
    text_task_pure: bool
    fast_path: bool
    history: list[Any]
    history_summary: str
    pipeline_timings: ChatPipelineTimings
    pipeline_stages: list[str]


class ChatTurnPreparationIngressService:
    @classmethod
    def _think_target(cls, key: str) -> str:
        return ChatTurnPreparationContentService.stream_think_target(key)

    @classmethod
    def prepare(
        cls,
        *,
        message: str,
        request,
        workspace_context: dict,
        history_source: list,
        prepare_history: Callable[[list], tuple[str, list]],
        history_keep: int,
        on_stream_activity: Callable[..., None] | None = None,
    ) -> ChatTurnPreparationIngressResult:
        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target=cls._think_target("questionHistory"),
                    message=ChatTurnPreparationContentService.stream_think(
                        "ingressQuestion"
                    ),
                    entry_id="think-question-history",
                    state="active",
                )
            )

        canvas_action = ChatCanvasContentService.resolve(
            message,
            history_source,
            workspace_context,
        )
        canvas_open_payload = (
            canvas_action.open_payload if canvas_action and canvas_action.open_payload else None
        )
        canvas_operational_update = ChatCanvasIntentService.is_canvas_operational_update_request(
            message
        )

        attachment_ids = getattr(request, "attachment_ids", None)
        allowed_action_ids = workspace_context.get("allowedActionIds") or []

        pre_tool = ChatIntelligencePipelineService.resolve_pre_tool_decisions(
            message,
            allowed_action_ids,
            attachment_ids=attachment_ids,
            previous_messages=history_source,
        )
        operational_optimize = pre_tool.operational_optimize
        analysis_mode = pre_tool.analysis_mode
        text_task_category = ChatTextTaskIntentService.classify(message)
        text_task_pure = ChatTextTaskIntentService.is_pure_text_task(
            message,
            previous_messages=history_source,
        )

        if text_task_pure:
            operational_optimize = False
            analysis_mode = False

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            if analysis_mode:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target=cls._think_target("analysisMode"),
                        message=ChatTurnPreparationContentService.stream_think(
                            "analysisMode"
                        ),
                        detail=ChatTurnPreparationContentService.stream_think(
                            "analysisDetail"
                        ),
                    )
                )
            elif operational_optimize:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target=cls._think_target("operationalOptimize"),
                        message=ChatTurnPreparationContentService.stream_think(
                            "operationalOptimize"
                        ),
                        detail=ChatTurnPreparationContentService.stream_think(
                            "operationalOptimizeDetail"
                        ),
                    )
                )
            else:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target=cls._think_target("openapiRoute"),
                        message=ChatTurnPreparationContentService.stream_think(
                            "openapiRoute"
                        ),
                        detail=ChatTurnPreparationContentService.stream_think(
                            "openapiRouteDetail"
                        ),
                        entry_id="think-openapi-route",
                        state="active",
                    )
                )

        if canvas_action or canvas_operational_update:
            operational_optimize = False
            analysis_mode = False

        fast_path = bool(canvas_action)

        if operational_optimize:
            keep = max(1, int(history_keep))
            history_summary, history = "", list(history_source[-keep:])
        else:
            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.think(
                        target=cls._think_target("conversationHistory"),
                        message=ChatTurnPreparationContentService.stream_think(
                            "historyReview"
                        ),
                        entry_id="think-history-summary",
                        state="active",
                    )
                )

            history_summary, history = prepare_history(history_source)

            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.think(
                        target=cls._think_target("conversationHistory"),
                        message=ChatTurnPreparationContentService.stream_think(
                            "historyDone"
                        ),
                        entry_id="think-history-summary",
                        state="done",
                        level="success",
                    )
                )

        if (
            on_stream_activity
            and not analysis_mode
            and not operational_optimize
            and not canvas_action
        ):
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target=cls._think_target("openapiRoute"),
                    message=ChatTurnPreparationContentService.stream_think(
                        "openapiRouteDone"
                    ),
                    detail=ChatTurnPreparationContentService.stream_think(
                        "openapiRouteDoneDetail"
                    ),
                    entry_id="think-openapi-route",
                    state="done",
                    level="success",
                )
            )

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target=cls._think_target("questionHistory"),
                    message=ChatTurnPreparationContentService.stream_think(
                        "questionHistoryDone"
                    ),
                    entry_id="think-question-history",
                    state="done",
                    level="success",
                )
            )

        return ChatTurnPreparationIngressResult(
            canvas_action=canvas_action,
            canvas_open_payload=canvas_open_payload,
            canvas_operational_update=canvas_operational_update,
            attachment_ids=attachment_ids,
            allowed_action_ids=allowed_action_ids,
            operational_optimize=operational_optimize,
            analysis_mode=analysis_mode,
            text_task_category=text_task_category,
            text_task_pure=text_task_pure,
            fast_path=fast_path,
            history=history,
            history_summary=history_summary,
            pipeline_timings=ChatPipelineTimings(),
            pipeline_stages=["ingress"],
        )
