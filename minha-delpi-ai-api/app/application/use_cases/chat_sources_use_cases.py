import os
import uuid
from dataclasses import replace
from pathlib import Path
from uuid import UUID

from werkzeug.utils import secure_filename

from app.application.dto.chat_source_response import ChatSourceResponse
from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.services.chat_attachment_text_extractor import ChatAttachmentTextExtractor
from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)
from app.application.use_cases.ingest_knowledge_document_use_case import (
    IngestKnowledgeDocumentUseCase,
)
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.services.workspace_file_ingest_policy_service import (
    WorkspaceFileIngestPolicyService,
)


def _source_response(document, chunk_count: int | None = None) -> ChatSourceResponse:
    metadata = document.metadata or {}
    extractor = metadata.get("extractor")

    return ChatSourceResponse(
        id=str(document.id),
        title=document.title,
        source_type=document.source_type,
        source_ref=document.source_ref,
        scope=metadata.get("scope"),
        project_id=metadata.get("projectId"),
        agent_id=metadata.get("agentId"),
        attachment_id=metadata.get("attachmentId"),
        original_filename=metadata.get("originalFilename"),
        content_type=metadata.get("contentType"),
        active=bool(document.active),
        metadata=metadata,
        created_at=document.created_at.isoformat(),
        updated_at=document.updated_at.isoformat(),
        chunk_count=chunk_count,
        indexed=(chunk_count or 0) > 0,
        extractor=extractor if isinstance(extractor, dict) else None,
        index_reason=metadata.get("indexReason"),
    )


class ChatSourceFileStorage:
    def __init__(self, storage_root: str | None = None):
        self.storage_root = Path(
            storage_root
            or os.getenv("CHAT_SOURCE_STORAGE_PATH")
            or "/tmp/minha-delpi-chat-sources"
        )

    def save(
        self,
        *,
        user_id: str,
        scope: str,
        owner_id: str,
        original_filename: str,
        content: bytes,
    ) -> dict:
        if not content:
            raise ValueError("File is empty")

        family = WorkspaceFileIngestPolicyService.family_for_storage_scope(scope)

        if len(content) > WorkspaceFileIngestPolicyService.max_size_bytes(family):
            raise ValueError("File exceeds maximum size")

        safe_name = secure_filename(original_filename) or "arquivo"

        if not WorkspaceFileIngestPolicyService.is_extension_allowed(family, safe_name):
            raise ValueError("File type is not allowed")

        extension = Path(safe_name).suffix.lower()

        storage_dir = self.storage_root / user_id / scope / owner_id
        storage_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}{extension}"
        storage_path = storage_dir / filename
        storage_path.write_bytes(content)

        return {
            "filename": filename,
            "originalFilename": original_filename,
            "storagePath": str(storage_path),
            "extension": extension,
            "sizeBytes": len(content),
        }


class CreateProjectSourceUseCase:
    def __init__(
        self,
        project_repository: ChatProjectRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
        ingest_use_case: IngestKnowledgeDocumentUseCase,
        text_extractor: ChatAttachmentTextExtractor,
        file_storage: ChatSourceFileStorage | None = None,
    ):
        self.project_repository = project_repository
        self.knowledge_repository = knowledge_repository
        self.ingest_use_case = ingest_use_case
        self.text_extractor = text_extractor
        self.file_storage = file_storage or ChatSourceFileStorage()

    def execute_text(
        self,
        *,
        user_id: str,
        project_id: str,
        title: str,
        content: str,
        metadata: dict | None = None,
    ) -> ChatSourceResponse:
        project = self._get_project(user_id=user_id, project_id=project_id)

        document = self.ingest_use_case.execute(
            IngestDocumentRequest(
                user_id=user_id,
                title=title,
                source_type="project_source",
                source_ref=project_id,
                content=content,
                metadata={
                    **(metadata or {}),
                    "scope": "project_source",
                    "userId": user_id,
                    "projectId": str(project.id),
                    "projectName": project.name,
                },
            )
        )

        created = self.knowledge_repository.get_document_by_id(UUID(document["id"]))
        return _source_response(created, document["chunks"])

    def execute_file(
        self,
        *,
        user_id: str,
        project_id: str,
        original_filename: str,
        content_type: str | None,
        content: bytes,
    ) -> ChatSourceResponse:
        project = self._get_project(user_id=user_id, project_id=project_id)

        saved = self.file_storage.save(
            user_id=user_id,
            scope="project",
            owner_id=project_id,
            original_filename=original_filename,
            content=content,
        )

        extracted = self.text_extractor.extract(
            storage_path=saved["storagePath"],
            filename=original_filename,
            content_type=content_type,
        )

        if not extracted["supported"] or not str(extracted.get("content") or "").strip():
            raise ValueError("File could not be extracted or is unsupported")

        document = self.ingest_use_case.execute(
            IngestDocumentRequest(
                user_id=user_id,
                title=original_filename,
                source_type="project_source",
                source_ref=saved["storagePath"],
                content=extracted["content"],
                metadata={
                    "scope": "project_source",
                    "userId": user_id,
                    "projectId": str(project.id),
                    "projectName": project.name,
                    "originalFilename": original_filename,
                    "contentType": content_type,
                    "storagePath": saved["storagePath"],
                    "sizeBytes": saved["sizeBytes"],
                    "extractor": extracted["metadata"],
                },
            )
        )

        created = self.knowledge_repository.get_document_by_id(UUID(document["id"]))
        return _source_response(created, document["chunks"])

    def _get_project(self, *, user_id: str, project_id: str):
        result = self.project_repository.get_accessible_by_id(
            project_id=UUID(project_id),
            user_id=UUID(user_id),
        )

        if not result:
            raise ValueError("Project not found or inaccessible")

        project, role = result

        if role not in {"owner", "editor"}:
            raise ValueError("Project is read-only")

        return project


