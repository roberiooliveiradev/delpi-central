"""DocumentVisionOcrProcessRunner — isolamento de segfault OCR."""

from app.domain.exceptions.vision_exceptions import VisionOcrProcessCrashedError
from app.infrastructure.vision.document_vision_ocr_process_runner import (
    DocumentVisionOcrProcessRunner,
)


class _FakeProcess:
    def __init__(self, *, exit_code: int):
        self.exitcode = exit_code
        self._alive = True
        self._joined = False

    def start(self) -> None:
        return None

    def is_alive(self) -> bool:
        return self._alive

    def join(self, timeout=None) -> None:
        del timeout
        self._alive = False
        self._joined = True

    def terminate(self) -> None:
        self._alive = False

    def kill(self) -> None:
        self._alive = False


def test_runner_raises_on_negative_exit_code(monkeypatch, tmp_path):
    heartbeats: list[int] = []

    class _Ctx:
        def Process(self, **_kwargs):
            return _FakeProcess(exit_code=-11)

    monkeypatch.setattr(
        "app.infrastructure.vision.document_vision_ocr_process_runner.mp.get_context",
        lambda _name: _Ctx(),
    )
    monkeypatch.setattr(
        "app.infrastructure.vision.document_vision_ocr_process_runner.tempfile.mkstemp",
        lambda **_kwargs: (-1, str(tmp_path / "result.pkl")),
    )
    monkeypatch.setattr(
        "app.infrastructure.vision.document_vision_ocr_process_runner.os.close",
        lambda _fd: None,
    )

    try:
        DocumentVisionOcrProcessRunner.run(
            {"kind": "attachment_metadata", "kwargs": {}},
            timeout_seconds=5,
            heartbeat=lambda: heartbeats.append(1),
            heartbeat_interval_seconds=0.01,
        )
        assert False, "expected VisionOcrProcessCrashedError"
    except VisionOcrProcessCrashedError as exc:
        assert exc.exit_code == -11
        assert "signal_11" in exc.message


def test_process_isolation_settings_from_json():
    from app.domain.services.chat_document_vision_content_service import (
        ChatDocumentVisionContentService,
    )

    assert ChatDocumentVisionContentService.process_isolation_enabled() is True
    assert ChatDocumentVisionContentService.process_isolation_timeout_seconds() >= 30
