from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)


def make_knowledge_ingestion_pipeline_service() -> KnowledgeIngestionPipelineService:
    return KnowledgeIngestionPipelineService()
