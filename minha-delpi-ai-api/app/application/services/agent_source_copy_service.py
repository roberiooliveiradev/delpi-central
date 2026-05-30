from uuid import UUID

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.use_cases.ingest_knowledge_document_use_case import IngestKnowledgeDocumentUseCase
from app.domain.entities.chat_agent import ChatAgent
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class AgentSourceCopyService:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        ingest_use_case: IngestKnowledgeDocumentUseCase,
    ):
        self.knowledge_repository = knowledge_repository
        self.ingest_use_case = ingest_use_case

    def copy_agent_sources(
        self,
        *,
        user_id: str,
        source_agent: ChatAgent,
        target_agent: ChatAgent,
    ) -> int:
        documents = self.knowledge_repository.list_documents_by_metadata(
            filters={
                "scope": "agent_source",
                "agentId": str(source_agent.id),
            },
            limit=200,
            active=True,
        )

        copied = 0

        for document, _chunk_count in documents:
            chunks = self.knowledge_repository.list_chunks_by_document_id(
                document.id,
                limit=500,
            )

            if not chunks:
                continue

            content = "\n\n".join(
                chunk.content.strip()
                for chunk in sorted(chunks, key=lambda item: item.chunk_index)
                if chunk.content and chunk.content.strip()
            )

            if not content:
                continue

            metadata = dict(document.metadata or {})
            metadata.update(
                {
                    "scope": "agent_source",
                    "userId": user_id,
                    "agentId": str(target_agent.id),
                    "agentName": target_agent.name,
                    "copiedFromAgentId": str(source_agent.id),
                    "copiedFromDocumentId": str(document.id),
                }
            )

            self.ingest_use_case.execute(
                IngestDocumentRequest(
                    user_id=user_id,
                    title=document.title,
                    source_type="agent_source",
                    source_ref=str(target_agent.id),
                    content=content,
                    metadata=metadata,
                )
            )
            copied += 1

        return copied
