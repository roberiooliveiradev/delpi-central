from app.application.services.chat_tool_context_parallel_read_service import (
    ChatToolContextParallelReadService,
)


def test_plan_batches_groups_consecutive_analysis_reads():
    batches = ChatToolContextParallelReadService.plan_batches(
        [True, True, False, True]
    )
    assert batches
    assert batches[0] == [0, 1]


def test_plan_batches_keeps_single_when_below_min(monkeypatch):
    monkeypatch.setattr(
        ChatToolContextParallelReadService,
        "min_batch",
        classmethod(lambda cls: 2),
    )
    assert ChatToolContextParallelReadService.plan_batches([True]) == []
    assert ChatToolContextParallelReadService.plan_batches([True, True]) == [[0, 1]]
