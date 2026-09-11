#!/usr/bin/env python3
"""Gate J-R2 — bloqueia corpus com requiredDimensions abaixo da matriz canônica.

Uso:
  PYTHONPATH=. python3 scripts/assert_corpus_required_dimensions.py
  PYTHONPATH=. python3 scripts/assert_corpus_required_dimensions.py --corpus path.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.domain.services.chat_required_dimensions_matrix_service import (  # noqa: E402
    ChatRequiredDimensionsMatrixService,
)

_DEFAULT = _ROOT / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v2.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=_DEFAULT)
    args = parser.parse_args()
    path = args.corpus
    if not path.is_file():
        print(f"FAIL corpus ausente: {path}")
        return 2
    corpus = json.loads(path.read_text(encoding="utf-8"))
    report = ChatRequiredDimensionsMatrixService.validate_corpus(corpus)
    payload = report.as_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not report.ok:
        print(
            f"REQUIRED_DIMENSIONS_MATRIX=FAIL failing={len(report.failing)} "
            f"authority={report.source_doc}"
        )
        return 1
    print("REQUIRED_DIMENSIONS_MATRIX=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
