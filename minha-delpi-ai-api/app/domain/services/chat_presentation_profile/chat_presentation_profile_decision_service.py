"""Delegate — perfis declarativos de apresentação."""

from __future__ import annotations

from typing import Any

from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.openapi_operation_contract_service import (
    OpenApiOperationContractService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_facade_access import (
    presentation_profile_service,
)



class ChatPresentationProfileDecisionService:
    @classmethod
    def presentation_decision_config(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        profile = presentation_profile_service().resolve_profile(path, entity)
        raw = profile.get("presentationDecision")

        return dict(raw) if isinstance(raw, dict) else {}

    @classmethod
    def resolve_default_preferred_format(
        cls,
        *,
        path: str | None,
        session_format: str | None = None,
        entity: str | None = None,
        has_tree: bool = False,
        has_table: bool = False,
        has_chart: bool = False,
        has_text: bool = False,
        has_kpi: bool = False,
    ) -> str | None:
        token = str(session_format or "").strip().lower()

        if token in {"table", "text", "tree", "chart", "topics", "canvas"}:
            if token == "topics":
                return "text"

            return token

        profile = presentation_profile_service().resolve_profile(path, entity)
        policy = str(profile.get("defaultViewPolicy") or "generic").strip().lower()
        flags = presentation_profile_service().flags(path, entity)

        if policy == "text_when_available" and has_text and "stock" not in flags:
            return "text"

        if policy == "stock" or "stock" in flags:
            if policy == "text_when_available" and has_text:
                return "text"

            if has_chart and not has_table:
                return "chart"

            if has_table:
                return "table"

            if has_chart:
                return "chart"

            return "text" if has_text else None

        if policy == "tree_when_available":
            if has_tree and ("tree" in flags or "analyser" in flags):
                return "tree"

        if policy == "kpi_when_available":
            if has_kpi and "kpi" in flags:
                return "kpi"

        if policy == "text_when_available":
            if has_text:
                return "text"

        if policy == "table_when_available":
            if has_table and ("table" in flags or "analyser" in flags):
                return "table"

        return cls._generic_default_preferred_format(
            has_tree=has_tree,
            has_table=has_table,
            has_chart=has_chart,
            has_text=has_text,
            has_kpi=has_kpi,
        )

    @classmethod
    def apply_visual_order(
        cls,
        decision: dict[str, Any],
        *,
        path: str | None,
        entity: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        views = list(decision.get("availableViews") or [])

        if not views:
            return

        normalized = {str(view).strip().lower() for view in views}
        profile = presentation_profile_service().resolve_profile(path, entity)
        priority = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]

        ordered: list[str] = []

        for view in priority:
            if view in normalized and view not in ordered:
                ordered.append(view)

        for view in sorted(normalized):
            if view not in ordered:
                ordered.append(view)

        stack_policy = str(profile.get("stackLayoutPolicy") or "on_demand").strip().lower()
        schema_first = presentation_profile_service().uses_schema_first_presentation(path, entity)
        force_stack = stack_policy == "always" and len(ordered) >= 2 and not schema_first

        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        if (
            isinstance(metadata, dict)
            and ChatPresentationTextModeService.is_user_explicit_text_mode(metadata)
        ):
            # Composite (visão integrada) em modo Texto mantém stack: narrativa +
            # tabelas/árvore embutidas e visuais na toolbar (Playbook 23).
            from app.domain.services.chat_presentation_rich_stack_policy_service import (
                ChatPresentationRichStackPolicyService,
            )

            if (
                len(ordered) >= 2
                and ChatPresentationRichStackPolicyService._is_composite_metadata(metadata)
            ):
                decision["layoutMode"] = "stack"
            else:
                decision["layoutMode"] = "single"

            decision["visualOrder"] = ordered
            decision["presentationProfileKey"] = profile.get("profileKey")
            return

        if len(ordered) >= 2 and (force_stack or str(decision.get("layoutMode") or "") != "single"):
            selected = str(decision.get("selected") or "").strip().lower()

            if (
                not force_stack
                and isinstance(metadata, dict)
                and ChatPresentationTextModeService.is_user_explicit_text_mode(metadata)
            ):
                decision["visualOrder"] = ordered
                decision["presentationProfileKey"] = profile.get("profileKey")
                return

            explicit = (
                str(metadata.get("explicitSessionFormat") or "").strip().lower()
                if isinstance(metadata, dict)
                else ""
            )

            if not force_stack and explicit and str(decision.get("layoutMode") or "") == "single":
                decision["visualOrder"] = ordered
                decision["presentationProfileKey"] = profile.get("profileKey")
                return

            if not force_stack and selected == "text" and str(decision.get("layoutMode") or "") == "single":
                decision["visualOrder"] = ordered
                decision["presentationProfileKey"] = profile.get("profileKey")
                return

            if stack_policy == "always" and not schema_first:
                decision["layoutMode"] = "stack"
            elif selected != "text":
                decision["layoutMode"] = "stack"

        decision["visualOrder"] = ordered
        decision["presentationProfileKey"] = profile.get("profileKey")

    @classmethod
    def humanized_narrative_mode(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> str:
        profile = presentation_profile_service().resolve_profile(path, entity)
        mode = str(profile.get("humanizedNarrative") or "enrich").strip().lower()

        if mode in {"skip", "enrich"}:
            return mode

        return "enrich"

    @classmethod
    def data_answer_lead_alignment(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> str:
        profile = presentation_profile_service().resolve_profile(path, entity)
        mode = str(profile.get("dataAnswerLeadAlignment") or "inject").strip().lower()

        if mode in {"inject", "preserve_template"}:
            return mode

        return "inject"

    @classmethod
    def should_auto_force_chart(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        has_tree: bool = False,
        has_chart: bool = False,
    ) -> bool:
        if has_tree or has_chart:
            return False

        profile = presentation_profile_service().resolve_profile(path, entity)

        if str(profile.get("chartPolicy") or "auto").strip().lower() == "skip":
            return False

        flags = presentation_profile_service().flags(path, entity)

        return not (flags & {"tree", "analyser"})

    @classmethod
    def _generic_default_preferred_format(
        cls,
        *,
        has_tree: bool,
        has_table: bool,
        has_chart: bool,
        has_text: bool,
        has_kpi: bool,
    ) -> str | None:
        if has_kpi:
            return "kpi"

        if has_chart:
            return "chart"

        if has_table:
            return "table"

        if has_text:
            return "text"

        return None

