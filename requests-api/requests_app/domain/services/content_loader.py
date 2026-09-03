from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content" / "pt-BR"


@lru_cache(maxsize=1)
def _engine_bundle() -> dict[str, Any]:
    path = _CONTENT_ROOT / "engine.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=32)
def load_workflow_definition(name: str) -> dict[str, Any]:
    path = _CONTENT_ROOT / "workflows" / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Workflow content not found: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def engine_reason(code: str, *, field: str | None = None) -> str:
    bundle = _engine_bundle()
    template = str(bundle.get("reasons", {}).get(code) or code)
    if field:
        labels = bundle.get("fieldLabels") or {}
        label = str(labels.get(field) or field)
        return template.format(field=label)
    return template
