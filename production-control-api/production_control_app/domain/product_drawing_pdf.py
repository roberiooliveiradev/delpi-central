from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DrawingFile:
    """PDF document handle for PCP BFF responses.

    Prefer ``content`` (bytes from api-delpi). ``path`` remains for legacy/test fakes.
    """

    filename: str
    media_type: str = "application/pdf"
    path: Path | None = None
    content: bytes | None = None

    def __post_init__(self) -> None:
        if self.content is None and self.path is None:
            raise ValueError("DrawingFile requires content or path")
