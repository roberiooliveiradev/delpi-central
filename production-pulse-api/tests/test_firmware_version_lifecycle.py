from production_pulse_app.domain.services.firmware_version_lifecycle import (
    can_edit_source,
    can_publish,
    firmware_lifecycle_state,
    validate_source_text,
)


def test_lifecycle_states():
    assert firmware_lifecycle_state({"published_at": None, "archived_at": None}) == "draft"
    assert firmware_lifecycle_state({"published_at": "x", "archived_at": None}) == "published"
    assert firmware_lifecycle_state({"published_at": "x", "archived_at": "y"}) == "archived"


def test_can_publish_requires_artifact():
    draft_no_bin = {
        "published_at": None,
        "archived_at": None,
        "artifact_path": None,
        "artifact_sha256": None,
    }
    assert can_publish(draft_no_bin) is False
    draft_with_bin = {
        **draft_no_bin,
        "artifact_path": "k/v/u.bin",
        "artifact_sha256": "abc",
    }
    assert can_publish(draft_with_bin) is True


def test_source_editable_only_on_draft():
    assert can_edit_source({"published_at": None, "archived_at": None}) is True
    assert can_edit_source({"published_at": "x", "archived_at": None}) is False


def test_validate_source_text_rejects_empty_and_large():
    assert validate_source_text("  ") is None
    assert validate_source_text("void setup(){}") == "void setup(){}"
    try:
        validate_source_text("x" * (256 * 1024 + 1))
        assert False, "expected error"
    except ValueError as exc:
        assert str(exc) == "firmwareSourceTooLarge"
