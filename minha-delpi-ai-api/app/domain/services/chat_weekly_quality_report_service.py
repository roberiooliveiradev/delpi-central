"""Relatório semanal de qualidade — Playbook 10."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class ChatWeeklyQualityReportService:
    @classmethod
    def build_markdown(cls, *, summary: dict[str, Any], period_start: datetime, period_end: datetime) -> str:
        health = summary.get("health") if isinstance(summary.get("health"), dict) else {}
        feedback = summary.get("feedback") if isinstance(summary.get("feedback"), dict) else {}
        adoption = summary.get("adoption") if isinstance(summary.get("adoption"), dict) else {}
        efficiency = summary.get("efficiency") if isinstance(summary.get("efficiency"), dict) else {}
        security = summary.get("security") if isinstance(summary.get("security"), dict) else {}

        top_reasons = feedback.get("topReasons") or []
        top_intents = feedback.get("topIntents") or []
        alerts = feedback.get("alerts") or []

        lines = [
            "# Relatório Semanal de Qualidade do Chat",
            "",
            f"Período: {period_start.date().isoformat()} → {period_end.date().isoformat()}",
            "",
            "## Resumo",
            "",
            f"- Total de feedback: {feedback.get('total', 0)}",
            f"- Feedback positivo: {feedback.get('positive', 0)}",
            f"- Feedback negativo: {feedback.get('negative', 0)}",
            f"- CSAT: {cls._pct(health.get('csat'))}",
            f"- Perda de contexto reportada: {health.get('lostContextCount', 0)}",
            "",
            "## Adoção",
            "",
            f"- Usuários ativos: {adoption.get('activeUsers', 0)}",
            f"- Sessões ativas: {adoption.get('activeSessions', 0)}",
            f"- Mensagens enviadas: {adoption.get('messagesSent', 0)}",
            f"- Cliques em chips: {adoption.get('interactivityClicks', 0)}",
            "",
            "## Eficiência",
            "",
            f"- Latência média (ms): {efficiency.get('latencyAvgMs', '—')}",
            f"- Mensagens por sessão: {efficiency.get('messagesPerSession', '—')}",
            f"- Tokens estimados: {efficiency.get('tokensUsed', '—')}",
            "",
            "## Segurança",
            "",
            f"- Entradas bloqueadas: {security.get('blockedCount', 0)}",
            f"- Entradas sinalizadas: {security.get('flaggedCount', 0)}",
            "",
            "## Top 5 motivos de feedback",
            "",
        ]

        if top_reasons:
            for row in top_reasons:
                if isinstance(row, dict):
                    lines.append(f"- {row.get('key')}: {row.get('count')}")
        else:
            lines.append("- Nenhum feedback no período.")

        lines.extend(["", "## Top 5 intents com feedback", ""])

        if top_intents:
            for row in top_intents:
                if isinstance(row, dict):
                    lines.append(f"- {row.get('key')}: {row.get('count')}")
        else:
            lines.append("- —")

        lines.extend(["", "## Alertas", ""])

        if alerts:
            for alert in alerts:
                if isinstance(alert, dict):
                    lines.append(f"- {alert.get('message')}")
        else:
            lines.append("- Nenhum alerta crítico.")

        lines.extend(
            [
                "",
                "## Melhorias recomendadas",
                "",
                "- Revisar motivos recorrentes e criar testes de regressão.",
                "- Priorizar perda de contexto e consultas erradas.",
                "- Validar adoção de chips e apresentação rica.",
                "",
            ]
        )

        return "\n".join(lines)

    @classmethod
    def default_period(cls) -> tuple[datetime, datetime]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)
        return start, end

    @classmethod
    def _pct(cls, value: object) -> str:
        if not isinstance(value, (int, float)):
            return "—"

        return f"{round(float(value) * 100)}%"
