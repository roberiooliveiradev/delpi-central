#!/usr/bin/env python3
"""Avaliação live 90262008 — API /analyser + PDF sintético do cenário de regressão."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.application.services.chat_drawing_report_export_service import (
    ChatDrawingReportExportService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from tests.fixtures.drawing_validation_rule_regression_cases import (
    pdf_extract_stamp_bom_nested_mp,
)

configure_domain_infrastructure_ports()

BASE = "http://delpi-gateway"
CODE = "90262008"


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
        payload = json.loads(response.read().decode("utf-8"))

    return str(payload["access_token"])


def main() -> int:
    token = _token()
    req = urllib.request.Request(
        f"{BASE}/apps/api-delpi/products/{CODE}/analyser?view=full",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        analyser = json.loads(response.read().decode("utf-8"))["data"]

    pdf_extract = {
        **pdf_extract_stamp_bom_nested_mp(),
        "revision": "08",
        "internalRevision": "04",
    }

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
        "segment_length_pending",
        "revision_critical",
    }
    false_positives = [
        item for item in items if item.get("templateKey") in false_positive_templates
    ]

    revision_items = [
        item
        for item in items
        if item.get("item") == "Revisão"
        or "revis" in str(item.get("item", "")).lower()
    ]

    print("=" * 60)
    print(f"PRODUTO {CODE} — avaliação pós-fix")
    print("=" * 60)
    print(
        f"Status geral: {analysis.get('status')} ({analysis.get('overallLabel')})"
    )
    print(
        f"Críticos: {analysis.get('criticalErrors')} | "
        f"Pendentes: {len(pending)} | Checklist: {len(items)}"
    )
    print(f"Paridade export: {export.get('checklistConsistency')}")
    print()

    print("--- Revisão ---")
    for item in revision_items:
        print(
            f"  [{item.get('status')}] {item.get('item')} | "
            f"PDF: {item.get('pdfEvidence')} | API: {item.get('apiEvidence')}"
        )

    print("\n--- Falsos positivos (devem ser zero) ---")
    if false_positives:
        for item in false_positives:
            print(
                f"  FAIL {item.get('templateKey')}: "
                f"{item.get('item')} ({item.get('status')})"
            )
    else:
        print("  OK — nenhum nas categorias corrigidas")

    print("\n--- Críticos reais ---")
    if critical:
        for item in critical:
            print(
                f"  • [{item.get('section')}] {item.get('item')} — "
                f"{item.get('recommendation')}"
            )
    else:
        print("  (nenhum)")

    print("\n--- Pendentes (amostra) ---")
    for item in pending[:10]:
        print(f"  • [{item.get('section')}] {item.get('item')}")

    print("\n--- Conclusão ---")
    print(str(analysis.get("conclusion") or "—")[:400])

    marker = report.find("## 5.")
    print("\n--- Checklist (trecho) ---")
    print(report[marker : marker + 1500] if marker >= 0 else report[:1000])

    return 1 if false_positives else 0


if __name__ == "__main__":
    sys.exit(main())
