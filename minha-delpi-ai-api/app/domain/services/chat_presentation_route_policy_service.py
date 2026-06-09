"""Política de formato nativo por rota DELPI (tabela × árvore × gráfico)."""

from __future__ import annotations

_TREE_PATH_TOKENS = ("/structure", "/parents")
_TABLE_PATH_TOKENS = (
    "/guide",
    "/inspection",
    "/suppliers",
    "/customers",
    "/purchases",
    "/sales",
    "/pricing",
    "/prices",
    "/movements",
    "/invoices",
    "/search",
)
_STOCK_PATH_TOKEN = "/stock"
_ANALYSER_PATH_TOKEN = "/analyser"
_FACTORY_STATUS_PATH_TOKEN = "/factory-status"
_PRODUCTION_STATUS_PATH_TOKEN = "/production-status"
_SHIPPING_STATUS_PATH_TOKEN = "/shipping-status"
_STRUCTURE_EXCLUSIVITY_PATH_TOKEN = "/structure/exclusivity"


class ChatPresentationRoutePolicyService:
    @classmethod
    def path_lowered(cls, path: str | None) -> str:
        return str(path or "").strip().lower()

    @classmethod
    def is_tree_route(cls, path: str | None) -> bool:
        lowered = cls.path_lowered(path)

        return any(token in lowered for token in _TREE_PATH_TOKENS)

    @classmethod
    def is_table_route(cls, path: str | None) -> bool:
        lowered = cls.path_lowered(path)

        if any(token in lowered for token in _TABLE_PATH_TOKENS):
            return True

        if _ANALYSER_PATH_TOKEN in lowered:
            return True

        return False

    @classmethod
    def is_stock_route(cls, path: str | None) -> bool:
        return _STOCK_PATH_TOKEN in cls.path_lowered(path)

    @classmethod
    def is_analyser_route(cls, path: str | None) -> bool:
        return _ANALYSER_PATH_TOKEN in cls.path_lowered(path)

    @classmethod
    def is_factory_status_route(cls, path: str | None) -> bool:
        return _FACTORY_STATUS_PATH_TOKEN in cls.path_lowered(path)

    @classmethod
    def is_production_status_route(cls, path: str | None) -> bool:
        return _PRODUCTION_STATUS_PATH_TOKEN in cls.path_lowered(path)

    @classmethod
    def is_shipping_status_route(cls, path: str | None) -> bool:
        return _SHIPPING_STATUS_PATH_TOKEN in cls.path_lowered(path)

    @classmethod
    def is_structure_exclusivity_route(cls, path: str | None) -> bool:
        return _STRUCTURE_EXCLUSIVITY_PATH_TOKEN in cls.path_lowered(path)

    @classmethod
    def resolve_default_preferred_format(
        cls,
        *,
        path: str | None,
        session_format: str | None = None,
        has_tree: bool = False,
        has_table: bool = False,
        has_chart: bool = False,
        has_text: bool = False,
        has_kpi: bool = False,
    ) -> str | None:
        token = str(session_format or "").strip().lower()

        if token in {"table", "text", "tree", "chart", "topics"}:
            if token == "topics":
                return "text"
            return token

        lowered = cls.path_lowered(path)

        if cls.is_stock_route(lowered):
            if has_chart and not has_table:
                return "chart"
            if has_table:
                return "table"
            if has_chart:
                return "chart"
            return "text" if has_text else None

        if has_tree and (cls.is_tree_route(lowered) or cls.is_analyser_route(lowered)):
            return "tree"

        if has_table and cls.is_table_route(lowered):
            return "table"

        if has_kpi:
            return "kpi"

        if has_chart:
            return "chart"

        if has_table:
            return "table"

        if has_text:
            return "text"

        return None

    @classmethod
    def apply_visual_order(cls, decision: dict, *, path: str | None) -> None:
        views = list(decision.get("availableViews") or [])
        if not views:
            return

        normalized = {str(view).strip().lower() for view in views}
        ordered: list[str] = []

        if "text" in normalized:
            ordered.append("text")

        lowered = cls.path_lowered(path)

        if cls.is_stock_route(lowered):
            for view in ("table", "chart", "tree", "kpi", "dashboard"):
                if view in normalized and view not in ordered:
                    ordered.append(view)
        elif cls.is_analyser_route(lowered):
            for view in ("table", "tree", "chart", "kpi", "dashboard"):
                if view in normalized and view not in ordered:
                    ordered.append(view)
        elif cls.is_factory_status_route(lowered) or cls.is_production_status_route(lowered):
            for view in ("table", "text", "chart", "tree", "kpi", "dashboard"):
                if view in normalized and view not in ordered:
                    ordered.append(view)
        elif (
            cls.is_shipping_status_route(lowered)
            or cls.is_structure_exclusivity_route(lowered)
        ):
            for view in ("table", "text", "chart", "tree", "kpi", "dashboard"):
                if view in normalized and view not in ordered:
                    ordered.append(view)
        elif cls.is_tree_route(lowered):
            for view in ("tree", "table", "chart", "kpi", "dashboard"):
                if view in normalized and view not in ordered:
                    ordered.append(view)
        elif cls.is_table_route(lowered):
            for view in ("table", "chart", "tree", "kpi", "dashboard"):
                if view in normalized and view not in ordered:
                    ordered.append(view)
        else:
            for view in (
                "table",
                "tree",
                "chart",
                "line_chart",
                "bar_chart",
                "horizontal_bar",
                "donut",
                "kpi",
                "dashboard",
            ):
                if view in normalized and view not in ordered:
                    ordered.append(view)

        for view in sorted(normalized):
            if view not in ordered:
                ordered.append(view)

        if len(ordered) >= 2:
            decision["layoutMode"] = "stack"

        decision["visualOrder"] = ordered
