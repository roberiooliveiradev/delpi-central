"""Port: current-user PersonProfile from Core (Transformômetro → Core boundary)."""

from __future__ import annotations

from typing import Protocol


class PersonProfileReaderPort(Protocol):
    """Read-only self PersonProfile. No user_id selector, no S2S identity."""

    def get_my_person_profile(self, authorization: str) -> dict: ...
