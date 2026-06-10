"""Gate R11 — chips pós-resposta tier A derivados de presentationDecision."""

from __future__ import annotations

from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)
from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def tier_a_interactivity_cases() -> list[dict]:
    output: list[dict] = []

    for case in ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases():
        labels = case.get("expected_interactivity_labels")

        if not isinstance(labels, list) or not labels:
            continue

        output.append({**case, "expected_interactivity_labels": labels})

    return output


def build_metadata(case: dict) -> dict:
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    envelope = load_api_delpi_fixture_with_meta(str(case["fixture"]))

    return use_case._build_presentation_metadata(
        action={"path": case["path"]},
        sanitized_data=envelope,
        resolved_path=str(case["path"]),
        request_parameters={"userMessage": str(case.get("user_message") or "")},
    )


def interactivity_labels(metadata: dict) -> list[str]:
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {**metadata, "ok": True},
        }
    ]
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(tool_calls)

    return [str(item.get("label") or "").strip() for item in suggestions if item.get("label")]


def validate_tier_a_interactivity_cases() -> list[str]:
    warnings: list[str] = []

    for case in tier_a_interactivity_cases():
        metadata = build_metadata(case)
        labels = interactivity_labels(metadata)
        expected = [str(label).strip() for label in case["expected_interactivity_labels"]]

        for label in expected:
            if label not in labels:
                warnings.append(
                    f"{case['id']}: chip «{label}» ausente (obteve {labels[:6]})"
                )

    return warnings
