"""Reapresenta o último resultado operacional (tabela/gráfico/texto) sem nova rota errada."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_pagination_consolidation_service import (
    ChatPaginationConsolidationService,
)


class ChatPresentationFormatRefinementService:
    _FORMAT_TABLE_HINTS = (
        "em tabela",
        "formato tabela",
        "em formato de tabela",
        "mostra em tabela",
        "mostre em tabela",
        "como tabela",
        "ver como tabela",
        "ver em tabela",
        "exibir tabela",
        "exiba em tabela",
    )
    _FORMAT_CHART_HINTS = (
        "em gráfico",
        "em grafico",
        "como gráfico",
        "como grafico",
        "mostre em gráfico",
        "mostre em grafico",
        "gerar gráfico",
        "gerar grafico",
        "ver como gráfico",
    )
    _FORMAT_TEXT_HINTS = (
        "em texto",
        "formato texto",
        "só texto",
        "so texto",
        "apenas texto",
        "sem tabela",
        "sem gráfico",
    )
    _FORMAT_TREE_HINTS = (
        "em árvore",
        "em arvore",
        "como árvore",
        "como arvore",
        "mostre em árvore",
    )
    _REFERENCE_HINTS = (
        "dados acima",
        "resultado acima",
        "consulta acima",
        "resposta acima",
        "tabela acima",
        "gráfico acima",
        "grafico acima",
        "dados anteriores",
        "resultado anterior",
        "consulta anterior",
        "último resultado",
        "ultimo resultado",
        "última consulta",
        "ultima consulta",
        "o que mostrou",
        "que você mostrou",
        "que voce mostrou",
        "mostrados acima",
        "apresentados acima",
        "acima em",
        "dados acima",
        "mesmos dados",
        "mesmo dado",
        "mesmo resultado",
        "mesmos resultados",
        "mesma resposta",
    )

    @classmethod
    def looks_like_format_refinement(cls, message: str | None) -> bool:
        lowered = str(message or "").strip().lower()

        if not lowered:
            return False

        has_format = bool(cls.detect_requested_format(lowered))
        has_reference = any(token in lowered for token in cls._REFERENCE_HINTS)

        if has_format and has_reference:
            return True

        if has_format and any(
            token in lowered
            for token in (
                "último",
                "ultimo",
                "anterior",
                "mesmo dado",
                "mesmos dados",
                "mesma consulta",
            )
        ):
            return True

        return False

    @classmethod
    def detect_requested_format(cls, message: str) -> str | None:
        lowered = str(message or "").lower()

        if any(h in lowered for h in cls._FORMAT_TEXT_HINTS):
            return "text"

        if any(h in lowered for h in cls._FORMAT_TREE_HINTS):
            return "tree"

        if any(h in lowered for h in cls._FORMAT_TABLE_HINTS):
            return "table"

        if any(h in lowered for h in cls._FORMAT_CHART_HINTS):
            return "chart"

        return None

    @classmethod
    def collect_last_successful_operation(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        for item in reversed((previous_messages or [])[-16:]):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()

                if "/system/tables" in path:
                    continue

                arguments = tool_call.get("arguments") or {}
                parameters = arguments.get("parameters") or {}

                if not isinstance(parameters, dict):
                    parameters = {}

                action_id = str(
                    tool_meta.get("actionId") or arguments.get("actionId") or ""
                ).strip()

                if not action_id and not path:
                    continue

                return {
                    "actionId": action_id,
                    "path": str(tool_meta.get("path") or ""),
                    "parameters": dict(parameters),
                    "metadata": dict(tool_meta),
                    "arguments": dict(arguments) if isinstance(arguments, dict) else {},
                }

        return None

    @classmethod
    def resolve_payload(
        cls,
        previous_messages: list[Any] | None,
        *,
        operation: dict[str, Any],
    ) -> object | None:
        cached = ChatPaginationConsolidationService.load_cached_payload(previous_messages)

        if isinstance(cached, dict) and cached.get("items"):
            return {"data": cached}

        presentation = operation.get("metadata") or {}
        table_pres = presentation.get("tablePresentation")
        primary = presentation.get("presentation")

        for candidate in (table_pres, primary):
            if not isinstance(candidate, dict):
                continue

            rows = candidate.get("rows")

            if isinstance(rows, list) and rows:
                return {
                    "data": {
                        "items": rows,
                        "total": len(rows),
                        "page": 1,
                        "page_size": len(rows),
                        "total_pages": 1,
                    }
                }

        return None

    @staticmethod
    def _message_metadata(item: Any) -> dict[str, Any]:
        if hasattr(item, "metadata"):
            metadata = getattr(item, "metadata", None)

            return metadata if isinstance(metadata, dict) else {}

        if isinstance(item, dict):
            metadata = item.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        return {}
