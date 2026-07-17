from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PresentationRealtimeSession:
    """Identidade e capacidade validadas antes de entrar na sala WebSocket."""

    user_id: str
    display_name: str
    role: str
    can_edit: bool
    allow_presence: bool = True

