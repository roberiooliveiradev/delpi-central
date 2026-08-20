class VisionMemoryLimitedError(Exception):
    """Memória insuficiente para OCR pesado (EasyOCR / visão)."""

    code = "vision.memory_limited"

    def __init__(self, message: str = "vision_memory_limited"):
        self.message = message
        super().__init__(message)


class VisionOcrProcessCrashedError(Exception):
    """Processo filho de OCR morreu (ex.: segfault Pillow/fitz) — Flask/SSE permanece vivo."""

    code = "vision.ocr_process_crashed"

    def __init__(
        self,
        message: str = "vision_ocr_process_crashed",
        *,
        exit_code: int | None = None,
    ):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)
