from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


def setup_function() -> None:
    InteractionRoomContentService.clear_cache()


def test_bundle_has_required_sections() -> None:
    bundle = InteractionRoomContentService.bundle()
    for section in ("errors", "messages", "empty", "filters", "activity", "notifications"):
        assert isinstance(bundle.get(section), dict)
        assert bundle[section]


def test_empty_state_copy() -> None:
    assert InteractionRoomContentService.empty("title") == "Nenhuma mensagem."
    assert "registrada aqui" in InteractionRoomContentService.empty("body")
    assert InteractionRoomContentService.empty("cta")


def test_errors_and_ok_messages() -> None:
    assert "não encontrada" in InteractionRoomContentService.error("roomNotFound")
    assert InteractionRoomContentService.message("postOk")
    assert InteractionRoomContentService.message("previewDenied")


def test_filters_and_activity() -> None:
    assert InteractionRoomContentService.filter_label("mentioned") == "Mencionaram-me"
    assert InteractionRoomContentService.activity("sending")
