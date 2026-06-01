#!/usr/bin/env python3
"""Smoke local — Playbook 07 interatividade."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.application.services.chat_interactivity_suggestion_service import (
    ChatInteractivitySuggestionService,
)
from tests.fixtures.interactivity_cases import INTERACTIVITY_CASES


def main() -> int:
    failed = 0

    for case in INTERACTIVITY_CASES:
        metadata = dict(case.get("metadata") or {})

        ChatInteractivitySuggestionService.attach_to_assistant_metadata(
            metadata,
            workspace_context={"capabilities": {"canvas": True}, "userActivatedAgent": True},
            tool_calls=case.get("tool_calls"),
        )

        interactivity = metadata.get("interactivity")

        if not interactivity or not interactivity.get("suggestions"):
            print(f"FAIL {case['id']} missing interactivity", file=sys.stderr)
            failed += 1
            continue

        print(f"OK {case['id']} primary={len(interactivity['suggestions'])}")

    if failed:
        return 1

    print("Smoke interactivity: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
