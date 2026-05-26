from typing import Protocol, Optional
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class ConsentDTO:
    id: UUID
    user_id: UUID
    purpose: str
    granted: bool
    granted_at: datetime | None
    revoked_at: datetime | None


class ConsentRepositoryPort(Protocol):
    def list_by_user(self, user_id: UUID) -> list[ConsentDTO]: ...
    def get_by_user_and_purpose(self, user_id: UUID, purpose: str) -> Optional[ConsentDTO]: ...
    def grant(self, *, user_id: UUID, purpose: str, ip_address: str | None = None, user_agent: str | None = None) -> ConsentDTO: ...
    def revoke(self, user_id: UUID, purpose: str) -> Optional[ConsentDTO]: ...
    def revoke_all(self, user_id: UUID) -> int: ...
