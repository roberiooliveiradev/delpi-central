#!/usr/bin/env python3
"""Smoke — correção textual pura sem tools/API."""

from __future__ import annotations

import sys

from app.application.services.chat_text_correction_follow_up_service import (
    ChatTextCorrectionFollowUpService,
)
from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


def main() -> int:
    failed = 0
    msg = "corrija: o estoque esta baixo"

    if not ChatTextTaskIntentService.is_pure_text_task(msg):
        print("FAIL is_pure_text_task", file=sys.stderr)
        failed += 1
    else:
        print("OK is_pure_text_task")

    if not ChatTextCorrectionIntentService.is_text_correction(msg):
        print("FAIL is_text_correction", file=sys.stderr)
        failed += 1
    else:
        print("OK is_text_correction")

    subtype = ChatTextCorrectionIntentService.classify_subtype(msg)

    if subtype != "text_correct_basic":
        print(f"FAIL subtype ({subtype})", file=sys.stderr)
        failed += 1
    else:
        print("OK subtype text_correct_basic")

    source = ChatTextCorrectionIntentService.extract_source_text(msg)

    if "estoque" not in (source or "").lower():
        print(f"FAIL extract_source_text ({source!r})", file=sys.stderr)
        failed += 1
    else:
        print("OK extract_source_text")

    metadata: dict = {}
    ChatTextCorrectionFollowUpService.attach_to_assistant_metadata(
        metadata,
        message=msg,
        answer="Segue a versão corrigida:\n\nO estoque está baixo.",
    )

    if metadata.get("textTask", {}).get("type") != "correction":
        print(f"FAIL textTask metadata ({metadata})", file=sys.stderr)
        failed += 1
    else:
        print("OK textTask metadata")

    chips = metadata.get("textCorrectionFollowUpSuggestions") or []

    if len(chips) < 3:
        print(f"FAIL follow-up chips ({len(chips)})", file=sys.stderr)
        failed += 1
    else:
        print(f"OK follow-up chips ({len(chips)})")

    mixed = "consulte o estoque do produto 10080001 e corrija o texto do resultado"

    if ChatTextTaskIntentService.is_pure_text_task(mixed):
        print("FAIL mixed should not be pure text_task", file=sys.stderr)
        failed += 1
    else:
        print("OK mixed not pure text_task")

    if failed:
        return 1

    print("Smoke text correction: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
