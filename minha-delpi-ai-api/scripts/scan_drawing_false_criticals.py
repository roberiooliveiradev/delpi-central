#!/usr/bin/env python3
"""Varre PDFs locais e lista críticos suspeitos de falso positivo."""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_analyser_fetch_service import (
    ChatDrawingAnalyserFetchService,
)
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()

PDF_DIR = _API_ROOT / "desenhos"
MAX_MB = float(__import__("os").environ.get("DRAWING_SCAN_MAX_MB", "1.5"))
SUSPECT_KEYS = ("bom_extra", "bom_quantity", "guide_component")


def main() -> int:
    results: list[dict] = []
    suspects: list[dict] = []

    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        if pdf.stat().st_size > MAX_MB * 1024 * 1024:
            results.append({"code": pdf.stem, "skipped": "large_pdf"})
            continue

        code = pdf.stem.split("-")[0]

        try:
            root = ChatDrawingAnalyserFetchService.fetch_root(
                product_code=code,
                access_token=None,
            )

            if not root:
                results.append({"code": code, "skipped": "no_analyser"})
                continue

            extract = ChatDrawingPdfExtractionService.extract_from_storage_path(
                str(pdf),
                filename=pdf.name,
            )
            package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
                product_code=code,
                payload=root,
                has_pdf_attachment=True,
                api_ok=True,
                pdf_extract=extract,
            )
            analysis = package.get("drawingAnalysis") or {}
            comparison = ChatDrawingBomComparisonService.compare(
                root=root,
                pdf_extract=extract,
                product_code=code,
            )
            critical_items = [
                item
                for item in analysis.get("items") or []
                if item.get("status") == "critical_error"
            ]
            row = {
                "code": code,
                "pdf": pdf.name,
                "status": analysis.get("status"),
                "critical": int(analysis.get("criticalErrors") or 0),
                "extra": list(comparison.extra_in_pdf)[:6],
                "missing": list(comparison.missing_in_pdf)[:6],
                "crit": [
                    (
                        item.get("templateKey") or item.get("item"),
                        str(item.get("pdfEvidence") or "")[:60],
                    )
                    for item in critical_items
                ],
            }
            results.append(row)

            for key, evidence in row["crit"]:
                normalized = str(key or "").lower()

                if any(token in normalized for token in SUSPECT_KEYS):
                    suspects.append(
                        {
                            "code": code,
                            "suspect": key,
                            "evidence": evidence,
                            "extra": row["extra"],
                            "status": row["status"],
                        }
                    )

            del extract, package, root
            gc.collect()
        except Exception as exc:
            results.append({"code": code, "error": str(exc)[:120]})

    payload = {
        "scanned": len(results),
        "suspects": suspects,
        "critical": [
            row
            for row in results
            if int(row.get("critical") or 0) > 0
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
