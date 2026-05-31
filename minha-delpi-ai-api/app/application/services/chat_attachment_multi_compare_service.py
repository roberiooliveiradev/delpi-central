"""Comparação de múltiplos anexos indexados (Playbook 07)."""

from __future__ import annotations

import re
from typing import Any


class ChatAttachmentMultiCompareService:
    _COMPARE_RE = re.compile(
        r"\b(compar|versus|confront|cruzar|diferen[cç]a|vs\.?|entre\s+(?:os\s+)?(?:dois\s+)?arquivos?|planilhas?)\b",
        re.IGNORECASE,
    )

    @classmethod
    def wants_compare(cls, message: str) -> bool:
        normalized = str(message or "").strip()

        if not normalized:
            return False

        return bool(cls._COMPARE_RE.search(normalized))

    @classmethod
    def indexed_spreadsheet_summaries(
        cls,
        attachments: list[dict] | None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for attachment in attachments or []:
            if not isinstance(attachment, dict):
                continue

            meta = attachment.get("metadata")

            if not isinstance(meta, dict):
                continue

            preview = meta.get("preview")

            if not isinstance(preview, dict):
                continue

            if preview.get("kind") != "spreadsheet":
                continue

            status = str(attachment.get("status") or "")

            if status != "indexed" and not meta.get("indexed"):
                continue

            name = str(
                attachment.get("original_filename")
                or attachment.get("filename")
                or "arquivo"
            ).strip()
            columns = preview.get("columns") if isinstance(preview.get("columns"), list) else []

            items.append(
                {
                    "filename": name,
                    "columns": [str(column) for column in columns[:20]],
                    "sheetTitle": preview.get("sheetTitle"),
                }
            )

        return items

    @classmethod
    def should_enrich_turn(cls, *, message: str, attachments: list[dict] | None) -> bool:
        attachment_list = list(attachments or [])

        if len(attachment_list) < 2:
            return False

        if cls.wants_compare(message):
            return True

        normalized = str(message or "").strip().lower()

        return normalized in {"compare", "comparar", "comparar planilhas", "comparar arquivos"}

    @classmethod
    def build_context_hint(
        cls,
        *,
        message: str,
        attachments: list[dict] | None,
    ) -> str | None:
        if not cls.should_enrich_turn(message=message, attachments=attachments):
            return None

        summaries = cls.indexed_spreadsheet_summaries(attachments)
        names = [
            str(item.get("original_filename") or item.get("filename") or "").strip()
            for item in attachments or []
            if isinstance(item, dict)
        ]
        names = [name for name in names if name]

        if len(summaries) >= 2:
            lines = [
                "Comparação de anexos nesta mensagem:",
                "Use os trechos indexados de cada arquivo e destaque diferenças de colunas, totais e inconsistências.",
            ]

            for summary in summaries[:5]:
                cols = ", ".join(summary["columns"][:12]) if summary["columns"] else "(colunas não detectadas)"
                sheet = summary.get("sheetTitle")

                if sheet:
                    lines.append(f"- **{summary['filename']}** ({sheet}): {cols}.")
                else:
                    lines.append(f"- **{summary['filename']}**: {cols}.")

            return "\n".join(lines)

        if len(names) >= 2:
            listed = ", ".join(names[:5])

            return (
                "O usuário anexou vários arquivos e pediu comparação. "
                f"Arquivos: {listed}. "
                "Quando a indexação terminar, compare estrutura, colunas e totais; "
                "se a leitura automática falhar, peça qual coluna ou métrica priorizar."
            )

        return None
