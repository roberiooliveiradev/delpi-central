"""Application contracts for C3-INTERACTION-RUNTIME-01.

Provider SDK objects, Flask objects, and permission snapshots are
forbidden here. The request carries the already-resolved authoritative
PlatformAccessContext plus untrusted user text only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.platform_access import PlatformAccessContext
from app.domain.evidence.model import EpistemicClass


@dataclass(frozen=True, slots=True)
class InteractiveTurnRequest:
    """One bounded interactive turn request.

    access_context is the Core-resolved authority projection — it carries
    identity and effective permissions, and it is never extended from
    request body fields. input_text is untrusted user data.
    """

    access_context: PlatformAccessContext | None
    input_text: str


@dataclass(frozen=True, slots=True)
class InteractiveTurnResult:
    """Bounded application response for one interaction turn.

    Exposes correlation IDs and validated result content only. No raw
    provider payload, credentials, instruction body, or authority
    snapshot is ever part of this contract.
    """

    session_id: str
    user_turn_id: str
    result_turn_id: str
    content: str
    epistemic_class: EpistemicClass | None
    limitations: tuple[str, ...]
    generated_at: str
    model_invocation_id: str

    def is_fact(self) -> bool:
        return False

    def authorizes_act(self) -> bool:
        return False
