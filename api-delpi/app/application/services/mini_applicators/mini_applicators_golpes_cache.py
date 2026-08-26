from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypeVar

from app.composition.query_cache_composer import build_query_cache

T = TypeVar("T")

_GOLPES_BATCH_CACHE_NAMESPACE = "mini-applicators-golpes-batch"
_GOLPES_BATCH_DATA_FINAL_BUCKET_SECONDS = 60


def _bucket_data_final(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    bucket = int(parsed.timestamp()) // _GOLPES_BATCH_DATA_FINAL_BUCKET_SECONDS
    return str(bucket)


def golpes_batch_cache_key(*, filial: str, items: list[dict[str, Any]]) -> str:
    normalized = [
        {
            "codigo_ferramenta": str(item.get("codigo_ferramenta") or "").strip(),
            "data_inicial": str(item.get("data_inicial") or "").strip(),
            "data_final": _bucket_data_final(str(item.get("data_final") or "").strip()),
        }
        for item in items
    ]
    payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    branch = filial.strip()
    return f"{_GOLPES_BATCH_CACHE_NAMESPACE}:{branch}:{digest}"


def get_or_set_cached_golpes_batch(
    *,
    filial: str,
    items: list[dict[str, Any]],
    factory: Callable[[], T],
) -> T:
    cache = build_query_cache()
    key = golpes_batch_cache_key(filial=filial, items=items)
    return cache.get_or_set(key, factory)
