from app.application.services.chat_stream_activity_service import ChatStreamActivityService


def test_tool_finished_reports_empty_data_as_warning():
    entry = ChatStreamActivityService.tool_finished(
        index=1,
        total=2,
        metadata={"ok": True, "statusCode": 200, "path": "/products/10080047/analyser"},
        path="/products/10080047/analyser",
        data={"data": {"items": []}},
    )

    assert entry["level"] == "warning"
    assert entry["verb"] == "Sem dados"
    assert "/analyser" in entry["target"]


def test_tool_finished_reports_http_404_as_error():
    entry = ChatStreamActivityService.tool_finished(
        index=1,
        total=1,
        metadata={
            "ok": False,
            "statusCode": 404,
            "path": "/products/99999999",
        },
        path="/products/99999999",
    )

    assert entry["level"] == "error"
    assert entry["verb"] == "Falhou"
    assert "404" in (entry.get("detail") or "")
