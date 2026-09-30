from __future__ import annotations

import pytest

from bpmn_modeler.application.errors import ApplicationError
from bpmn_modeler.application.policy import RecognitionState
from bpmn_modeler.application.use_cases import (
    ArtifactInput,
    CallerIdentity,
)
from bpmn_modeler.infrastructure.validation.intake import intake_bytes

from . import fixtures as fx
from .conftest import clean_input

VIEWER = CallerIdentity("viewer", frozenset({"bpmn-modeler.view"}))
EDITOR = CallerIdentity(
    "editor", frozenset({"bpmn-modeler.view", "bpmn-modeler.edit"})
)


def test_create_model_produces_blank_artifact(service, caller):
    outcome = service.create_model("Novo Processo", caller)
    assert outcome.version == 1
    assert outcome.artifact_sha256
    read = service.get_working_copy(outcome.model_id, caller)
    assert "bpmn:definitions" in read.artifact.content
    assert 'targetNamespace="urn:delpi:bpmn-modeler"' in read.artifact.content


def test_create_model_requires_edit(service, caller):
    with pytest.raises(ApplicationError) as err:
        service.create_model("X", VIEWER)
    assert err.value.code == "UNAUTHORIZED_OPERATION"


@pytest.mark.parametrize("name", ["", "   ", "x" * 121])
def test_invalid_display_name(service, caller, name):
    with pytest.raises(ApplicationError) as err:
        service.create_model(name, caller)
    assert err.value.code == "INVALID_DISPLAY_NAME"


def test_import_model_roundtrip(service, caller):
    raw = clean_input(fx.FX_VALID_001)
    outcome = service.import_model(raw, "Imported", caller)
    assert outcome.version == 1
    read = service.get_working_copy(outcome.model_id, caller)
    assert read.artifact.content == fx.FX_VALID_001  # byte-exact
    assert read.artifact_sha256 == outcome.artifact_sha256


def test_import_rejected_states(service, caller):
    for content in (fx.FX_BADXML_001, fx.FX_NOTBPMN_001, fx.FX_SEC_001):
        with pytest.raises(ApplicationError) as err:
            service.import_model(clean_input(content), "X", caller)
        assert err.value.code == "VALIDATION_BLOCKED"
        assert err.value.details["recognition_state"] != "BPMN_RECOGNIZED"


def test_import_with_issues_allowed(service, caller):
    outcome = service.import_model(clean_input(fx.FX_REF_001), "Broken", caller)
    assert outcome.version == 1


def test_inspect_never_persists(service, caller, repository):
    result = service.inspect_import(clean_input(fx.FX_SEC_002))
    assert result.recognition_state == RecognitionState.INPUT_REJECTED_SECURITY
    assert result.eligible_to_import is False
    assert repository.store == {}


def test_save_noop_and_conflict(service, caller, model_id):
    wc = service.get_working_copy(model_id, caller)
    raw = clean_input(wc.artifact.content)
    outcome = service.save_working_copy(model_id, raw, wc.version, caller)
    assert outcome.changed is False

    edited = wc.artifact.content.replace("<bpmn:process", '<bpmn:process name="n"')
    outcome = service.save_working_copy(model_id, clean_input(edited), wc.version, caller)
    assert outcome.changed and outcome.version == wc.version + 1

    with pytest.raises(ApplicationError) as err:
        service.save_working_copy(model_id, clean_input(edited), wc.version, caller)
    assert err.value.code == "CONFLICT"


def test_save_blocked_for_mustunderstand(service, caller):
    outcome = service.import_model(clean_input(fx.FX_EXT_003), "Ext", caller)
    wc = service.get_working_copy(outcome.model_id, caller)
    mutated = wc.artifact.content.replace('key="a"', 'key="b"')
    with pytest.raises(ApplicationError) as err:
        service.save_working_copy(
            outcome.model_id, clean_input(mutated), wc.version, caller
        )
    assert err.value.code == "VALIDATION_BLOCKED"


def test_revision_lifecycle(service, caller, model_id):
    wc = service.get_working_copy(model_id, caller)
    edited = wc.artifact.content.replace("<bpmn:process", '<bpmn:process name="n"')
    service.save_working_copy(model_id, clean_input(edited), 1, caller)

    r1 = service.create_revision(model_id, 2, caller)
    assert r1.revision_number == 1

    with pytest.raises(ApplicationError) as err:
        service.create_revision(model_id, 3, caller)
    assert err.value.code == "NO_CHANGES"

    edited2 = edited.replace('name="n"', 'name="n2"')
    service.save_working_copy(model_id, clean_input(edited2), 3, caller)
    service.create_revision(model_id, 4, caller)

    r3 = service.restore_revision(model_id, 1, 5, caller)
    assert r3.revision_number == 3
    revision3 = service.get_revision(model_id, 3, caller)
    assert revision3.origin.value == "restore"
    read = service.get_working_copy(model_id, caller)
    assert read.artifact.content == edited
    # old revisions intact
    assert len(service.list_revisions(model_id, 1, 50, caller).items) == 3


def test_archive_matrix(service, caller, model_id):
    out = service.archive_model(model_id, 1, caller)
    assert out.version == 2

    with pytest.raises(ApplicationError) as err:
        service.rename_model(model_id, "Novo", 2, caller)
    assert err.value.code == "MODEL_ARCHIVED"
    with pytest.raises(ApplicationError) as err:
        service.save_working_copy(
            model_id, clean_input("<x/>"), 2, caller
        )
    assert err.value.code == "MODEL_ARCHIVED"
    with pytest.raises(ApplicationError) as err:
        service.create_revision(model_id, 2, caller)
    assert err.value.code == "MODEL_ARCHIVED"

    # archived reads + duplicate still work
    service.get_working_copy(model_id, caller)
    dup = service.duplicate_model(model_id, "Cópia", caller)
    assert dup.version == 1

    noop = service.archive_model(model_id, 2, caller)
    assert noop.changed is False

    out = service.unarchive_model(model_id, 2, caller)
    assert out.version == 3
    service.rename_model(model_id, "Volta", 3, caller)


def test_rename_noop(service, caller, model_id):
    outcome = service.rename_model(model_id, "Fixture Model", 1, caller)
    assert outcome.changed is False and outcome.version == 1


def test_revision_ownership(service, caller):
    a = service.create_model("A", caller).model_id
    service.create_model("B", caller)
    with pytest.raises(ApplicationError) as err:
        service.get_revision(a, 99, caller)
    assert err.value.code == "REVISION_NOT_FOUND"


def test_get_missing_model(service, caller):
    import uuid

    with pytest.raises(ApplicationError) as err:
        service.get_model(str(uuid.uuid4()), caller)
    assert err.value.code == "MODEL_NOT_FOUND"


def test_validate_candidate_is_zero_write(service, caller, model_id):
    report = service.validate_working_copy(
        model_id, clean_input(fx.FX_REF_001), caller
    )
    assert any(i.rule_id == "BPMN-STRUCT-010" for i in report.issues)
    model = service.get_model(model_id, caller)
    assert model.version == 1


def test_list_models_pagination(service, caller):
    for i in range(3):
        service.create_model(f"M{i}", caller)
    page = service.list_models(
        query=None, archived="active", sort="display_name", direction="asc",
        page=1, page_size=2, caller=caller,
    )
    assert len(page.items) == 2 and page.has_more
