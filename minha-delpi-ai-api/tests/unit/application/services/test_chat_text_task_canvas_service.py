from app.application.services.chat_text_task_canvas_service import (
    ChatTextTaskCanvasService,
)


def test_should_update_canvas_for_lousa():
    assert ChatTextTaskCanvasService.should_update_canvas("corrija o texto da lousa") is True


def test_attach_version_history():
    metadata: dict = {}

    ChatTextTaskCanvasService.attach_version_history(
        metadata,
        previous_messages=[],
        new_markdown="Texto novo",
        title="Rascunho",
    )

    assert metadata["textCanvasUpdated"] is True
    assert len(metadata["textCanvasVersions"]) == 1
    assert metadata["textCanvasVersions"][0]["markdown"] == "Texto novo"
