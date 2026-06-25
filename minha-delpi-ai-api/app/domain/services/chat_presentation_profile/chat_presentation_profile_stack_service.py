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



class ChatPresentationProfileStackService:
    @classmethod
    def stack_plan_config(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        presentation_mode: str | None = None,
    ) -> dict[str, Any]:
        mode = str(presentation_mode or "").strip()

        if mode == "summary_then_evidence":
            return presentation_profile_service().stack_plan_config_for_evidence_first(path, entity)

        profile = presentation_profile_service().resolve_profile(path, entity)
        stack_key = str(profile.get("stackPlan") or "default").strip() or "default"
        resolved = presentation_profile_service().node("stackPlans", stack_key)

        if isinstance(resolved, dict):
            return dict(resolved)

        default_plan = presentation_profile_service().node("stackPlans", "default")

        return dict(default_plan) if isinstance(default_plan, dict) else {}

    @classmethod
    def stack_plan_config_for_evidence_first(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        base = presentation_profile_service().node("stackPlans", "summary_then_evidence")
        plan = dict(base) if isinstance(base, dict) else {}
        route_plan = presentation_profile_service().stack_plan_config(path, entity)

        if route_plan.get("tableRoleOrder"):
            plan["tableRoleOrder"] = list(route_plan["tableRoleOrder"])

        base_rules = dict(plan.get("sectionRules") or {})
        route_rules = dict(route_plan.get("sectionRules") or {})

        if route_rules.get("presentationProfile"):
            base_rules["presentationProfile"] = route_rules["presentationProfile"]

        if route_rules.get("framing"):
            base_rules["framing"] = route_rules["framing"]

        route_visibility = route_rules.get("visibility")

        if isinstance(route_visibility, dict):
            merged_visibility = dict(base_rules.get("visibility") or {})

            for section in ("guide", "inspection"):
                if section in route_visibility:
                    merged_visibility[section] = route_visibility[section]

            base_rules["visibility"] = merged_visibility

        plan["sectionRules"] = base_rules
        plan["profileFirst"] = False
        plan["highlightsAfterProfile"] = False
        return plan

