#!/usr/bin/env python3
"""Validação live — 90264227-1.pdf + API analyser."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]

if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_pdf_extraction_service import ChatDrawingPdfExtractionService
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()

CODE = "90264227"
PDF = _API_ROOT / "desenhos" / "90264227-1.pdf"
_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_API_PREFIX = os.environ.get("SMOKE_API_PREFIX", "/apps/api-delpi").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode()
    url = f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token"
    request = urllib.request.Request(
        url,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def main() -> int:
    if not PDF.is_file():
        print(f"PDF ausente: {PDF}", file=sys.stderr)
        return 1

    token = _token()
    request = urllib.request.Request(
        f"{_BASE_URL}{_API_PREFIX}/products/{CODE}/analyser",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        analyser = json.loads(response.read().decode("utf-8"))

    root = analyser.get("data") if isinstance(analyser.get("data"), dict) else {}
    pdf_extract = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(PDF),
        filename=PDF.name,
    )

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=CODE,
        payload=root,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=pdf_extract,
    )
    analysis = package.get("drawingAnalysis") or {}

    summary = {
        "pdf": str(PDF),
        "status": analysis.get("status"),
        "criticalErrors": analysis.get("criticalErrors"),
        "warnings": analysis.get("warnings"),
        "extractionConfidence": (analysis.get("validationLayers") or {}).get(
            "extractionConfidence"
        ),
        "extractionQualityRetry": pdf_extract.get("extractionQualityRetry"),
        "componentCodes": pdf_extract.get("componentCodes"),
        "intermediateCodes": pdf_extract.get("intermediateCodes"),
        "dimensions": pdf_extract.get("dimensions"),
        "criticalItems": [
            {
                "section": item.get("section"),
                "item": item.get("item"),
                "templateKey": item.get("templateKey"),
            }
            for item in (analysis.get("items") or [])
            if isinstance(item, dict) and item.get("status") == "critical_error"
        ],
        "pendingItems": [
            {
                "section": item.get("section"),
                "item": item.get("item"),
                "templateKey": item.get("templateKey"),
            }
            for item in (analysis.get("items") or [])
            if isinstance(item, dict) and item.get("status") in {"pending", "error"}
        ],
        "okCount": sum(
            1
            for item in (analysis.get("items") or [])
            if isinstance(item, dict) and item.get("status") == "ok"
        ),
    }

    out = Path(__file__).resolve().parent / "validate_90264227_live_report.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nRelatório: {out}")

    return 0 if analysis.get("status") != "rejected" else 2


if __name__ == "__main__":
    raise SystemExit(main())
