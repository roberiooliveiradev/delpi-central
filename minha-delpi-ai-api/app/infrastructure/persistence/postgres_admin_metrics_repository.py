from datetime import datetime, timedelta, timezone

from app.domain.ports.admin_metrics_repository_port import AdminMetricsRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.audit_log_model import AiAuditLogModel
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel
from app.infrastructure.db.models.knowledge_chunk_model import AiKnowledgeChunkModel
from app.infrastructure.db.models.knowledge_document_model import AiKnowledgeDocumentModel


class PostgresAdminMetricsRepository(AdminMetricsRepositoryPort):
    def get_summary(self) -> dict:
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        sessions = db.session.query(AiChatSessionModel).count()
        messages = db.session.query(AiChatMessageModel).count()
        documents = db.session.query(AiKnowledgeDocumentModel).count()
        active_documents = (
            db.session.query(AiKnowledgeDocumentModel)
            .filter(AiKnowledgeDocumentModel.active.is_(True))
            .count()
        )
        chunks = db.session.query(AiKnowledgeChunkModel).count()
        audit_logs = db.session.query(AiAuditLogModel).count()

        recent_tool_calls = (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action == "chat.tool.called")
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

        recent_errors = (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action.ilike("%error%"))
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

        return {
            "sessions": sessions,
            "messages": messages,
            "knowledgeDocuments": documents,
            "activeKnowledgeDocuments": active_documents,
            "knowledgeChunks": chunks,
            "auditLogs": audit_logs,
            "recentToolCalls24h": recent_tool_calls,
            "recentErrors24h": recent_errors,
        }
