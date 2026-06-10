"""Pacote de visuais auxiliares — chat base (herdado por qualquer agente/rota)."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_profile_visual_bundle_service import (
    ChatPresentationProfileVisualBundleService,
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
        explicit_format: str | None = None,
        user_message: str | None = None,
        entity: str | None = None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        root = cls._resolve_bundle_root(presenter, data, path=path)

        if not isinstance(root, dict):
            return

        entity = entity or cls._resolve_entity(data, path=path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        view_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]

        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        if not ChatPresentationTextFirstPolicyService.should_build_visual_bundle(
            path=path,
            entity=entity,
            explicit_format=explicit_format,
            user_message=user_message,
        ):
            cls._sync_latent_available_formats(metadata, view_order)
            cls._ensure_text_embed_tree_for_markdown(
                metadata,
                profile=profile,
                root=root,
                path=path,
                presenter=presenter,
                explicit_format=explicit_format,
            )
            cls._ensure_text_embed_chart_for_markdown(
                metadata,
                profile=profile,
                root=root,
                path=path,
                presenter=presenter,
                explicit_format=explicit_format,
            )
            return

        primary_type = cls._primary_type(metadata)
        chart_policy = ChatPresentationProfileVisualBundleService.chart_policy(profile)

        ChatPresentationProfileVisualBundleService.enrich_from_profile(
            metadata,
            profile=profile,
            root=root,
            path=path,
            presenter=presenter,
            primary_type=primary_type,
            view_order=view_order,
            attach_auxiliary=cls._attach_auxiliary,
            dashboard_input_slots=cls._dashboard_input_slots,
        )

        if chart_policy != "skip" and not cls._slot_value(metadata, "chart"):
            cls._ensure_chart(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
            )

        cls._ensure_generic_kpi_bundle(
            metadata,
            root=root,
            path=path,
            presenter=presenter,
            primary_type=primary_type,
            view_order=view_order,
        )

        cls._sync_available_formats(metadata, view_order)

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
    def _dashboard_input_slots(
        cls,
        metadata: dict[str, Any],
        *,
        list_role: str = "list",
    ) -> dict[str, dict[str, Any] | None]:
        kpi_slot = metadata.get("kpiPresentation")
        tree_slot = metadata.get("treePresentation")
        chart_slot = metadata.get("chartPresentation")
        table_slot = metadata.get("tablePresentation")

        if not isinstance(table_slot, dict) and isinstance(metadata.get("tablePresentations"), list):
            tables = metadata["tablePresentations"]

            for candidate in tables:
                if isinstance(candidate, dict) and candidate.get("role") == list_role:
                    table_slot = candidate
                    break

            if not isinstance(table_slot, dict):
                for candidate in tables:
                    if isinstance(candidate, dict) and candidate.get("type") == "table":
                        table_slot = candidate
                        break

            if not isinstance(table_slot, dict) and tables and isinstance(tables[-1], dict):
                table_slot = tables[-1]

        return {
            "kpi": kpi_slot if isinstance(kpi_slot, dict) else None,
            "tree": tree_slot if isinstance(tree_slot, dict) else None,
            "chart": chart_slot if isinstance(chart_slot, dict) else None,
            "table": table_slot if isinstance(table_slot, dict) else None,
        }

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
            existing = metadata.get("presentation")

            if view == "dashboard" or not isinstance(existing, dict):
                metadata["presentation"] = presentation
            elif not existing:
                metadata["presentation"] = presentation

            return

        if not metadata.get(slot):
            metadata[slot] = presentation

    @classmethod
    def _ensure_text_embed_tree_for_markdown(
        cls,
        metadata: dict[str, Any],
        *,
        profile: dict[str, Any],
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        explicit_format: str | None,
    ) -> None:
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        if ChatPresentationTextFirstPolicyService.normalize_explicit_format(explicit_format) != "text":
            return

        ChatPresentationProfileVisualBundleService.ensure_text_embed_tree(
            metadata,
            profile=profile,
            root=root,
            path=path,
            presenter=presenter,
            attach_auxiliary=cls._attach_auxiliary,
            primary_type=cls._primary_type(metadata),
        )

    @classmethod
    def _ensure_text_embed_chart_for_markdown(
        cls,
        metadata: dict[str, Any],
        *,
        profile: dict[str, Any],
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        explicit_format: str | None,
    ) -> None:
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        if ChatPresentationTextFirstPolicyService.normalize_explicit_format(explicit_format) != "text":
            return

        ChatPresentationProfileVisualBundleService.ensure_text_embed_chart(
            metadata,
            profile=profile,
            root=root,
            path=path,
            presenter=presenter,
            attach_auxiliary=cls._attach_auxiliary,
            primary_type=cls._primary_type(metadata),
        )

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
    def _ensure_generic_kpi_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if cls._slot_value(metadata, "kpi"):
            return

        if "kpi" not in view_order:
            return

        kpi = presenter._build_kpi_chart(root, path)

        if isinstance(kpi, dict) and str(kpi.get("type") or "").strip().lower() == "kpi":
            cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if cls._slot_value(metadata, "dashboard") or "dashboard" not in view_order:
            return

        dashboard = presenter.build_dashboard_presentation(root, path=path)

        if isinstance(dashboard, dict) and dashboard.get("type") == "dashboard":
            cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

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
    def _sync_latent_available_formats(
        cls,
        metadata: dict[str, Any],
        view_order: list[str],
    ) -> None:
        formats = list(metadata.get("availableFormats") or [])
        seen = {str(token).strip().lower() for token in formats}

        for view in view_order:
            mapped = "chart" if view in {
                "line_chart",
                "bar_chart",
                "horizontal_bar",
                "donut",
                "area_chart",
            } else view

            if mapped == "text":
                if metadata.get("textPresentation") and "text" not in seen:
                    formats.append("text")
                    seen.add("text")

                continue

            if mapped in seen:
                continue

            if mapped in {"table", "tree", "chart", "kpi", "dashboard"}:
                formats.append(mapped)
                seen.add(mapped)

        if metadata.get("textPresentation") and "text" not in seen:
            formats.insert(0, "text")

        if metadata.get("textPresentation") and "canvas" not in seen:
            formats.append("canvas")

        metadata["availableFormats"] = formats

    @classmethod
    def _resolve_bundle_root(
        cls,
        presenter: ExternalActionResultPresenter,
        data: Any,
        *,
        path: str = "",
    ) -> dict | None:
        root = presenter._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        from app.domain.services.chat_presentation_operational_root_service import (
            ChatPresentationOperationalRootService,
        )

        entity = cls._resolve_entity(data, path=path)

        return ChatPresentationOperationalRootService.resolve_bundle_root(
            root,
            path=path,
            entity=entity,
        )

    @classmethod
    def _resolve_entity(cls, data: Any, *, path: str) -> str | None:
        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
        entity = str(profile.entity or "").strip()

        return entity or None
