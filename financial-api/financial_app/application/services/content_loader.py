from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


@lru_cache(maxsize=8)
def load_content(name: str) -> dict[str, Any]:
    path = _CONTENT_DIR / name
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}
