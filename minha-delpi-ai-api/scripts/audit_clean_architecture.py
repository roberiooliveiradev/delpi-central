#!/usr/bin/env python3
"""Auditoria de clean architecture — minha-delpi-ai-api (baseline Fase 0)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

GOD_FILES = {
    "external_action_result_presenter.py": APP / "domain/services/external_actions/external_action_result_presenter.py",
    "external_action_selection_service.py": APP / "application/services/external_actions/external_action_selection_service.py",
    "chat_routes.py": APP / "interfaces/http/routes/chat_routes.py",
    "chat_tool_context_service.py": APP / "application/services/chat_tool_context_service.py",
    "send_chat_message_use_case.py": APP / "application/use_cases/send_chat_message_use_case.py",
    "stream_chat_message_use_case.py": APP / "application/use_cases/stream_chat_message_use_case.py",
    "chat_turn_preparation_service.py": APP / "application/services/chat_turn/chat_turn_preparation_service.py",
}

DOMAIN_INFRA_PATTERNS = (
    re.compile(r"from\s+app\.infrastructure\."),
    re.compile(r"import\s+app\.infrastructure\."),
)


def count_lines(path: Path) -> int:
    if not path.is_file():
        return 0

    return sum(1 for _ in path.open(encoding="utf-8"))


def domain_infra_imports() -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    domain_dir = APP / "domain"

    for path in sorted(domain_dir.rglob("*.py")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(pattern.search(line) for pattern in DOMAIN_INFRA_PATTERNS):
                violations.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "line": line_no,
                        "snippet": line.strip(),
                    }
                )

    return violations


def interfaces_postgres_usage() -> list[str]:
    routes_dir = APP / "interfaces"
    matches: list[str] = []

    for path in sorted(routes_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))

        if "Postgres" in text and "Repository" in text:
            matches.append(rel)
            continue

        if "make_postgres_" in text:
            matches.append(rel)

    return matches


def build_report() -> dict:
    god_lines = {name: count_lines(path) for name, path in GOD_FILES.items()}
    violations = domain_infra_imports()

    return {
        "godFileLines": god_lines,
        "domainInfrastructureImports": {
            "count": len(violations),
            "samples": violations[:25],
        },
        "interfacesPostgresFiles": interfaces_postgres_usage(),
        "targets": {
            "godFileLinesMax": 1200,
            "domainInfrastructureImportsMax": 0,
            "interfacesPostgresFilesMax": 0,
            "sendStreamUseCaseLinesMax": 500,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Grava baseline em docs/architecture/clean-architecture-baseline.json",
    )
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON")
    args = parser.parse_args()

    report = build_report()

    if args.write_baseline:
        out = ROOT / "docs/architecture/clean-architecture-baseline.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Baseline gravado em {out}")

    if args.json or not args.write_baseline:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    targets = report["targets"]
    failed = False

    if report["domainInfrastructureImports"]["count"] > targets["domainInfrastructureImportsMax"]:
        failed = True

    if report["interfacesPostgresFiles"]:
        failed = True

    for name, lines in report["godFileLines"].items():
        if name.endswith("_use_case.py") and lines > targets["sendStreamUseCaseLinesMax"]:
            failed = True

        if lines > targets["godFileLinesMax"]:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
