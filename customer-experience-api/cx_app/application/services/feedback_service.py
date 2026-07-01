from __future__ import annotations

from typing import Any

from cx_app.application.services.participant_service import ParticipantNotFoundError
from cx_app.domain.feedback import FeedbackInput
from cx_app.infrastructure.persistence.feedback_repository import FeedbackRepository
from cx_app.infrastructure.persistence.participant_repository import ParticipantRepository

RATING_MIN = 1
RATING_MAX = 5
MAX_TEXT_LEN = 2000


class FeedbackAlreadyExistsError(RuntimeError):
    """Já existe feedback para este participante (1 por token)."""


class FeedbackValidationError(ValueError):
    """Dados de feedback inválidos."""


class FeedbackService:
    def __init__(
        self,
        participant_repository: ParticipantRepository | None = None,
        feedback_repository: FeedbackRepository | None = None,
    ) -> None:
        self.participants = participant_repository or ParticipantRepository()
        self.feedback = feedback_repository or FeedbackRepository()

    def get_status(self, token: str) -> dict[str, Any]:
        participant = self._active_participant(token)
        submitted = self.feedback.exists_for_participant(participant["id"])
        return {"fullName": participant.get("full_name"), "submitted": submitted}

    def submit(self, token: str, data: FeedbackInput) -> dict[str, Any]:
        participant = self._active_participant(token)
        self._validate(data)

        if self.feedback.exists_for_participant(participant["id"]):
            raise FeedbackAlreadyExistsError(token)

        created = self.feedback.create(
            {
                "participant_id": participant["id"],
                "rating": data.rating,
                "liked_most": _truncate(data.liked_most),
                "suggestions": _truncate(data.suggestions),
            }
        )
        return self.to_public_view(created)

    # ----- internos --------------------------------------------------------

    def _active_participant(self, token: str) -> dict[str, Any]:
        row = self.participants.get_by_token(token)
        if not row or not row.get("is_active"):
            raise ParticipantNotFoundError(token)
        return row

    @staticmethod
    def _validate(data: FeedbackInput) -> None:
        if not isinstance(data.rating, int) or not (RATING_MIN <= data.rating <= RATING_MAX):
            raise FeedbackValidationError(
                f"Nota inválida. Escolha um valor entre {RATING_MIN} e {RATING_MAX}."
            )

    @staticmethod
    def to_public_view(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "rating": row.get("rating"),
            "likedMost": row.get("liked_most"),
            "suggestions": row.get("suggestions"),
            "createdAt": row.get("created_at"),
        }


def _truncate(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[:MAX_TEXT_LEN]
