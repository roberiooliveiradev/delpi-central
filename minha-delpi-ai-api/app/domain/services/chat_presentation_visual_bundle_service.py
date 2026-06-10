"""Pacote de visuais auxiliares — chat base (herdado por qualquer agente/rota)."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

_AUXILIARY_SLOTS: dict[str, str] = {
    "chart": "chartPresentation",
    "tree": "treePresentation",
    "kpi": "kpiPresentation",
    "dashboard": "dashboardPresentation",
    "table": "tablePresentation",
}


class ChatPresentationVisualBundleService:
    """Preenche slots auxiliares sem substituir a visão primária escolhida pelo decisor."""

    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        path: str,
        data: Any,
        presenter: ExternalActionResultPresenter,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        root = presenter._unwrap_data(data)

        if not isinstance(root, dict):
            return

        entity = cls._resolve_entity(data, path=path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        profile_key = str(profile.get("profileKey") or "generic")
        view_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]
        primary_type = cls._primary_type(metadata)
        is_factory_profile = profile_key == "factory_status" or ChatPresentationProfileService.has_flag(
            path,
            "factory_status",
            entity=entity,
        )
        is_mp_intelligence_profile = (
            profile_key == "raw_material_price_intelligence"
            or ChatPresentationProfileService.has_flag(
                path,
                "raw_material_price_intelligence",
                entity=entity,
            )
        )

        if not is_factory_profile and not is_mp_intelligence_profile:
            cls._ensure_chart(metadata, root=root, path=path, presenter=presenter, primary_type=primary_type)

        if profile_key == "stock" or ChatPresentationProfileService.has_flag(path, "stock", entity=entity):
            cls._enrich_stock_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_factory_profile:
            cls._enrich_factory_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_mp_intelligence_profile:
            cls._enrich_raw_material_price_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        cls._sync_available_formats(metadata, view_order)

    @classmethod
    def _enrich_stock_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        items = root.get("items")

        if not isinstance(items, list) or not items:
            return

        stock = presenter._stock()

        if "kpi" in view_order:
            kpi = stock.build_stock_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = stock.build_stock_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "dashboard" in view_order:
            kpi_slot = metadata.get("kpiPresentation")
            chart_slot = metadata.get("chartPresentation")
            table_slot = metadata.get("tablePresentation")

            if not isinstance(table_slot, dict) and isinstance(metadata.get("tablePresentations"), list):
                tables = metadata["tablePresentations"]

                if tables and isinstance(tables[-1], dict):
                    table_slot = tables[-1]

            dashboard = stock.build_stock_dashboard_presentation(
                root,
                path,
                kpi=kpi_slot if isinstance(kpi_slot, dict) else None,
                chart=chart_slot if isinstance(chart_slot, dict) else None,
                table=table_slot if isinstance(table_slot, dict) else None,
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_factory_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if "kpi" in view_order:
            kpi = presenter.build_factory_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = presenter.build_factory_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = presenter.build_factory_chart_presentation(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            kpi_slot = metadata.get("kpiPresentation")
            chart_slot = metadata.get("chartPresentation")
            table_slot = metadata.get("tablePresentation")

            if not isinstance(table_slot, dict) and isinstance(metadata.get("tablePresentations"), list):
                tables = metadata["tablePresentations"]

                for candidate in tables:
                    if isinstance(candidate, dict) and candidate.get("role") == "stock":
                        table_slot = candidate
                        break

                if not isinstance(table_slot, dict) and tables and isinstance(tables[-1], dict):
                    table_slot = tables[-1]

            dashboard = presenter.build_factory_dashboard_presentation(
                root,
                path,
                kpi=kpi_slot if isinstance(kpi_slot, dict) else None,
                chart=chart_slot if isinstance(chart_slot, dict) else None,
                table=table_slot if isinstance(table_slot, dict) else None,
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_raw_material_price_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if "kpi" in view_order:
            kpi = presenter.build_raw_material_price_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = presenter.build_raw_material_price_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = presenter.build_raw_material_price_chart_presentation(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            kpi_slot = metadata.get("kpiPresentation")
            chart_slot = metadata.get("chartPresentation")
            table_slot = metadata.get("tablePresentation")

            if not isinstance(table_slot, dict) and isinstance(metadata.get("tablePresentations"), list):
                tables = metadata["tablePresentations"]

                for candidate in tables:
                    if isinstance(candidate, dict) and candidate.get("role") == "profile":
                        table_slot = candidate
                        break

                if not isinstance(table_slot, dict) and tables and isinstance(tables[0], dict):
                    table_slot = tables[0]

            dashboard = presenter.build_raw_material_price_dashboard_presentation(
                root,
                path,
                kpi=kpi_slot if isinstance(kpi_slot, dict) else None,
                chart=chart_slot if isinstance(chart_slot, dict) else None,
                table=table_slot if isinstance(table_slot, dict) else None,
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _ensure_chart(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
    ) -> None:
        if cls._slot_value(metadata, "chart"):
            return

        chart = presenter.build_chart_presentation(
            root,
            path=path,
            force=True,
        )

        if chart:
            cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

    @classmethod
    def _attach_auxiliary(
        cls,
        metadata: dict[str, Any],
        view: str,
        presentation: dict[str, Any],
        *,
        primary_type: str,
    ) -> None:
        slot = _AUXILIARY_SLOTS.get(view)

        if not slot or not isinstance(presentation, dict):
            return

        if primary_type == view:
            if not metadata.get("presentation"):
                metadata["presentation"] = presentation

            return

        if not metadata.get(slot):
            metadata[slot] = presentation

    @classmethod
    def _slot_value(cls, metadata: dict[str, Any], view: str) -> dict[str, Any] | None:
        slot = _AUXILIARY_SLOTS.get(view)
        presentation = metadata.get(slot) if slot else None

        if isinstance(presentation, dict):
            return presentation

        primary = metadata.get("presentation")

        if isinstance(primary, dict) and str(primary.get("type") or "").strip().lower() == view:
            return primary

        return None

    @classmethod
    def _primary_type(cls, metadata: dict[str, Any]) -> str:
        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            return str(presentation.get("type") or "").strip().lower()

        return ""

    @classmethod
    def _sync_available_formats(cls, metadata: dict[str, Any], view_order: list[str]) -> None:
        formats = list(metadata.get("availableFormats") or [])
        seen = {str(token).strip().lower() for token in formats}

        for view in view_order:
            if view in {"line_chart", "bar_chart", "horizontal_bar", "donut", "area_chart"}:
                mapped = "chart"
            else:
                mapped = view

            if mapped == "text":
                token = "text"

                if token not in seen and metadata.get("textPresentation"):
                    formats.append(token)
                    seen.add(token)

                continue

            if cls._slot_value(metadata, mapped) and mapped not in seen:
                formats.append(mapped)
                seen.add(mapped)

        if metadata.get("textPresentation") and "text" not in seen:
            formats.append("text")
            seen.add("text")

        if metadata.get("textPresentation"):
            canvas = "canvas"

            if canvas not in seen:
                formats.append(canvas)

        metadata["availableFormats"] = formats

    @classmethod
    def _resolve_entity(cls, data: Any, *, path: str) -> str | None:
        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
        entity = str(profile.entity or "").strip()

        return entity or None
