#!/usr/bin/env python3
"""Alinha globalReleasePass de manifests ao invariante do runner (J-R3 / A11-03).

Não inventa PASS. Apenas corrige contradições true↔reason/liveDeferred/offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.domain.services.chat_evidence_reproducibility_service import (  # noqa: E402
    ChatEvidenceReproducibilityService,
)

_DEFAULTS = [
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/e11-s9-final-candidate-offline-v1/manifest.json",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=_DEFAULTS)
    parser.add_argument("--check", action="store_true", help="somente validar")
    args = parser.parse_args()
    exit_code = 0
    for path in args.paths:
        if not path.is_file():
            print(f"MISSING {path}")
            exit_code = 2
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        before = ChatEvidenceReproducibilityService.validate_manifest(data, path=str(path))
        if args.check:
            status = "PASS" if before.ok else "FAIL"
            print(f"{status} {path} errors={list(before.errors)}")
            if not before.ok:
                exit_code = 1
            continue
        if before.ok:
            print(f"OK_UNCHANGED {path}")
            continue
        aligned = ChatEvidenceReproducibilityService.align_global_release_pass(data)
        path.write_text(json.dumps(aligned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        after = ChatEvidenceReproducibilityService.validate_manifest(aligned, path=str(path))
        print(
            f"ALIGNED {path} previous={data.get('globalReleasePass')} "
            f"now={aligned.get('globalReleasePass')} ok={after.ok}"
        )
        if not after.ok:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
