from __future__ import annotations

from math import ceil


class ChatDataCoverageNoticeService:
    """Detecta respostas parciais (paginação API, profundidade, SQL paginado) para o chat."""

    _INTERMEDIATE_PRODUCT_TYPES = frozenset(
        {"PA", "PI", "AI", "SP", "ME", "MC", "GR", "EM", "BN"}
    )

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
        lowered_path = str(path or "").lower()

        if "/system/tables" in lowered_path and (
            "/columns" in lowered_path or "/schema" in lowered_path or "/relations" in lowered_path
        ):
            return None

        root = cls._unwrap(data)
        messages: list[str] = []
        details: dict = {}

        if isinstance(root, dict):
            sql_notice = cls._sql_resultset_notice(root)

            if sql_notice:
                messages.append(sql_notice["message"])
                details["sqlResultset"] = sql_notice

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

        depth_root = root if isinstance(root, dict) else None

        if isinstance(depth_root, dict) and "/analyser" in str(path or "").lower():
            structure = depth_root.get("structure")

            if isinstance(structure, dict):
                depth_root = structure

        depth_notice = cls._depth_notice(
            path=path,
            parameters=parameters,
            root=depth_root,
        )

        if depth_notice:
            messages.append(depth_notice["message"])
            details["depth"] = depth_notice

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
    def _sql_resultset_notice(cls, root: dict) -> dict | None:
        resultsets = root.get("resultsets")

        if not isinstance(resultsets, list):
            return None

        for resultset in resultsets:
            if not isinstance(resultset, dict):
                continue

            data = resultset.get("data")

            if not isinstance(data, list):
                continue

            shown = len(data)
            total = cls._as_int(resultset.get("total"))

            if total is None or total <= shown:
                continue

            return {
                "message": (
                    f"Consulta SQL parcial: {shown} de {total} registro(s) nesta resposta da API. "
                    "Peça a próxima página, aumente page_size ou refine a consulta para ver todos."
                ),
                "shown": shown,
                "total": total,
            }

        return None

    @classmethod
    def _resolve_kind(cls, details: dict) -> str:
        if details.get("sqlResultset"):
            return "preview"

        if details.get("pagination") or details.get("structurePagination") or details.get("stockPagination"):
            return "pagination"

        if details.get("depth"):
            return "depth"

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
    def _depth_notice(
        cls,
        *,
        path: str,
        parameters: dict | None,
        root: dict | None = None,
    ) -> dict | None:
        params = parameters or {}
        max_depth = cls._as_int(params.get("max_depth"))

        if max_depth is None or max_depth >= 999:
            return None

        if not cls._depth_likely_truncated(root, max_depth=max_depth):
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
    def _depth_likely_truncated(cls, root: dict | None, *, max_depth: int) -> bool:
        if not isinstance(root, dict):
            return False

        for flag in ("depth_limit_reached", "truncated_by_depth", "has_more_levels"):
            if root.get(flag):
                return True

        items = root.get("items")

        if not isinstance(items, list) or not items:
            return False

        return cls._tree_has_truncated_branch(items, depth=1, max_depth=max_depth)

    @classmethod
    def _tree_has_truncated_branch(
        cls,
        items: list,
        *,
        depth: int,
        max_depth: int,
    ) -> bool:
        for item in items:
            if not isinstance(item, dict):
                continue

            item_type = str(item.get("type") or "").upper()
            components = item.get("components")

            if (
                depth >= max_depth
                and item_type in cls._INTERMEDIATE_PRODUCT_TYPES
            ):
                return True

            if isinstance(components, list) and components:
                if cls._tree_has_truncated_branch(
                    components,
                    depth=depth + 1,
                    max_depth=max_depth,
                ):
                    return True

        return False

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
