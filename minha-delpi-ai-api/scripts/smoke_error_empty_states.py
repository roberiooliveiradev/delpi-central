#!/usr/bin/env python3
"""Smoke local — Playbook 06 erros e resultados vazios."""

from __future__ import annotations

import sys

from app.application.services.chat_error_handling_service import ChatErrorHandlingService
from tests.fixtures.error_empty_states_cases import ERROR_EMPTY_STATES_CASES


def main() -> int:
    failed = 0

    for case in ERROR_EMPTY_STATES_CASES:
        metadata: dict = {}

        ChatErrorHandlingService.attach_to_assistant_metadata(
            metadata,
            message=case["message"],
            answer=case["answer"],
            tool_calls=case.get("tool_calls"),
            attachments=case.get("attachments"),
        )

        handling = metadata.get("errorHandling")

        if not handling or handling.get("type") != case["expect_type"]:
            print(
                f"FAIL {case['id']} expected {case['expect_type']} got {handling}",
                file=sys.stderr,
            )
            failed += 1
            continue

        if not metadata.get("errorRecoveryFollowUpSuggestions"):
            print(f"FAIL {case['id']} missing recovery chips", file=sys.stderr)
            failed += 1
            continue

        print(f"OK {case['id']} {case['expect_type']}")

    if failed:
        return 1

    print("Smoke error empty states: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
