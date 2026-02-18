# app/extensions/rate_limit.py

import time
from functools import wraps
from flask import request, jsonify, g

_BUCKETS: dict[str, list[float]] = {}  # key -> timestamps


def rate_limit(max_requests: int, per_seconds: int, key_prefix: str = "rl"):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            user_id = str(getattr(user, "id", "anon"))

            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
            key = f"{key_prefix}:{user_id}:{ip}:{request.path}"

            now = time.time()
            window_start = now - per_seconds

            hits = _BUCKETS.get(key, [])
            hits = [t for t in hits if t >= window_start]

            if len(hits) >= max_requests:
                return jsonify({
                    "error": "Too Many Requests",
                    "detail": f"Limit {max_requests}/{per_seconds}s"
                }), 429

            hits.append(now)
            _BUCKETS[key] = hits

            return fn(*args, **kwargs)
        return wrapper
    return decorator
