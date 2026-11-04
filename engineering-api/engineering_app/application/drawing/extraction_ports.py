"""Neutral extraction contracts (R6-B) — application layer only.

NO concrete adapter imports live here: the provider registry and
factories belong to infrastructure; the default production extractor
is injected by the composition root via `set_default_extractor_factory`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from engineering_app.application.drawing.pdf_text_extractor import (
    PdfTextExtraction,
)

_MAX_RENDER_PAGES_ENV = "ENG_DRAWING_MAX_RENDER_PAGES"
_TOKEN_SAMPLE_LIMIT_ENV = "ENG_DRAWING_TOKEN_SAMPLE_LIMIT"
# RQ-VAL-029: desenhos oficiais multipágina (≥14 páginas observadas no
# acervo) exigem cobertura além do teto legado de 5 páginas; o cap é
# único e governado — não um número hardcoded por consumidor.
_DEFAULT_MAX_RENDER_PAGES = 25
_DEFAULT_TOKEN_SAMPLE_LIMIT = 5000


def max_render_pages() -> int:
    """Teto de páginas renderizadas/OCR por documento (visual pipeline).

    ``ENG_DRAWING_MAX_RENDER_PAGES`` ajusta o limite operacional sem
    deploy; default 25 cobre os documentos extensos do acervo DELPI."""
    try:
        value = int(
            os.getenv(_MAX_RENDER_PAGES_ENV, "").strip()
            or _DEFAULT_MAX_RENDER_PAGES
        )
    except ValueError:
        return _DEFAULT_MAX_RENDER_PAGES
    return max(1, min(value, 50))


def token_sample_limit() -> int:
    """Teto de tokens OCR preservados por página/documento no run record.

    O sample alimenta ``build_understanding`` — não é depuração, é a
    evidência de trabalho; ``ENG_DRAWING_TOKEN_SAMPLE_LIMIT`` governa."""
    try:
        value = int(
            os.getenv(_TOKEN_SAMPLE_LIMIT_ENV, "").strip()
            or _DEFAULT_TOKEN_SAMPLE_LIMIT
        )
    except ValueError:
        return _DEFAULT_TOKEN_SAMPLE_LIMIT
    return max(100, min(value, 20000))


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

    def render_region(
        self,
        pdf_bytes: bytes,
        *,
        page: int,
        region_px: list[float],
        reference_dpi: int,
        dpi: int = 300,
        margin_px: int = 8,
    ) -> "RenderedRegion":
        """Recorte direcionado (R13): renderiza do PDF original apenas a
        região indicada — nunca upscaling de raster já degradado.

        ``region_px`` está em ``pixels_pdfium_top_left`` no espaço de
        ``reference_dpi`` (o DPI do render que produziu as coordenadas);
        ``dpi`` é a resolução efetiva do novo render. Capacidade opcional:
        adapters que não implementam devem declarar
        ``capabilities["region_render"]=False``.
        """
        ...


class OcrExtractionPort(Protocol):
    """Raster image bytes → recognized text + coordinates."""

    def extract_text(self, image_bytes: bytes) -> "OcrResult": ...


class ImagePreprocessingPort(Protocol):
    """Raster image bytes → preprocessed raster image (R7).

    ``mode`` is a governed profile name, never free-form operation
    chaining: ``raw_render`` | ``grayscale`` | ``adaptive_threshold``.
    """

    def preprocess(
        self, image_bytes: bytes, *, mode: str = "grayscale"
    ) -> "PreprocessResult": ...


@dataclass
class RenderedPage:
    page: int
    image_bytes: bytes
    width: int
    height: int
    dpi: int
    provider_id: str
    format: str = "png"
    # R7-04: proveniência espacial — transformação PDF→pixel explícita.
    scale: float | None = None  # dpi/72 — fator pontos→pixels aplicado
    rotation: int | None = None  # graus da página fonte (0/90/180/270)
    page_width_pt: float | None = None  # dimensão da página em pontos PDF
    page_height_pt: float | None = None
    coordinate_system: str = "pixels_pdfium_top_left"


@dataclass
class RenderedRegion:
    """Raster de um recorte direcionado com transformação explícita (R13)."""

    page: int
    image_bytes: bytes
    width: int
    height: int
    dpi: int
    provider_id: str
    region_px: list[float]  # recorte no espaço de reference_dpi
    offset_px: tuple[float, float]  # origem do recorte (px @ dpi)
    scale: float
    coordinate_system: str = "pixels_pdfium_top_left"
    format: str = "png"
    rotation: int | None = None
    limitations: list[str] = field(default_factory=list)


@dataclass
class PreprocessResult:
    """Raster output + rastreabilidade das operações aplicadas (R7-05)."""

    image_bytes: bytes
    profile: str
    ops_applied: list[str] = field(default_factory=list)
    width: int = 0
    height: int = 0
    provider_id: str = ""
    limitations: list[str] = field(default_factory=list)


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
    # R7-03/06: proveniência do modelo/engine — nunca fato oficial.
    metadata: dict[str, Any] = field(default_factory=dict)


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
