#!/usr/bin/env python3
"""Generate DAVI capability expansion evidence (no runtime mutation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from davi_capability_expansion_lib import (  # noqa: E402
    build_inventory_document,
    git_sha,
    write_artifacts,
)


def main() -> int:
    source_head = git_sha("HEAD")
    try:
        origin_main = git_sha("origin/main")
    except Exception:
        origin_main = source_head
    doc = build_inventory_document(source_head=source_head, origin_main=origin_main)
    paths = write_artifacts(doc)
    summary = {
        "taskId": doc["metadata"]["taskId"],
        "source_head": source_head,
        "origin_main": origin_main,
        "TOTAL_OPERATIONS": doc["technical_operation_counts"]["TOTAL_OPERATIONS"],
        "TOTAL_GET": doc["technical_operation_counts"]["TOTAL_GET"],
        "DAVI_ELIGIBLE_READ": doc["technical_operation_counts"]["DAVI_ELIGIBLE_READ"],
        "MCP_TOOLS": doc["mcp_tools"],
        "SEMANTIC_CAPABILITIES": doc["semantic_capability_counts"]["TOTAL_SEMANTIC_CAPABILITIES"],
        "WAVE_1_FROZEN": doc["wave_1_freeze"]["count"],
        "EXPECTED_ELIGIBLE_AFTER_IMPLEMENTATION": doc["wave_1_freeze"][
            "expected_eligible_after_implementation"
        ],
        "artifacts": {k: str(v) for k, v in paths.items()},
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
