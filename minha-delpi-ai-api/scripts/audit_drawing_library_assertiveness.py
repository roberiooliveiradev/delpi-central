#!/usr/bin/env python3
"""Auditoria assertividade — amostra aleatória da biblioteca de PDFs.

Descobre PDFs em `desenhos/` e `DRAWING_PDF_LIBRARY_DIR` (ex.: X:\\DESENHOS DELPI EM PDF
→ montar no WSL: `/mnt/x/DESENHOS DELPI EM PDF`).

Uso:
  cd minha-delpi-ai-api
  python scripts/audit_drawing_library_assertiveness.py --random 8 --seed 42
  DRAWING_PDF_LIBRARY_DIR=/mnt/x/DESENHOS\\ DELPI\\ EM\\ PDF \\
    python scripts/audit_drawing_library_assertiveness.py --random 10 --assertiveness-gate
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from scripts.validate_drawing_samples import (  # noqa: E402
    TARGET_CODES,
    _DRAWINGS_DIRS,
    _fetch_token,
    _validate_code,
)

from app.application.services.chat_drawing_validation_assertiveness_metrics_service import (  # noqa: E402
    ChatDrawingValidationAssertivenessMetricsService,
)

SUSPECT_TEMPLATE_KEYS = frozenset(
    {
        "bom_quantity_mismatch",
        "bom_extra",
        "bom_extra_item",
        "intermediate_extra",
        "intermediate_extra_item",
        "guide_component",
        "decape_mismatch",
        "revision_critical",
    }
)


def _discover_codes() -> list[str]:
    codes: set[str] = set()

    for directory in _DRAWINGS_DIRS:
        if not directory.is_dir():
            continue

        for pdf in directory.glob("*.pdf"):
            stem = pdf.stem.strip()

            if stem:
                codes.add(stem.split("-")[0])

    return sorted(codes)


def _select_codes(*, random_count: int, seed: int, explicit: list[str]) -> list[str]:
    if explicit:
        return explicit

    discovered = _discover_codes()

    if not discovered:
        return list(TARGET_CODES)

    if random_count <= 0 or random_count >= len(discovered):
        return discovered

    rng = random.Random(seed)
    return sorted(rng.sample(discovered, random_count))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auditoria assertividade — biblioteca de PDFs (amostra aleatória)",
    )
    parser.add_argument(
        "--random",
        type=int,
        default=0,
        metavar="N",
        help="Quantidade de PDFs aleatórios (0 = todos descobertos)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Semente para amostragem")
    parser.add_argument(
        "--codes",
        default="",
        help="Lista explícita de códigos (vírgula) — ignora --random",
    )
    parser.add_argument(
        "--assertiveness-gate",
        action="store_true",
        help="Falha se baseline ou taxa de falsos críticos exceder limiar",
    )
    parser.add_argument(
        "--max-mb",
        type=float,
        default=float(os.environ.get("DRAWING_AUDIT_MAX_MB", "2.5")),
        help="Ignora PDFs maiores que este limite",
    )
    args = parser.parse_args()

    explicit = [token.strip() for token in args.codes.split(",") if token.strip()]
    codes = _select_codes(random_count=args.random, seed=args.seed, explicit=explicit)

    print(f"Biblioteca: {[str(path) for path in _DRAWINGS_DIRS]}")
    print(f"Códigos selecionados ({len(codes)}): {', '.join(codes)}\n")

    token = _fetch_token()
    rows: list[dict] = []

    for code in codes:
        row = _validate_code(code, token=token)
        pdf_path = row.get("pdfPath")

        if pdf_path:
            size_mb = Path(str(pdf_path)).stat().st_size / (1024 * 1024)

            if size_mb > args.max_mb:
                row["skipped"] = "large_pdf"
                rows.append(row)
                print(f"⊘ {code} ignorado — PDF {size_mb:.1f} MB > {args.max_mb} MB")
                continue

        rows.append(row)
        icon = "✓" if int(row.get("criticalErrors") or 0) == 0 else "✗"
        suspects = [
            item
            for item in row.get("criticalItems") or []
            if str(item.get("templateKey") or "") in SUSPECT_TEMPLATE_KEYS
        ]
        suspect_flag = " ⚠" if suspects else ""
        print(
            f"{icon}{suspect_flag} {code} status={row.get('validationStatus')} "
            f"críticos={row.get('criticalErrors')} pdf={'sim' if row.get('pdfPath') else 'não'}"
        )

        for item in suspects:
            print(f"    ? [{item.get('section')}] {item.get('item')} ({item.get('templateKey')})")

    out = Path(__file__).resolve().parent / "audit_drawing_library_report.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório: {out}")

    metrics = ChatDrawingValidationAssertivenessMetricsService.aggregate(rows)
    print(
        "\nAssertividade: "
        f"false_critical_rate={metrics.get('falseCriticalRate')} "
        f"(limiar={metrics.get('maxFalseCriticalRate')})"
    )

    for sample in metrics.get("samples") or []:
        flag = "FAIL" if sample.get("falseCritical") or not sample.get("statusOk") else "OK"
        print(
            f"  [{flag}] {sample.get('code')} "
            f"críticos={sample.get('criticalErrors')} status={sample.get('validationStatus')}"
        )

    if args.assertiveness_gate and not metrics.get("passesGate"):
        print("\n✗ Gate de assertividade reprovado.")
        return 1

    if args.assertiveness_gate:
        print("\n✓ Gate de assertividade aprovado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
