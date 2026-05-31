"""Chips após modo treinamento (Playbook 10)."""

from __future__ import annotations

from app.application.services.chat_onboarding_service import ChatOnboardingService


class ChatOnboardingFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        pipeline_stages: list[str] | None = None,
    ) -> None:
        stages = list(pipeline_stages or [])

        if "onboarding_training" not in stages and not ChatOnboardingService.is_training_request(
            message,
        ):
            return

        suggestions = ChatOnboardingService.training_follow_up_suggestions()

        if suggestions:
            metadata["onboardingFollowUpSuggestions"] = suggestions
