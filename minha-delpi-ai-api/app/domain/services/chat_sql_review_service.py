"""Revisão estruturada de SQL colado — Playbook Especialista SQL Avançado §48."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)
from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService


class ChatSqlReviewService:
    _JOIN = re.compile(r"\b(left|right|inner|full|cross)?\s*join\b", re.IGNORECASE)
    _GROUP_BY = re.compile(r"\bgroup\s+by\b", re.IGNORECASE)
    _HAVING = re.compile(r"\bhaving\b", re.IGNORECASE)
    _AGG = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.IGNORECASE)

    @classmethod
    def review(cls, sql: str | None, *, dialect: str = "generic") -> dict[str, Any]:
        text = ChatSqlPerformanceAdvisorService.extract_sql_block(sql) or str(sql or "").strip()

        if not text:
            return {"checklist": [], "riskLevel": "unknown", "blocked": False}

        checklist: list[dict[str, str]] = []
        blocked = ChatSqlSafetyService.contains_destructive_sql(text)

        if blocked:
            checklist.append(
                {
                    "item": "seguranca",
                    "status": "fail",
                    "detail": "Comando destrutivo ou administrativo detectado.",
                }
            )
        else:
            checklist.append(
                {
                    "item": "seguranca",
                    "status": "pass",
                    "detail": "Somente leitura (SELECT) ou equivalente seguro.",
                }
            )

        if re.search(r"\bselect\b", text, re.IGNORECASE):
            checklist.append(
                {
                    "item": "sintaxe_basica",
                    "status": "pass",
                    "detail": "Estrutura SELECT identificada.",
                }
            )
        else:
            checklist.append(
                {
                    "item": "sintaxe_basica",
                    "status": "fail",
                    "detail": "Não foi possível identificar um SELECT válido.",
                }
            )

        if cls._JOIN.search(text):
            checklist.append(
                {
                    "item": "joins",
                    "status": "warn",
                    "detail": "Joins presentes — valide chaves e risco de duplicidade 1:N.",
                }
            )

        if cls._AGG.search(text) and not cls._GROUP_BY.search(text):
            checklist.append(
                {
                    "item": "agregacao",
                    "status": "fail",
                    "detail": "Agregação sem GROUP BY explícito.",
                }
            )
        elif cls._GROUP_BY.search(text):
            checklist.append(
                {
                    "item": "agregacao",
                    "status": "pass",
                    "detail": "GROUP BY presente.",
                }
            )

        if cls._HAVING.search(text) and not cls._GROUP_BY.search(text):
            checklist.append(
                {
                    "item": "having",
                    "status": "fail",
                    "detail": "HAVING sem GROUP BY.",
                }
            )

        performance = ChatSqlPerformanceAdvisorService.analyze(text, dialect=dialect)

        for issue in performance.get("issues") or []:
            checklist.append(
                {
                    "item": str(issue.get("code") or "performance"),
                    "status": "warn" if issue.get("severity") == "warn" else "info",
                    "detail": str(issue.get("message") or ""),
                }
            )

        fail_count = sum(1 for item in checklist if item["status"] == "fail")
        warn_count = sum(1 for item in checklist if item["status"] == "warn")

        if blocked or fail_count:
            risk = "high"
        elif warn_count:
            risk = "medium"
        else:
            risk = "low"

        return {
            "checklist": checklist,
            "riskLevel": risk,
            "blocked": blocked,
            "dialect": dialect,
            "performanceScore": performance.get("score"),
        }
