"""TM-GPI-007 — minimal personal context for TÉO (profile != authorization)."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.core.auth_actor import actor_from_request
from tm_app.infrastructure.gateways.core_person_profile_gateway import (
    CorePersonProfileGateway,
)

_ALLOWED_RESPONSE_KEYS = frozenset(
    {"display_name", "email", "job_title", "profile_complete"}
)


class UserContextService:
    """Projects authenticated identity + PersonProfile into a minimal GPT contract."""

    def __init__(
        self,
        *,
        person_profile_gateway: CorePersonProfileGateway | None = None,
    ) -> None:
        self._profiles = person_profile_gateway or CorePersonProfileGateway()

    def get_my_context(self, request: Request) -> dict[str, Any]:
        user = getattr(request.state, "user", None)
        if user is None:
            raise GptActionsError(
                "Usuário não autenticado.",
                401,
                {"error_kind": "authn"},
            )

        _user_id, email, display_name = actor_from_request(request)
        email_value = str(email).strip() if email else None
        display_value = str(display_name).strip() if display_name else None

        profile = self._profiles.get_my_person_profile(
            request.headers.get("Authorization")
        )
        job_title_raw = profile.get("job_title")
        job_title = (
            str(job_title_raw).strip()
            if isinstance(job_title_raw, str) and job_title_raw.strip()
            else None
        )

        profile_complete = bool(display_value and email_value)

        payload = {
            "display_name": display_value,
            "email": email_value,
            "job_title": job_title,
            "profile_complete": profile_complete,
        }
        assert set(payload.keys()) <= _ALLOWED_RESPONSE_KEYS
        return payload
