#!/usr/bin/env python3
"""Compara dois diretórios de golden já normalizados.

Uso:
  python compare_golden.py golden golden-bff

Não chama a rede. Rode a suíte duas vezes com LNF_WRITE_GOLDEN=1 e
LNF_BASE_URL de cada alvo, copiando golden/ entre as execuções.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load(root: Path) -> dict[str, object]:
    found: dict[str, object] = {}
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*.json")):
        found[str(path.relative_to(root))] = json.loads(path.read_text(encoding="utf-8"))
    return found


def main() -> int:
    if len(sys.argv) != 3:
        print("uso: python compare_golden.py <golden-a> <golden-b>", file=sys.stderr)
        return 2
    left = _load(Path(sys.argv[1]))
    right = _load(Path(sys.argv[2]))
    keys = sorted(set(left) | set(right))
    diffs = 0
    for key in keys:
        if key not in left or key not in right:
            print(f"ONLY {key}")
            diffs += 1
            continue
        if left[key] != right[key]:
            print(f"DIFF {key}")
            diffs += 1
    print(f"files={len(keys)} diffs={diffs}")
    return 1 if diffs else 0


if __name__ == "__main__":
    raise SystemExit(main())
