#!/usr/bin/env python3
"""Valida typing_correction_rules.json — regras compiláveis (P14-0)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app" / "content" / "pt-BR" / "assistant" / "typing_correction_rules.json"


def main() -> int:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    rules = payload.get("rules")

    if not isinstance(rules, list) or not rules:
        print("typing_correction_rules.json: rules must be a non-empty list", file=sys.stderr)
        return 1

    compiled = 0

    for index, raw in enumerate(rules):
        if not isinstance(raw, dict):
            print(f"rule[{index}] must be an object", file=sys.stderr)
            return 1

        pattern = str(raw.get("pattern") or "").strip()
        replacement = str(raw.get("replacement") or "").strip()

        if not pattern or not replacement:
            print(f"rule[{index}] missing pattern or replacement", file=sys.stderr)
            return 1

        try:
            re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            print(f"rule[{index}] invalid regex: {exc}", file=sys.stderr)
            return 1

        compiled += 1

    print(f"Validated {compiled} rules in {CATALOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
