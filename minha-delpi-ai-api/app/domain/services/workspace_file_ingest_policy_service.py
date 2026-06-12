from __future__ import annotations

from pathlib import Path
from typing import Literal

WorkspaceFileIngestFamily = Literal[
    "session_attachment",
    "agent_source",
    "project_source",
    "global_knowledge",
    "context_paste",
]

_SESSION_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".txt",
        ".md",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".csv",
        ".json",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }
)

_WORKSPACE_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".txt",
        ".md",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".csv",
        ".json",
    }
)

_CONTEXT_EXTENSIONS = frozenset({".txt", ".md", ".csv", ".tsv", ".json"})

_MAX_SIZE_BYTES = 25 * 1024 * 1024

_FAMILY_EXTENSIONS: dict[str, frozenset[str]] = {
    "session_attachment": _SESSION_EXTENSIONS,
    "agent_source": _WORKSPACE_EXTENSIONS,
    "project_source": _WORKSPACE_EXTENSIONS,
    "global_knowledge": _WORKSPACE_EXTENSIONS,
    "context_paste": _CONTEXT_EXTENSIONS,
}


class WorkspaceFileIngestPolicyService:
    """Política canônica de extensão e tamanho por família de ingestão (Playbook 17)."""

    @staticmethod
    def allowed_extensions(family: WorkspaceFileIngestFamily | str) -> frozenset[str]:
        return _FAMILY_EXTENSIONS.get(str(family), _WORKSPACE_EXTENSIONS)

    @staticmethod
    def extension_for_filename(filename: str) -> str:
        safe = str(filename or "").strip()
        return Path(safe).suffix.lower()

    @staticmethod
    def is_extension_allowed(
        family: WorkspaceFileIngestFamily | str,
        filename: str,
    ) -> bool:
        extension = WorkspaceFileIngestPolicyService.extension_for_filename(filename)
        return extension in WorkspaceFileIngestPolicyService.allowed_extensions(family)

    @staticmethod
    def max_size_bytes(_family: WorkspaceFileIngestFamily | str | None = None) -> int:
        return _MAX_SIZE_BYTES

    @staticmethod
    def accept_attribute(family: WorkspaceFileIngestFamily | str) -> str:
        extensions = sorted(WorkspaceFileIngestPolicyService.allowed_extensions(family))
        return ",".join(extensions)
