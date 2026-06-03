from app.application.services.chat_stream_activity_service import ChatStreamActivityService


def test_think_entry_uses_pensar_group():
    entry = ChatStreamActivityService.think(target="intenção operacional")

    assert entry["group"] == "Pensar"
    assert entry["phase"] == "think"
    assert entry["verb"] == "Pensando"


def test_plan_step_uses_planejar_group():
    entry = ChatStreamActivityService.plan_step(
        step=2,
        total=3,
        target="estoque · 10080047",
    )

    assert entry["group"] == "Planejar novos passos"
    assert entry["phase"] == "plan"


def test_emit_planned_actions_creates_plan_lines():
    collected: list[dict] = []

    ChatStreamActivityService.emit_planned_actions(
        collected.append,
        [
            {
                "name": "execute_external_action",
                "arguments": {"actionId": "stock", "parameters": {"code": "10080047"}},
                "reason": "Estoque do produto.",
            }
        ],
    )

    assert len(collected) >= 2
    assert collected[0]["phase"] == "plan"
    assert any("10080047" in str(item.get("target") or "") for item in collected)


def test_tool_finished_failure_warns_user_in_log():
    entry = ChatStreamActivityService.tool_finished(
        index=1,
        total=1,
        metadata={"ok": False, "statusCode": 500, "error": "boom"},
        path="/products/10080047",
    )

    assert entry["level"] == "error"
    assert entry["state"] == "failed"
    assert entry["message"] == "Não consegui concluir essa consulta."
    assert entry["path"] == "/products/10080047"
    # detalhe técnico preservado para o painel/admin
    assert entry.get("detail")
