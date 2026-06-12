import pytest

from app.application.use_cases.chat_sources_use_cases import ChatSourceFileStorage
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.workspace_file_ingest_policy_service import (
    WorkspaceFileIngestPolicyService,
)
from tests.fixtures.workspace_file_ingest_cases import (
    POLICY_EXTENSION_CASES,
    READING_STATUS_LABEL_CASES,
    STORAGE_SCOPE_CASES,
)


@pytest.mark.parametrize(("status", "expected_label"), READING_STATUS_LABEL_CASES)
def test_f6_reading_status_labels_from_attachments_json(status, expected_label):
    labels = ChatAssistantContentService.get_mapping("attachments", "preview", "readingStatus")

    assert labels[status] == expected_label


@pytest.mark.parametrize(("family", "filename", "allowed"), POLICY_EXTENSION_CASES)
def test_policy_extension_matrix(family, filename, allowed):
    assert (
        WorkspaceFileIngestPolicyService.is_extension_allowed(family, filename) is allowed
    )


@pytest.mark.parametrize(("scope", "family"), STORAGE_SCOPE_CASES)
def test_storage_scope_maps_to_ingest_family(scope, family):
    assert WorkspaceFileIngestPolicyService.family_for_storage_scope(scope) == family


def test_workspace_ingest_errors_use_attachments_json():
    assert "extrair texto" in ChatAssistantContentService.get(
        "attachments",
        "ingestUi",
        "workspace",
        "extractFailed",
    )


def test_agent_source_storage_rejects_images(tmp_path, monkeypatch):
    monkeypatch.setenv("CHAT_SOURCE_STORAGE_PATH", str(tmp_path))
    storage = ChatSourceFileStorage()

    with pytest.raises(ValueError, match="permitido"):
        storage.save(
            user_id="user-1",
            scope="agent",
            owner_id="agent-1",
            original_filename="foto.png",
            content=b"png-bytes",
        )
