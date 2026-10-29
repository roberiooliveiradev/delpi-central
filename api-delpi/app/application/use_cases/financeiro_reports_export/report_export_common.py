"""Shared export machinery for the closing analytical reports.

One policy for every governed report export (P7/R05/R08): the SAME
payload the query contract returns, the same metadata identity
(competence, branch, scope, as_of, source, engine, parity state,
SHA-256 content hash, generated_by/at) and the same honesty watermark
— never an official seal while parity is pending.
"""

from __future__ import annotations

import hashlib
import io
import json
from typing import Any

from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ClosingReportPdfSpec,
    ReportTableSection,
    render_closing_report_pdf,
)

EXPORT_PAGE_SIZE = 50000
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_PDF = "pdf"
EXPORT_FORMATS = (EXPORT_FORMAT_CSV, EXPORT_FORMAT_PDF)

# Statuses representing a real population — anything else never becomes
# a document (a header-only file could masquerade as zero data).
EXPORTABLE_STATUSES = frozenset(
    {"available", "incomplete", "no_matching_items"}
)

_SCOPE_LABELS = {
    "all_products": "Todos os produtos",
    "mp_pi_pa": "Somente MP, PI e PA",
}


class ReportNotExportableError(RuntimeError):
    """Payload status cannot certify a document (e.g. source_missing)."""


class ReportExportTruncatedError(RuntimeError):
    """Item population exceeded the export batch — never certify part."""


def scope_label(scope: str | None) -> str:
    return _SCOPE_LABELS.get(scope or "", scope or "")


def content_hash(payload: dict[str, Any], hashed_keys: tuple[str, ...]) -> str:
    """SHA-256 over the data the document certifies — canonical JSON,
    stable across key order."""
    material = {key: payload.get(key) for key in hashed_keys}
    blob = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def export_metadata(
    payload: dict[str, Any], *, generated_by: str | None
) -> list[tuple[str, str]]:
    """Identity block stamped on every exported report (PDF + CSV)."""
    provenance = payload.get("provenance") or {}
    return [
        ("Competência", str(payload.get("period") or "—")),
        ("Filial", str(payload.get("branchCode") or "—")),
        ("Escopo", scope_label(payload.get("reportScope"))),
        ("Referência", str(payload.get("dataAsOf") or "—")),
        ("Fonte", str(payload.get("source") or "—")),
        ("Motor", str(provenance.get("engine") or "—")),
        ("Produtor oficial", str(provenance.get("officialProducer") or "—")),
        ("Status", str(payload.get("status") or "—")),
        ("Paridade", str(payload.get("parityStatus") or "UNVERIFIED")),
        ("Gerado por", generated_by or "desconhecido"),
    ]


def watermark(payload: dict[str, Any]) -> str | None:
    """Honest parity watermark — the export is never an official seal."""
    official = bool(
        payload.get("officialP7")
        or payload.get("officialMatr989")
        or payload.get("officialMatr320")
    )
    if official:
        return None
    return (
        "RELATÓRIO OPERACIONAL — PARIDADE OFICIAL PENDENTE. "
        "Não substitui a emissão oficial do Protheus."
    )


def build_pdf(
    *,
    title: str,
    payload: dict[str, Any],
    hashed_keys: tuple[str, ...],
    sections: list[ReportTableSection],
    generated_by: str | None,
    extra_metadata: list[tuple[str, str]] | None = None,
) -> io.BytesIO:
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metadata = export_metadata(payload, generated_by=generated_by)
    metadata.extend(extra_metadata or [])
    metadata.append(("Gerado em", stamp))
    metadata.append(
        ("SHA-256", content_hash(payload, hashed_keys)[:16] + "…")
    )
    spec = ClosingReportPdfSpec(
        title=title,
        metadata=metadata,
        sections=sections,
        watermark=watermark(payload),
        footer_note=watermark(payload) or title,
    )
    return io.BytesIO(
        render_closing_report_pdf(spec, generated_stamp=stamp)
    )


def csv_safe_text(value: Any) -> Any:
    """OWASP CSV formula injection guard — text cells opening with a
    formula character are neutralized with a leading apostrophe."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value
