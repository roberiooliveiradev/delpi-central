from app.domain.services.quality_action_plans.action_responsibles_service import (
    build_legacy_action_responsible_fields,
    normalize_responsibles_payload,
    split_legacy_responsible_names,
)


def test_split_legacy_responsible_names() -> None:
    assert split_legacy_responsible_names("Ana / Bruno") == ["Ana", "Bruno"]
    assert split_legacy_responsible_names("Ana") == ["Ana"]
    assert split_legacy_responsible_names("") == []


def test_normalize_responsibles_payload_deduplicates_users() -> None:
    result = normalize_responsibles_payload(
        [
            {"user_id": "user-1", "display_name": "Ana"},
            {"user_id": "user-1", "display_name": "Ana Silva"},
        ]
    )
    assert len(result) == 1
    assert result[0]["user_id"] == "user-1"


def test_build_legacy_action_responsible_fields_joins_names() -> None:
    user_id, name = build_legacy_action_responsible_fields(
        [
            {"user_id": "user-1", "display_name": "Ana"},
            {"user_id": "user-2", "display_name": "Bruno"},
        ]
    )
    assert user_id == "user-1"
    assert name == "Ana / Bruno"


def test_normalize_from_legacy_single_user() -> None:
    result = normalize_responsibles_payload(
        None,
        legacy_user_id="user-1",
        legacy_name="Ana",
    )
    assert result == [{"user_id": "user-1", "display_name": "Ana"}]
