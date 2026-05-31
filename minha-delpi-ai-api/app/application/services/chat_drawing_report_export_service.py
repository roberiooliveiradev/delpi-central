"""Exportação do relatório de análise de desenho — Onda 12.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ChatDrawingReportExportService:
    @classmethod
    def build_export_payload(
        cls,
        *,
        package: dict[str, Any],
        report_markdown: str,
    ) -> dict[str, str]:
        analysis = package.get("drawingAnalysis") if isinstance(package, dict) else {}
        code = str(analysis.get("productCode") or "desenho").strip()
        safe_code = "".join(char for char in code if char.isalnum()) or "desenho"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")

        return {
            "filename": f"relatorio-desenho-{safe_code}-{stamp}.md",
            "mimeType": "text/markdown; charset=utf-8",
            "markdown": str(report_markdown or "").strip(),
        }

    @classmethod
    def attach_to_metadata(
        cls,
        metadata: dict,
        *,
        package: dict[str, Any] | None,
        report_markdown: str | None,
    ) -> None:
        if not package or not str(report_markdown or "").strip():
            return

        metadata["drawingAnalysisExport"] = cls.build_export_payload(
            package=package,
            report_markdown=str(report_markdown or ""),
        )
