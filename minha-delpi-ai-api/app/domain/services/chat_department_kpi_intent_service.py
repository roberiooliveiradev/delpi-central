"""Heurísticas de seleção para KPIs departamentais (comercial, financeiro, produção, RH, qualidade)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@dataclass(frozen=True)
class DepartmentKpiMatch:
    path_token: str
    domain_prefix: str
    reason: str
    operation_hint: str = ""


def invalidate_department_kpi_rules_cache() -> None:
    _rules_content.cache_clear()


@lru_cache(maxsize=1)
def _rules_content() -> list[tuple[str, str, tuple[str, ...], tuple[str, ...], str]]:
    bundle = ChatAssistantContentService.load_bundle("department_kpi_rules")
    rules = bundle.get("rules")

    if not isinstance(rules, list):
        return ()

    normalized_rules: list[tuple[str, str, tuple[str, ...], tuple[str, ...], str]] = []

    for rule in rules:
        if not isinstance(rule, dict):
            continue

        domain_prefix = str(rule.get("domainPrefix") or "").strip()
        path_token = str(rule.get("pathToken") or "").strip()
        label = str(rule.get("label") or "").strip()
        keywords = rule.get("keywords") or []
        excludes = rule.get("excludes") or []

        if not domain_prefix or not path_token or not label:
            continue

        normalized_rules.append(
            (
                domain_prefix,
                path_token,
                tuple(str(item).strip() for item in keywords if str(item).strip()),
                tuple(str(item).strip() for item in excludes if str(item).strip()),
                label,
            )
        )

    return tuple(normalized_rules)


class ChatDepartmentKpiIntentService:
    """Mapeia perguntas em português para tokens de path da api-delpi (sem código de produto)."""

    @classmethod
    def _rules(cls) -> tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], str], ...]:
        return _rules_content()

    @classmethod
    def resolve(cls, message: str) -> DepartmentKpiMatch | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        if cls._has_product_code(normalized):
            return None

        if cls._looks_like_supplies_domain(normalized):
            return None

        best: DepartmentKpiMatch | None = None
        best_score = 0

        for domain_prefix, path_token, keywords, excludes, label in cls._rules():
            if any(exclude in normalized for exclude in excludes):
                continue

            score = sum(2 for keyword in keywords if keyword in normalized)

            if score <= 0:
                continue

            if "otd" in normalized and "/supplies/" in domain_prefix:
                continue

            if score > best_score:
                best_score = score
                best = DepartmentKpiMatch(
                    path_token=path_token,
                    domain_prefix=domain_prefix,
                    reason=f"A pergunta solicita {label}.",
                    operation_hint=label,
                )

        return best

    @classmethod
    def _has_product_code(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        return bool(ChatProductQueryIntentService.extract_product_code(normalized))

    @classmethod
    def _looks_like_supplies_domain(cls, normalized: str) -> bool:
        supplies_terms = (
            "cpv",
            "giro de estoque",
            "idd",
            "inventory-turnover",
            "valor total de estoque",
            "estoque da empresa",
            "estoque total",
        )

        if any(term in normalized for term in supplies_terms):
            return True

        if "otd" in normalized and any(
            term in normalized for term in ("compra", "fornecedor", "suprimentos")
        ):
            return True

        return False
