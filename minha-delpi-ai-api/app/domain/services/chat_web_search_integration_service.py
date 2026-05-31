"""Integração pesquisa web com anexos e dados internos — Playbook Fase 4."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


@dataclass(frozen=True)
class WebSearchIntegration:
    mode: str
    product_code: str | None = None
    attachment_label: str | None = None
    extra_queries: tuple[str, ...] = ()
    synthesis_note: str = ""
    allow_operational_companion: bool = False

    def merge_queries(self, queries: tuple[str, ...]) -> tuple[str, ...]:
        ordered = list(queries)

        for candidate in self.extra_queries:
            cleaned = str(candidate or "").strip()

            if cleaned and cleaned not in ordered:
                ordered.append(cleaned)

        return tuple(ordered)


class ChatWebSearchIntegrationService:
    _ATTACHMENT_TERMS = (
        "anexo",
        "anexado",
        "anexada",
        "arquivo anex",
        "datasheet anex",
        "pdf anex",
        "compare esse",
        "comparar esse",
        "com esse arquivo",
        "com o arquivo",
    )

    _INTERNAL_PRODUCT_TERMS = (
        "nosso produto",
        "produto interno",
        "consulte nosso",
        "consulte o produto",
        "no erp",
        "no sistema",
        "codigo interno",
        "código interno",
        "sku interno",
    )

    _SOURCE_COMPARE_TERMS = (
        "compare fontes",
        "comparar fontes",
        "cruzar fontes",
        "cruze fontes",
        "divergencia entre fontes",
        "divergência entre fontes",
        "fontes divergem",
    )

    _TECHNICAL_TABLE_TERMS = (
        "tabela comparativa",
        "tabela tecnica",
        "tabela técnica",
        "especificacoes tecnicas",
        "especificações técnicas",
        "parametros tecnicos",
        "parâmetros técnicos",
        "ficha tecnica compar",
        "ficha técnica compar",
    )

    _BRAND_IN_TEXT = re.compile(
        r"\b(weg|siemens|schneider|abb|rockwell|omron|festo)\b",
        re.IGNORECASE,
    )

    @classmethod
    def resolve(
        cls,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
    ) -> WebSearchIntegration | None:
        raw = str(message or "").strip()

        if not raw or not ChatWebSearchIntentService.matches(raw):
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(raw) or raw
        attachment_text = str(attachment_context or "").strip()
        product_code = ChatProductQueryIntentService.resolve_product_code(
            raw,
            previous_messages=previous_messages,
        )

        if cls._matches_attachment_hybrid(normalized, attachment_text):
            return cls._build_attachment_integration(
                raw,
                normalized,
                attachment_text=attachment_text,
                product_code=product_code,
            )

        if product_code and cls._matches_internal_product_hybrid(normalized):
            return cls._build_internal_product_integration(
                raw,
                product_code=product_code,
            )

        if any(term in normalized for term in cls._SOURCE_COMPARE_TERMS):
            return WebSearchIntegration(
                mode="source_compare",
                synthesis_note=cls._source_compare_synthesis_note(),
            )

        if any(term in normalized for term in cls._TECHNICAL_TABLE_TERMS):
            return WebSearchIntegration(
                mode="technical_table",
                synthesis_note=cls._technical_table_synthesis_note(),
            )

        return None

    @classmethod
    def should_allow_operational_companion(cls, message: str) -> bool:
        integration = cls.resolve(message)

        return bool(integration and integration.allow_operational_companion)

    @classmethod
    def apply_to_payload(cls, payload: dict | None, integration: WebSearchIntegration | None) -> dict | None:
        if not isinstance(payload, dict) or not integration:
            return payload

        payload = {**payload, "integrationMode": integration.mode}

        if integration.product_code:
            payload["integrationProductCode"] = integration.product_code

        if integration.attachment_label:
            payload["integrationAttachment"] = integration.attachment_label

        return payload

    @classmethod
    def format_integration_footer(cls, payload: dict | None) -> str | None:
        if not isinstance(payload, dict):
            return None

        mode = str(payload.get("integrationMode") or "").strip()

        if mode == "internal_product":
            code = str(payload.get("integrationProductCode") or "").strip()

            if code:
                return (
                    "\n\n---\n"
                    f"*Integração interna + web:* o código **{code}** veio da sua mensagem. "
                    "Dados do ERP têm prioridade; use a web só como complemento público."
                )

        if mode == "attachment_compare":
            label = str(payload.get("integrationAttachment") or "anexo").strip()

            return (
                "\n\n---\n"
                f"*Integração anexo + web:* compare o conteúdo de **{label}** com as fontes "
                "listadas e destaque divergências antes de decidir."
            )

        if mode == "source_compare":
            evaluation = payload.get("sourceEvaluation") or {}
            types = evaluation.get("sourceTypes") or []

            if isinstance(types, list) and len(types) >= 2:
                joined = ", ".join(str(item) for item in types[:4])

                return (
                    "\n\n---\n"
                    f"*Comparação de fontes:* tipos encontrados — {joined}. "
                    "Se houver conflito, priorize fabricante/oficial."
                )

        return None

    @classmethod
    def _matches_attachment_hybrid(cls, normalized: str, attachment_text: str) -> bool:
        if attachment_text:
            return True

        return any(term in normalized for term in cls._ATTACHMENT_TERMS)

    @classmethod
    def _matches_internal_product_hybrid(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._INTERNAL_PRODUCT_TERMS):
            return True

        return "produto" in normalized and any(
            term in normalized for term in ("consulte", "pesquise", "busque", "compare", "cruze")
        )

    @classmethod
    def _build_attachment_integration(
        cls,
        message: str,
        normalized: str,
        *,
        attachment_text: str,
        product_code: str | None,
    ) -> WebSearchIntegration:
        label = cls._attachment_label(attachment_text)
        brands = cls._extract_brands(f"{message} {attachment_text[:1200]}")
        extra: list[str] = []

        if product_code:
            extra.append(f"{product_code} datasheet oficial")

        for brand in brands[:2]:
            extra.append(f"{brand} datasheet site oficial pdf")

        if label and not extra:
            extra.append(f"{label} datasheet oficial pdf")

        return WebSearchIntegration(
            mode="attachment_compare",
            product_code=product_code,
            attachment_label=label,
            extra_queries=tuple(extra),
            synthesis_note=cls._attachment_synthesis_note(label),
        )

    @classmethod
    def _build_internal_product_integration(
        cls,
        message: str,
        *,
        product_code: str,
    ) -> WebSearchIntegration:
        brands = cls._extract_brands(message)
        extra = [f"{product_code} datasheet pdf", f"{product_code} ficha tecnica"]

        if brands:
            domain = {"weg": "weg.net", "siemens": "siemens.com"}.get(brands[0].lower())

            if domain:
                extra.append(f"site:{domain} {product_code} datasheet")

        return WebSearchIntegration(
            mode="internal_product",
            product_code=product_code,
            extra_queries=tuple(extra),
            synthesis_note=cls._internal_product_synthesis_note(product_code),
            allow_operational_companion=True,
        )

    @classmethod
    def _attachment_label(cls, attachment_text: str) -> str:
        if not attachment_text:
            return "anexo"

        for line in attachment_text.splitlines():
            cleaned = line.strip()

            if cleaned.startswith("### "):
                return cleaned.removeprefix("### ").strip() or "anexo"

        return "anexo"

    @classmethod
    def _extract_brands(cls, text: str) -> list[str]:
        found: list[str] = []

        for match in cls._BRAND_IN_TEXT.finditer(str(text or "")):
            brand = match.group(1).lower()

            if brand not in found:
                found.append(brand)

        return found

    @staticmethod
    def _attachment_synthesis_note(label: str) -> str:
        return (
            f"Há um anexo ({label}) no contexto da conversa. "
            "Cruze trechos da web com o anexo; destaque divergências e não trate o anexo "
            "como substituto de fonte oficial."
        )

    @staticmethod
    def _internal_product_synthesis_note(product_code: str) -> str:
        return (
            f"A pergunta combina dado interno (produto {product_code}) com busca pública. "
            "Nunca substitua dado interno por informação da web sem avisar; "
            "use a web para datasheet ou referência externa complementar."
        )

    @staticmethod
    def _source_compare_synthesis_note() -> str:
        return (
            "Compare fontes distintas; se divergirem, explique o conflito e indique qual "
            "tipo de fonte é mais confiável (oficial > distribuidor > fórum)."
        )

    @staticmethod
    def _technical_table_synthesis_note() -> str:
        return (
            "Quando houver especificações nos trechos, inclua tabela markdown comparativa "
            "com colunas claras (ex.: Parâmetro | Valor | Fonte)."
        )
