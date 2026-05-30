from datetime import datetime, timedelta, timezone

from app.application.services.llm_cost_estimator_service import LlmCostEstimatorService
from app.domain.ports.admin_metrics_repository_port import AdminMetricsRepositoryPort
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.infrastructure.db.models.audit_log_model import AiAuditLogModel
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel
from app.infrastructure.db.models.knowledge_chunk_model import AiKnowledgeChunkModel
from app.infrastructure.db.models.knowledge_document_model import AiKnowledgeDocumentModel


class PostgresAdminMetricsRepository(AdminMetricsRepositoryPort):
    def get_summary(self, *, hours: int = 24) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)

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

        message_metrics = self._message_metrics_window(since=since)
        rag_failures = self._rag_failures_window(since=since)
        agent_metrics = self._agent_metrics_window(since=since)
        user_profile_metrics = self._user_profile_metrics_window(since=since)
        rag_test_metrics = self._rag_test_metrics_window(since=since)
        cost_estimator = LlmCostEstimatorService()

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
            "windowHours": safe_hours,
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
                "assertivenessRate": rag_test_metrics["assertivenessRate"],
                "ragTests24h": rag_test_metrics["totalTests"],
                "ragTestsAssertive24h": rag_test_metrics["assertiveTests"],
                "agentMetrics": agent_metrics,
                "userProfileMetrics": user_profile_metrics,
                "costTable": cost_estimator.list_cost_table(),
                "costBreakdown24h": message_metrics["costBreakdown24h"],
                "notes": [
                    "Latência e tokens são estimativas registradas no fluxo de mensagens.",
                    "Assertividade RAG considera score mínimo "
                    f"{Settings.RAG_ASSERTIVENESS_MIN_SCORE} e chunks recuperados nos testes.",
                    "Tabela de custo: env (LLM_COST_TABLE_JSON) ou painel admin (persistida no banco).",
                    f"Janela analisada: últimas {safe_hours} horas.",
                ],
            },
        }

    def get_timeseries(self, *, hours: int = 168, bucket_hours: int = 24) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        safe_bucket = max(1, min(int(bucket_hours), safe_hours))
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=safe_hours)

        buckets: list[dict] = []
        cursor = start

        while cursor < end:
            bucket_end = min(cursor + timedelta(hours=safe_bucket), end)
            since = cursor

            message_metrics = self._message_metrics_window(since=since, until=bucket_end)
            audit_count = (
                db.session.query(AiAuditLogModel)
                .filter(AiAuditLogModel.created_at >= since)
                .filter(AiAuditLogModel.created_at < bucket_end)
                .count()
            )

            buckets.append(
                {
                    "start": since.isoformat(),
                    "end": bucket_end.isoformat(),
                    "auditLogs": audit_count,
                    "messagesInstrumented": message_metrics["instrumentedMessages"],
                    "tokensUsed": message_metrics["tokensUsed"],
                    "estimatedCost": message_metrics["estimatedCost"],
                    "latencyAvgMs": message_metrics["latencyAvgMs"],
                }
            )

            cursor = bucket_end

        return {
            "windowHours": safe_hours,
            "bucketHours": safe_bucket,
            "buckets": buckets,
        }


    def _apply_created_at_filters(self, query, *, since: datetime, until: datetime | None = None):
        query = query.filter(AiAuditLogModel.created_at >= since)

        if until is not None:
            query = query.filter(AiAuditLogModel.created_at < until)

        return query

    def _rag_failures_window(self, *, since: datetime, until: datetime | None = None) -> int:
        query = db.session.query(AiAuditLogModel).filter(
            AiAuditLogModel.action.in_(["chat.message.sent", "chat.message.streamed"])
        )
        rows = self._apply_created_at_filters(query, since=since, until=until).all()

        failures = 0

        for row in rows:
            metadata = row.audit_metadata or {}

            if not isinstance(metadata, dict):
                continue

            rag_enabled = metadata.get("rag_enabled") is True
            sources = metadata.get("sources") or []

            if rag_enabled and len(sources) == 0:
                failures += 1

        return failures

    def _user_profile_metrics_window(
        self,
        *,
        since: datetime,
        until: datetime | None = None,
    ) -> list[dict]:
        query = db.session.query(AiAuditLogModel).filter(AiAuditLogModel.user_id.isnot(None))
        rows = self._apply_created_at_filters(query, since=since, until=until).all()

        counts: dict[str, int] = {}

        for row in rows:
            user_key = str(row.user_id)
            counts[user_key] = counts.get(user_key, 0) + 1

        return [
            {"key": key, "count": count}
            for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

    def _rag_test_metrics_window(
        self,
        *,
        since: datetime,
        until: datetime | None = None,
    ) -> dict:
        query = db.session.query(AiAuditLogModel).filter(
            AiAuditLogModel.action == "admin.rag.tested"
        )
        rows = self._apply_created_at_filters(query, since=since, until=until).all()

        total_tests = len(rows)
        assertive_tests = 0

        for row in rows:
            metadata = row.audit_metadata or {}

            if not isinstance(metadata, dict):
                continue

            if metadata.get("assertive") is True:
                assertive_tests += 1
                continue

            score = self._metric_number_from_metadata(metadata, "score")
            chunk_count = int(self._metric_number_from_metadata(metadata, "chunk_count"))

            if score >= Settings.RAG_ASSERTIVENESS_MIN_SCORE and chunk_count > 0:
                assertive_tests += 1

        assertiveness_rate = (
            round(assertive_tests / total_tests, 4) if total_tests > 0 else None
        )

        return {
            "totalTests": total_tests,
            "assertiveTests": assertive_tests,
            "assertivenessRate": assertiveness_rate,
        }

    def _agent_metrics_window(
        self,
        *,
        since: datetime,
        until: datetime | None = None,
    ) -> list[dict]:
        query = db.session.query(AiAuditLogModel).filter(
            AiAuditLogModel.action.in_(["chat.message.sent", "chat.message.streamed"])
        )
        rows = self._apply_created_at_filters(query, since=since, until=until).all()

        counts: dict[str, int] = {}

        for row in rows:
            metadata = row.audit_metadata or {}

            if not isinstance(metadata, dict):
                continue

            agent_id = metadata.get("agentId") or "sem_agente"
            counts[str(agent_id)] = counts.get(str(agent_id), 0) + 1

        return [
            {"key": key, "count": count}
            for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

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

    def _message_metrics_window(
        self,
        *,
        since: datetime,
        until: datetime | None = None,
    ) -> dict:
        query = db.session.query(AiAuditLogModel).filter(
            AiAuditLogModel.action.in_(["chat.message.sent", "chat.message.streamed"])
        )
        rows = self._apply_created_at_filters(query, since=since, until=until).all()

        latencies = []
        total_tokens = 0
        estimated_cost = 0.0
        cost_breakdown: dict[str, dict] = {}

        for row in rows:
            metadata = row.audit_metadata or {}
            latency = self._metric_number_from_metadata(metadata, "latency_ms")

            if latency > 0:
                latencies.append(latency)

            total_tokens += int(
                self._metric_number_from_metadata(metadata, "total_tokens_estimated")
            )
            estimated_cost += self._metric_number_from_metadata(metadata, "estimated_cost")

            provider = str(metadata.get("provider") or Settings.LLM_PROVIDER)
            model = str(
                metadata.get("model")
                or (
                    Settings.VLLM_MODEL
                    if provider == "vllm"
                    else Settings.OLLAMA_MODEL
                )
            )
            breakdown_key = f"{provider}::{model}"
            bucket = cost_breakdown.setdefault(
                breakdown_key,
                {
                    "provider": provider,
                    "model": model,
                    "messages": 0,
                    "tokensUsed": 0,
                    "estimatedCost": 0.0,
                },
            )
            bucket["messages"] += 1
            bucket["tokensUsed"] += int(
                self._metric_number_from_metadata(metadata, "total_tokens_estimated")
            )
            bucket["estimatedCost"] += self._metric_number_from_metadata(
                metadata,
                "estimated_cost",
            )

        latency_avg = round(sum(latencies) / len(latencies), 2) if latencies else None

        breakdown_items = [
            {
                "provider": item["provider"],
                "model": item["model"],
                "messages": item["messages"],
                "tokensUsed": int(item["tokensUsed"]),
                "estimatedCost": round(item["estimatedCost"], 6)
                if item["estimatedCost"]
                else None,
            }
            for item in sorted(
                cost_breakdown.values(),
                key=lambda entry: entry["estimatedCost"],
                reverse=True,
            )
        ]

        return {
            "latencyAvgMs": latency_avg,
            "tokensUsed": total_tokens,
            "estimatedCost": round(estimated_cost, 6) if estimated_cost else None,
            "instrumentedMessages": len(rows),
            "costBreakdown24h": breakdown_items,
        }
