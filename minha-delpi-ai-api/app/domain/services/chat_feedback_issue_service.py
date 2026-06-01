"""Issues automáticas a partir de feedback recorrente — Playbook 10."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class ChatFeedbackIssueService:
    _ISSUE_TEMPLATES = {
        "context_loss": {
            "title": "Chat perde contexto em follow-ups",
            "description": (
                "Usuários reportaram perda de contexto em sequências de mensagens. "
                "Revisar ChatReferenceResolutionService e memória de sessão."
            ),
            "suggestedAction": "Adicionar teste multi-turn de herança de produto/período.",
        },
        "high_negative_rate": {
            "title": "Taxa elevada de feedback negativo",
            "description": "Mais de 35% dos feedbacks na janela foram negativos.",
            "suggestedAction": "Revisar roteamento, prompts e painel admin de qualidade.",
        },
    }

    @classmethod
    def evaluate_alerts(
        cls,
        alerts: list[dict[str, Any]] | None,
        *,
        source: str = "feedback_auto",
        feedback_summary: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        from app.infrastructure.persistence.postgres_chat_quality_issue_repository import (
            PostgresChatQualityIssueRepository,
        )

        repository = PostgresChatQualityIssueRepository()

        for alert in alerts or []:
            if not isinstance(alert, dict):
                continue

            code = str(alert.get("code") or "").strip()

            if not code:
                continue

            if repository.find_open_by_code(code):
                continue

            template = cls._template_for_code(code, alert)
            metadata = {
                "alert": alert,
                "suggestedAction": template.get("suggestedAction"),
                "feedbackSummary": cls._compact_summary(feedback_summary),
            }
            external_url = cls._maybe_create_github_issue(
                title=str(template["title"]),
                body=f"{template['description']}\n\nAlerta: {alert.get('message')}",
            )

            issue = repository.create(
                code=code,
                title=str(template["title"]),
                description=str(template["description"]),
                source=source,
                metadata=metadata,
                external_url=external_url,
            )
            created.append(issue)

        return created

    @classmethod
    def _template_for_code(cls, code: str, alert: dict[str, Any]) -> dict[str, str]:
        if code in cls._ISSUE_TEMPLATES:
            return dict(cls._ISSUE_TEMPLATES[code])

        if code.startswith("recurring_"):
            reason = code.replace("recurring_", "", 1)

            return {
                "title": f"Feedback recorrente: {reason}",
                "description": str(alert.get("message") or f"Motivo {reason} reportado repetidamente."),
                "suggestedAction": f"Criar teste de regressão para motivo `{reason}`.",
            }

        return {
            "title": f"Alerta de qualidade: {code}",
            "description": str(alert.get("message") or code),
            "suggestedAction": "Investigar no painel admin de qualidade.",
        }

    @classmethod
    def _compact_summary(cls, feedback_summary: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(feedback_summary, dict):
            return {}

        return {
            "csat": feedback_summary.get("csat"),
            "totalFeedback": feedback_summary.get("totalFeedback"),
            "negativeCount": feedback_summary.get("negativeCount"),
            "lostContextCount": feedback_summary.get("lostContextCount"),
        }

    @classmethod
    def _maybe_create_github_issue(cls, *, title: str, body: str) -> str | None:
        token = os.getenv("CHAT_QUALITY_GITHUB_TOKEN", "").strip()
        repo = os.getenv("CHAT_QUALITY_GITHUB_REPO", "").strip()

        if not token or not repo or "/" not in repo:
            return None

        payload = json.dumps({"title": title[:240], "body": body[:8000]}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "minha-delpi-chat-quality-bot",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

        html_url = parsed.get("html_url")

        return str(html_url).strip() if html_url else None
