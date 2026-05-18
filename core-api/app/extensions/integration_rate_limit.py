# app/extensions/integration_rate_limit.py

import os
import time
from functools import wraps

from flask import jsonify, request

_BUCKETS: dict[str, list[float]] = {}


def integration_rate_limit(
    max_requests: int | None = None,
    per_seconds: int | None = None,
    *,
    key_prefix: str = "int",
):
    """Rate limit for integration routes (keyed by client IP + path)."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            limit = max_requests
            window = per_seconds
            if limit is None:
                limit = int(os.getenv("NOTIFICATIONS_INTEGRATION_RATE_LIMIT", "60"))
            if window is None:
                window = int(os.getenv("NOTIFICATIONS_INTEGRATION_RATE_WINDOW_SECONDS", "60"))

            ip = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
            if not ip:
                ip = request.remote_addr or "unknown"

            key = f"{key_prefix}:{ip}:{request.path}"
            now = time.time()
            window_start = now - window

            hits = [t for t in _BUCKETS.get(key, []) if t >= window_start]
            if len(hits) >= limit:
                return (
                    jsonify(
                        {
                            "error": "Too Many Requests",
                            "detail": f"Integration limit {limit}/{window}s exceeded",
                        }
                    ),
                    429,
                )

            hits.append(now)
            _BUCKETS[key] = hits
            return fn(*args, **kwargs)

        return wrapper

    return decorator
