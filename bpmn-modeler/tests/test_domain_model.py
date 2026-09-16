import pytest

from bpmn_modeler.domain import CanonicalBpmnArtifact, Model, WorkingCopy


def test_model_can_be_created_with_a_working_copy() -> None:
    artifact = CanonicalBpmnArtifact(content="<definitions />")
    working_copy = WorkingCopy(artifact=artifact)

    model = Model(id="model-001", working_copy=working_copy)

    assert model.id == "model-001"
    assert model.working_copy is working_copy


@pytest.mark.parametrize("model_id", ["", " ", "\t\n"])
def test_model_requires_a_non_blank_identity(model_id: str) -> None:
    artifact = CanonicalBpmnArtifact(content="<definitions />")

    with pytest.raises(ValueError, match="model id must not be empty"):
        Model(id=model_id, working_copy=WorkingCopy(artifact=artifact))


def test_working_copy_can_replace_its_current_artifact() -> None:
    original = CanonicalBpmnArtifact(content="<definitions id='before' />")
    replacement = CanonicalBpmnArtifact(content="<definitions id='after' />")
    working_copy = WorkingCopy(artifact=original)

    working_copy.replace_artifact(replacement)

    assert working_copy.artifact is replacement


def test_canonical_artifact_preserves_content_without_parsing_or_normalizing() -> None:
    content = "  not parsed <custom:anything attr='1'/>\n"

    artifact = CanonicalBpmnArtifact(content=content)

    assert artifact.content == content
