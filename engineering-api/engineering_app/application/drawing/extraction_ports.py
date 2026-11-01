"""Neutral extraction ports & provider catalog (R6-A).

Contracts by capability, not vendor. Adapters live in infrastructure;
the domain/application orchestration selects implementations through
`resolve_extraction_provider` — never by arbitrary request-supplied
class names. Production default is `pypdf_baseline`; experimental
providers are disabled unless explicitly enabled by backend config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from engineering_app.application.drawing.pdf_text_extractor import (
    PdfTextExtraction,
)

DEFAULT_PROVIDER = "pypdf_baseline"


class PdfExtractionPort(Protocol):
    """PDF bytes → neutral ExtractionResult (same contract as baseline)."""

    def extract(
        self, pdf_bytes: bytes, *, filename: str | None = None
    ) -> PdfTextExtraction: ...

    def capability_descriptor(self) -> "ProviderCapability": ...


class DrawingAnalysisErrorCompat(RuntimeError):
    pass


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


@dataclass
class _ProviderEntry:
    factory: Callable[[], PdfExtractionPort]
    status: str  # baseline | experimental
    enabled_by_default: bool


def _pypdf_factory() -> PdfExtractionPort:
    from engineering_app.infrastructure.extraction.pypdf_adapter import (
        PypdfExtractionAdapter,
    )

    return PypdfExtractionAdapter()


def _pdfplumber_factory() -> PdfExtractionPort:
    from engineering_app.infrastructure.extraction.pdfplumber_adapter import (
        PdfplumberExtractionAdapter,
    )

    return PdfplumberExtractionAdapter()


# Explicit allowlist — no dynamic/untrusted imports (R6A-05/08/10).
_PROVIDER_CATALOG: dict[str, _ProviderEntry] = {
    "pypdf_baseline": _ProviderEntry(
        _pypdf_factory, "baseline", enabled_by_default=True
    ),
    "pdfplumber_experimental": _ProviderEntry(
        _pdfplumber_factory, "experimental", enabled_by_default=False
    ),
}


class ProviderResolutionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def list_providers() -> list[dict[str, Any]]:
    """Capability descriptors for authorized introspection/tests."""
    out: list[dict[str, Any]] = []
    for pid, entry in _PROVIDER_CATALOG.items():
        desc = entry.factory().capability_descriptor()
        out.append(
            {
                "provider_id": pid,
                "status": entry.status,
                "enabled_by_default": entry.enabled_by_default,
                "descriptor": {
                    "version": desc.version,
                    "capabilities": desc.capabilities,
                    "formats": desc.formats,
                    "runs_local": desc.runs_local,
                    "license": desc.license,
                    "limits": desc.limits,
                },
            }
        )
    return out


def resolve_extraction_provider(
    provider_id: str | None = None,
) -> PdfExtractionPort:
    """Backend-governed selection; experimental providers require
    explicit opt-in via EVA_DRAWING_EXTRACTION_PROVIDER env var."""
    pid = (
        provider_id
        or os.environ.get("EVA_DRAWING_EXTRACTION_PROVIDER")
        or DEFAULT_PROVIDER
    ).strip()
    entry = _PROVIDER_CATALOG.get(pid)
    if entry is None:
        raise ProviderResolutionError(
            "unknown_provider",
            f"Provider de extração '{pid}' não consta no catálogo "
            "autorizado.",
        )
    if not entry.enabled_by_default and provider_id != pid and not (
        os.environ.get("EVA_DRAWING_EXTRACTION_PROVIDER") == pid
    ):
        raise ProviderResolutionError(
            "provider_not_enabled",
            f"Provider experimental '{pid}' não habilitado neste "
            "ambiente.",
        )
    return entry.factory()
