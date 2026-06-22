#!/usr/bin/env python3
"""Valida desenhos alvo — API /analyser + PDF local + layout/confiança.

Uso:
  cd minha-delpi-ai-api
  DRAWING_VALIDATE_CODES=90264227 python scripts/validate_drawing_samples.py
  DRAWING_VALIDATE_CODES=90263149,90264227 python scripts/validate_drawing_samples.py --assertiveness-gate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

TARGET_CODES = [
    token.strip()
    for token in os.environ.get(
        "DRAWING_VALIDATE_CODES",
        "90262834,90263622,90264227",
    ).split(",")
    if token.strip()
]
_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_API_PREFIX = os.environ.get("SMOKE_API_PREFIX", "/apps/api-delpi").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_DRAWINGS_DIRS = [
    Path(__file__).resolve().parents[1] / "desenhos",
    Path(
        os.environ.get(
            "DRAWING_PDF_LIBRARY_DIR",
            "/mnt/x/DESENHOS DELPI EM PDF",
        )
    ),
]


def _tesseract_available() -> bool:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _request(method: str, url: str, *, token: str | None = None) -> tuple[int, dict | None, str]:
    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            body = json.loads(raw) if raw else None
            return response.status, body, raw[:500]
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")

        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = None

        return exc.code, body, raw[:500]


def _fetch_token() -> str:
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


def _download_pdf(code: str, *, token: str, target: Path) -> bool:
    request = urllib.request.Request(
        f"{_BASE_URL}{_API_PREFIX}/products/{code}/drawing/pdf",
        headers={
            "Accept": "application/pdf",
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read()
    except urllib.error.HTTPError:
        return False

    if not payload.startswith(b"%PDF"):
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return True


def _resolve_pdf(code: str, *, token: str) -> Path | None:
    for directory in _DRAWINGS_DIRS:
        candidate = directory / f"{code}.pdf"

        if candidate.is_file():
            return candidate

    cache_dir = Path(__file__).resolve().parent / ".drawing_samples_cache"
    cached = cache_dir / f"{code}.pdf"

    if cached.is_file():
        return cached

    if _download_pdf(code, token=token, target=cached):
        return cached

    return None


def _validate_code(code: str, *, token: str) -> dict:
    chat_root = Path(__file__).resolve().parents[1]

    if str(chat_root) not in sys.path:
        sys.path.insert(0, str(chat_root))

    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_drawing_pdf_extraction_service import (
        ChatDrawingPdfExtractionService,
    )
    from app.domain.services.chat_drawing_validation_orchestration_service import (
        ChatDrawingValidationOrchestrationService,
    )

    configure_domain_infrastructure_ports()

    status, analyser, _ = _request(
        "GET",
        f"{_BASE_URL}{_API_PREFIX}/products/{code}/analyser",
        token=token,
    )
    row: dict = {
        "code": code,
        "analyserHttp": status,
        "hasProduct": False,
        "hasStructure": False,
        "hasGuide": False,
        "hasInspection": False,
        "pdfPath": None,
        "validationStatus": None,
        "criticalErrors": None,
        "warnings": None,
        "checklistItems": 0,
        "criticalItems": [],
        "pendingItems": [],
    }

    if status != 200 or not isinstance(analyser, dict) or not analyser.get("success"):
        row["analyserError"] = analyser.get("message") if isinstance(analyser, dict) else status
        return row

    root = analyser.get("data") if isinstance(analyser.get("data"), dict) else {}
    product = root.get("product") if isinstance(root.get("product"), dict) else {}
    row["hasProduct"] = bool(product)
    row["hasStructure"] = bool((root.get("structure") or {}).get("items"))
    row["hasGuide"] = bool((root.get("guide") or {}).get("items"))
    row["hasInspection"] = bool((root.get("inspection") or {}).get("items"))
    row["description"] = product.get("description")

    pdf_path = _resolve_pdf(code, token=token)
    pdf_extract = None
    has_pdf = False

    if pdf_path:
        has_pdf = True
        row["pdfPath"] = str(pdf_path)
        pdf_extract = ChatDrawingPdfExtractionService.extract_from_storage_path(
            str(pdf_path),
            filename=pdf_path.name,
        )
        row["pdfPageCount"] = pdf_extract.get("pageCount")
        row["pdfComponentCount"] = len(pdf_extract.get("componentCodes") or [])
        row["pdfLegible"] = pdf_extract.get("legible")
        row["pageLayoutAnalysis"] = pdf_extract.get("pageLayoutAnalysis")

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=code,
        payload=root,
        has_pdf_attachment=has_pdf,
        api_ok=True,
        pdf_extract=pdf_extract,
    )
    analysis = package.get("drawingAnalysis") or {}
    row["validationStatus"] = analysis.get("status")
    row["criticalErrors"] = analysis.get("criticalErrors")
    row["warnings"] = analysis.get("warnings")
    row["checklistItems"] = len(analysis.get("items") or [])
    row["multipageCoverage"] = analysis.get("multipageCoverage")
    row["extractionConfidence"] = (analysis.get("validationLayers") or {}).get(
        "extractionConfidence"
    )
    row["visionRefinement"] = analysis.get("visionRefinement")
    row["bomVisionRefinement"] = (pdf_extract or {}).get("bomVisionRefinement")

    for item in analysis.get("items") or []:
        if not isinstance(item, dict):
            continue

        if item.get("status") == "critical_error":
            row["criticalItems"].append(
                {
                    "section": item.get("section"),
                    "item": item.get("item"),
                    "templateKey": item.get("templateKey"),
                }
            )
        elif item.get("status") in {"pending", "error"}:
            row["pendingItems"].append(
                {
                    "section": item.get("section"),
                    "item": item.get("item"),
                    "templateKey": item.get("templateKey"),
                }
            )

    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida desenhos alvo (API + PDF local)")
    parser.add_argument(
        "--assertiveness-gate",
        action="store_true",
        help="Falha se false_critical_rate > limiar da baseline (15.8.6)",
    )
    args = parser.parse_args()

    print(f"Base URL: {_BASE_URL}{_API_PREFIX}\n")

    if not _tesseract_available():
        print(
            "⚠ Tesseract não encontrado no PATH — extração regional do PDF ficará vazia.\n"
            "  Use o container delpi-minha-delpi-ai-api ou instale tesseract-ocr (por+eng).\n"
        )

    token = _fetch_token()
    rows = []

    for code in TARGET_CODES:
        row = _validate_code(code, token=token)
        rows.append(row)
        icon = "✓" if row.get("validationStatus") not in {"rejected", None} else "✗"
        print(
            f"{icon} {code} analyser={row.get('analyserHttp')} "
            f"cadastro={'sim' if row.get('hasProduct') else 'não'} "
            f"pdf={'sim' if row.get('pdfPath') else 'não'} "
            f"status={row.get('validationStatus') or '—'} "
            f"críticos={row.get('criticalErrors') if row.get('criticalErrors') is not None else '—'}"
        )

        for item in row.get("criticalItems") or []:
            print(f"    ❌ [{item.get('section')}] {item.get('item')}")

        for item in (row.get("pendingItems") or [])[:5]:
            print(f"    ⚠️ [{item.get('section')}] {item.get('item')}")

    out = Path(__file__).resolve().parent / "validate_drawing_samples_report.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório: {out}")

    failed = [
        row
        for row in rows
        if row.get("analyserHttp") != 200 or not row.get("hasProduct")
    ]

    if args.assertiveness_gate:
        chat_root = Path(__file__).resolve().parents[1]

        if str(chat_root) not in sys.path:
            sys.path.insert(0, str(chat_root))

        from app.application.services.chat_drawing_validation_assertiveness_metrics_service import (
            ChatDrawingValidationAssertivenessMetricsService,
        )

        metrics = ChatDrawingValidationAssertivenessMetricsService.aggregate(rows)
        print(
            "\nAssertividade: "
            f"false_critical_rate={metrics.get('falseCriticalRate')} "
            f"(limiar={metrics.get('maxFalseCriticalRate')}) "
            f"pending_avg={metrics.get('pendingRateAvg')}"
        )

        for sample in metrics.get("samples") or []:
            flag = "FAIL" if sample.get("falseCritical") or not sample.get("statusOk") else "OK"
            print(
                f"  [{flag}] {sample.get('code')} "
                f"críticos={sample.get('criticalErrors')} "
                f"status={sample.get('validationStatus')}"
            )

        if not metrics.get("passesGate"):
            print("\n✗ Gate de assertividade reprovado.")
            return 1

        print("\n✓ Gate de assertividade aprovado.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
