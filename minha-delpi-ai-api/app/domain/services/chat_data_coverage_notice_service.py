from __future__ import annotations

from math import ceil


class ChatDataCoverageNoticeService:
    """Detecta respostas parciais (paginação, profundidade, prévia) para o chat."""

    MAX_TABLE_ROWS = 100

    @classmethod
    def build(
        cls,
        data,
        *,
        path: str = "",
        parameters: dict | None = None,
        presentation: dict | None = None,
        table_presentation: dict | None = None,
    ) -> dict | None:
        root = cls._unwrap(data)
        messages: list[str] = []
        details: dict = {}

        if isinstance(root, dict):
            pagination = cls._pagination_notice(root, path=path)

            if pagination:
                messages.append(pagination["message"])
                details["pagination"] = pagination

            if isinstance(root.get("structure"), dict):
                structure_notice = cls._pagination_notice(
                    root["structure"],
                    path=path,
                    context="structure",
                )

                if structure_notice:
                    messages.append(structure_notice["message"])
                    details["structurePagination"] = structure_notice

            stock = root.get("stock")

            if isinstance(stock, dict):
                stock_notice = cls._pagination_notice(
                    stock,
                    path=path,
                    context="stock",
                )

                if stock_notice:
                    messages.append(stock_notice["message"])
                    details["stockPagination"] = stock_notice

        depth_notice = cls._depth_notice(path=path, parameters=parameters)

        if depth_notice:
            messages.append(depth_notice["message"])
            details["depth"] = depth_notice

        table_notice = cls._table_preview_notice(
            table_presentation or presentation,
            root if isinstance(root, dict) else None,
        )

        if table_notice:
            messages.append(table_notice["message"])
            details["tablePreview"] = table_notice

        if not messages:
            return None

        deduped = list(dict.fromkeys(messages))

        return {
            "kind": cls._resolve_kind(details),
            "message": " ".join(deduped),
            "messages": deduped,
            "details": details,
        }

    @classmethod
    def append_to_markdown(cls, markdown: str, notice: dict | None) -> str:
        body = str(markdown or "").strip()
        message = str((notice or {}).get("message") or "").strip()

        if not message:
            return body

        block = f"> **Cobertura dos dados:** {message}"

        if not body:
            return block

        return f"{body}\n\n{block}"

    @classmethod
    def _resolve_kind(cls, details: dict) -> str:
        if details.get("pagination") or details.get("structurePagination") or details.get("stockPagination"):
            return "pagination"

        if details.get("depth"):
            return "depth"

        if details.get("tablePreview"):
            return "preview"

        return "partial"

    @classmethod
    def _pagination_notice(
        cls,
        payload: dict,
        *,
        path: str = "",
        context: str = "items",
    ) -> dict | None:
        items = payload.get("items")

        if not isinstance(items, list):
            return None

        shown = len(items)
        total = cls._as_int(payload.get("total"))
        page = cls._as_int(payload.get("page"))
        page_size = cls._as_int(payload.get("page_size"))
        total_pages = cls._as_int(payload.get("total_pages"))

        if page and page_size and total is not None and (total > shown or (total_pages and total_pages > 1)):
            if total_pages is None and total > 0:
                total_pages = max(1, ceil(total / page_size))

            label = cls._context_label(path, context)

            return {
                "message": (
                    f"{label} parcial: página {page}"
                    f"{f' de {total_pages}' if total_pages else ''} "
                    f"({shown} de {total} registro(s) nesta resposta). "
                    "Peça a próxima página ou aumente page_size para ver mais."
                ),
                "page": page,
                "pageSize": page_size,
                "total": total,
                "shown": shown,
                "totalPages": total_pages,
            }

        if total is not None and total > shown:
            label = cls._context_label(path, context)

            return {
                "message": (
                    f"{label} parcial: {shown} de {total} registro(s) nesta resposta. "
                    "Pode haver mais dados além do que está sendo exibido."
                ),
                "total": total,
                "shown": shown,
            }

        return None

    @classmethod
    def _depth_notice(cls, *, path: str, parameters: dict | None) -> dict | None:
        params = parameters or {}
        max_depth = cls._as_int(params.get("max_depth"))

        if max_depth is None or max_depth >= 999:
            return None

        lowered = str(path or "").lower()

        if "/structure" in lowered:
            return {
                "message": (
                    f"A estrutura foi consultada com profundidade limitada "
                    f"(max_depth={max_depth}). Níveis mais profundos podem estar ocultos."
                ),
                "maxDepth": max_depth,
            }

        if "/parents" in lowered:
            return {
                "message": (
                    f"A consulta de produtos pai foi limitada a {max_depth} nível(is) "
                    f"(max_depth={max_depth}). Hierarquias acima disso podem estar incompletas."
                ),
                "maxDepth": max_depth,
            }

        return {
            "message": (
                f"A consulta foi limitada a {max_depth} nível(is) de profundidade "
                f"(max_depth={max_depth})."
            ),
            "maxDepth": max_depth,
        }

    @classmethod
    def _table_preview_notice(
        cls,
        presentation: dict | None,
        root: dict | None,
    ) -> dict | None:
        if not isinstance(presentation, dict) or presentation.get("type") != "table":
            return None

        rows = presentation.get("rows")

        if not isinstance(rows, list) or not rows:
            return None

        shown = len(rows)
        total = None

        if isinstance(root, dict):
            total = cls._as_int(root.get("total"))

            items = root.get("items")

            if isinstance(items, list) and (total is None or total < len(items)):
                total = len(items)

        if shown < cls.MAX_TABLE_ROWS and (total is None or total <= shown):
            return None

        if total is not None and total > shown:
            return {
                "message": (
                    f"A tabela exibe {shown} linha(s) de {total} registro(s) retornados "
                    f"(prévia limitada a {cls.MAX_TABLE_ROWS})."
                ),
                "shown": shown,
                "total": total,
            }

        if shown >= cls.MAX_TABLE_ROWS:
            return {
                "message": (
                    f"A tabela exibe no máximo {cls.MAX_TABLE_ROWS} linhas nesta visualização."
                ),
                "shown": shown,
            }

        return None

    @classmethod
    def _context_label(cls, path: str, context: str) -> str:
        lowered = str(path or "").lower()

        if context == "structure" or "/structure" in lowered:
            return "Estrutura"

        if context == "stock" or "/stock" in lowered:
            return "Estoque"

        if "/parents" in lowered:
            return "Produtos pai"

        if "/search" in lowered:
            return "Busca"

        if "/lmp" in lowered or "/production" in lowered:
            return "Listagem"

        return "Resultado"

    @classmethod
    def _as_int(cls, value) -> int | None:
        if value in (None, ""):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _unwrap(cls, data):
        root = data

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        return root
