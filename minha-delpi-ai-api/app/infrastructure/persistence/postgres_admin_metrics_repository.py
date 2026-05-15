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

        message_metrics = self._message_metrics_24h(since=since)
        rag_failures = self._rag_failures_24h(since=since)

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
                "latencyAvgMs": message_metrics["latencyAvgMs"],
                "tokensUsed": message_metrics["tokensUsed"],
                "estimatedCost": message_metrics["estimatedCost"],
                "instrumentedMessages": message_metrics["instrumentedMessages"],
                "ragFailures": rag_failures,
                "assertivenessRate": None,
                "agentMetrics": [],
                "userProfileMetrics": [],
                "notes": [
                    "Latência e tokens são estimativas registradas no fluxo de mensagens a partir desta versão.",
                    "Métricas por agente e usuário/perfil dependem de eventos auditáveis padronizados.",
                ],
            },
        }


    def _rag_failures_24h(self, *, since: datetime) -> int:
        rows = (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.created_at >= since)
            .filter(AiAuditLogModel.action.in_(["chat.message.sent", "chat.message.streamed"]))
            .all()
        )

        failures = 0

        for row in rows:
            metadata = row.metadata or {}

            if not isinstance(metadata, dict):
                continue

            rag_enabled = metadata.get("rag_enabled") is True
            sources = metadata.get("sources") or []

            if rag_enabled and len(sources) == 0:
                failures += 1

        return failures

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


    def _metric_number_from_metadata(self, metadata: dict | None, key: str) -> float:
        if not isinstance(metadata, dict):
            return 0.0

        value = metadata.get(key)

        if value is None:
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _message_metrics_24h(self, *, since: datetime) -> dict:
        rows = (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.created_at >= since)
            .filter(AiAuditLogModel.action.in_(["chat.message.sent", "chat.message.streamed"]))
            .all()
        )

        latencies = []
        total_tokens = 0
        estimated_cost = 0.0

        for row in rows:
            metadata = row.metadata or {}
            latency = self._metric_number_from_metadata(metadata, "latency_ms")

            if latency > 0:
                latencies.append(latency)

            total_tokens += int(
                self._metric_number_from_metadata(metadata, "total_tokens_estimated")
            )
            estimated_cost += self._metric_number_from_metadata(metadata, "estimated_cost")

        latency_avg = round(sum(latencies) / len(latencies), 2) if latencies else None

        return {
            "latencyAvgMs": latency_avg,
            "tokensUsed": total_tokens,
            "estimatedCost": round(estimated_cost, 6) if estimated_cost else None,
            "instrumentedMessages": len(rows),
        }
