import hashlib
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from helpdesk_app.domain.models import (
    IdempotencyClaim,
    OAuthSession,
    PendingAuthorization,
    StoredResponse,
)


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


class MemoryUserTokenStore:
    """In-memory mirror of the governed ``glpi_user_tokens`` lifecycle.

    A row exists for every identity under BFF management — including
    ``adopted`` (authorized takeover pending rotation) and ``revoked``
    states, which carry no usable token. ``get`` only returns usable
    plaintext; presence of the row itself is what marks the identity as
    BFF-governed (``has_record``).
    """

    def __init__(self):
        self._rows: dict[int, dict] = {}
        self._locks: dict[int, threading.Lock] = {}
        self._guard = threading.Lock()

    def get(self, glpi_user_id: int) -> str | None:
        row = self._rows.get(int(glpi_user_id))
        if not row or row["revoked_at"] is not None:
            return None
        return row["token"] or None

    def save(self, glpi_user_id: int, api_token: str, *, source: str = "provisioned") -> None:
        self._rows[int(glpi_user_id)] = {
            "token": api_token,
            "source": source,
            "revoked_at": None,
        }

    def has_record(self, glpi_user_id: int) -> bool:
        return int(glpi_user_id) in self._rows

    def is_revoked(self, glpi_user_id: int) -> bool:
        row = self._rows.get(int(glpi_user_id))
        return bool(row) and row["revoked_at"] is not None

    def adopt(self, glpi_user_id: int) -> None:
        self._rows[int(glpi_user_id)] = {
            "token": "",
            "source": "adopted",
            "revoked_at": None,
        }

    def revoke(self, glpi_user_id: int) -> None:
        self._rows[int(glpi_user_id)] = {
            "token": "",
            "source": "revoked",
            "revoked_at": datetime.now(timezone.utc),
        }

    def delete(self, glpi_user_id: int) -> None:
        self._rows.pop(int(glpi_user_id), None)

    @contextmanager
    def provision_lock(self, glpi_user_id: int):
        key = int(glpi_user_id)
        with self._guard:
            lock = self._locks.setdefault(key, threading.Lock())
        lock.acquire()
        try:
            yield
        finally:
            lock.release()


class MemoryIdempotencyStore:
    def __init__(self):
        self._rows: dict[tuple[str, str, str], dict] = {}
        self._lock = threading.Lock()

    def get(self, subject: str, operation: str, key: str) -> StoredResponse | None:
        row = self._rows.get((subject, operation, key))
        if row is None or row["state"] != "completed":
            return None
        return row["response"]

    def claim(
        self,
        subject: str,
        operation: str,
        key: str,
        intent: dict,
    ) -> StoredResponse | IdempotencyClaim | None:
        with self._lock:
            row = self._rows.get((subject, operation, key))
            if row is None:
                self._rows[(subject, operation, key)] = {
                    "state": "in_flight",
                    "intent": dict(intent),
                    "claimed_at": datetime.now(timezone.utc),
                    "response": None,
                }
                return None
            if row["intent"] != dict(intent):
                # Key reused with a different intent — never replay the
                # stored response (it belongs to another write) and
                # never execute; block for operator review.
                return IdempotencyClaim(
                    claimed_at=row["claimed_at"], intent=row["intent"]
                )
            if row["state"] == "completed":
                return row["response"]
            return IdempotencyClaim(
                claimed_at=row["claimed_at"], intent=row["intent"]
            )

    def save(self, subject: str, operation: str, key: str, response: StoredResponse) -> None:
        with self._lock:
            row = self._rows.setdefault(
                (subject, operation, key),
                {"state": "in_flight", "intent": None, "claimed_at": None},
            )
            row["state"] = "completed"
            row["response"] = response

    def release(self, subject: str, operation: str, key: str) -> None:
        with self._lock:
            row = self._rows.get((subject, operation, key))
            if row is not None and row["state"] == "in_flight":
                del self._rows[(subject, operation, key)]