class ListProjectSourcesUseCase:
    def __init__(
        self,
        project_repository: ChatProjectRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
    ):
        self.project_repository = project_repository
        self.knowledge_repository = knowledge_repository

    def execute(self, *, user_id: str, project_id: str) -> list[ChatSourceResponse]:
        result = self.project_repository.get_accessible_by_id(
            project_id=UUID(project_id),
            user_id=UUID(user_id),
        )

        if not result:
            raise ValueError("Project not found or inaccessible")

        documents = self.knowledge_repository.list_documents_by_metadata(
            filters={
                "scope": "project_source",
                "projectId": project_id,
            },
            limit=200,
            active=True,
        )

        return [_source_response(document, chunk_count) for document, chunk_count in documents]


class CreateAgentSourceUseCase:
    def __init__(
        self,
        agent_repository: ChatAgentRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
        ingest_use_case: IngestKnowledgeDocumentUseCase,
        text_extractor: ChatAttachmentTextExtractor,
        file_storage: ChatSourceFileStorage | None = None,
        pipeline: KnowledgeIngestionPipelineService | None = None,
    ):
        self.agent_repository = agent_repository
        self.knowledge_repository = knowledge_repository
        self.ingest_use_case = ingest_use_case
        self.text_extractor = text_extractor
        self.file_storage = file_storage or ChatSourceFileStorage()
        self.pipeline = pipeline or KnowledgeIngestionPipelineService()

    def _find_duplicate_agent_source(
        self,
        agent_id: str,
        content_hash: str | None,
    ):
        normalized_hash = str(content_hash or "").strip()

        if not normalized_hash:
            return None

        documents = self.knowledge_repository.list_documents_by_metadata(
            filters={
                "scope": "agent_source",
                "agentId": agent_id,
                "contentHash": normalized_hash,
            },
            limit=1,
            active=True,
        )

        return documents[0] if documents else None

    def execute_text(
        self,
        *,
        user_id: str,
        agent_id: str,
        title: str,
        content: str,
        metadata: dict | None = None,
    ) -> ChatSourceResponse:
        agent, _role = self._get_agent(user_id=user_id, agent_id=agent_id)

        prepared = self.pipeline.prepare(
            content,
            title=title,
            source_type="agent_source",
            source_ref=str(agent.id),
            document_metadata=metadata,
        )

        duplicate = self._find_duplicate_agent_source(str(agent.id), prepared.content_hash)

        if duplicate:
            document, chunk_count = duplicate
            return replace(_source_response(document, chunk_count), duplicate=True)

        document = self.ingest_use_case.execute(
            IngestDocumentRequest(
                user_id=user_id,
                title=title,
                source_type="agent_source",
                source_ref=str(agent.id),
                content=content,
                metadata={
                    **(metadata or {}),
                    "scope": "agent_source",
                    "userId": user_id,
                    "agentId": str(agent.id),
                    "agentName": agent.name,
                },
            )
        )

        created = self.knowledge_repository.get_document_by_id(UUID(document["id"]))
        return _source_response(created, document["chunks"])

    def execute_file(
        self,
        *,
        user_id: str,
        agent_id: str,
        original_filename: str,
        content_type: str | None,
        content: bytes,
    ) -> ChatSourceResponse:
        agent, _role = self._get_agent(user_id=user_id, agent_id=agent_id)

        saved = self.file_storage.save(
            user_id=user_id,
            scope="agent",
            owner_id=agent_id,
            original_filename=original_filename,
            content=content,
        )

        extracted = self.text_extractor.extract(
            storage_path=saved["storagePath"],
            filename=original_filename,
            content_type=content_type,
        )

        if not extracted["supported"] or not str(extracted.get("content") or "").strip():
            raise ValueError("File could not be extracted or is unsupported")

        extracted_content = str(extracted.get("content") or "").strip()

        prepared = self.pipeline.prepare(
            extracted_content,
            title=original_filename,
            source_type="agent_source",
            source_ref=str(agent.id),
            document_metadata={
                "originalFilename": original_filename,
                "contentType": content_type,
            },
        )

        duplicate = self._find_duplicate_agent_source(str(agent.id), prepared.content_hash)

        if duplicate:
            try:
                Path(saved["storagePath"]).unlink(missing_ok=True)
            except OSError:
                pass

            document, chunk_count = duplicate
            return replace(_source_response(document, chunk_count), duplicate=True)

        document = self.ingest_use_case.execute(
            IngestDocumentRequest(
                user_id=user_id,
                title=original_filename,
                source_type="agent_source",
                source_ref=saved["storagePath"],
                content=extracted_content,
                metadata={
                    "scope": "agent_source",
                    "userId": user_id,
                    "agentId": str(agent.id),
                    "agentName": agent.name,
                    "originalFilename": original_filename,
                    "contentType": content_type,
                    "storagePath": saved["storagePath"],
                    "sizeBytes": saved["sizeBytes"],
                    "extractor": extracted["metadata"],
                },
            )
        )

        created = self.knowledge_repository.get_document_by_id(UUID(document["id"]))
        return _source_response(created, document["chunks"])

    def _get_agent(self, *, user_id: str, agent_id: str):
        result = self.agent_repository.get_accessible_by_id(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
        )

        if not result:
            raise ValueError("Agent not found or inaccessible")

        agent, role = result

        if role not in {"owner", "editor", "system"}:
            raise ValueError("Agent is read-only")

        return agent, role


