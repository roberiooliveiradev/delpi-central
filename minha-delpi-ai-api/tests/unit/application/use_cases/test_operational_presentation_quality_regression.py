"""Regressão de qualidade — perguntas operacionais devem ser legíveis e orientadas à intenção."""

from __future__ import annotations

import json

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta
from tests.fixtures.operational_presentation_quality_cases import (
    OPERATIONAL_PRESENTATION_QUALITY_CASES,
)


def _evaluate_expectations(
    meta: dict,
    *,
    forbidden: list[str] | None = None,
    required: list[str] | None = None,
) -> list[str]:
    blob = json.dumps(meta, ensure_ascii=False).lower()
    gaps: list[str] = []

    for token in forbidden or []:
        if str(token).lower() in blob:
            gaps.append(f"forbidden:{token}")

    for token in required or []:
        if str(token).lower() not in blob:
            gaps.append(f"required:{token}")

    return gaps


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build(case: dict) -> dict:
    envelope = load_api_delpi_fixture_with_meta(case["fixture"])

    return _use_case()._build_presentation_metadata(
        action={"path": case["path"]},
        sanitized_data=envelope,
        resolved_path=case["path"],
        request_parameters={"userMessage": case["user_message"]},
    )


def test_operational_presentation_quality_cases():
    failures: list[str] = []

    for case in OPERATIONAL_PRESENTATION_QUALITY_CASES:
        meta = _build(case)
        gaps = _evaluate_expectations(
            meta,
            forbidden=case.get("forbidden"),
            required=case.get("required"),
        )

        if case.get("data_answer_required"):
            answer = str(
                ((meta.get("dataAnswer") or {}).get("summary") or {}).get("answer") or ""
            ).strip()

            if not answer:
                gaps.append("missing_data_answer_summary")

        if gaps:
            failures.append(f"{case['id']}: {', '.join(gaps)}")

    assert not failures, "\n".join(failures)
