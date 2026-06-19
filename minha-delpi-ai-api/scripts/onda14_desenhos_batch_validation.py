#!/usr/bin/env python3
"""Homologação batch Onda 14 — PDFs em desenhos/ vs casos H1–H13."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.infrastructure.config.settings import Settings
from tests.fixtures.drawing_hierarchical_regression_cases import pdf_regression_cases

configure_domain_infrastructure_ports()

Settings.CHAT_DOCUMENT_VISION_ENABLED = True
Settings.CHAT_DOCUMENT_VISION_BACKEND = "auto"
Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

_VISION_RUNTIME_STUB = {
    "documentVisionEnabled": True,
    "documentVisionMaxPages": max(1, int(Settings.CHAT_DOCUMENT_VISION_MAX_PAGES)),
    "documentVisionStampCropEnabled": True,
    "documentVisionAutoVlmFallback": False,
    "documentVisionImageDescribeEnabled": False,
    "documentVisionMaxChars": max(1, int(Settings.CHAT_DOCUMENT_VISION_MAX_CHARS)),
}

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "tests/fixtures/drawing_hierarchical_baseline_2026-06.json"
DESENHOS_DIR = ROOT / "desenhos"
TARGET_RATE = 10  # meta fase 14.8 (≥ 10/13)


def _load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def main() -> int:
    baseline = _load_baseline()
    baseline_ok = int(baseline.get("productCodeCorrect") or 0)
    cases = pdf_regression_cases()

    if not DESENHOS_DIR.is_dir():
        print(f"AVISO: pasta {DESENHOS_DIR} ausente — batch local ignorado.", file=sys.stderr)
        return 0

    available = {path.name for path in DESENHOS_DIR.glob("*.pdf")}
    runnable = [case for case in cases if case.pdf in available]

    if not runnable:
        print(f"AVISO: nenhum PDF dos casos H* em {DESENHOS_DIR}.", file=sys.stderr)
        return 0

    print(f"Onda 14 — batch {len(runnable)}/{len(cases)} PDFs em {DESENHOS_DIR}\n")
    header = f"{'caso':<6} {'arquivo':<16} {'esperado':<10} {'obtido':<10} {'flag':<6}"
    print(header)
    print("-" * len(header))

    ok = 0
    failures: list[dict] = []
    dims_ok = 0
    bom_ok = 0

    for case in runnable:
        pdf_path = DESENHOS_DIR / str(case.pdf)

        with patch(
            "app.application.services.chat_document_vision_service._vision_runtime",
            return_value=_VISION_RUNTIME_STUB,
        ):
            vision = ChatDocumentVisionService.extract_from_storage_path(
                str(pdf_path),
                filename=pdf_path.name,
                content_type="application/pdf",
            )
        obtained = str(vision.get("productCode") or "").strip() or None
        expected = case.expected_product_code
        passed = obtained == expected
        dims = vision.get("dimensions") if isinstance(vision.get("dimensions"), dict) else {}
        bom_count = len(vision.get("bomRows") or [])
        dims_partial = any(
            dims.get(key) is not None
            for key in ("totalLengthMm", "leftDecapeMm", "rightDecapeMm")
        )

        if passed:
            ok += 1

        if dims_partial:
            dims_ok += 1

        if bom_count > 0:
            bom_ok += 1

        flag = "OK" if passed else "FAIL"
        print(
            f"{case.id:<6} {case.pdf:<16} {expected or '-':<10} "
            f"{obtained or '-':<10} {flag:<6} "
            f"dims={'Y' if dims_partial else 'n'} bom={bom_count}"
        )

        if not passed:
            failures.append(
                {
                    "case": case.id,
                    "file": case.pdf,
                    "expected": expected,
                    "obtained": obtained,
                    "engine": vision.get("engine"),
                    "warnings": vision.get("warnings") or [],
                }
            )

    total = len(runnable)
    print("\n--- Resumo ---")
    summary = {
        "ok": ok,
        "total": total,
        "rate": round(ok / total, 4) if total else 0,
        "dimensionsPartial": dims_ok,
        "bomRowsPopulated": bom_ok,
        "baseline_ok": baseline_ok,
        "target_ok": TARGET_RATE,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    baseline_cases = int(baseline.get("pdfCasesInBaseline") or 13)

    if failures:
        print("\n--- Falhas ---")
        for item in failures:
            print(json.dumps(item, ensure_ascii=False))

    if total >= baseline_cases:
        if ok < baseline_ok:
            print(
                f"\nREGRESSÃO: {ok}/{total} < baseline {baseline_ok}/{baseline_cases}.",
                file=sys.stderr,
            )
            return 2

        if ok < TARGET_RATE:
            print(
                f"\nABAIXO DA META 14.8: {ok}/{total} (meta ≥ {TARGET_RATE}).",
                file=sys.stderr,
            )
            return 3

        return 0

    if ok < total:
        print(
            f"\nFALHA batch parcial: {ok}/{total} casos H* disponíveis em desenhos/.",
            file=sys.stderr,
        )
        return 2

    print(
        f"\nBatch parcial {total}/{baseline_cases} casos H* — "
        f"{ok}/{total} OK (baseline completo exige {baseline_cases} PDFs).",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
