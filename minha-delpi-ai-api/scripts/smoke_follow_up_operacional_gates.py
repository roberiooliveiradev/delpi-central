#!/usr/bin/env python3
"""Gates offline do playbook follow-up operacional (P0–P2) — sem stack HTTP.

Uso:
  cd minha-delpi-ai-api
  .venv/bin/python scripts/smoke_follow_up_operacional_gates.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==")
    result = subprocess.run(command, cwd=_ROOT)

    if result.returncode != 0:
        raise SystemExit(result.returncode)


_ROOT = Path(__file__).resolve().parents[1]
_PY = str(_ROOT / ".venv" / "bin" / "python")


def main() -> None:
    pytest = [_PY, "-m", "pytest", "-q"]

    _run(
        "Follow-up intent",
        [*pytest, "tests/unit/domain/services/test_chat_follow_up_intent_service.py"],
    )
    _run(
        "Capabilities + treinamento",
        [*pytest, "tests/unit/application/services/test_chat_capabilities_service.py"],
    )
    _run(
        "Follow-up routing (P1.1)",
        [*pytest, "tests/unit/domain/services/test_chat_operational_follow_up_routing_service.py"],
    )
    _run(
        "Date inheritance (P1.0)",
        [
            *pytest,
            "tests/unit/domain/services/test_chat_operational_date_parameter_service.py",
            "-k",
            "inherit or playbook or follow",
        ],
    )
    _run(
        "Project sources slot (P2)",
        [
            *pytest,
            "tests/unit/domain/services/test_chat_project_sources_slot_rag.py",
            "tests/unit/domain/services/test_chat_project_source_slot_resolver_service.py",
            "tests/unit/domain/services/test_chat_project_sources_intent_service.py",
        ],
    )
    _run(
        "Action selection regression",
        [
            *pytest,
            "tests/unit/domain/services/test_chat_intelligence_regression.py::test_action_selection_regression",
        ],
    )
    _run(
        "Operational route registry",
        [_PY, "scripts/generate_operational_route_registry.py", "--check"],
    )

    print("\nOK — gates offline do playbook follow-up operacional.")


if __name__ == "__main__":
    main()
