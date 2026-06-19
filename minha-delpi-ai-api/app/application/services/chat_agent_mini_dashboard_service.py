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

        panels: list[dict[str, Any]] = [
            {"id": "usage-kpi", "title": "Indicadores", "presentation": kpi_panel},
            {
                "id": "activity-bar",
                "title": "Volume",
                "presentation": activity_chart,
            },
        ]

        user_ranking_panel = cls._build_user_ranking_panel(stats)
        if user_ranking_panel is not None:
            panels.append(
                {
                    "id": "user-ranking",
                    "title": "Ranking de usuários",
                    "presentation": user_ranking_panel,
                }
            )

        return {
            "type": "dashboard",
            "title": "Painel do agente",
            "panels": panels,
        }

    @classmethod
    def _build_user_ranking_panel(cls, stats: dict[str, Any]) -> dict[str, Any] | None:
        raw_ranking = stats.get("userRanking")
        if not isinstance(raw_ranking, list) or not raw_ranking:
            return None

        rows: list[dict[str, Any]] = []

        for index, entry in enumerate(raw_ranking, start=1):
            if not isinstance(entry, dict):
                continue

            rows.append(
                {
                    "rank": index,
                    "user": cls._user_display_label(entry),
                    "messages": int(entry.get("messages") or 0),
                    "sessions": int(entry.get("sessions") or 0),
                }
            )

        if not rows:
            return None

        return {
            "type": "table",
            "title": "Ranking de usuários",
            "columns": [
                {"key": "rank", "label": "#", "dataType": "number"},
                {"key": "user", "label": "Usuário", "dataType": "text"},
                {"key": "messages", "label": "Mensagens", "dataType": "number"},
                {"key": "sessions", "label": "Conversas", "dataType": "number"},
            ],
            "rows": rows,
        }

    @classmethod
    def _user_display_label(cls, entry: dict[str, Any]) -> str:
        name = str(entry.get("userName") or "").strip()
        email = str(entry.get("userEmail") or "").strip()

        if name and email:
            return f"{name} ({email})"

        if name:
            return name

        if email:
            return email

        user_id = str(entry.get("userId") or "").strip()
        if user_id:
            return f"Usuário {user_id[:8]}…"

        return "Usuário desconhecido"

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
