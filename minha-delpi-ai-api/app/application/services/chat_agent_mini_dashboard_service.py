"""Mini dashboard e recomendações por agente — Playbook gráficos Fase 4."""

from __future__ import annotations

from typing import Any


class ChatAgentMiniDashboardService:
    @classmethod
    def build_dashboard(cls, stats: dict[str, Any]) -> dict[str, Any]:
        window_hours = int(stats.get("windowHours") or 168)
        window_days = max(1, round(window_hours / 24))
        sessions = int(stats.get("sessionsInWindow") or 0)
        messages = int(stats.get("messagesInWindow") or 0)
        total_sessions = int(stats.get("totalSessions") or 0)
        providers = int(stats.get("actionProvidersCount") or 0)
        shares = int(stats.get("sharesCount") or 0)

        msgs_per_session = round(messages / sessions, 1) if sessions else 0.0

        kpi_panel = {
            "type": "kpi",
            "title": f"Uso ({window_days} dias)",
            "cards": [
                {"label": "Conversas no período", "value": sessions},
                {"label": "Mensagens no período", "value": messages},
                {"label": "Total de conversas", "value": total_sessions},
                {"label": "Providers/actions", "value": providers},
                {"label": "Compartilhamentos", "value": shares},
                {
                    "label": "Mensagens / conversa",
                    "value": msgs_per_session if sessions else "—",
                },
            ],
        }

        activity_chart = {
            "type": "chart",
            "title": "Atividade na janela",
            "chartType": "bar",
            "data": [
                {"metric": "Conversas", "value": sessions},
                {"metric": "Mensagens", "value": messages},
            ],
            "config": {
                "xAxis": "metric",
                "yAxis": "value",
                "legend": False,
            },
        }

        return {
            "type": "dashboard",
            "title": "Painel do agente",
            "panels": [
                {"id": "usage-kpi", "title": "Indicadores", "presentation": kpi_panel},
                {
                    "id": "activity-bar",
                    "title": "Volume",
                    "presentation": activity_chart,
                },
            ],
        }

    @classmethod
    def build_recommendations(
        cls,
        stats: dict[str, Any],
        *,
        specialization: dict[str, Any] | None = None,
    ) -> list[str]:
        items: list[str] = []

        sessions = int(stats.get("sessionsInWindow") or 0)
        messages = int(stats.get("messagesInWindow") or 0)
        providers = int(stats.get("actionProvidersCount") or 0)

        spec = specialization if isinstance(specialization, dict) else {}
        spec_enabled = bool(spec.get("enabled"))
        allowed_tools = spec.get("allowedTools") if isinstance(spec.get("allowedTools"), list) else []

        if sessions == 0:
            items.append(
                "Nenhuma conversa na janela — teste na aba Simulação ou compartilhe o agente com a equipe."
            )

        if providers == 0:
            items.append(
                "Sem providers/actions vinculados — configure integrações no builder do agente."
            )

        if sessions > 0 and messages / sessions > 40:
            items.append(
                "Muitas mensagens por conversa — revise prompt, skills ou escopo de conhecimento."
            )

        if spec_enabled is False and specialization is not None:
            items.append(
                "Especialização desligada — ative um preset para focar RAG e diretrizes do domínio."
            )

        if spec_enabled and not allowed_tools:
            items.append(
                "Especialização sem tools permitidas — o agente depende só de conhecimento interno."
            )

        if not items:
            items.append(
                "Uso dentro do esperado — acompanhe tendências em Qualidade → Métricas no admin."
            )

        return items[:4]
