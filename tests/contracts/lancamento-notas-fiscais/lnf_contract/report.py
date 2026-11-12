"""Registro de resultado por caso. Não grava token nem corpo bruto."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
GOLDEN = ROOT / "golden"

_ROWS: list[dict] = []


def record(
    *,
    route: str,
    case: str,
    profile: str,
    expected: str,
    obtained: str,
    outcome: str,
    note: str = "",
) -> None:
    _ROWS.append(
        {
            "route": route,
            "case": case,
            "profile": profile,
            "expected": expected,
            "obtained": obtained,
            "outcome": outcome,
            "note": note,
        }
    )


def rows() -> list[dict]:
    return list(_ROWS)


def flush() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "outcomes.json").write_text(
        json.dumps(_ROWS, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_golden(operation_id: str, case: str, payload: dict) -> None:
    import os

    if os.getenv("LNF_WRITE_GOLDEN") != "1":
        return
    folder = GOLDEN / operation_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{case}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
