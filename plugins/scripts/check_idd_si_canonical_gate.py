#!/usr/bin/env python3
"""Gate: Nota IDD dos cards deve vir do SI (iddScoreLabel), sem dual-path local.

Uso (raiz do monorepo):
  python3 plugins/scripts/check_idd_si_canonical_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PLUGINS = [
    "dashboard-quality",
    "dashboard-commercial",
    "commercial",
    "dashboard-production",
    "dashboard-supplies",
    "dashboard-financial",
    "dashboard-engineering",
    "dashboard-hr",
]

FORBIDDEN_CALLS = (
    "resolveConsolidatedIddScoreLabel(",
    "resolveIddScoreLabel(",
    "calculateIndicatorIddScore(",
)

SKIP_NAME_PARTS = (
    "goalDisplay.ts",
    ".test.ts",
    ".test.tsx",
    ".test.mjs",
)


def main() -> int:
    violations: list[str] = []
    for plugin in PLUGINS:
        root = ROOT / "plugins" / plugin / "src"
        if not root.is_dir():
            violations.append(f"missing src: {plugin}")
            continue
        for path in root.rglob("*.tsx"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(
                r"buildKpiGoalPresentationWithBranchIdd\s*\(", text
            ):
                snippet = text[match.start() : match.start() + 900]
                if "iddScoreLabel" not in snippet:
                    line = text[: match.start()].count("\n") + 1
                    rel = path.relative_to(ROOT)
                    violations.append(
                        f"{rel}:{line} buildKpiGoalPresentationWithBranchIdd "
                        "sem iddScoreLabel (SI)"
                    )
        for path in list(root.rglob("*.ts")) + list(root.rglob("*.tsx")):
            name = path.name
            if any(part in name for part in SKIP_NAME_PARTS):
                continue
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_CALLS:
                if forbidden not in text:
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if forbidden in line and not line.strip().startswith("//"):
                        rel = path.relative_to(ROOT)
                        violations.append(
                            f"{rel}:{i} {forbidden.rstrip('(')} "
                            "fora do kit (dual-path)"
                        )
    if violations:
        print("FAIL — dual-path Nota IDD detectado:")
        for item in violations:
            print(f"  - {item}")
        return 1
    print("OK — inventário de plugins com Nota IDD canônica via SI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
