"""TM-GPI-007 — minimal personal context for TÉO (profile != authorization)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.gpt_actions.person_profile_reader_port import (
    PersonProfileReaderPort,
)

_ALLOWED_RESPONSE_KEYS = frozenset(
    {"display_name", "email", "job_title", "profile_complete"}
)


@dataclass(frozen=True)
class AuthenticatedUserContext:
    """Normalized identity extracted at the HTTP/interface boundary."""

    display_name: str | None
    email: str | None
    authorization: str


class UserContextService:
    """Projects authenticated identity + PersonProfile into a minimal GPT contract."""

    def __init__(self, person_profile_reader: PersonProfileReaderPort) -> None:
        self._profiles = person_profile_reader

    def get_my_context(self, user: AuthenticatedUserContext) -> dict[str, Any]:
        authorization = str(user.authorization or "").strip()
        if not authorization:
            raise GptActionsError(
                "Usuário não autenticado.",
                401,
                {"error_kind": "authn"},
            )

        email_value = str(user.email).strip() if user.email else None
        display_value = str(user.display_name).strip() if user.display_name else None

        profile = self._profiles.get_my_person_profile(authorization)
        job_title_raw = profile.get("job_title")
        job_title = (
            str(job_title_raw).strip()
            if isinstance(job_title_raw, str) and job_title_raw.strip()
            else None
        )

        payload = {
            "display_name": display_value,
            "email": email_value,
            "job_title": job_title,
            "profile_complete": bool(display_value and email_value),
        }
        assert set(payload.keys()) <= _ALLOWED_RESPONSE_KEYS
        return payload
