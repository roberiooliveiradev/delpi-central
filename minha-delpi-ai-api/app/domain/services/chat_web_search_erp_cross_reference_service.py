"""Cruzamento automático ERP × pesquisa web — Playbook pesquisa web, Fase 4."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatWebSearchErpCrossReferenceService:
    @classmethod
    def should_cross_reference(
        cls,
        *,
        internal_data: object | None,
        web_payload: dict | None,
        message: str = "",
    ) -> bool:
        if not isinstance(web_payload, dict):
            return False

        if str(web_payload.get("searchStatus") or "") != "success":
            return False

        if internal_data is None:
            return False

        if str(web_payload.get("integrationMode") or "") == "internal_product":
            return True

        product = cls.extract_product_summary(internal_data)

        if not product:
            return False

        code = str(product.get("code") or "").strip()
        message_code = ChatProductQueryIntentService.extract_product_code(message)

        return bool(code and message_code and code == message_code)

    @classmethod
    def enrich_payload(
        cls,
        payload: dict | None,
        internal_data: object | None,
    ) -> dict | None:
        if not isinstance(payload, dict) or internal_data is None:
            return payload

        product = cls.extract_product_summary(internal_data)

        if not product:
            return payload

        web_highlights = cls._web_highlights(payload)
        payload = {
            **payload,
            "erpCrossReference": {
                "productCode": product.get("code"),
                "description": product.get("description"),
                "brand": product.get("brand"),
                "webHighlights": web_highlights,
            },
        }

        return payload

    @classmethod
    def format_cross_reference_block(cls, payload: dict | None) -> str | None:
        if not isinstance(payload, dict):
            return None

        cross = payload.get("erpCrossReference")

        if not isinstance(cross, dict):
            return None

        code = str(cross.get("productCode") or "").strip()
        description = str(cross.get("description") or "").strip()
        brand = str(cross.get("brand") or "").strip()
        highlights = cross.get("webHighlights") or []

        lines = ["", "## Cruzamento ERP × web", ""]

        if code or description:
            internal_line = "**Dado interno (ERP):**"

            if code:
                internal_line += f" produto `{code}`"

            if description:
                internal_line += f" — {description}"

            if brand:
                internal_line += f" ({brand})"

            lines.append(internal_line)

        if isinstance(highlights, list) and highlights:
            lines.append("")
            lines.append("**Referências públicas encontradas:**")

            for item in highlights[:4]:
                if not isinstance(item, dict):
                    continue

                title = str(item.get("title") or "Fonte").strip()
                url = str(item.get("url") or "").strip()
                official = item.get("isOfficial") is True
                tag = " (oficial)" if official else ""

                if url:
                    lines.append(f"- [{title}]({url}){tag}")
                else:
                    lines.append(f"- {title}{tag}")

        lines.append("")
        lines.append(
            "*O cadastro interno tem prioridade; use a web como complemento "
            "(datasheet, manual, norma) e valide divergências antes de decisões críticas.*"
        )

        return "\n".join(lines).strip()

    @classmethod
    def append_to_direct_answer(
        cls,
        *,
        direct_answer: str | None,
        internal_data: object | None,
        web_payload: dict | None,
        message: str = "",
    ) -> tuple[str | None, dict | None]:
        if not cls.should_cross_reference(
            internal_data=internal_data,
            web_payload=web_payload,
            message=message,
        ):
            return direct_answer, web_payload

        enriched = cls.enrich_payload(web_payload, internal_data) or web_payload
        block = cls.format_cross_reference_block(enriched)

        if not block:
            return direct_answer, enriched

        if direct_answer:
            return f"{direct_answer.rstrip()}\n\n{block}", enriched

        return block, enriched

    @classmethod
    def extract_product_summary(cls, data: object | None) -> dict[str, str] | None:
        if data is None:
            return None

        if isinstance(data, dict):
            direct = cls._product_from_mapping(data)

            if direct:
                return direct

            for value in data.values():
                found = cls.extract_product_summary(value)

                if found:
                    return found

            return None

        if isinstance(data, list):
            for item in data:
                found = cls.extract_product_summary(item)

                if found:
                    return found

        return None

    @classmethod
    def _product_from_mapping(cls, mapping: dict) -> dict[str, str] | None:
        code = cls._first_string(
            mapping,
            "code",
            "product_code",
            "productCode",
            "sku",
            "X3_CODIGO",
        )
        description = cls._first_string(
            mapping,
            "description",
            "product_description",
            "name",
            "title",
            "X3_DESCRIC",
        )
        brand = cls._first_string(mapping, "brand", "manufacturer", "fabricante", "marca")

        if not code and not description:
            product = mapping.get("product")

            if isinstance(product, dict):
                return cls._product_from_mapping(product)

            return None

        return {
            "code": code or "",
            "description": description or "",
            "brand": brand or "",
        }

    @classmethod
    def _web_highlights(cls, payload: dict) -> list[dict]:
        results = payload.get("results")

        if not isinstance(results, list):
            return []

        highlights: list[dict] = []

        for item in results[:4]:
            if not isinstance(item, dict):
                continue

            url = str(item.get("url") or "").strip()

            if not url:
                continue

            highlights.append(
                {
                    "title": str(item.get("title") or url).strip(),
                    "url": url,
                    "isOfficial": item.get("isOfficial") is True,
                }
            )

        return highlights

    @staticmethod
    def _first_string(mapping: dict, *keys: str) -> str:
        for key in keys:
            value = mapping.get(key)

            if value is None:
                continue

            cleaned = str(value).strip()

            if cleaned:
                return cleaned

        return ""
