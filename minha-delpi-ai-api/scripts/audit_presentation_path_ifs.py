#!/usr/bin/env python3
"""Inventário de `if`/`elif` por path — Playbook 12 fase R0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_refactor_baseline_service import (  # noqa: E402
    ChatPresentationRefactorBaselineService,
)

configure_domain_infrastructure_ports()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON completo")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Grava docs/architecture/presentation-refactor-baseline-jun2026.json",
    )
    parser.add_argument(
        "--check-baseline",
        action="store_true",
        help="Falha se o inventário divergir do baseline versionado",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Falha se gate DOCIE Fase 19 (path literals em domain/application) > 0",
    )
    args = parser.parse_args()

    report = ChatPresentationRefactorBaselineService.build_report()
    summary = report.get("summary") or {}

    if args.write_baseline:
        target = ChatPresentationRefactorBaselineService.write_baseline()
        print(f"Baseline gravado em {target}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "Playbook 12 — inventário de apresentação declarativa (R0)\n"
            f"  arquivos auditados: {summary.get('auditFileCount', 0)}\n"
            f"  condicionais por path: {summary.get('totalPathConditionals', 0)}\n"
            f"  condicionais montagem tabela (use case): "
            f"{summary.get('useCaseTableAssemblyPathConditionalCount', 0)}\n"
            f"  handlers rota (section availability): "
            f"{summary.get('sectionAvailabilityRouteHandlerCount', 0)}\n"
            f"  linhas section availability: {summary.get('sectionAvailabilityLineCount', 0)}\n"
            f"  métodos _enrich_* dedicados: {summary.get('visualBundleDedicatedEnrichCount', 0)}\n"
            f"  perfis tier A sem visualBuilders: "
            f"{summary.get('tierAMissingVisualBuildersCount', 0)}\n"
            f"  perfis tier A sem tableAssembly: "
            f"{summary.get('tierAMissingTableAssemblyCount', 0)}"
        )

        profile_gaps = report.get("profileGaps") or {}
        tier_a_missing = profile_gaps.get("tierAMissingVisualBuilders") or []
        if tier_a_missing:
            print("\nTier A sem visualBuilders:")
            for key in tier_a_missing:
                print(f"  - {key}")

    exit_code = 0

    if args.check_baseline:
        comparison = ChatPresentationRefactorBaselineService.compare_to_stored()
        if not comparison["ok"]:
            exit_code = 1
            drift = comparison.get("drift") or []
            print(f"\nERRO: {len(drift)} divergência(s) vs baseline", file=sys.stderr)
            for item in drift[:20]:
                print(
                    f"  - {item['field']}: baseline={item['baseline']} current={item['current']}",
                    file=sys.stderr,
                )

    if args.check:
        ok, errors = ChatPresentationRefactorBaselineService.run_docie_gate_check()

        if not ok:
            exit_code = 1
            print("DOCIE Fase 19 — apresentação entity-first", file=sys.stderr)

            for item in errors:
                print(f"  - {item}", file=sys.stderr)
        elif not args.json and not args.write_baseline and not args.check_baseline:
            report = ChatPresentationRefactorBaselineService.build_docie_gate_report()
            summary = report.get("summary") or {}
            print(
                "DOCIE Fase 19 OK — "
                f"{summary.get('auditFileCount', 0)} arquivos, "
                f"{summary.get('totalPathConditionals', 0)} condicionais por path."
            )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
