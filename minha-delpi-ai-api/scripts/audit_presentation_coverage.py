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

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_coverage_service import (  # noqa: E402
    ChatPresentationCoverageService,
)
from tests.fixtures.presentation_interactivity_gate import (  # noqa: E402
    validate_tier_a_interactivity_cases,
)
from tests.fixtures.presentation_table_role_gate import validate_table_roles_for_ci  # noqa: E402

configure_domain_infrastructure_ports()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=ChatPresentationCoverageService.default_openapi_baseline_path(),
        help="Caminho para openapi_baseline.json",
    )
    parser.add_argument(
        "--stored-baseline",
        type=Path,
        default=ChatPresentationCoverageService.default_stored_baseline_path(),
        help="Baseline congelado em docs/architecture/",
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
    parser.add_argument(
        "--check-profiles",
        action="store_true",
        help="Falha se rotas tier A usarem perfil generic ou profileKey ausente",
    )
    parser.add_argument(
        "--check-new-operations",
        action="store_true",
        help="Falha se houver operações novas vs baseline sem entidade/perfil",
    )
    parser.add_argument(
        "--check-table-roles",
        action="store_true",
        help="Falha se fixtures tier A (tierAPipelineCases) produzirem tabela sem role",
    )
    parser.add_argument(
        "--check-visual-builders",
        action="store_true",
        help="Alerta se perfil declarar viewOrder kpi/tree/chart/dashboard sem visualBuilders",
    )
    parser.add_argument(
        "--check-interactivity-chips",
        action="store_true",
        help="Falha se fixtures tier A com expected_interactivity_labels não produzirem chips",
    )
    parser.add_argument(
        "--check-playbook12",
        action="store_true",
        help="Falha se qualquer gate R12 (perfis, roles, chips, path baseline) divergir",
    )
    parser.add_argument(
        "--check-commentary-profiles",
        action="store_true",
        help="Falha se rotas tier A não tiverem commentaryProfileKey declarativo no perfil",
    )
    args = parser.parse_args()

    report = ChatPresentationCoverageService.build_report(baseline_path=args.baseline)
    rows = ChatPresentationCoverageService.build_matrix(baseline_path=args.baseline)
    summary = report["summary"]
    metrics = summary.get("metrics") or {}

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
            f"  tier B+ ratio: {metrics.get('tierBPlusRatio', 0):.0%}\n"
            f"  tier A/B perfil mapeado: {metrics.get('tierABProfileMappedRatio', 0):.0%}\n"
            f"  entidades roteadas: {summary['entityRoutedCount']} "
            f"({summary['entityRoutedRatio']:.0%})\n"
            f"  sem entidade mapeada: {summary['unmappedEntityCount']}"
        )

    expected = summary.get("operationCount", 0)

    if expected < 100:
        print(f"ERRO: esperado ≥100 operações, encontrado {expected}", file=sys.stderr)
        return 1

    exit_code = 0

    if args.check_profiles or args.check_new_operations:
        validation = ChatPresentationCoverageService.validate_for_ci(
            openapi_baseline_path=args.baseline,
            stored_baseline_path=args.stored_baseline,
        )

        if args.check_profiles:
            profile_gaps = validation.get("profileGaps") or []

            if profile_gaps:
                exit_code = 1
                print(f"\nERRO: {len(profile_gaps)} gap(s) de perfil", file=sys.stderr)

                for gap in profile_gaps[:12]:
                    print(
                        f"  - [{gap['kind']}] {gap['operation_id']} "
                        f"{gap['path']} ({gap['detail']})",
                        file=sys.stderr,
                    )

        if args.check_new_operations:
            new_gaps = validation.get("newOperationGaps") or []
            new_ops = validation.get("newOperations") or []

            if new_ops:
                print(f"\nNovas operações vs baseline: {len(new_ops)}")

                for row in new_ops[:8]:
                    print(f"  + {row['operation_id']} {row['path']}")

            if new_gaps:
                exit_code = 1
                print(f"\nERRO: {len(new_gaps)} nova(s) operação(ões) sem contrato", file=sys.stderr)

                for gap in new_gaps[:12]:
                    print(
                        f"  - [{gap['kind']}] {gap['operation_id']} "
                        f"{gap['path']} ({gap['detail']})",
                        file=sys.stderr,
                    )

    if args.check_table_roles:
        table_role_validation = validate_table_roles_for_ci()
        table_role_gaps = table_role_validation.get("tableRoleGaps") or []

        if table_role_gaps:
            exit_code = 1
            print(
                f"\nERRO: {len(table_role_gaps)} gap(s) de role em tier A",
                file=sys.stderr,
            )

            for gap in table_role_gaps[:12]:
                print(
                    f"  - [{gap['case_id']}] {gap['profile_key']} {gap['path']} "
                    f"({gap['detail']})",
                    file=sys.stderr,
                )
        else:
            print("\nOK: tierAPipelineCases — todas as tabelas com role")

    if args.check_visual_builders:
        builder_validation = ChatPresentationCoverageService.validate_visual_builders_for_ci()
        warnings = builder_validation.get("visualBuilderWarnings") or []

        if warnings:
            print(f"\nAVISO: {len(warnings)} perfil(is) com viewOrder sem visualBuilders")

            for warning in warnings[:12]:
                print(
                    f"  - {warning['profile_key']} view={warning['view']} "
                    f"({warning['detail']})"
                )
        else:
            print("\nOK: viewOrder alinhado a visualBuilders")

    if args.check_interactivity_chips:
        chip_gaps = validate_tier_a_interactivity_cases()

        if chip_gaps:
            exit_code = 1
            print(
                f"\nERRO: {len(chip_gaps)} gap(s) de chips pós-resposta tier A",
                file=sys.stderr,
            )

            for gap in chip_gaps[:12]:
                print(f"  - {gap}", file=sys.stderr)
        else:
            print("\nOK: tierAPipelineCases — chips pós-resposta declarados")

    if args.check_commentary_profiles:
        commentary_validation = ChatPresentationCoverageService.validate_commentary_profiles_for_ci(
            openapi_baseline_path=args.baseline,
        )
        commentary_gaps = commentary_validation.get("commentaryProfileGaps") or []

        if commentary_gaps:
            exit_code = 1
            print(
                f"\nERRO: {len(commentary_gaps)} gap(s) de commentaryProfileKey tier A",
                file=sys.stderr,
            )

            for gap in commentary_gaps[:12]:
                print(
                    f"  - [{gap['kind']}] {gap['operation_id']} "
                    f"{gap['path']} ({gap['detail']})",
                    file=sys.stderr,
                )
        else:
            print("\nOK: tier A com commentaryProfileKey declarativo ou resolvido")

    if args.check_playbook12:
        from tests.fixtures.presentation_playbook12_regression_gate import (  # noqa: E402
            validate_playbook12_ci_gates,
        )

        playbook12 = validate_playbook12_ci_gates(
            openapi_baseline_path=args.baseline,
            stored_baseline_path=args.stored_baseline,
        )
        blocking = playbook12.get("blockingIssues") or []
        warnings = playbook12.get("visualBuilderWarnings") or []

        if blocking:
            exit_code = 1
            print(
                f"\nERRO: Playbook 12 — {len(blocking)} gate(s) bloqueante(s)",
                file=sys.stderr,
            )

            for issue in blocking[:20]:
                print(f"  - {issue}", file=sys.stderr)
        else:
            print(
                "\nOK: Playbook 12 — entity contract + gates CI "
                f"({playbook12.get('entityContractCaseCount')} entidades, "
                f"{playbook12.get('tierAPipelineCaseCount')} fixtures tier A)"
            )

        if warnings:
            print(f"\nAVISO: {len(warnings)} perfil(is) com viewOrder sem visualBuilders")

            for warning in warnings[:12]:
                print(
                    f"  - {warning['profile_key']} view={warning['view']} "
                    f"({warning['detail']})"
                )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
