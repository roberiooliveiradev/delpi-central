from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class CompleteInternalNcActionRequest:
    action_id: str
    actor_user_id: str
    completion_notes: Optional[str] = None