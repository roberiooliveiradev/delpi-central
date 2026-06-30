from __future__ import annotations

from app.domain.services.quality_action_plans.quality_action_plan_reference_service import (
    classify_plan_reference,
    normalize_plan_code,
)


def test_classify_plan_reference_uuid() -> None:
    assert classify_plan_reference("f0e274de-cc4b-4b68-b9cb-881408f9374b") == "uuid"


def test_classify_plan_reference_code() -> None:
    assert classify_plan_reference("PAC-2026-0029") == "code"
    assert classify_plan_reference("pac-2026-0029") == "code"


def test_classify_plan_reference_invalid() -> None:
    assert classify_plan_reference("PAC-2026-0029-extra") == "invalid"
    assert classify_plan_reference("not-a-plan") == "invalid"
    assert classify_plan_reference("") == "invalid"


def test_normalize_plan_code() -> None:
    assert normalize_plan_code("pac-2026-0029") == "PAC-2026-0029"
