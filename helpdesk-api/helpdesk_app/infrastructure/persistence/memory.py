import hashlib
from datetime import datetime, timezone

from helpdesk_app.domain.models import OAuthSession, PendingAuthorization, StoredResponse


def _hash_state(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


class MemoryStateStore:
    def __init__(self, now=None):
        self._rows: dict[str, PendingAuthorization] = {}
        self._consumed: set[str] = set()
        self._now = now or (lambda: datetime.now(timezone.utc))

    def save(self, *, state: str, subject: str, code_verifier: str, expires_at) -> None:
        self._rows[_hash_state(state)] = PendingAuthorization(subject, code_verifier, expires_at)

    def consume(self, state: str) -> PendingAuthorization | None:
        key = _hash_state(state)
        if key in self._consumed:
            return None
        pending = self._rows.get(key)
        if pending is None or pending.expires_at <= self._now():
            return None
        self._consumed.add(key)
        return pending


class MemorySessionStore:
    def __init__(self):
        self._rows: dict[str, OAuthSession] = {}

    def get(self, subject: str) -> OAuthSession | None:
        return self._rows.get(subject)

    def save(self, session: OAuthSession) -> None:
        self._rows[session.subject] = session

    def delete(self, subject: str) -> None:
        self._rows.pop(subject, None)


class MemoryIdempotencyStore:
    def __init__(self):
        self._rows: dict[tuple[str, str, str], StoredResponse] = {}

    def get(self, subject: str, operation: str, key: str) -> StoredResponse | None:
        return self._rows.get((subject, operation, key))

    def save(self, subject: str, operation: str, key: str, response: StoredResponse) -> None:
        self._rows[(subject, operation, key)] = response
