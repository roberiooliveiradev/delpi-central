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

_STATUS_LABELS = {
    "available": "Disponível",
    "incomplete": "Incompleto (filiais ausentes)",
    "no_matching_items": "Sem dados para o filtro",
    "source_missing": "Posição histórica indisponível",
    "unavailable": "Indisponível",
}

_PARITY_LABELS = {
    "PENDING": "Paridade oficial pendente",
    "UNVERIFIED": "Paridade oficial não verificada",
}

# Monetary-presentation policy (doc 119 §11.6): totals keep integral
# Decimal precision; ≤ R$ 0,01 drift between displayed parcels is
# legitimate display rounding, never a calculation adjustment.
MONETARY_POLICY_NOTE = (
    "Os totais são calculados com precisão integral. Diferenças de um "
    "centavo entre parcelas apresentadas podem decorrer do "
    "arredondamento individual para exibição."
)


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


def status_label(status: str | None) -> str:
    return _STATUS_LABELS.get(status or "", status or "—")


def parity_label(parity: str | None) -> str:
    return _PARITY_LABELS.get(parity or "", parity or "UNVERIFIED")


def branch_label(branch: str | None) -> str:
    if not branch or branch == "all":
        return "Todas as filiais"
    return branch


def emission_stamp() -> str:
    """Data/hora de emissão em PT-BR — horário de Brasília (UTC−3, sem
    horário de verão desde 2019), com o fuso identificado."""
    from datetime import datetime, timedelta, timezone

    brasilia = timezone(timedelta(hours=-3))
    return datetime.now(brasilia).strftime("%d/%m/%Y %H:%M") + " (Brasília)"


def export_metadata(
    payload: dict[str, Any], *, generated_by: str | None
) -> list[tuple[str, str]]:
    """Identity block stamped on every exported report (PDF + CSV)."""
    provenance = payload.get("provenance") or {}
    return [
        ("Competência", str(payload.get("period") or "—")),
        ("Filial", branch_label(payload.get("branchCode"))),
        ("Escopo", scope_label(payload.get("reportScope"))),
        ("Data-base", str(payload.get("dataAsOf") or "—")),
        ("Fonte", str(payload.get("source") or "—")),
        ("Motor", str(provenance.get("engine") or "—")),
        ("Produtor oficial", str(provenance.get("officialProducer") or "—")),
        ("Status", status_label(payload.get("status"))),
        ("Paridade", parity_label(payload.get("parityStatus"))),
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
    stamp = emission_stamp()
    metadata = export_metadata(payload, generated_by=generated_by)
    metadata.extend(extra_metadata or [])
    metadata.append(("Emitido em", stamp))
    metadata.append(
        ("SHA-256 do conteúdo", content_hash(payload, hashed_keys))
    )
    spec = ClosingReportPdfSpec(
        title=title,
        metadata=metadata,
        sections=sections,
        watermark=watermark(payload),
        footer_note=(
            f"{title} — competência {payload.get('period') or '—'}"
        ),
        policy_note=MONETARY_POLICY_NOTE,
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
