from functools import wraps

from flask import g, request

from app.composition.rate_limit_composer import get_rate_limit_service
from app.infrastructure.config.settings import Settings


def rate_limit(bucket: str, limit: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not Settings.RATE_LIMIT_ENABLED:
                return fn(*args, **kwargs)

            user_id = getattr(getattr(g, "current_user", None), "sub", None)
            subject = user_id or request.remote_addr or "anonymous"

            key = f"{bucket}:{subject}"

            get_rate_limit_service().check(
                key=key,
                limit=limit,
                window_seconds=Settings.RATE_LIMIT_WINDOW_SECONDS,
                message=f"Rate limit exceeded for {bucket}",
            )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
