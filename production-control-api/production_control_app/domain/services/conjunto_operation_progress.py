"""Progresso fabril por pacote (C2_NUM+C2_ITEM) a partir das operações SH8."""

from __future__ import annotations

from typing import Any

from production_control_app.domain.services.production_order_key import (
    order_belongs_to_package,
    package_key_from_order,
)


def operation_key(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("production_order") or "").strip(),
        str(item.get("operation_code") or "").strip(),
    )


def _operation_status(item: dict[str, Any]) -> tuple[str, bool]:
    status = str(item.get("production_status") or "not_started").strip() or "not_started"
    running = bool(item.get("is_in_production")) or status == "in_progress"
    return status, running


def compute_conjunto_progress(operations: list[dict[str, Any]]) -> dict[str, int | float]:
    """Percentual ponderado: operação apontada = 1; em produção = 0,5."""
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for item in operations:
        key = operation_key(item)
        if not key[0] or not key[1]:
            continue
        deduped[key] = item

    total = len(deduped)
    if total == 0:
        return {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "percent": 0,
        }

    completed = 0
    in_progress = 0
    weighted = 0.0
    for item in deduped.values():
        status, running = _operation_status(item)
        if running:
            in_progress += 1
            weighted += 0.5
        elif status == "started":
            completed += 1
            weighted += 1.0

    percent = int(round((weighted / total) * 100))
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "percent": max(0, min(100, percent)),
    }


def filter_operations_for_packages(
    operations: list[dict[str, Any]],
    package_keys: set[str],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in package_keys}
    for item in operations:
        order = str(item.get("production_order") or "").strip()
        for key in package_keys:
            if order_belongs_to_package(order, key):
                grouped[key].append(item)
                break
    return grouped


# Alias legado — testes / callers antigos.
filter_operations_for_conjuntos = filter_operations_for_packages


def package_keys_from_orders(production_orders: list[str]) -> dict[str, str]:
    """Mapa OP mãe → pacote C2_NUM+C2_ITEM (8 dígitos)."""
    mapping: dict[str, str] = {}
    for raw in production_orders:
        order = str(raw or "").strip()
        key = package_key_from_order(order)
        if order and key:
            mapping[order] = key
    return mapping


def conjunto_keys_from_orders(production_orders: list[str]) -> dict[str, str]:
    """Alias de ``package_keys_from_orders`` (progresso do mapa de entrega)."""
    return package_keys_from_orders(production_orders)
