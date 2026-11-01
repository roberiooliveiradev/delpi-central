"""Provider registry — infrastructure layer (R6-B).

Owns the allowlist catalog and concrete factories. Application code
never resolves providers through this module; production gets the
default via the composition hook, benchmarks get explicit experimental
resolution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from engineering_app.application.drawing.extraction_ports import (
    PdfExtractionPort,
    ProviderResolutionError,
)

DEFAULT_PROVIDER = "pypdf_baseline"
_ENV_PROVIDER = "EVA_DRAWING_EXTRACTION_PROVIDER"


@dataclass
class _Entry:
    factory: Callable[[], PdfExtractionPort]
    status: str


def _pypdf() -> PdfExtractionPort:
    from engineering_app.infrastructure.extraction.pypdf_adapter import (
        PypdfExtractionAdapter,
    )

    return PypdfExtractionAdapter()


def _pdfplumber() -> PdfExtractionPort:
    from engineering_app.infrastructure.extraction.pdfplumber_adapter import (
        PdfplumberExtractionAdapter,
    )

    return PdfplumberExtractionAdapter()


def _pdfium() -> PdfExtractionPort:
    from engineering_app.infrastructure.extraction.pdfium_adapter import (
        PdfiumExtractionAdapter,
    )

    return PdfiumExtractionAdapter()


_CATALOG: dict[str, _Entry] = {
    "pypdf_baseline": _Entry(_pypdf, "baseline"),
    "pdfplumber_experimental": _Entry(_pdfplumber, "experimental"),
    "pdfium_experimental": _Entry(_pdfium, "experimental"),
}


def resolve_extraction_provider(
    provider_id: str | None = None,
    *,
    allow_experimental: bool = False,
) -> PdfExtractionPort:
    """Backend-governed resolution (R6B-02).

    Experimental providers require `allow_experimental=True` — an
    explicit id alone is NOT authorization. `EVA_DRAWING_EXTRACTION_
    PROVIDER` is operator config and may select an experimental default.
    """
    env_pid = os.environ.get(_ENV_PROVIDER)
    pid = (provider_id or env_pid or DEFAULT_PROVIDER).strip()
    entry = _CATALOG.get(pid)
    if entry is None:
        raise ProviderResolutionError(
            "unknown_provider",
            f"Provider '{pid}' não consta no catálogo autorizado.",
        )
    if entry.status == "experimental":
        env_authorized = provider_id is None and env_pid == pid
        if not (allow_experimental or env_authorized):
            raise ProviderResolutionError(
                "provider_not_enabled",
                f"Provider experimental '{pid}' exige habilitação "
                "explícita pelo backend.",
            )
    return entry.factory()


def list_providers() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for pid, entry in _CATALOG.items():
        desc = entry.factory().capability_descriptor()
        out.append(
            {
                "provider_id": pid,
                "status": entry.status,
                "descriptor": {
                    "version": desc.version,
                    "capabilities": desc.capabilities,
                    "formats": desc.formats,
                    "runs_local": desc.runs_local,
                    "license": desc.license,
                },
            }
        )
    return out
