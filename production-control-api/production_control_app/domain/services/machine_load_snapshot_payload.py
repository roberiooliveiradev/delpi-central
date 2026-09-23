"""Leitura do payload do snapshot da carga máquina.

A linha do snapshot guarda a fila em ``payload_json``, que chega como texto ou
como dict dependendo do driver. Quem precisa da fila congelada (carga máquina,
alimentador de linha, cockpit público) usa este módulo — um segundo decodificador
divergiria justamente no caso chato: payload vazio, texto inválido ou lista.
"""

from __future__ import annotations

import json
from typing import Any

OPERATIONS_KEY = "operations"
WORK_CENTERS_KEY = "work_centers"


def decode_snapshot_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Payload do snapshot como dict novo (seguro para mutar antes de regravar)."""
    raw_payload = row.get("payload_json") if isinstance(row, dict) else None
    if isinstance(raw_payload, str):
        payload = json.loads(raw_payload)
    elif isinstance(raw_payload, dict):
        payload = raw_payload
    else:
        payload = {}
    return dict(payload)


def dict_items(payload: dict[str, Any] | list[Any] | None) -> list[dict[str, Any]]:
    """Itens dict de uma lista crua ou do campo ``items`` de um envelope."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def payload_operations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Fila completa gravada no snapshot, em qualquer das formas aceitas."""
    return dict_items(payload.get(OPERATIONS_KEY))


def payload_work_centers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return dict_items(payload.get(WORK_CENTERS_KEY))
