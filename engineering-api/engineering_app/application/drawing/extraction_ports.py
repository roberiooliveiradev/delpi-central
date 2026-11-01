"""Neutral extraction contracts (R6-B) — application layer only.

NO concrete adapter imports live here: the provider registry and
factories belong to infrastructure; the default production extractor
is injected by the composition root via `set_default_extractor_factory`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from engineering_app.application.drawing.pdf_text_extractor import (
    PdfTextExtraction,
)


class PdfExtractionPort(Protocol):
    """PDF bytes → neutral PdfTextExtraction (baseline contract)."""

    def extract(
        self, pdf_bytes: bytes, *, filename: str | None = None
    ) -> PdfTextExtraction: ...

    def capability_descriptor(self) -> "ProviderCapability": ...


class PdfRenderingPort(Protocol):
    """PDF bytes → rasterized page image (experimental pipelines)."""

    def render_page(
        self, pdf_bytes: bytes, *, page: int, dpi: int = 150
    ) -> "RenderedPage": ...


class OcrExtractionPort(Protocol):
    """Raster image bytes → recognized text + coordinates."""

    def extract_text(self, image_bytes: bytes) -> "OcrResult": ...


class ImagePreprocessingPort(Protocol):
    """Raster image bytes → preprocessed raster image bytes."""

    def preprocess(self, image_bytes: bytes, *, mode: str = "binarize") -> bytes: ...


@dataclass
class RenderedPage:
    page: int
    image_bytes: bytes
    width: int
    height: int
    dpi: int
    provider_id: str
    format: str = "png"


@dataclass
class OcrToken:
    text: str
    confidence: float | None
    box: list[float] | None  # provider coordinate system


@dataclass
class OcrResult:
    provider_id: str
    text: str
    tokens: list[OcrToken] = field(default_factory=list)
    duration_ms: int = 0
    limitations: list[str] = field(default_factory=list)


@dataclass
class ProviderCapability:
    """Self-described real capabilities of an adapter (R6A-05)."""

    provider_id: str
    version: str
    status: str  # baseline | experimental | unavailable
    capabilities: dict[str, bool] = field(default_factory=dict)
    formats: list[str] = field(default_factory=list)
    runs_local: bool = True
    requires_credentials: bool = False
    license: str | None = None
    limits: dict[str, Any] = field(default_factory=dict)
    license_notes: str | None = None


class ProviderResolutionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# --- composition hook (default production extractor) -------------------------

_default_factory: Callable[[], PdfExtractionPort] | None = None


def set_default_extractor_factory(
    factory: Callable[[], PdfExtractionPort],
) -> None:
    """Registered by the composition root — the ONLY way production
    resolves the default provider (backend-governed, allowlisted)."""
    global _default_factory
    _default_factory = factory


def get_default_extractor() -> PdfExtractionPort:
    if _default_factory is None:
        raise ProviderResolutionError(
            "no_default_extractor",
            "Nenhum extractor default registrado pelo composition root.",
        )
    return _default_factory()
