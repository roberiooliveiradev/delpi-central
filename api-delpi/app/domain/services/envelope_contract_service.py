"""Golden files de contrato de envelope para rotas críticas (Fase 4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.interface.http.route_contract_registry import resolve_contract

_GOLDEN_PATH = Path(__file__).resolve().parents[2] / "content" / "envelope_contract_golden.json"


def load_envelope_contract_golden() -> dict[str, Any]:
    raw = _GOLDEN_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def validate_envelope_contract_golden() -> list[str]:
    payload = load_envelope_contract_golden()
    errors: list[str] = []

    for route in payload.get("routes") or []:
        operation_id = route.get("operationId")
        if not operation_id:
            errors.append(f"Rota sem operationId: {route}")
            continue

        entity, shape = resolve_contract(operation_id)
        expected_entity = route.get("entity")
        expected_shape = route.get("shape")

        if expected_entity and entity != expected_entity:
            errors.append(
                f"{operation_id}: entity esperado {expected_entity}, registry {entity}"
            )
        if expected_shape and shape != expected_shape:
            errors.append(
                f"{operation_id}: shape esperado {expected_shape}, registry {shape}"
            )

    return errors
