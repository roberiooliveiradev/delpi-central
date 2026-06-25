#!/usr/bin/env python3
"""Auditoria de clean architecture — minha-delpi-ai-api (baseline Fase 0)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP = ROOT / "app"
BASELINE_PATH = ROOT / "docs/architecture/clean-architecture-baseline.json"

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

DOMAIN_APPLICATION_PATTERNS = (
    re.compile(r"from\s+app\.application\."),
    re.compile(r"import\s+app\.application\."),
)


def count_lines(path: Path) -> int:
    if not path.is_file():
        return 0

    return sum(1 for _ in path.open(encoding="utf-8"))


def domain_application_imports() -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    domain_dir = APP / "domain"

    for path in sorted(domain_dir.rglob("*.py")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(pattern.search(line) for pattern in DOMAIN_APPLICATION_PATTERNS):
                violations.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "line": line_no,
                        "snippet": line.strip(),
                    }
                )

    return violations


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


def load_architecture_baseline() -> dict:
    if not BASELINE_PATH.is_file():
        return {}

    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def resolve_targets(baseline: dict) -> dict[str, int]:
    defaults = {
        "godFileLinesMax": 1200,
        "domainInfrastructureImportsMax": 0,
        "domainApplicationImportsMax": 0,
        "interfacesPostgresFilesMax": 0,
        "sendStreamUseCaseLinesMax": 500,
    }
    stored = baseline.get("targets", {})
    resolved = {**defaults, **stored}

    # Ratchet: teto de domain→application vem do baseline gravado (só reduz manualmente).
    app_baseline = baseline.get("domainApplicationImports", {})
    if "count" in app_baseline:
        resolved["domainApplicationImportsMax"] = int(app_baseline["count"])

    return resolved


def build_report(baseline: dict | None = None) -> dict:
    baseline = baseline if baseline is not None else load_architecture_baseline()
    god_lines = {name: count_lines(path) for name, path in GOD_FILES.items()}
    infra_violations = domain_infra_imports()
    application_violations = domain_application_imports()

    return {
        "godFileLines": god_lines,
        "domainInfrastructureImports": {
            "count": len(infra_violations),
            "samples": infra_violations[:25],
        },
        "domainApplicationImports": {
            "count": len(application_violations),
            "samples": application_violations[:25],
        },
        "interfacesPostgresFiles": interfaces_postgres_usage(),
        "targets": resolve_targets(baseline),
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

    baseline = load_architecture_baseline()
    report = build_report(baseline)

    if args.write_baseline:
        out = BASELINE_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            **report,
            "notes": (
                "jun/2026: domain→infra zerado; domain→application em ratchet (W3). "
                "Reduzir count no baseline ao eliminar imports."
            ),
        }
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Baseline gravado em {out}")

    if args.json or not args.write_baseline:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    targets = report["targets"]
    failed = False

    if report["domainInfrastructureImports"]["count"] > targets["domainInfrastructureImportsMax"]:
        failed = True

    if report["domainApplicationImports"]["count"] > targets["domainApplicationImportsMax"]:
        failed = True

    if report["interfacesPostgresFiles"]:
        failed = True

    try:
        from app.infrastructure.content.hardcoded_pt_string_scanner import (
            diff_against_baseline,
            load_baseline,
            scan_protected_paths,
        )

        baseline_path = ROOT / "tests/fixtures/hardcoded_pt_strings_baseline.json"
        findings = scan_protected_paths()
        new_items, _removed = diff_against_baseline(
            findings,
            load_baseline(baseline_path),
        )

        if new_items:
            failed = True
    except Exception:
        failed = True

    for name, lines in report["godFileLines"].items():
        if name.endswith("_use_case.py") and lines > targets["sendStreamUseCaseLinesMax"]:
            failed = True

        if lines > targets["godFileLinesMax"]:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
