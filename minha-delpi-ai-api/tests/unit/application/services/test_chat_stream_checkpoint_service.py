from app.application.services.chat_stream_checkpoint_service import (
    ChatStreamCheckpointService,
)


def test_should_commit_on_incremental_checkpoints():
    assert ChatStreamCheckpointService.should_commit({"type": "user_persisted"})
    assert ChatStreamCheckpointService.should_commit({"type": "session_renamed"})
    assert ChatStreamCheckpointService.should_commit({"type": "assistant_pending"})
    assert ChatStreamCheckpointService.should_commit({"type": "done"})
    assert not ChatStreamCheckpointService.should_commit({"type": "activity"})
    assert not ChatStreamCheckpointService.should_commit({"type": "token"})
