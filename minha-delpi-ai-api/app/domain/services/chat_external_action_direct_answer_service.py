from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class ChatExternalActionKind:
    PRODUCT = "product"
    LMP_LIST = "lmp_list"
    LMP_DETAIL = "lmp_detail"
    SQL = "sql"
    GENERIC = "generic"


class ChatExternalActionDirectAnswerService:
    _ZERO_RECORDS_RE = ChatProductQueryIntentService._ZERO_RECORDS_RE

    @classmethod
    def classify(cls, *, path: str | None, operation_id: str | None, humanized: dict) -> str:
        normalized_path = str(path or "").lower()
        normalized_operation = str(operation_id or "").lower()
        titulo = str(humanized.get("titulo") or "").lower()

        if "/products/" in normalized_path or "produto" in titulo:
            return ChatExternalActionKind.PRODUCT

        if "/lmps/" in normalized_path and "{" in normalized_path:
            return ChatExternalActionKind.LMP_DETAIL

        if "lmp" in normalized_path or "lmp" in titulo or "get_lmp" in normalized_operation:
            if "list" in normalized_operation or normalized_path.rstrip("/").endswith("/lmps"):
                return ChatExternalActionKind.LMP_LIST

            if "sale_number" in titulo or normalized_path.count("/lmps/") >= 1:
                return ChatExternalActionKind.LMP_DETAIL

            return ChatExternalActionKind.LMP_LIST

        if "/data/sql" in normalized_path or "sql" in normalized_operation:
            return ChatExternalActionKind.SQL

        linhas = humanized.get("linhas") or []

        if linhas and cls._looks_like_lmp_lines(linhas):
            return ChatExternalActionKind.LMP_LIST

        return ChatExternalActionKind.GENERIC

    @classmethod
    def format(
        cls,
        humanized: dict,
        *,
        message: str,
        path: str | None = None,
        operation_id: str | None = None,
    ) -> str | None:
        kind = cls.classify(path=path, operation_id=operation_id, humanized=humanized)

        if kind == ChatExternalActionKind.PRODUCT:
            intent = ChatProductQueryIntentService.detect(message)
            return ChatProductQueryIntentService.format_direct_answer(
                humanized,
                intent=intent,
            )

        if kind == ChatExternalActionKind.LMP_LIST:
            return cls._format_lmp_list(humanized)

        if kind == ChatExternalActionKind.LMP_DETAIL:
            return cls._format_lmp_detail(humanized)

        if kind == ChatExternalActionKind.SQL:
            return cls._format_sql(humanized)

        return cls._format_generic(humanized)

    @classmethod
    def _format_lmp_list(cls, humanized: dict) -> str | None:
        lines = cls._clean_lines(humanized)

        if not lines:
            return "**LMPs**\n\nNenhuma LMP encontrada para os filtros informados."

        title = str(humanized.get("titulo") or "LMPs").strip()
        body = "\n".join(f"- {line}" for line in lines[:10])

        if len(lines) > 10:
            body += f"\n- … e mais {len(lines) - 10} registro(s)."

        return f"**{title}**\n\n{body}"

    @classmethod
    def _format_lmp_detail(cls, humanized: dict) -> str | None:
        lines = cls._clean_lines(humanized)

        if not lines:
            return None

        title = str(humanized.get("titulo") or "Detalhe da LMP").strip()
        parts = [f"**{title}**", lines[0]]

        for line in lines[1:6]:
            if not cls._ZERO_RECORDS_RE.search(line):
                parts.append(line)

        return "\n\n".join(parts)

    @classmethod
    def _format_sql(cls, humanized: dict) -> str | None:
        lines = cls._clean_lines(humanized)
        title = str(humanized.get("titulo") or "Resultado da consulta SQL").strip()

        if not lines:
            return f"**{title}**\n\nA consulta não retornou registros."

        if len(lines) == 1:
            return f"**{title}**\n\n{lines[0]}"

        body = "\n".join(f"- {line}" for line in lines[:15])

        if len(lines) > 15:
            body += f"\n- … e mais {len(lines) - 15} linha(s)."

        return f"**{title}**\n\n{body}"

    @classmethod
    def _format_generic(cls, humanized: dict) -> str | None:
        lines = [
            line
            for line in cls._clean_lines(humanized)
            if not cls._ZERO_RECORDS_RE.search(line)
        ]

        if not lines:
            lines = cls._clean_lines(humanized)

        if not lines:
            return None

        title = str(humanized.get("titulo") or "Resultado da API").strip()
        body = "\n".join(f"- {line}" for line in lines[:12])

        if len(lines) > 12:
            body += f"\n- … e mais {len(lines) - 12} item(ns)."

        return f"**{title}**\n\n{body}"

    @classmethod
    def _clean_lines(cls, humanized: dict) -> list[str]:
        return [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line).strip()
        ]

    @classmethod
    def _looks_like_lmp_lines(cls, lines: list) -> bool:
        sample = " ".join(str(line).lower() for line in lines[:3])

        return any(
            token in sample
            for token in ("ov", "ordem", "lmp", "amostra", "engenharia", "sale_number")
        )
