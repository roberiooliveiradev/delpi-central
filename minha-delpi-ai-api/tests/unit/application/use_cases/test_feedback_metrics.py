from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.get_admin_feedback_summary_use_case import (
    GetAdminFeedbackSummaryUseCase,
)
from app.application.use_cases.upsert_chat_message_feedback_use_case import (
    UpsertChatMessageFeedbackUseCase,
)
from app.domain.services.chat_feedback_admin_metrics_service import (
    ChatFeedbackAdminMetricsService,
)
from app.domain.services.chat_feedback_content_service import ChatFeedbackContentService
from app.domain.services.chat_feedback_context_service import ChatFeedbackContextService
from app.domain.services.chat_response_metadata_service import ChatResponseMetadataService


def test_f1_thumbs_down_prompts_reason_via_content_service():
    prompt = ChatFeedbackContentService.thanks_for_rating(-1)

    assert prompt
    assert "faltou" in prompt.lower()


def test_f2_lost_context_offers_corrective_actions():
    actions = ChatFeedbackContentService.corrective_actions_for_reason("lost_context")
    labels = {item["label"] for item in actions}

    assert "Tentar corrigir" in labels
    assert any(item.get("query") for item in actions)


def test_f3_bad_format_offers_change_format():
    actions = ChatFeedbackContentService.corrective_actions_for_reason("bad_format")
    labels = {item["label"] for item in actions}

    assert "Trocar formato" in labels


def test_f4_missing_source_offers_official_source():
    actions = ChatFeedbackContentService.corrective_actions_for_reason("missing_source")
    labels = {item["label"] for item in actions}

    assert "Buscar fonte oficial" in labels


def test_f5_text_artificial_offers_rewrite():
    actions = ChatFeedbackContentService.corrective_actions_for_reason("text_artificial")
    labels = {item["label"] for item in actions}

    assert "Reescrever" in labels


def test_f6_registers_response_metadata_with_intent_and_tool():
    metadata: dict = {
        "intentRouting": {
            "intent": "operational_query",
            "subIntent": "stock_lookup",
            "confidence": 0.94,
        },
        "toolCalls": [{"metadata": {"path": "/products/{code}/stock"}}],
    }

    ChatResponseMetadataService.attach_to_assistant_metadata(
        metadata,
        workspace_context={"agent": "products", "agentId": "agent-1"},
        session_id="session-1",
        duration_ms=1200,
    )

    response_metadata = metadata["responseMetadata"]

    assert response_metadata["intent"] == "operational_query"
    assert response_metadata["usedTool"] is True
    assert response_metadata["toolPath"] == "/products/{code}/stock"
    assert response_metadata["durationMs"] == 1200


def test_f7_dashboard_aggregates_by_agent():
    summary = ChatFeedbackAdminMetricsService.aggregate_rows(
        [
            {
                "rating": -1,
                "reason": "wrong_data",
                "contextMetadata": {"intent": "stock_lookup", "agent": "products"},
                "createdAt": "2026-06-01T10:00:00Z",
                "messageId": "m1",
            },
            {
                "rating": 1,
                "contextMetadata": {"intent": "stock_lookup", "agent": "products"},
                "createdAt": "2026-06-01T11:00:00Z",
                "messageId": "m2",
            },
        ],
        hours=168,
        since_iso="2026-05-25T00:00:00Z",
    )

    assert summary["totalFeedback"] == 2
    assert summary["positiveCount"] == 1
    assert summary["negativeCount"] == 1
    assert summary["feedbackByAgent"][0]["key"] == "products"


def test_f8_recurring_feedback_generates_alert():
    rows = [
        {
            "rating": -1,
            "reason": "lost_context",
            "contextMetadata": {"intent": "supplier_lookup"},
            "messageId": f"m{i}",
            "createdAt": "2026-06-01T10:00:00Z",
        }
        for i in range(4)
    ]

    summary = ChatFeedbackAdminMetricsService.aggregate_rows(
        rows,
        hours=168,
        since_iso="2026-05-25T00:00:00Z",
    )

    assert summary["lostContextCount"] == 4
    assert any(alert["code"] == "context_loss" for alert in summary["alerts"])


def test_f9_positive_feedback_registers_thanks():
    thanks = ChatFeedbackContentService.thanks_for_rating(1, seed="msg-1")

    assert thanks


def test_f10_admin_debug_includes_response_quality():
    metadata: dict = {"adminDebug": {}}

    ChatResponseMetadataService.attach_to_assistant_metadata(
        metadata,
        workspace_context={"agent": "products"},
        session_id="s1",
        duration_ms=850,
    )

    quality = metadata["adminDebug"]["responseQuality"]

    assert "durationMs" in quality


def test_f11_sensitive_comment_is_masked():
    masked = ChatFeedbackContextService.sanitize_comment(
        "Produto 10080001 e e-mail joao@empresa.com.br"
    )

    assert masked is not None
    assert "10080001" not in masked
    assert "joao@empresa.com.br" not in masked


def test_f12_action_failure_alert_on_high_negative_rate():
    rows = [{"rating": -1, "reason": "wrong_query", "contextMetadata": {}} for _ in range(4)]
    rows.extend([{"rating": 1, "contextMetadata": {}} for _ in range(4)])

    summary = ChatFeedbackAdminMetricsService.aggregate_rows(
        rows,
        hours=168,
        since_iso="2026-05-25T00:00:00Z",
    )

    assert any(alert["code"] == "high_negative_rate" for alert in summary["alerts"])


def test_get_admin_feedback_summary_use_case_delegates_to_repository():
    repository = MagicMock()
    repository.list_feedback_since.return_value = []

    summary = GetAdminFeedbackSummaryUseCase(repository).execute(hours=24)

    assert summary["totalFeedback"] == 0
    repository.list_feedback_since.assert_called_once()


def test_upsert_feedback_persists_context_metadata():
    session_id = str(uuid4())
    message_id = str(uuid4())
    user_id = str(uuid4())

    session = MagicMock()
    session.user_id = user_id
    session.agent_id = None

    assistant = MagicMock()
    assistant.metadata = {
        "intentRouting": {"intent": "operational_query", "confidence": 0.9},
        "toolCalls": [],
    }

    session_repository = MagicMock()
    session_repository.get_session_by_id.return_value = session

    feedback_repository = MagicMock()
    feedback_repository.get_message_session_id.return_value = session_id
    feedback_repository.get_assistant_message.return_value = assistant
    feedback_repository.upsert_feedback.return_value = {"messageId": message_id, "rating": -1}

    use_case = UpsertChatMessageFeedbackUseCase(session_repository, feedback_repository)

    result = use_case.execute(
        user_id=user_id,
        session_id=session_id,
        message_id=message_id,
        rating=-1,
        reason="lost_context",
    )

    assert result is not None
    feedback_repository.upsert_feedback.assert_called_once()
    kwargs = feedback_repository.upsert_feedback.call_args.kwargs

    assert kwargs["context_metadata"]["intent"] == "operational_query"
    assert result["correctiveActions"]
