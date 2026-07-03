#!/usr/bin/env python3
"""Auditoria de acoplamento direto a gateways Ollama/vLLM fora da infra."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

SCAN_DIRS = (
    APP / "domain",
    APP / "application",
)

BLOCKED_IMPORT_PATTERNS = (
    re.compile(r"from\s+app\.infrastructure\.llm\.ollama_llm_gateway"),
    re.compile(r"from\s+app\.infrastructure\.llm\.vllm_llm_gateway"),
    re.compile(r"from\s+app\.infrastructure\.llm\.openai_compatible_llm_gateway"),
    re.compile(r"from\s+app\.infrastructure\.llm\.ollama_warmup_service"),
    re.compile(r"from\s+app\.infrastructure\.llm\.ollama_model_create_gateway"),
    re.compile(r"import\s+app\.infrastructure\.llm\.ollama_llm_gateway"),
    re.compile(r"import\s+app\.infrastructure\.llm\.vllm_llm_gateway"),
)

ALLOWLIST: dict[str, set[int]] = {
    "app/application/services/chat_fine_tuning_service.py": {310},
}


def scan_violations() -> list[dict[str, str | int]]:
    violations: list[dict[str, str | int]] = []

    for base_dir in SCAN_DIRS:
        for path in sorted(base_dir.rglob("*.py")):
            rel = str(path.relative_to(ROOT))
            allowed_lines = ALLOWLIST.get(rel, set())

            for line_no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if line_no in allowed_lines:
                    continue

                if any(pattern.search(line) for pattern in BLOCKED_IMPORT_PATTERNS):
                    violations.append(
                        {
                            "file": rel,
                            "line": line_no,
                            "snippet": line.strip(),
                        }
                    )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Retorna código de saída 1 se houver violações.",
    )
    args = parser.parse_args()

    violations = scan_violations()

    if violations:
        print("LLM provider coupling violations:")
        for item in violations:
            print(f"  {item['file']}:{item['line']} — {item['snippet']}")

        if args.check:
            return 1

        return 0

    print("OK — domain/application sem import direto de gateways LLM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
