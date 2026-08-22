from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


@lru_cache(maxsize=None)
def load_bundle(name: str) -> dict[str, Any]:
    """Carrega um catálogo JSON de conteúdo/configuração do Portal Financeiro."""
    path = _CONTENT_DIR / f"{name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def get_path(bundle: str, *keys: str, default: Any = None) -> Any:
    node: Any = load_bundle(bundle)
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def text(bundle: str, *keys: str, default: str = "") -> str:
    value = get_path(bundle, *keys, default=default)
    return str(value) if value is not None else default


def number(bundle: str, *keys: str, default: float = 0.0) -> float:
    value = get_path(bundle, *keys, default=default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def integer(bundle: str, *keys: str, default: int = 0) -> int:
    value = get_path(bundle, *keys, default=default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def string_set(bundle: str, *keys: str) -> frozenset[str]:
    value = get_path(bundle, *keys, default=[])
    if not isinstance(value, list):
        return frozenset()
    return frozenset(str(item).strip() for item in value if str(item).strip())


def string_list(bundle: str, *keys: str) -> list[str]:
    value = get_path(bundle, *keys, default=[])
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
