"""Gate — chaves de coluna da API devem existir em column_labels.fields antes do LLM."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "api_delpi_responses"
COLUMN_LABELS_PATH = ROOT / "app" / "content" / "pt-BR" / "assistant" / "column_labels.json"

_CONTAINER_KEYS = frozenset(
    {
        "items",
        "product",
        "materials",
        "summary",
        "simulation",
        "structure",
        "production",
        "shipping",
        "indicators",
        "last_purchase",
        "root",
        "guide",
        "inspection",
        "customers",
        "suppliers",
        "prices",
        "raw_material_stock",
        "price_history",
        "budget_history",
        "page",
        "total_pages",
        "success",
        "message",
        "data",
        "warnings",
        "stock",
        "table",
        "components",
        "by_cfop",
        "by_tm",
        "top_documents",
        "top_products",
    }
)


def _load_field_keys() -> set[str]:
    bundle = json.loads(COLUMN_LABELS_PATH.read_text(encoding="utf-8"))
    keys = set((bundle.get("fields") or {}).keys())

    for profile in (bundle.get("tableProfiles") or {}).values():
        for pair in profile.get("preferredColumns") or []:
            if isinstance(pair, list) and pair:
                keys.add(str(pair[0]))

    return keys


def _collect_payload_keys(obj: object) -> set[str]:
    keys: set[str] = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).startswith("_"):
                continue

            keys.add(str(key))
            keys |= _collect_payload_keys(value)
    elif isinstance(obj, list):
        for item in obj[:40]:
            keys |= _collect_payload_keys(item)

    return keys


def find_missing_column_vocab_keys() -> list[str]:
    known = _load_field_keys()
    observed: set[str] = set()

    if FIXTURES_DIR.is_dir():
        for path in sorted(FIXTURES_DIR.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8")).get("data")
            observed |= _collect_payload_keys(payload)

    missing = sorted(
        key
        for key in observed
        if key not in _CONTAINER_KEYS and key not in known
    )

    return missing


def validate_column_vocab_for_ci() -> dict[str, object]:
    missing = find_missing_column_vocab_keys()

    return {
        "ok": not missing,
        "missingKeys": missing,
    }
