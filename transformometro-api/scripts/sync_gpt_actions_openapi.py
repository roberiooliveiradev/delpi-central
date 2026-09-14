#!/usr/bin/env python3
"""Gera docs/gpt-actions/openapi-gpt-actions.json a partir do builder canônico.

Uso:
  PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
"""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent
SHARED_ROOT = REPO_ROOT / "shared"

for _path in (API_ROOT, SHARED_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from tm_app.application.gpt_actions.openapi_builder import (  # noqa: E402
    count_operations,
    write_gpt_actions_openapi,
)


def main() -> int:
    out = API_ROOT / "docs" / "gpt-actions" / "openapi-gpt-actions.json"
    doc = write_gpt_actions_openapi(out)
    total = count_operations(doc)
    print(f"Wrote {out} with {total} operations")
    if total > 30:
        print("ERROR: Custom GPT limit is ~30 operations", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
