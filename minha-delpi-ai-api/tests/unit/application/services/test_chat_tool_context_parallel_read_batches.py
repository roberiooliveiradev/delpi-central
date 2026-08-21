from app.application.services.chat_tool_context_parallel_read_service import (
    ChatToolContextParallelReadService,
)


def test_plan_batches_groups_consecutive_analysis_reads():
    batches = ChatToolContextParallelReadService.plan_batches(
        [True, True, False, True]
    )
    assert batches
    assert batches[0] == [0, 1]


def test_execute_batch_wraps_worker_with_flask_app_context(monkeypatch):
    seen = {"ctx": False}

    class FakeApp:
        def app_context(self):
            return self

        def __enter__(self):
            seen["ctx"] = True
            return self

        def __exit__(self, *args):
            return False

    class FakeUseCase:
        def execute(self, request):
            return {"ok": True, "actionId": request.arguments.get("actionId")}

    monkeypatch.setattr(
        ChatToolContextParallelReadService,
        "min_batch",
        classmethod(lambda cls: 2),
    )
    monkeypatch.setattr(
        ChatToolContextParallelReadService,
        "max_workers",
        classmethod(lambda cls: 2),
    )
    monkeypatch.setattr(
        ChatToolContextParallelReadService,
        "_capture_flask_app",
        classmethod(lambda cls: FakeApp()),
    )

    outcomes = ChatToolContextParallelReadService.execute_batch(
        host=type("H", (), {"execute_tool_use_case": FakeUseCase()})(),
        user_id="u1",
        access_token="t1",
        selected_tools=[
            {"name": "execute_external_action", "arguments": {"actionId": "a"}},
            {"name": "execute_external_action", "arguments": {"actionId": "b"}},
        ],
        indices=[0, 1],
    )

    assert seen["ctx"] is True
    assert set(outcomes) == {0, 1}
    assert all(item.error is None for item in outcomes.values())


def test_plan_batches_keeps_single_when_below_min(monkeypatch):
    monkeypatch.setattr(
        ChatToolContextParallelReadService,
        "min_batch",
        classmethod(lambda cls: 2),
    )
    assert ChatToolContextParallelReadService.plan_batches([True]) == []
    assert ChatToolContextParallelReadService.plan_batches([True, True]) == [[0, 1]]
