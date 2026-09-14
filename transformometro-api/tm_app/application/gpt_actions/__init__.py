"""GPT Actions facade — compact OpenAPI surface for OpenAI Custom GPT."""

from tm_app.application.gpt_actions.entities import (
    GptAnalysisView,
    GptEntity,
    GptMeetingMinuteWorkflow,
    ENTITY_CAPABILITIES,
)
from tm_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    GPT_ACTIONS_OPERATION_IDS,
)
from tm_app.application.gpt_actions.registration_guide import build_registration_guide

__all__ = [
    "GptAnalysisView",
    "GptEntity",
    "GptMeetingMinuteWorkflow",
    "ENTITY_CAPABILITIES",
    "build_gpt_actions_openapi",
    "GPT_ACTIONS_OPERATION_IDS",
    "build_registration_guide",
]
