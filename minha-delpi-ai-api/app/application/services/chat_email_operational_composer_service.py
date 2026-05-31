"""E-mail corporativo montado somente com dados de consultas autorizadas (Fase 5)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_email_intent_service import ChatEmailIntentService


class ChatEmailOperationalComposerService:
    @classmethod
    def build_from_summary(
        cls,
        summary: dict,
        message: str,
    ) -> dict[str, Any] | None:
        title = str(summary.get("titulo") or "").strip()
        lines = [
            str(line).strip()
            for line in (summary.get("linhas") or [])
            if str(line or "").strip()
        ][:12]
        path = str(summary.get("path") or "").strip()

        if not title and not lines:
            return None

        product_code = cls._extract_product_code(summary, lines, message)
        subject = cls._infer_subject(title or "Consulta operacional", product_code, message)
        recipient = ChatEmailIntentService.extract_context(message).get("recipient")
        greeting = cls._greeting(recipient, message)
        intro = cls._intro_line(title, product_code, message)
        audience = ChatEmailIntentService.extract_context(message).get("audience")

        body_lines = [greeting, "", intro, ""]

        if lines:
            body_lines.append("Com base na consulta realizada na plataforma, seguem os principais pontos:")
            body_lines.append("")
            body_lines.extend(f"- {line}" for line in lines)
        else:
            body_lines.append(
                "- Os detalhes completos estão na consulta operacional desta conversa."
            )

        body_lines.extend(
            [
                "",
                "Fico à disposição para complementar ou detalhar por filial, se necessário.",
                "",
                "Atenciosamente,",
                "",
                "[Seu nome]",
                "",
                "---",
                cls._source_footer(title, path),
            ]
        )

        body = "\n".join(body_lines)
        text = f"Assunto: {subject}\n\n{body}"

        return {
            "text": text,
            "subject": subject,
            "textTask": {
                "type": "email",
                "subtype": "email_create",
                "source": "operational_data",
                "recipient": recipient,
                "audience": audience,
                "tone": ChatEmailIntentService.extract_context(message).get("tone"),
                "subject": subject,
                "inventedFieldsPrevented": True,
                "missingFields": ["senderName"] if not ChatEmailIntentService.extract_context(message).get("senderSignature") else [],
            },
            "dataSource": {
                "title": title,
                "path": path or None,
                "productCode": product_code,
                "lineCount": len(lines),
            },
        }

    @classmethod
    def _greeting(cls, recipient: str | None, message: str) -> str:
        lowered = (message or "").lower()

        if recipient:
            return f"Prezado(a) {recipient},"

        if "fornecedor" in lowered:
            return "Prezado(a),"

        return "Prezados(as),"

    @classmethod
    def _intro_line(cls, title: str, product_code: str | None, message: str) -> str:
        lowered = (message or "").lower()
        topic = title.lower()

        if "compras" in lowered:
            return (
                f"Gostaria de compartilhar o resultado da consulta de {topic}"
                + (f" do produto {product_code}" if product_code else "")
                + ", conforme dados autorizados na plataforma."
            )

        if "fornecedor" in lowered:
            return (
                f"Poderia, por gentileza, considerar as informações abaixo referentes a {topic}"
                + (f" (produto {product_code})" if product_code else "")
                + "?"
            )

        return (
            f"Segue, para conhecimento, o resumo de {topic}"
            + (f" do produto {product_code}" if product_code else "")
            + ", com base na consulta autorizada nesta sessão."
        )

    @classmethod
    def _source_footer(cls, title: str, path: str) -> str:
        parts = ["Fonte dos dados: consulta autorizada na plataforma"]

        if title:
            parts.append(f"— {title}")

        if path:
            parts.append(f"({path})")

        return " ".join(parts) + "."

    @classmethod
    def _infer_subject(cls, title: str, product_code: str | None, message: str) -> str:
        lowered = (message or "").lower()

        if "compras" in lowered:
            return f"Informação de compras — {title}" + (f" — {product_code}" if product_code else "")

        if "fornecedor" in lowered:
            return f"Atualização para fornecedor — {title}" + (f" — {product_code}" if product_code else "")

        return f"Atualização — {title}" + (f" — produto {product_code}" if product_code else "")

    @classmethod
    def _extract_product_code(
        cls,
        summary: dict,
        lines: list[str],
        message: str,
    ) -> str | None:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        code = ChatProductQueryIntentService.extract_product_code(message)

        if code:
            return code

        path = str(summary.get("path") or "")
        match = re.search(r"/products/(\d{5,9})", path)

        if match:
            return match.group(1)

        blob = " ".join(lines)
        match = re.search(r"\b(\d{5,9})\b", blob)

        return match.group(1) if match else None
