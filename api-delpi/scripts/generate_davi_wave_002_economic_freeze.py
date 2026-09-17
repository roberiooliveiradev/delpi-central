#!/usr/bin/env python3
"""Generate DAVI Wave 2 economic freeze evidence (no runtime mutation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from davi_wave_002_economic_freeze_lib import (  # noqa: E402
    build_documents,
    git_sha,
    write_artifacts,
)


def main() -> int:
    source_head = git_sha("HEAD")
    try:
        origin_main = git_sha("origin/main")
    except Exception:
        origin_main = source_head
    inventory, freeze = build_documents(source_head=source_head, origin_main=origin_main)
    paths = write_artifacts(inventory, freeze)
    summary = {
        "taskId": inventory["metadata"]["taskId"],
        "source_head": source_head,
        "origin_main": origin_main,
        "current_eligible": freeze["current_eligible"],
        "frozen_count": freeze["new_capabilities"],
        "expected_eligible_after_implementation": freeze[
            "expected_eligible_after_implementation"
        ],
        "capability_ids": freeze["capability_ids"],
        "deferred": freeze["deferred_capability_ids"],
        "artifacts": {k: str(v) for k, v in paths.items()},
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
