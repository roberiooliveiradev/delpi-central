class VisionMemoryLimitedError(Exception):
    """Memória insuficiente para OCR pesado (EasyOCR / visão)."""

    code = "vision.memory_limited"

    def __init__(self, message: str = "vision_memory_limited"):
        self.message = message
        super().__init__(message)
