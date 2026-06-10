from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService


def test_is_generating_metadata():
    assert ChatMessageDeliveryService.is_generating(
        {"delivery": {"status": "generating"}}
    )


def test_ready_metadata_sets_playback_pending():
    metadata = ChatMessageDeliveryService.ready_metadata({}, playback_pending=True)

    assert metadata["delivery"]["status"] == "ready"
    assert metadata["delivery"]["playbackPending"] is True


def test_session_has_pending_assistant_when_last_is_user():
    assert ChatMessageDeliveryService.session_has_pending_assistant(
        [{"role": "user", "content": "oi"}]
    )


def test_client_metadata_for_response_includes_interactivity():
    metadata = {
        "intelligence": {"intent": "operational_query"},
        "interactivity": {"suggestions": [{"id": "view_chart", "label": "Ver em gráfico"}]},
        "presentationFollowUpSuggestions": [{"id": "view_chart", "label": "Ver em gráfico"}],
        "internalOnly": True,
    }

    filtered = ChatMessageDeliveryService.client_metadata_for_response(metadata)

    assert filtered is not None
    assert "interactivity" in filtered
    assert "presentationFollowUpSuggestions" in filtered
    assert "internalOnly" not in filtered
