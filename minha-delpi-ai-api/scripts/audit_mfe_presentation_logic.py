#!/usr/bin/env python3
"""Gate Playbook 13 P6 — evita reintroduzir lógica de apresentação no MFE."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
MFE_COMPONENTS = REPO_ROOT / "plugins" / "minha-delpi-chat" / "src" / "ui" / "components"

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "shouldRenderDashboardSegment (usar payload pruned da API)",
        re.compile(r"\bshouldRenderDashboardSegment\s*\("),
    ),
    (
        "isExplicitDashboardSession (modo painel vem do payload/renderPlan)",
        re.compile(r"\bisExplicitDashboardSession\s*\("),
    ),
    (
        "inferência client-side de allowlist por presentationMode",
        re.compile(
            r"presentationMode\s*===\s*['\"]summary_then_evidence['\"]\s*\?\s*['\"]allowlist['\"]",
        ),
    ),
    (
        "shouldSkipTableSegment (dedup estrutural vem da API pruned)",
        re.compile(r"\bshouldSkipTableSegment\s*\("),
    ),
    (
        "isSummaryThenEvidenceMode (usar planUsesSummaryThenEvidence do stackPlan)",
        re.compile(r"\bisSummaryThenEvidenceMode\s*\("),
    ),
    (
        "stripRichUiRedundantProseFromMarkdown (texto final vem da API com renderHints)",
        re.compile(r"\bstripRichUiRedundantProseFromMarkdown\s*\("),
    ),
    (
        "buildPlanOrderedStackSegments (usar buildSegmentsFromRenderPlan)",
        re.compile(r"\bbuildPlanOrderedStackSegments\s*\("),
    ),
)

ALLOWLIST_FILES = frozenset(
    {
        "chatPresentation.ts",
        "presentationStackBlueprint.ts",
        "presentationStackBlueprint.live.test.ts",
        "presentationStackPlan.humanized.test.ts",
        "presentationStackSections.test.ts",
        "presentationStructureDedup.ts",
        "presentationStructureDedup.test.ts",
        "richStackPresentation.test.ts",
        "presentationRenderHints.test.ts",
    }
)


def scan_file(path: Path) -> list[str]:
    if path.name in ALLOWLIST_FILES:
        return []

    text = path.read_text(encoding="utf-8")
    findings: list[str] = []

    for label, pattern in FORBIDDEN_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line} — {label}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    if not MFE_COMPONENTS.is_dir():
        print(f"SKIP: diretório MFE não encontrado ({MFE_COMPONENTS}).")
        return 0

    findings: list[str] = []

    for path in sorted(MFE_COMPONENTS.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue

        findings.extend(scan_file(path))

    if findings:
        print("Gate P6 MFE — padrões proibidos encontrados:")
        for item in findings:
            print(f"  - {item}")
        return 1

    print("Gate P6 MFE — OK (nenhum padrão proibido fora da allowlist).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
