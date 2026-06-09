#!/usr/bin/env python3
"""Auditoria de cobertura de apresentação — 130 rotas OpenAPI × perfis do chat (Fase 0)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domain.services.chat_presentation_coverage_service import (  # noqa: E402
    ChatPresentationCoverageService,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=ChatPresentationCoverageService.default_openapi_baseline_path(),
        help="Caminho para openapi_baseline.json",
    )
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Grava docs/architecture/presentation-coverage-baseline.json",
    )
    parser.add_argument(
        "--write-csv",
        type=Path,
        help="Grava matriz CSV no caminho informado",
    )
    args = parser.parse_args()

    report = ChatPresentationCoverageService.build_report(baseline_path=args.baseline)
    rows = ChatPresentationCoverageService.build_matrix(baseline_path=args.baseline)
    summary = report["summary"]

    if args.write_baseline:
        target = ROOT / "docs" / "architecture" / "presentation-coverage-baseline.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Baseline gravado em {target}")

    if args.write_csv:
        args.write_csv.parent.mkdir(parents=True, exist_ok=True)
        args.write_csv.write_text(
            ChatPresentationCoverageService.rows_to_csv(rows),
            encoding="utf-8",
        )
        print(f"CSV gravado em {args.write_csv}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "Apresentação — cobertura OpenAPI\n"
            f"  operações: {summary['operationCount']}\n"
            f"  tier A (rica produto): {summary['tierCounts']['A']}\n"
            f"  tier B (KPI/LMP roteado): {summary['tierCounts']['B']}\n"
            f"  tier C (genérico): {summary['tierCounts']['C']}\n"
            f"  tier D (SQL/system): {summary['tierCounts']['D']}\n"
            f"  entidades roteadas: {summary['entityRoutedCount']} "
            f"({summary['entityRoutedRatio']:.0%})\n"
            f"  sem entidade mapeada: {summary['unmappedEntityCount']}"
        )

    expected = summary.get("operationCount", 0)

    if expected < 100:
        print(f"ERRO: esperado ≥100 operações, encontrado {expected}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
