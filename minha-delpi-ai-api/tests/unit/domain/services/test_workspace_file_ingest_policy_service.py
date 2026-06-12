from app.domain.services.workspace_file_ingest_policy_service import (
    WorkspaceFileIngestPolicyService,
)


def test_session_attachment_allows_images():
    assert WorkspaceFileIngestPolicyService.is_extension_allowed(
        "session_attachment",
        "foto.png",
    )


def test_workspace_source_rejects_images():
    assert not WorkspaceFileIngestPolicyService.is_extension_allowed(
        "agent_source",
        "foto.png",
    )
    assert WorkspaceFileIngestPolicyService.is_extension_allowed(
        "project_source",
        "manual.pdf",
    )


def test_context_paste_accepts_text_formats_only():
    assert WorkspaceFileIngestPolicyService.is_extension_allowed("context_paste", "ctx.csv")
    assert not WorkspaceFileIngestPolicyService.is_extension_allowed(
        "context_paste",
        "ctx.pdf",
    )


def test_accept_attribute_lists_extensions():
    accept = WorkspaceFileIngestPolicyService.accept_attribute("session_attachment")

    assert ".pdf" in accept
    assert ".png" in accept


def test_storage_scope_maps_to_family():
    assert WorkspaceFileIngestPolicyService.family_for_storage_scope("agent") == "agent_source"
    assert WorkspaceFileIngestPolicyService.family_for_storage_scope("project") == "project_source"
