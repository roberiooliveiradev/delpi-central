"""Perfis declarativos de apresentação — rotas e entidades api-delpi (Fase 2)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)
from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.openapi_operation_contract_service import (
    OpenApiOperationContractService,
)


class ChatPresentationProfileService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_profiles"

    _SESSION_FORMAT_ALIASES = {
        "topics": "text",
    }

    @classmethod
    def entity_set(cls, set_key: str) -> frozenset[str]:
        raw = cls.node("entitySets", str(set_key or "").strip())

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(
            str(item).strip()
            for item in raw
            if str(item).strip()
        )

    @classmethod
    def is_enriched_openapi_presentation(
        cls,
        *,
        delpi_metadata: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> bool:
        if isinstance(profile, dict):
            if str(profile.get("openapiPresentationStrategy") or "").strip().lower() == "enriched":
                return True

        if not isinstance(delpi_metadata, dict):
            return False

        presentation = delpi_metadata.get("presentation")

        if not isinstance(presentation, dict):
            return False

        return str(presentation.get("strategy") or "").strip().lower() == "enriched"

    @classmethod
    def allows_automatic_rich_stack(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if isinstance(metadata, dict):
            cached = metadata.get("presentationProfile")

            if isinstance(cached, dict) and cls.is_enriched_openapi_presentation(profile=cached):
                profile = cached
            else:
                profile = cls.resolve_profile(
                    path,
                    entity,
                    delpi_metadata=delpi_metadata or metadata.get("delpiMetadata"),
                    metadata=metadata,
                )
        else:
            profile = cls.resolve_profile(
                path,
                entity,
                delpi_metadata=delpi_metadata,
            )

        if not cls.is_enriched_openapi_presentation(
            delpi_metadata=delpi_metadata,
            profile=profile,
        ):
            return False

        stack_policy = str(profile.get("stackLayoutPolicy") or "on_demand").strip().lower()

        return stack_policy == "always"

    @classmethod
    def _stamp_openapi_presentation_strategy(
        cls,
        profile: dict[str, Any],
        delpi_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if cls.is_enriched_openapi_presentation(delpi_metadata=delpi_metadata):
            profile["openapiPresentationStrategy"] = "enriched"

        return profile

    @classmethod
    def uses_schema_first_presentation(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> bool:
        """Playbook 22 — default global: API as-delivered; legacy só com flag explícita."""
        profile_key = str(cls.resolve_profile_key(path, entity)).strip()
        profile_only = cls.profile(profile_key)
        explicit = str(profile_only.get("presentationStrategy") or "").strip().lower()

        return explicit != "legacy"

    @classmethod
    def is_rich_stack_profile(cls, profile_key: str | None) -> bool:
        key = str(profile_key or "").strip()

        if not key:
            return False

        profile_only = cls.profile(key)
        defaults = cls.node("defaults") or {}
        strategy = str(
            profile_only.get("presentationStrategy")
            or defaults.get("presentationStrategy")
            or "as_delivered"
        ).strip().lower()

        if strategy != "legacy":
            return False

        if key in cls.entity_set("richStackProfiles"):
            return True

        merged = dict(defaults)
        merged.update(profile_only)

        return str(merged.get("stackLayoutPolicy") or "on_demand").strip().lower() == "always"

    @classmethod
    def uses_presentation_table_assembly(cls, entity: str | None) -> bool:
        """Deprecated — table assembly removido; mantido para compat de gates legados."""
        return False

    @classmethod
    def entity_routed_for_present(cls) -> frozenset[str]:
        merged: set[str] = set()

        for key in (
            "profilePresent",
            "kpiPresent",
            "lmpPresent",
            "sqlPresent",
            "systemPresent",
            "saleOrderPresent",
            "entityRoutedExtra",
        ):
            merged.update(cls.entity_set(key))

        return frozenset(merged)

    @classmethod
    def entity_presentation_routing(cls) -> dict[str, Any]:
        node = cls.node("entityPresentationRouting")

        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def prose_delivery_mode(
        cls,
        *,
        entity: str | None = None,
        path: str | None = None,
    ) -> str | None:
        """P3.2 — modo canônico de prosa por entidade ou perfil declarativo."""
        allowed = frozenset({"template", "llm", "direct"})
        token = str(entity or "").strip()
        by_entity = cls.node("proseDeliveryByEntity")

        if isinstance(by_entity, dict) and token:
            mode = str(by_entity.get(token) or "").strip().lower()

            if mode in allowed:
                return mode

        if not path and not token:
            return None

        profile_key = cls.resolve_profile_key(path, entity)
        by_profile = cls.node("proseDeliveryByProfile")

        if isinstance(by_profile, dict):
            mode = str(by_profile.get(profile_key) or "").strip().lower()

            if mode in allowed:
                return mode

        if token:
            by_entity_set = cls.node("proseDeliveryByEntitySet")

            if isinstance(by_entity_set, dict):
                for set_key, configured in by_entity_set.items():
                    if token not in cls.entity_set(str(set_key or "")):
                        continue

                    mode = str(configured or "").strip().lower()

                    if mode in allowed:
                        return mode

        if token or path:
            from app.domain.services.chat_presentation_coverage_service import (
                ChatPresentationCoverageService,
            )
            from app.domain.services.chat_presentation_prose_delivery_content_service import (
                ChatPresentationProseDeliveryContentService,
            )

            tier = ChatPresentationCoverageService.classify_tier(
                entity=token or None,
                path=str(path or ""),
            )
            tier_mode = ChatPresentationProseDeliveryContentService.prose_delivery_mode_for_tier(
                tier,
            )

            if tier_mode in allowed:
                return tier_mode

        return None

    @classmethod
    def operational_empty_route_key(cls, entity: str | None) -> str | None:
        mapping = cls.entity_presentation_routing().get("operationalEmptyKeys") or {}
        token = str(entity or "").strip()
        key = mapping.get(token) if token else None

        return str(key) if key else None

    @classmethod
    def is_product_operational_entity(cls, entity: str | None) -> bool:
        token = str(entity or "").strip()
        entities = cls.entity_presentation_routing().get("productOperationalEntities") or []

        return bool(token and token in entities)

    @classmethod
    def list_route_entity(cls, entity: str | None) -> str | None:
        mapping = cls.entity_presentation_routing().get("listRouteEntities") or {}
        token = str(entity or "").strip()
        route = mapping.get(token) if token else None

        return str(route) if route else None

    @classmethod
    def is_no_chart_entity(cls, entity: str | None) -> bool:
        token = str(entity or "").strip()
        entities = cls.entity_presentation_routing().get("noChartEntities") or []

        return bool(token and token in entities)

    @classmethod
    def entity_set_profile_contracts(cls) -> dict[str, dict[str, Any]]:
        raw = cls.node("entitySetProfileContracts")

        if not isinstance(raw, dict):
            return {}

        resolved: dict[str, dict[str, Any]] = {}

        for contract_key, contract in raw.items():
            if not isinstance(contract, dict):
                continue

            set_key = str(contract.get("entitySetKey") or contract_key).strip()
            profile_key = str(contract.get("profileKey") or "").strip()
            allowed = [
                str(item).strip()
                for item in (contract.get("allowedProfileKeys") or [profile_key])
                if str(item).strip()
            ]
            disallowed = [
                str(item).strip()
                for item in (contract.get("disallowedProfileKeys") or [])
                if str(item).strip()
            ]

            if not set_key or not profile_key:
                continue

            resolved[str(contract_key).strip()] = {
                "entitySetKey": set_key,
                "profileKey": profile_key,
                "allowedProfileKeys": tuple(allowed or [profile_key]),
                "disallowedProfileKeys": tuple(disallowed),
                "validatePathWithoutEntity": contract.get("validatePathWithoutEntity") is True,
                "entitySet": cls.entity_set(set_key),
            }

        return resolved

    @classmethod
    def resolve_profile_contract(
        cls,
        entity: str | None,
        *,
        path: str | None = None,
    ) -> dict[str, Any] | None:
        token = str(entity or "").strip()

        if not token:
            return None

        for contract in cls.entity_set_profile_contracts().values():
            if token in contract.get("entitySet") or frozenset():
                resolved_key = cls.resolve_profile_key(path, token)

                return {
                    **contract,
                    "entity": token,
                    "resolvedProfileKey": resolved_key,
                    "matchesExpected": resolved_key in set(contract.get("allowedProfileKeys") or ()),
                    "isDisallowed": resolved_key in set(contract.get("disallowedProfileKeys") or ()),
                }

        return None

    @classmethod
    def entity_path_hints(cls) -> dict[str, str]:
        raw = cls.mapping("entityPathHints")

        return {
            str(entity): str(path)
            for entity, path in raw.items()
            if str(entity).strip() and str(path).strip()
        }

    @classmethod
    def entity_path_hint(cls, entity: str | None) -> str:
        token = str(entity or "").strip()

        if not token:
            return ""

        return str(cls.entity_path_hints().get(token) or "")

    @classmethod
    def path_entity_fallbacks(cls) -> tuple[tuple[str, str], ...]:
        rules = cls.node("pathEntityFallbacks") or []
        pairs: list[tuple[str, str]] = []

        if isinstance(rules, list):
            for rule in rules:
                if not isinstance(rule, dict):
                    continue

                fragment = str(rule.get("contains") or "").strip()
                entity = str(rule.get("entity") or "").strip()

                if fragment and entity:
                    pairs.append((fragment, entity))

        return tuple(
            sorted(pairs, key=lambda item: len(item[0]), reverse=True),
        )

    @classmethod
    def _matches_entity_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        if not hint_lower:
            return False

        if path_lower == hint_lower or path_lower.endswith(hint_lower):
            return True

        marker = "/products/"

        if marker not in hint_lower or marker not in path_lower:
            return False

        path_tail = path_lower.split(marker, 1)[1]
        hint_tail = hint_lower.split(marker, 1)[1]
        path_parts = [part for part in path_tail.split("/") if part]
        hint_parts = [part for part in hint_tail.split("/") if part]

        if not path_parts or not hint_parts:
            return False

        if hint_parts[0] not in {"0", "{code}"}:
            return False

        if not (path_parts[0].isdigit() or path_parts[0] in {"{code}", "0"}):
            return False

        return path_parts[1:] == hint_parts[1:]

    @classmethod
    def resolve_entity_from_path(cls, path: str | None) -> str | None:
        lowered = cls.path_lowered(path).rstrip("/")

        if not lowered:
            return None

        for entity, hint in cls.entity_path_hints().items():
            hint_lower = str(hint or "").lower().rstrip("/")

            if cls._matches_entity_path_hint(lowered, hint_lower):
                return entity

        for fragment, entity in cls.path_entity_fallbacks():
            if fragment in lowered:
                return entity

        parts = lowered.rstrip("/").split("/")

        if (
            len(parts) == 3
            and parts[1] == "products"
            and (parts[2].isdigit() or parts[2] in {"{code}", "0"})
        ):
            return "product"

        return None

    @classmethod
    def path_lowered(cls, path: str | None) -> str:
        return str(path or "").strip().lower()

    @classmethod
    def resolve_profile_key(cls, path: str | None, entity: str | None = None) -> str:
        entity_token = str(entity or "").strip() or cls.resolve_entity_from_path(path)

        if entity_token:
            mapped = cls.mapping("entityProfiles").get(entity_token)

            if mapped:
                return str(mapped)

            if OpenApiPresentationProfileDeriverService.is_openapi_backed_entity(entity_token):
                return "generic"

        lowered = cls.path_lowered(path)

        for rule in cls.node("pathRules") or []:
            if not isinstance(rule, dict):
                continue

            fragment = str(rule.get("contains") or "").strip().lower()

            if fragment and fragment in lowered:
                if cls._path_rule_suppressed(fragment, lowered):
                    continue

                return str(rule.get("profile") or "generic")

        return "generic"

    @classmethod
    def _path_rule_suppressed(cls, fragment: str, lowered_path: str) -> bool:
        """Evita colisões de fragmentos genéricos com rotas KPI de outros domínios."""
        if fragment == "/stock" and "/supplies/" in lowered_path:
            return True

        return False

    @classmethod
    def commentary_profile_key(
        cls,
        profile_key: str | None = None,
        *,
        path: str | None = None,
        entity: str | None = None,
    ) -> str | None:
        key = str(profile_key or "").strip()

        if not key:
            key = cls.resolve_profile_key(path, entity)

        profile = cls.profile(key)
        explicit = str(profile.get("commentaryProfileKey") or "").strip()

        if explicit:
            return explicit

        operational_keys = {
            "factory_status",
            "stock",
            "production_status",
            "shipping_status",
            "sale_pricing",
            "analyser",
        }

        if key in operational_keys:
            return key

        if key in {"table_list", "generic"}:
            return "generic_list"

        return None

    @classmethod
    def profile(cls, profile_key: str | None = None) -> dict[str, Any]:
        key = str(profile_key or "generic").strip() or "generic"
        resolved = cls.node("profiles", key)

        if isinstance(resolved, dict):
            return resolved

        defaults = cls.node("defaults")

        return defaults if isinstance(defaults, dict) else {}

    @classmethod
    def resolve_profile(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if isinstance(metadata, dict):
            cached = metadata.get("presentationProfile")

            if isinstance(cached, dict) and cached.get("profileKey"):
                return dict(cached)

            api_meta = metadata.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                shape = shape or str(api_meta.get("shape") or "").strip() or None
                entity = entity or str(api_meta.get("entity") or "").strip() or None

            delpi_metadata = delpi_metadata or metadata.get("delpiMetadata")

        return cls.build_resolved_profile(
            path=path,
            entity=entity,
            shape=shape,
            delpi_metadata=delpi_metadata,
        )

    @classmethod
    def build_resolved_profile(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entity_token = str(entity or "").strip() or None
        key = cls.resolve_profile_key(path, entity_token)

        if OpenApiPresentationProfileDeriverService.should_use_derived_profile(
            profile_key=key,
            entity=entity_token,
            shape=shape,
            delpi_metadata=delpi_metadata,
        ):
            profile = OpenApiPresentationProfileDeriverService.build_profile(
                entity=entity_token,
                shape=shape,
                delpi_metadata=delpi_metadata,
            )

            return cls._stamp_openapi_presentation_strategy(profile, delpi_metadata)

        merged = dict(cls.node("defaults") or {})
        merged.update(cls.profile(key))
        merged["profileKey"] = key

        return cls._stamp_openapi_presentation_strategy(merged, delpi_metadata)

    @classmethod
    def cache_presentation_profile(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        api_meta = metadata.get("apiDelpiResponseMeta")
        entity = None
        shape = None

        if isinstance(api_meta, dict):
            entity = str(api_meta.get("entity") or "").strip() or None
            shape = str(api_meta.get("shape") or "").strip() or None

        metadata["presentationProfile"] = cls.build_resolved_profile(
            path=metadata.get("path"),
            entity=entity,
            shape=shape,
            delpi_metadata=metadata.get("delpiMetadata"),
        )

    @classmethod
    def resolve_effective_profile_key(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        shape: str | None = None,
        operation_id: str | None = None,
    ) -> str:
        entity_token = str(entity or "").strip() or None
        shape_token = str(shape or "").strip() or None

        if not shape_token and operation_id:
            shape_token = OpenApiOperationContractService.shape_for_operation(operation_id)

        if not shape_token and entity_token:
            shape_token = OpenApiOperationContractService.shape_for_entity(entity_token)

        profile = cls.build_resolved_profile(
            path=path,
            entity=entity_token,
            shape=shape_token,
        )

        if profile.get("openapiDerived"):
            return OpenApiPresentationProfileDeriverService.json_profile_equivalent_for_shape(
                str(profile.get("openapiShape") or shape_token or ""),
            )

        return str(profile.get("profileKey") or cls.resolve_profile_key(path, entity_token))

    @classmethod
    def flags(cls, path: str | None, entity: str | None = None) -> frozenset[str]:
        profile = cls.resolve_profile(path, entity)
        raw = profile.get("flags") or []

        return frozenset(str(item).strip().lower() for item in raw if str(item).strip())

    @classmethod
    def has_flag(
        cls,
        path: str | None,
        flag: str,
        *,
        entity: str | None = None,
    ) -> bool:
        return str(flag or "").strip().lower() in cls.flags(path, entity)

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
            return cls.stack_plan_config_for_evidence_first(path, entity)

        profile = cls.resolve_profile(path, entity)
        stack_key = str(profile.get("stackPlan") or "default").strip() or "default"
        resolved = cls.node("stackPlans", stack_key)

        if isinstance(resolved, dict):
            return dict(resolved)

        default_plan = cls.node("stackPlans", "default")

        return dict(default_plan) if isinstance(default_plan, dict) else {}

    @classmethod
    def stack_plan_config_for_evidence_first(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        base = cls.node("stackPlans", "summary_then_evidence")
        plan = dict(base) if isinstance(base, dict) else {}
        route_plan = cls.stack_plan_config(path, entity)

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

    @classmethod
    def presentation_decision_config(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        profile = cls.resolve_profile(path, entity)
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

        profile = cls.resolve_profile(path, entity)
        policy = str(profile.get("defaultViewPolicy") or "generic").strip().lower()
        flags = cls.flags(path, entity)

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
        profile = cls.resolve_profile(path, entity)
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
        schema_first = cls.uses_schema_first_presentation(path, entity)
        force_stack = stack_policy == "always" and len(ordered) >= 2 and not schema_first

        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        if (
            isinstance(metadata, dict)
            and ChatPresentationTextModeService.is_user_explicit_text_mode(metadata)
        ):
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
        profile = cls.resolve_profile(path, entity)
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
        profile = cls.resolve_profile(path, entity)
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

        profile = cls.resolve_profile(path, entity)

        if str(profile.get("chartPolicy") or "auto").strip().lower() == "skip":
            return False

        flags = cls.flags(path, entity)

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
