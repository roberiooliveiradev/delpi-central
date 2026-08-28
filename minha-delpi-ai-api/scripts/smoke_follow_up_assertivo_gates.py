#!/usr/bin/env python3
"""Gates offline do follow-up assertivo (revise / challenge / clarify / switch).

Uso:
  cd minha-delpi-ai-api
  .venv/bin/python scripts/smoke_follow_up_assertivo_gates.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PY = str(_ROOT / ".venv" / "bin" / "python")


def _run(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==")
    result = subprocess.run(command, cwd=_ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    pytest = [_PY, "-m", "pytest", "-q"]

    _run(
        "Follow-up content + typo branch",
        [
            *pytest,
            "tests/unit/domain/services/test_chat_follow_up_turn_content_service.py",
        ],
    )
    _run(
        "Interpretador + grounding stages",
        [
            *pytest,
            "tests/unit/domain/services/test_chat_follow_up_turn_interpretation_service.py",
            "tests/unit/domain/services/test_chat_turn_grounding_service.py",
        ],
    )
    _run(
        "Reexec lastAction + merge params",
        [
            *pytest,
            "tests/unit/domain/services/test_operational_api_parameter_builder_service.py",
            "tests/unit/domain/services/test_chat_grounded_capability_planning_service.py",
            "-k",
            "revise or merge or filail or branch",
        ],
    )
    _run(
        "Skip-tools / missing_date",
        [
            *pytest,
            "tests/unit/application/services/test_turn_preparation_tool_routing.py",
            "-k",
            "revise or challenge or missing_date_suppressed",
        ],
    )
    _run(
        "Challenge / clarify / ack",
        [
            *pytest,
            "tests/unit/application/services/test_chat_follow_up_grounded_answer_service.py",
        ],
    )
    _run(
        "Fixtures FF-FOLLOW-*",
        [
            *pytest,
            "tests/unit/domain/services/test_flow_family_matrix_gates.py",
            "-k",
            "FF-FOLLOW",
        ],
    )

    print("\nOK — gates offline do follow-up assertivo.")


if __name__ == "__main__":
    main()
