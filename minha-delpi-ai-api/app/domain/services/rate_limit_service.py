import time
from collections import defaultdict, deque

from app.domain.exceptions.rate_limit_exceptions import RateLimitExceededError


class InMemoryRateLimitService:
    def __init__(self):
        self._buckets = defaultdict(deque)

    def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        message: str = "Rate limit exceeded",
    ) -> None:
        now = time.time()
        bucket = self._buckets[key]

        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()

        if len(bucket) >= limit:
            raise RateLimitExceededError(message)

        bucket.append(now)
