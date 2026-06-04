from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatExternalActionKind:
    PRODUCT = "product"
    PRODUCT_SEARCH = "product_search"
    SALE_ORDERS = "sale_orders"
    LMP_LIST = "lmp_list"
    LMP_DETAIL = "lmp_detail"
    SUPPLIES = "supplies"
    SQL = "sql"
    GENERIC = "generic"


class ChatExternalActionDirectAnswerService:
    _ZERO_RECORDS_RE = ChatProductQueryIntentService._ZERO_RECORDS_RE

    @classmethod
    def classify(cls, *, path: str | None, operation_id: str | None, humanized: dict) -> str:
        normalized_path = str(path or "").lower()
        normalized_operation = str(operation_id or "").lower()
        titulo = str(humanized.get("titulo") or "").lower()

        if ExternalActionSqlCapabilityService.is_sql_execution_context(
            path=normalized_path,
            operation_id=normalized_operation,
        ):
            return ChatExternalActionKind.SQL

        dados = humanized.get("dados")
        if isinstance(dados, dict) and ExternalActionSqlCapabilityService.is_sql_result_payload(
            dados
        ):
            return ChatExternalActionKind.SQL

        if (
            normalized_path.rstrip("/").endswith("/sales")
            or "list_sale_orders" in normalized_operation
        ) and "/products/" not in normalized_path:
            return ChatExternalActionKind.SALE_ORDERS

        if "/search" in normalized_path or "search_products" in normalized_operation:
            if "busca" in titulo or titulo == "busca de produtos":
                return ChatExternalActionKind.PRODUCT_SEARCH

        if "/products/" in normalized_path or (
            "produto" in titulo
            and not ExternalActionSqlCapabilityService.is_sql_execution_context(
                path=normalized_path
            )
        ):
            return ChatExternalActionKind.PRODUCT

        if "/lmps/" in normalized_path and "{" in normalized_path:
            return ChatExternalActionKind.LMP_DETAIL

        if "lmp" in normalized_path or "lmp" in titulo or "get_lmp" in normalized_operation:
            if "list" in normalized_operation or normalized_path.rstrip("/").endswith("/lmps"):
                return ChatExternalActionKind.LMP_LIST

            if "sale_number" in titulo or normalized_path.count("/lmps/") >= 1:
                return ChatExternalActionKind.LMP_DETAIL

            return ChatExternalActionKind.LMP_LIST

        if "/supplies/" in normalized_path or normalized_operation.startswith("get_supplies_"):
            return ChatExternalActionKind.SUPPLIES

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

        if kind == ChatExternalActionKind.SALE_ORDERS:
            return cls._format_sale_orders(humanized)

        if kind == ChatExternalActionKind.PRODUCT_SEARCH:
            return cls._format_product_search(humanized)

        if kind == ChatExternalActionKind.PRODUCT:
            intent = ChatProductQueryIntentService.detect(message)
            return ChatProductQueryIntentService.format_direct_answer(
                humanized,
                intent=intent,
                path=path,
            )

        if kind == ChatExternalActionKind.LMP_LIST:
            return cls._format_lmp_list(humanized)

        if kind == ChatExternalActionKind.LMP_DETAIL:
            return cls._format_lmp_detail(humanized)

        if kind == ChatExternalActionKind.SQL:
            return cls._format_sql(humanized, message=message)

        if kind == ChatExternalActionKind.SUPPLIES:
            return cls._format_supplies(humanized, operation_id=operation_id)

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
    def _format_sql(cls, humanized: dict, *, message: str | None = None) -> str | None:
        rows = cls._extract_sql_rows(humanized)
        title = str(
            humanized.get("titulo")
            or ExternalActionResponseContentService.get("sql", "defaultResultTitle")
        ).strip()

        from app.domain.services.chat_sql_production_schedule_date_service import (
            ChatSqlProductionScheduleDateService,
        )

        schedule = ChatSqlProductionScheduleDateService.resolve(message)
        today_label = ExternalActionResponseContentService.get("temporal", "today", default="hoje")

        if rows and cls._looks_like_production_schedule_row(rows[0]):
            if schedule and schedule.title != title:
                title = schedule.title

        if not rows:
            lines = cls._clean_lines(humanized)
            message_text = lines[0] if lines else ExternalActionResponseContentService.get(
                "sql",
                "emptyNoRows",
            )
            if schedule:
                fallback_title = ExternalActionResponseContentService.get(
                    "productionSchedule",
                    "titleTodayFallback",
                )

                if title == fallback_title or today_label in title.lower():
                    title = schedule.title

                if (
                    schedule.empty_message != message_text
                    and today_label in message_text
                ):
                    message_text = schedule.empty_message
            return f"**{title}**\n\n{message_text}"

        if rows and cls._looks_like_production_schedule_row(rows[0]):
            from app.domain.services.external_actions.external_action_result_presenter import (
                ExternalActionResultPresenter,
            )

            presenter = ExternalActionResultPresenter()
            body = "\n".join(
                f"- {presenter._format_production_schedule_row(row)}"
                for row in rows
                if isinstance(row, dict)
            )
            label = schedule.label if schedule else today_label
            summary = ExternalActionResponseContentService.format(
                "productionSchedule",
                "summaryWithCount",
                count=len(rows),
                label=label,
            )
            return f"**{title}**\n\n{summary}\n\n{body}".strip()

        lines = cls._clean_lines(humanized)

        if not lines:
            body = ExternalActionResponseContentService.format(
                "sql",
                "rowsCount",
                count=len(rows),
            )
            return f"**{title}**\n\n{body}"

        if len(lines) == 1:
            return f"**{title}**\n\n{lines[0]}"

        body = "\n".join(f"- {line}" for line in lines[:15])

        if len(lines) > 15:
            body += f"\n- {ExternalActionResponseContentService.format('sql', 'moreLines', count=len(lines) - 15)}"

        return f"**{title}**\n\n{body}"

    @classmethod
    def _format_supplies(
        cls,
        humanized: dict,
        *,
        operation_id: str | None = None,
    ) -> str | None:
        operation = str(operation_id or "").lower()
        default_title = "Indicador de suprimentos"

        if "cpv" in operation:
            default_title = "CPV (custo de produção vendido)"
        elif "otd" in operation:
            default_title = "OTD (entrega no prazo)"
        elif "inventory_turnover" in operation or "giro" in operation:
            default_title = "Giro de estoque (IDD)"
        elif "stock_value" in operation:
            default_title = "Valor total de estoque"

        lines = cls._clean_lines(humanized)

        if not lines:
            return f"**{default_title}**\n\nNenhum dado retornado para os filtros informados."

        title = str(humanized.get("titulo") or default_title).strip()
        body = "\n".join(f"- {line}" for line in lines[:12])

        if len(lines) > 12:
            body += f"\n- … e mais {len(lines) - 12} item(ns)."

        return f"**{title}**\n\n{body}"

    @classmethod
    def _format_product_search(cls, humanized: dict) -> str | None:
        lines = cls._clean_lines(humanized)

        if not lines:
            return "**Busca de produtos**\n\nNenhum produto encontrado para a busca informada."

        title = str(humanized.get("titulo") or "Busca de produtos").strip()
        body = "\n".join(f"- {line}" for line in lines[:15])

        return f"**{title}**\n\n{body}"

    @classmethod
    def _format_sale_orders(cls, humanized: dict) -> str | None:
        lines = cls._clean_lines(humanized)

        if not lines:
            return "**Ordens de Venda**\n\nNenhuma ordem de venda encontrada para o período informado."

        title = str(humanized.get("titulo") or "Ordens de Venda").strip()
        body = "\n".join(f"- {line}" for line in lines[:12])

        if len(lines) > 12:
            body += f"\n- … e mais {len(lines) - 12} registro(s)."

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
    def _extract_sql_rows(cls, humanized: dict) -> list[dict]:
        rows = humanized.get("sqlRows")

        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]

        dados = humanized.get("dados")

        if isinstance(dados, dict):
            nested_rows = dados.get("rows")

            if isinstance(nested_rows, list):
                return [row for row in nested_rows if isinstance(row, dict)]

        return []

    @classmethod
    def _looks_like_production_schedule_row(cls, row: dict) -> bool:
        if not isinstance(row, dict):
            return False

        keys = {str(key).upper() for key in row.keys()}

        return "COD_PRODUTO" in keys and (
            "DESCRICAO_PRODUTO" in keys or "QTD_PLANEJADA" in keys
        )

    @classmethod
    def _looks_like_lmp_lines(cls, lines: list) -> bool:
        sample = " ".join(str(line).lower() for line in lines[:3])

        return any(
            token in sample
            for token in ("ov", "ordem", "lmp", "amostra", "engenharia", "sale_number")
        )