class ListAgentSourcesUseCase:
    def __init__(
        self,
        agent_repository: ChatAgentRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
    ):
        self.agent_repository = agent_repository
        self.knowledge_repository = knowledge_repository

    def execute(self, *, user_id: str, agent_id: str) -> list[ChatSourceResponse]:
        result = self.agent_repository.get_accessible_by_id(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
        )

        if not result:
            raise ValueError("Agent not found or inaccessible")

        agent, _role = result

        documents = self.knowledge_repository.list_documents_by_metadata(
            filters={
                "scope": "agent_source",
                "agentId": str(agent.id),
            },
            limit=200,
            active=True,
        )

        return [_source_response(document, chunk_count) for document, chunk_count in documents]


class DeleteChatSourceUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        project_repository: ChatProjectRepositoryPort | None = None,
        agent_repository: ChatAgentRepositoryPort | None = None,
    ):
        self.knowledge_repository = knowledge_repository
        self.project_repository = project_repository
        self.agent_repository = agent_repository

    def execute(self, *, user_id: str, source_id: str) -> bool:
        document_id = UUID(source_id)
        document = self.knowledge_repository.get_document_by_id(document_id)

        if not document:
            return False

        metadata = document.metadata or {}

        if not self._can_delete(user_id=user_id, metadata=metadata):
            return False

        deactivated = self.knowledge_repository.deactivate_document(document_id)

        return deactivated is not None

    def _can_delete(self, *, user_id: str, metadata: dict) -> bool:
        scope = metadata.get("scope")
        user_uuid = UUID(user_id)

        if scope == "project_source":
            project_id = metadata.get("projectId")

            if not project_id or not self.project_repository:
                return False

            result = self.project_repository.get_accessible_by_id(
                project_id=UUID(project_id),
                user_id=user_uuid,
            )

            if not result:
                return False

            _project, role = result

            return role in {"owner", "editor"}

        if scope == "agent_source":
            agent_id = metadata.get("agentId")

            if not agent_id or not self.agent_repository:
                return False

            result = self.agent_repository.get_accessible_by_id(
                agent_id=UUID(agent_id),
                user_id=user_uuid,
            )

            if not result:
                return False

            _agent, role = result

            return role in {"owner", "editor", "system"}

        return str(metadata.get("userId") or "") == str(user_id)
