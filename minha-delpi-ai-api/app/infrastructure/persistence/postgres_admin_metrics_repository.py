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

        recent_audit_logs = (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

        action_distribution = self._count_by_field(
            AiAuditLogModel.action,
            since=since,
            limit=10,
        )
        context_distribution = self._count_by_field(
            AiAuditLogModel.context,
            since=since,
            limit=10,
        )
        error_distribution = self._count_by_field(
            AiAuditLogModel.action,
            since=since,
            limit=10,
            only_errors=True,
        )

        tool_usage_rate = self._safe_rate(recent_tool_calls, recent_audit_logs)
        error_rate = self._safe_rate(recent_errors, recent_audit_logs)

        return {
            "sessions": sessions,
            "messages": messages,
            "knowledgeDocuments": documents,
            "activeKnowledgeDocuments": active_documents,
            "knowledgeChunks": chunks,
            "auditLogs": audit_logs,
            "recentToolCalls24h": recent_tool_calls,
            "recentErrors24h": recent_errors,
            "recentAuditLogs24h": recent_audit_logs,
            "toolUsageRate24h": tool_usage_rate,
            "errorRate24h": error_rate,
            "actionDistribution24h": action_distribution,
            "contextDistribution24h": context_distribution,
            "errorDistribution24h": error_distribution,
            "advanced": {
                "latencyAvgMs": None,
                "tokensUsed": None,
                "estimatedCost": None,
                "ragFailures": None,
                "assertivenessRate": None,
                "agentMetrics": [],
                "userProfileMetrics": [],
                "notes": [
                    "Latência, tokens e custo dependem de instrumentação adicional no fluxo de mensagens.",
                    "Métricas por agente e usuário/perfil dependem de eventos auditáveis padronizados.",
                ],
            },
        }

    def _safe_rate(self, value: int, total: int) -> float:
        if total <= 0:
            return 0.0

        return round(value / total, 4)

    def _count_by_field(
        self,
        field,
        *,
        since: datetime,
        limit: int,
        only_errors: bool = False,
    ) -> list[dict]:
        query = (
            db.session.query(field.label("key"), db.func.count().label("count"))
            .filter(AiAuditLogModel.created_at >= since)
        )

        if only_errors:
            query = query.filter(AiAuditLogModel.action.ilike("%error%"))

        rows = (
            query
            .group_by(field)
            .order_by(db.func.count().desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "key": row.key or "sem_contexto",
                "count": int(row.count or 0),
            }
            for row in rows
        ]
