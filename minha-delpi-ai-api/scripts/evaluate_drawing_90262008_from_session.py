#!/usr/bin/env python3
"""Avaliação 90262008 com PDF real da conversa 5d934af6."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

from app.application.services.chat_drawing_report_export_service import (
    ChatDrawingReportExportService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()

SESSION_ID = "5d934af6-ec6e-4321-9fef-d49b7356bd9f"
CODE = "90262008"
PDF_PATH = (
    "/data/delpi/chat-attachments/4ac305a6-0569-40b8-a918-b908cfeba169/"
    f"{SESSION_ID}/f0240dfccbf946978319a13b9bbfa967.pdf"
)
BASE = "http://delpi-gateway"


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": "delpi-central",
            "username": "rober",
            "password": "1234",
        }
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/auth/realms/delpi/protocol/openid-connect/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return str(json.loads(response.read().decode("utf-8"))["access_token"])


def _analyser(token: str) -> dict:
    req = urllib.request.Request(
        f"{BASE}/apps/api-delpi/products/{CODE}/analyser?view=full",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))["data"]


def _stored_analysis() -> dict | None:
    import os

    import psycopg

    database_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+psycopg://", "postgresql://"
    )

    if not database_url:
        return None

    query = """
        SELECT metadata
        FROM ai_chat_messages
        WHERE session_id = %s AND role = 'assistant'
        ORDER BY created_at DESC
        LIMIT 1
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (SESSION_ID,))
            row = cur.fetchone()

    if not row or not row[0]:
        return None

    metadata = row[0]
    drawing = metadata.get("drawingAnalysis") if isinstance(metadata, dict) else None

    return drawing if isinstance(drawing, dict) else None


def main() -> int:
    print("Extraindo PDF anexado (OCR regional)…")
    pdf_extract = ChatDrawingPdfExtractionService.extract_from_storage_path(
        PDF_PATH,
        filename="90262008.pdf",
    )

    print(
        f"  legible={pdf_extract.get('legible')} "
        f"productCode={pdf_extract.get('productCode')} "
        f"internalRevision={pdf_extract.get('internalRevision')} "
        f"bomRows={len(pdf_extract.get('bomRows') or [])} "
        f"segments={pdf_extract.get('dimensions', {}).get('segmentLengthsMm')}"
    )

    token = _token()
    analyser = _analyser(token)

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=CODE,
        payload=analyser,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=pdf_extract,
    )

    analysis = package["drawingAnalysis"]
    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)
    export = ChatDrawingReportExportService.build_export_payload(
        package=package,
        report_markdown=report,
    )

    items = analysis.get("items") or []
    critical = [item for item in items if item.get("status") == "critical_error"]
    pending = [item for item in items if item.get("status") == "pending"]

    false_positive_templates = {
        "bom_extra",
        "guide_component_mismatch",
        "bom_quantity_mismatch",
        "revision_critical",
    }
    false_positives = [
        item for item in items if item.get("templateKey") in false_positive_templates
    ]
    segment_pending = [
        item for item in items if item.get("templateKey") == "segment_length_pending"
    ]

    stored = _stored_analysis()

    print("\n" + "=" * 60)
    print("AVALIAÇÃO — PDF real da conversa 5d934af6")
    print("=" * 60)
    print(
        f"Status: {analysis.get('status')} ({analysis.get('overallLabel')}) | "
        f"Críticos: {analysis.get('criticalErrors')} | Pendentes: {len(pending)} | "
        f"Itens: {len(items)}"
    )
    print(f"Paridade export: {export.get('checklistConsistency', {}).get('ok')}")

    if stored:
        print(
            f"\nConversa anterior: {stored.get('status')} ({stored.get('overallLabel')}) | "
            f"críticos={stored.get('criticalErrors')}"
        )

    print("\n--- Revisão ---")
    for item in items:
        if "revis" in str(item.get("item", "")).lower():
            print(
                f"  [{item.get('status')}] {item.get('item')} | "
                f"PDF: {item.get('pdfEvidence')} | API: {item.get('apiEvidence')}"
            )

    print("\n--- Falsos positivos alvo ---")
    if false_positives:
        for item in false_positives:
            print(f"  FAIL {item.get('templateKey')}: {item.get('item')}")
    else:
        print("  OK — bom_extra, guide_component, bom_quantity, revision_critical")

    print("\n--- segment_length_pending ---")
    if segment_pending:
        for item in segment_pending:
            print(f"  {item.get('pdfEvidence')} vs API {item.get('apiEvidence')}")
    else:
        print("  OK — nenhum")

    print("\n--- Críticos ---")
    if critical:
        for item in critical:
            print(f"  • [{item.get('section')}] {item.get('item')}")
    else:
        print("  (nenhum)")

    print("\n--- Conclusão ---")
    print(analysis.get("conclusion"))

    marker = report.find("## 5.")
    print("\n--- Checklist (início) ---")
    print(report[marker : marker + 2000] if marker >= 0 else report[:1500])

    failed = bool(false_positives) or bool(critical)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
