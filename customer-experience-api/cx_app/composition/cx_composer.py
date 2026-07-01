from __future__ import annotations

from functools import lru_cache

from cx_app.application.services.feedback_service import FeedbackService
from cx_app.application.services.form_response_service import FormResponseService
from cx_app.application.services.form_service import FormService
from cx_app.application.services.participant_service import ParticipantService


@lru_cache(maxsize=1)
def build_participant_service() -> ParticipantService:
    return ParticipantService()


@lru_cache(maxsize=1)
def build_feedback_service() -> FeedbackService:
    return FeedbackService()


@lru_cache(maxsize=1)
def build_form_service() -> FormService:
    return FormService()


@lru_cache(maxsize=1)
def build_form_response_service() -> FormResponseService:
    return FormResponseService()
