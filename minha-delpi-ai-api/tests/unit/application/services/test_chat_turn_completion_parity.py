"""Paridade pós-LLM — ChatTurnCompletionService (send vs stream)."""

from dataclasses import replace
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_turn.chat_turn_completion_service import (
    ChatTurnCompletionInput,
    ChatTurnCompletionService,
    ChatTurnPersistenceOptions,
)
from types import SimpleNamespace


def _prepared():
    return SimpleNamespace(
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
        history=[],
        history_summary="",
        tool_context={"context": "", "toolCalls": []},
        tool_calls=[],
        direct_answer="Resposta direta de teste.",
        rag={"context": ""},
        sources=[],
        canvas_open_payload=None,
        pipeline_timings=ChatPipelineTimings(),
        pipeline_stages=[],
        email_writing_mode=False,
        text_correction_mode=False,
        text_task_mode=False,
        intent_route=None,
        routing_disambiguation_suggestions=None,
    )


def _build_turn_input(*, answer: str) -> ChatTurnCompletionInput:
    session_id = uuid4()
    user_id = uuid4()
    user_message = MagicMock()
    user_message.id = uuid4()
    request = MagicMock()
    request.message = "pergunta teste"
    request.context = {}
    request.attachment_ids = None

    return ChatTurnCompletionInput(
        request=request,
        message="pergunta teste",
        user_id=user_id,
        session_id=session_id,
        workspace_context={"agentId": None, "agent": None, "project": None},
        attachments=[],
        previous_messages=[],
        history_source=[],
        prepared=_prepared(),
        answer=answer,
        sources=[],
        tool_context={"context": "", "toolCalls": []},
        tool_calls=[],
        direct_answer="Resposta direta de teste.",
        pipeline_timings=ChatPipelineTimings(),
        pipeline_stages=[],
        fast_path=False,
        operational_optimize=False,
        skip_rag=True,
        analysis_mode=False,
        llm_messages=[],
        admin_debug_payload=None,
        active_guidelines=[],
        started_at=0.0,
        user_message=user_message,
        canvas_open_payload=None,
    )


def _service() -> ChatTurnCompletionService:
    chat_repository = MagicMock()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()
    chat_repository.create_message.return_value = assistant_message
    chat_repository.update_assistant_message.return_value = assistant_message

    return ChatTurnCompletionService(
        chat_repository=chat_repository,
        audit_repository=MagicMock(),
        session_memory_service=None,
    )


def test_send_mode_persists_with_create_message():
    service = _service()
    turn = _build_turn_input(answer="Resposta direta de teste.")

    result = service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(mode="send"),
    )

    service.chat_repository.create_message.assert_called_once()
    service.chat_repository.update_assistant_message.assert_not_called()
    assert result.answer == "Resposta direta de teste."
    assert "stream" not in result.assistant_metadata
    service.audit_repository.log.assert_called()
    actions = [
        call.kwargs.get("action") or (call.args[1] if len(call.args) > 1 else None)
        for call in service.audit_repository.log.call_args_list
    ]
    assert "chat.message.sent" in actions


def test_stream_mode_sets_stream_flag_and_streamed_audit():
    service = _service()
    turn = _build_turn_input(answer="Resposta direta de teste.")

    result = service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(mode="stream_create", is_stream=True),
    )

    assert result.assistant_metadata.get("stream") is True
    actions = [
        call.kwargs.get("action") or (call.args[1] if len(call.args) > 1 else None)
        for call in service.audit_repository.log.call_args_list
    ]
    assert "chat.message.streamed" in actions


def test_stream_update_mode_uses_placeholder():
    service = _service()
    turn = _build_turn_input(answer="Resposta final.")
    placeholder = MagicMock()
    placeholder.id = uuid4()

    service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(
            mode="stream_update",
            is_stream=True,
            persist_before_playback=True,
            assistant_placeholder=placeholder,
        ),
    )

    call = service.chat_repository.update_assistant_message.call_args
    assert call.args[0] == placeholder.id
    assert call.args[1] == "Resposta final."
    assert isinstance(call.args[2], dict)
    service.chat_repository.create_message.assert_not_called()


def test_send_and_stream_share_core_metadata_keys():
    service = _service()
    turn = _build_turn_input(answer="Resposta direta de teste.")

    send_result = service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(mode="send"),
    )
    stream_result = service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(mode="stream_create", is_stream=True),
    )

    core_keys = {
        "toolCalls",
        "sources",
        "intelligence",
        "metrics",
        "directResponse",
        "rag",
    }

    assert core_keys.issubset(send_result.assistant_metadata.keys())
    assert core_keys.issubset(stream_result.assistant_metadata.keys())


def test_completion_uses_prepared_rag_stats_for_intelligence_metadata():
    service = _service()
    turn = _build_turn_input(answer="Fontes do projeto listadas.")
    turn.prepared.rag = {
        "context": "",
        "sources": [],
        "retrievedSourceCount": 2,
        "visibleSourceCount": 0,
        "retrievedChunkCount": 0,
    }

    result = service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(mode="send"),
    )

    intelligence = result.assistant_metadata["intelligence"]
    assert intelligence["ragRetrievedCount"] == 2
    assert intelligence["ragVisibleSourceCount"] == 0


def test_library_only_attachments_skip_user_message_snapshot_patch():
    service = _service()
    turn = replace(
        _build_turn_input(answer="Relatório de análise."),
        attachments=[
            {
                "id": "att-lib",
                "original_filename": "90263396.pdf",
                "metadata": {
                    "source": "api_delpi_library",
                    "productCode": "90263396",
                },
            }
        ],
        tool_context={
            "context": "",
            "toolCalls": [],
            "drawingAnalysisMode": True,
            "drawingLibraryFetch": {"productCode": "90263396"},
        },
    )

    service.complete_turn(
        turn,
        persistence=ChatTurnPersistenceOptions(mode="send"),
    )

    service.chat_repository.patch_message_metadata.assert_not_called()
