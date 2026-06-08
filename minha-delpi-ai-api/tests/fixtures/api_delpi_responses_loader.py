"""Carrega fixtures JSON do envelope api-delpi (Fase 0 baseline)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FIXTURES_DIR = Path(__file__).resolve().parent / "api_delpi_responses"


def load_api_delpi_fixture(name: str) -> dict[str, Any]:
    path = _FIXTURES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Fixture api-delpi não encontrada: {path}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Fixture inválida (esperado objeto JSON): {name}")
    return payload


def load_api_delpi_data(name: str) -> Any:
    envelope = load_api_delpi_fixture(name)
    return envelope.get("data")
