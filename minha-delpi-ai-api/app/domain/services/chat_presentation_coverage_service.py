"""Matriz de cobertura de apresentação — OpenAPI api-delpi × perfis do chat (Fase 0)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.openapi_operation_contract_service import (
    OpenApiOperationContractService,
)
from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

_RICH_PRODUCT_PATH_TOKENS: tuple[str, ...] = (
    "/analyser",
    "/factory-status",
    "/production-status",
    "/shipping-status",
    "/structure/exclusivity",
    "/raw-material-price-intelligence",
    "/cost-impact-simulation",
    "/last-purchase",
    "/purchase-price-history",
    "/purchase-budget-history",
    "/pricing",
    "/purchases",
)

_TIER_ORDER = ("A", "B", "C", "D")
_HUMANIZED_SHAPE_IDS = frozenset(
    {
        "field_value_profile",
        "generic_list",
        "categorical_ranking",
        "time_series",
        "hierarchy",
        "kpi_set",
        "empty_list",
        "large_list",
        "truncated",
        "logical_error",
    }
)

_SKIP_PROFILE_CONTRACT_ENTITIES = frozenset(
    {
        "sql_result",
        "protheus_table",
        "protheus_column",
        "protheus_index",
        "protheus_relation",
        "protheus_table_schema",
    }
)


@dataclass(frozen=True)
class PresentationCoverageRow:
    method: str
    path: str
    operation_id: str
    tags: tuple[str, ...]
    entity: str | None
    entity_routed: bool
    tier: str
    routed_by: str
    profile_key: str
    commentary_profile_key: str | None = None
    narrative_policy: str | None = None
    data_shape: str | None = None
    supported_formats: str | None = None
    default_view: str | None = None
    has_narrative: bool = False
    has_limitations: bool = False
    has_recommendations: bool = False
    has_shape_test: bool = False
    humanized_gaps: str | None = None


@dataclass(frozen=True)
class PresentationCoverageGap:
    kind: str
    operation_id: str
    path: str
    entity: str | None
    tier: str
    profile_key: str
    detail: str


@dataclass(frozen=True)
class VisualBuilderWarning:
    profile_key: str
    view: str
    detail: str


_CHART_VIEW_TOKENS = frozenset(
    {
        "chart",
        "line_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
        "grouped_bar",
        "stacked_bar",
    }
)
_VISUAL_BUILDER_VIEWS = frozenset({"kpi", "tree", "chart", "dashboard"})


class ChatPresentationCoverageService:
    @classmethod
    def default_openapi_baseline_path(cls) -> Path:
        repo_root = Path(__file__).resolve().parents[4]
        return repo_root / "api-delpi" / "app" / "content" / "openapi_baseline.json"

    @classmethod
    def default_stored_baseline_path(cls) -> Path:
        repo_root = Path(__file__).resolve().parents[3]
        return repo_root / "docs" / "architecture" / "presentation-coverage-baseline.json"

    @classmethod
    def _openapi_candidates(cls, baseline_path: Path | None = None) -> list[Path]:
        if baseline_path is not None:
            return [baseline_path]

        repo_root = Path(__file__).resolve().parents[4]
        return [
            repo_root / "api-delpi" / "app" / "content" / "openapi_baseline.json",
            Path(__file__).resolve().parents[3]
            / "docs"
            / "architecture"
            / "openapi_baseline.snapshot.json",
        ]

    @classmethod
    def _operations_from_stored_baseline(cls) -> list[dict[str, Any]]:
        stored = cls.load_stored_baseline()
        rows = stored.get("rows") or []
        operations: list[dict[str, Any]] = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            operation_id = str(row.get("operation_id") or row.get("operationId") or "").strip()

            if not operation_id:
                continue

            raw_tags = row.get("tags") or []
            tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]

            operations.append(
                {
                    "method": str(row.get("method") or "GET").upper(),
                    "path": str(row.get("path") or "").strip(),
                    "operationId": operation_id,
                    "tags": tags,
                }
            )

        return operations

    @classmethod
    def load_openapi_operations(cls, baseline_path: Path | None = None) -> list[dict[str, Any]]:
        for candidate in cls._openapi_candidates(baseline_path):
            if not candidate.is_file():
                continue

            payload = json.loads(candidate.read_text(encoding="utf-8"))
            operations = payload.get("operations")

            if not isinstance(operations, list):
                raise ValueError(f"OpenAPI baseline inválido: campo operations ausente ({candidate})")

            return [op for op in operations if isinstance(op, dict)]

        fallback = cls._operations_from_stored_baseline()

        if fallback:
            return fallback

        raise FileNotFoundError(
            "OpenAPI baseline não encontrado e docs/architecture/presentation-coverage-baseline.json está vazio"
        )

    @classmethod
    def load_stored_baseline(cls, baseline_path: Path | None = None) -> dict[str, Any]:
        path = baseline_path or cls.default_stored_baseline_path()

        if not path.is_file():
            return {"summary": {}, "rows": []}

        payload = json.loads(path.read_text(encoding="utf-8"))

        return payload if isinstance(payload, dict) else {"summary": {}, "rows": []}

    @classmethod
    def resolve_entity_for_path(cls, path: str) -> tuple[str | None, str]:
        profile = ChatOperationalResponseProfileService.resolve({}, path=path)
        return profile.entity, profile.routed_by

    @classmethod
    def resolve_profile_key(cls, *, path: str, entity: str | None) -> str:
        return ChatPresentationProfileService.resolve_profile_key(path, entity)

    @classmethod
    def registered_profile_keys(cls) -> frozenset[str]:
        profiles = ChatPresentationProfileService.node("profiles")

        if not isinstance(profiles, dict):
            return frozenset({"generic"})

        return frozenset(str(key) for key in profiles.keys()) | {"generic"}

    @classmethod
    def classify_tier(cls, *, entity: str | None, path: str) -> str:
        lowered = str(path or "").lower()

        if entity in ChatOperationalResponseProfileService.SQL_PRESENT_ENTITIES:
            return "D"

        if entity in ChatOperationalResponseProfileService.SYSTEM_PRESENT_ENTITIES:
            return "D"

        if entity and entity in ChatOperationalResponseProfileService.PROFILE_PRESENT_ENTITIES:
            if any(token in lowered for token in _RICH_PRODUCT_PATH_TOKENS):
                return "A"

            if any(
                token in lowered
                for token in ("/stock", "/structure", "/parents", "/guide", "/inspection")
            ):
                return "A"

            return "A"

        if entity and (
            entity in ChatOperationalResponseProfileService.KPI_PRESENT_ENTITIES
            or entity in ChatOperationalResponseProfileService.LMP_PRESENT_ENTITIES
        ):
            return "B"

        if entity and entity in ChatOperationalResponseProfileService.ENTITY_ROUTED_FOR_PRESENT:
            return "B"

        if entity:
            return "C"

        return "C"

    @classmethod
    def build_row(cls, operation: dict[str, Any]) -> PresentationCoverageRow:
        method = str(operation.get("method") or "GET").upper()
        path = str(operation.get("path") or "").strip()
        operation_id = str(operation.get("operationId") or "").strip()
        raw_tags = operation.get("tags") or []
        tags = tuple(str(tag).strip() for tag in raw_tags if str(tag).strip())

        entity, routed_by = cls.resolve_entity_for_path(path)
        tier = cls.classify_tier(entity=entity, path=path)
        entity_routed = ChatOperationalResponseProfileService.is_entity_routed_for_present(entity)
        profile_key = ChatPresentationProfileService.resolve_effective_profile_key(
            path,
            entity,
            operation_id=operation_id,
        )
        profile = ChatPresentationProfileService.build_resolved_profile(
            path=path,
            entity=entity,
            shape=OpenApiOperationContractService.shape_for_operation(operation_id)
            or OpenApiOperationContractService.shape_for_entity(entity),
        )
        commentary_profile_key = ChatPresentationProfileService.commentary_profile_key(
            profile_key,
            path=path,
            entity=entity,
        )
        narrative_policy = str(profile.get("narrativePolicy") or "").strip() or None
        humanized = cls._resolve_humanized_coverage_fields(
            profile=profile,
            profile_key=profile_key,
            commentary_profile_key=commentary_profile_key,
            tier=tier,
        )

        return PresentationCoverageRow(
            method=method,
            path=path,
            operation_id=operation_id,
            tags=tags,
            entity=entity,
            entity_routed=entity_routed,
            tier=tier,
            routed_by=routed_by,
            profile_key=profile_key,
            commentary_profile_key=commentary_profile_key,
            narrative_policy=narrative_policy,
            data_shape=humanized["data_shape"],
            supported_formats=humanized["supported_formats"],
            default_view=humanized["default_view"],
            has_narrative=humanized["has_narrative"],
            has_limitations=humanized["has_limitations"],
            has_recommendations=humanized["has_recommendations"],
            has_shape_test=humanized["has_shape_test"],
            humanized_gaps=humanized["humanized_gaps"],
        )

    @classmethod
    def build_matrix(
        cls,
        *,
        baseline_path: Path | None = None,
    ) -> list[PresentationCoverageRow]:
        operations = cls.load_openapi_operations(baseline_path)
        return [cls.build_row(operation) for operation in operations]

    @classmethod
    def summarize(cls, rows: list[PresentationCoverageRow]) -> dict[str, Any]:
        tier_counts: dict[str, int] = {tier: 0 for tier in _TIER_ORDER}
        routed_count = 0
        entity_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}
        tier_ab_profile_mapped = 0
        tier_ab_count = 0
        stack_layout_count = 0

        for row in rows:
            tier_counts[row.tier] = tier_counts.get(row.tier, 0) + 1

            if row.entity_routed:
                routed_count += 1

            if row.entity:
                entity_counts[row.entity] = entity_counts.get(row.entity, 0) + 1

            for tag in row.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            if row.tier in {"A", "B"}:
                tier_ab_count += 1

                if row.tier == "B" or row.profile_key != "generic":
                    tier_ab_profile_mapped += 1

        unmapped = sum(1 for row in rows if not row.entity)
        tier_b_plus = tier_counts.get("A", 0) + tier_counts.get("B", 0)
        operation_count = len(rows)

        metrics = {
            "tierBPlusCount": tier_b_plus,
            "tierBPlusRatio": round(tier_b_plus / operation_count, 4) if operation_count else 0.0,
            "tierABProfileMappedRatio": round(
                tier_ab_profile_mapped / tier_ab_count,
                4,
            )
            if tier_ab_count
            else 0.0,
            "stackLayoutRatio": round(stack_layout_count / operation_count, 4)
            if operation_count
            else 0.0,
            "sessionFormatRespectedRatio": None,
        }

        return {
            "operationCount": operation_count,
            "tierCounts": tier_counts,
            "entityRoutedCount": routed_count,
            "entityRoutedRatio": round(routed_count / operation_count, 4) if operation_count else 0.0,
            "unmappedEntityCount": unmapped,
            "distinctEntities": len(entity_counts),
            "topTags": sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:12],
            "profileCoverageRatio": ChatOperationalResponseProfileService.profile_coverage_ratio(),
            "entityPathHintCount": len(ChatPresentationProfileService.entity_path_hints()),
            "pathEntityFallbackCount": len(
                ChatPresentationProfileService.path_entity_fallbacks()
            ),
            "metrics": metrics,
        }

    @classmethod
    def build_entity_contract_cases(cls) -> tuple[dict[str, str], ...]:
        cases: list[dict[str, str]] = []

        for entity in sorted(ChatOperationalResponseProfileService.ENTITY_ROUTED_FOR_PRESENT):
            if entity in _SKIP_PROFILE_CONTRACT_ENTITIES:
                continue

            path = ChatPresentationProfileService.entity_path_hint(entity)

            if not path:
                continue

            cases.append(
                {
                    "entity": entity,
                    "path": path,
                    "tier": cls.classify_tier(entity=entity, path=path),
                }
            )

        return tuple(cases)

    @classmethod
    def find_profile_gaps(cls, rows: list[PresentationCoverageRow]) -> list[PresentationCoverageGap]:
        registered = cls.registered_profile_keys()
        gaps: list[PresentationCoverageGap] = []

        for row in rows:
            if row.tier not in {"A", "B"} or not row.entity:
                continue

            if row.profile_key not in registered:
                gaps.append(
                    PresentationCoverageGap(
                        kind="missing_profile_key",
                        operation_id=row.operation_id,
                        path=row.path,
                        entity=row.entity,
                        tier=row.tier,
                        profile_key=row.profile_key,
                        detail=f"profileKey «{row.profile_key}» ausente em presentation_profiles.json",
                    )
                )

            if row.tier == "A" and row.profile_key == "generic":
                if OpenApiPresentationProfileDeriverService.is_openapi_backed_entity(row.entity):
                    continue

                gaps.append(
                    PresentationCoverageGap(
                        kind="tier_a_generic_profile",
                        operation_id=row.operation_id,
                        path=row.path,
                        entity=row.entity,
                        tier=row.tier,
                        profile_key=row.profile_key,
                        detail="rota tier A exige perfil dedicado (não generic)",
                    )
                )

        return gaps

    @classmethod
    def find_entity_set_profile_gaps(cls) -> list[PresentationCoverageGap]:
        gaps: list[PresentationCoverageGap] = []

        for contract_key, contract in ChatPresentationProfileService.entity_set_profile_contracts().items():
            expected = str(contract.get("profileKey") or "").strip()
            allowed = frozenset(contract.get("allowedProfileKeys") or (expected,))
            disallowed = frozenset(contract.get("disallowedProfileKeys") or ())
            entity_set = contract.get("entitySet") or frozenset()

            for entity in sorted(entity_set):
                path = ChatPresentationProfileService.entity_path_hint(entity) or None
                resolved = ChatPresentationProfileService.resolve_effective_profile_key(
                    path,
                    entity,
                )
                operation_id = str(entity)
                path_label = path or f"entity:{entity}"

                if resolved not in allowed:
                    gaps.append(
                        PresentationCoverageGap(
                            kind="entity_set_profile_mismatch",
                            operation_id=operation_id,
                            path=path_label,
                            entity=entity,
                            tier="A",
                            profile_key=resolved,
                            detail=(
                                f"contrato «{contract_key}» exige perfil entre {sorted(allowed)}, "
                                f"resolvido «{resolved}»"
                            ),
                        )
                    )

                if resolved in disallowed:
                    gaps.append(
                        PresentationCoverageGap(
                            kind="entity_set_profile_disallowed",
                            operation_id=operation_id,
                            path=path_label,
                            entity=entity,
                            tier="A",
                            profile_key=resolved,
                            detail=(
                                f"contrato «{contract_key}» proíbe perfil «{resolved}» "
                                f"(esperado «{expected}»)"
                            ),
                        )
                    )

                if path and contract.get("validatePathWithoutEntity"):
                    path_only = ChatPresentationProfileService.resolve_effective_profile_key(
                        path,
                        ChatPresentationProfileService.resolve_entity_from_path(path),
                    )

                    if path_only in disallowed:
                        gaps.append(
                            PresentationCoverageGap(
                                kind="entity_set_path_rule_conflict",
                                operation_id=operation_id,
                                path=path,
                                entity=entity,
                                tier="A",
                                profile_key=path_only,
                                detail=(
                                    f"path «{path}» sem entity resolve «{path_only}» — "
                                    f"conflita com contrato «{contract_key}»"
                                ),
                            )
                        )

        return gaps

    @classmethod
    def find_commentary_profile_gaps(
        cls,
        rows: list[PresentationCoverageRow],
    ) -> list[PresentationCoverageGap]:
        gaps: list[PresentationCoverageGap] = []

        for row in rows:
            if row.tier != "A" or not row.entity:
                continue

            profile = ChatPresentationProfileService.profile(row.profile_key)
            explicit = str(profile.get("commentaryProfileKey") or "").strip()

            if explicit:
                continue

            if row.commentary_profile_key:
                continue

            gaps.append(
                PresentationCoverageGap(
                    kind="missing_commentary_profile",
                    operation_id=row.operation_id,
                    path=row.path,
                    entity=row.entity,
                    tier=row.tier,
                    profile_key=row.profile_key,
                    detail=(
                        f"perfil «{row.profile_key}» tier A sem commentaryProfileKey "
                        "declarativo em presentation_profiles.json"
                    ),
                )
            )

        return gaps

    @classmethod
    def validate_commentary_profiles_for_ci(
        cls,
        *,
        openapi_baseline_path: Path | None = None,
    ) -> dict[str, Any]:
        rows = cls.build_matrix(baseline_path=openapi_baseline_path)
        gaps = cls.find_commentary_profile_gaps(rows)

        return {
            "commentaryProfileGaps": [asdict(gap) for gap in gaps],
            "gapCount": len(gaps),
            "ok": not gaps,
        }

    @classmethod
    def find_new_operations(
        cls,
        rows: list[PresentationCoverageRow],
        *,
        stored_baseline: dict[str, Any] | None = None,
    ) -> list[PresentationCoverageRow]:
        baseline = stored_baseline or cls.load_stored_baseline()
        stored_rows = baseline.get("rows") or []
        known_ids = {
            str(item.get("operation_id") or item.get("operationId") or "").strip()
            for item in stored_rows
            if isinstance(item, dict)
        }
        known_ids.discard("")

        return [row for row in rows if row.operation_id not in known_ids]

    @classmethod
    def validate_new_operations(
        cls,
        new_rows: list[PresentationCoverageRow],
    ) -> list[PresentationCoverageGap]:
        gaps: list[PresentationCoverageGap] = []

        for row in new_rows:
            if not row.entity:
                gaps.append(
                    PresentationCoverageGap(
                        kind="new_operation_without_entity",
                        operation_id=row.operation_id,
                        path=row.path,
                        entity=row.entity,
                        tier=row.tier,
                        profile_key=row.profile_key,
                        detail="nova operação OpenAPI sem meta.entity/path mapeado",
                    )
                )

            if row.tier == "A" and row.profile_key == "generic":
                if OpenApiPresentationProfileDeriverService.is_openapi_backed_entity(row.entity):
                    continue

                gaps.append(
                    PresentationCoverageGap(
                        kind="new_operation_generic_profile",
                        operation_id=row.operation_id,
                        path=row.path,
                        entity=row.entity,
                        tier=row.tier,
                        profile_key=row.profile_key,
                        detail="nova operação tier A precisa de perfil JSON antes do merge",
                    )
                )

        return gaps

    @classmethod
    def validate_for_ci(
        cls,
        *,
        openapi_baseline_path: Path | None = None,
        stored_baseline_path: Path | None = None,
    ) -> dict[str, Any]:
        rows = cls.build_matrix(baseline_path=openapi_baseline_path)
        stored = cls.load_stored_baseline(stored_baseline_path)
        profile_gaps = cls.find_profile_gaps(rows)
        entity_set_profile_gaps = cls.find_entity_set_profile_gaps()
        new_rows = cls.find_new_operations(rows, stored_baseline=stored)
        new_gaps = cls.validate_new_operations(new_rows)
        summary = cls.summarize(rows)

        return {
            "summary": summary,
            "profileGaps": [asdict(gap) for gap in profile_gaps],
            "entitySetProfileGaps": [asdict(gap) for gap in entity_set_profile_gaps],
            "newOperations": [asdict(row) for row in new_rows],
            "newOperationGaps": [asdict(gap) for gap in new_gaps],
            "ok": not profile_gaps and not entity_set_profile_gaps and not new_gaps,
        }

    @classmethod
    def _builder_key_for_view(cls, view: str) -> str | None:
        token = str(view or "").strip().lower()

        if token in {"kpi", "tree", "dashboard"}:
            return token

        if token in _CHART_VIEW_TOKENS:
            return "chart"

        return None

    @classmethod
    def find_visual_builder_warnings(cls) -> list[VisualBuilderWarning]:
        profiles = ChatPresentationProfileService.node("profiles") or {}
        tier_a_keys = frozenset(ChatPresentationVocabularyService.playbook12_tier_a_profile_keys())
        warnings: list[VisualBuilderWarning] = []

        if not isinstance(profiles, dict):
            return warnings

        defaults = ChatPresentationProfileService.node("defaults") or {}

        for profile_key in sorted(profiles):
            if profile_key not in tier_a_keys:
                continue

            profile = profiles.get(profile_key)

            if not isinstance(profile, dict):
                continue

            strategy = str(
                profile.get("presentationStrategy")
                or defaults.get("presentationStrategy")
                or "as_delivered"
            ).strip().lower()

            if strategy != "legacy":
                continue

            view_order = profile.get("viewOrder") or []
            builders = profile.get("visualBuilders") or {}
            builder_map = builders if isinstance(builders, dict) else {}
            seen_builder_keys: set[str] = set()

            for view in view_order:
                builder_key = cls._builder_key_for_view(str(view))

                if not builder_key or builder_key in seen_builder_keys:
                    continue

                seen_builder_keys.add(builder_key)

                if builder_key not in _VISUAL_BUILDER_VIEWS:
                    continue

                if str(builder_map.get(builder_key) or "").strip():
                    continue

                warnings.append(
                    VisualBuilderWarning(
                        profile_key=str(profile_key),
                        view=str(view),
                        detail=(
                            f"viewOrder inclui «{view}» mas visualBuilders.{builder_key} "
                            "não está declarado"
                        ),
                    )
                )

        return warnings

    @classmethod
    def validate_visual_builders_for_ci(cls) -> dict[str, Any]:
        warnings = cls.find_visual_builder_warnings()

        return {
            "visualBuilderWarnings": [asdict(item) for item in warnings],
            "warningCount": len(warnings),
        }

    @classmethod
    def _shape_from_profile(
        cls,
        *,
        profile: dict[str, Any],
        commentary_profile_key: str | None,
    ) -> str:
        default_view = str(profile.get("defaultView") or "").strip().lower()
        shape_by_view = {
            "kpi": "kpi_set",
            "table": "generic_list",
            "line_chart": "time_series",
            "horizontal_bar": "categorical_ranking",
            "bar_chart": "categorical_ranking",
            "donut": "categorical_ranking",
            "tree": "hierarchy",
            "text": "field_value_profile",
            "dashboard": "kpi_set",
        }

        if default_view in shape_by_view:
            return shape_by_view[default_view]

        commentary = str(commentary_profile_key or "").strip()

        if commentary in {"factory_status", "production_status", "shipping_status"}:
            return "field_value_profile"

        if commentary == "stock":
            return "generic_list"

        if commentary == "structure_exclusivity":
            return "hierarchy"

        return commentary or "generic_list"

    @classmethod
    def _resolve_humanized_coverage_fields(
        cls,
        *,
        profile: dict[str, Any],
        profile_key: str,
        commentary_profile_key: str | None,
        tier: str,
    ) -> dict[str, Any]:
        default_view = str(profile.get("defaultView") or profile.get("defaultPrimary") or "").strip()
        view_order = profile.get("viewOrder") or []
        formats: list[str] = []

        if default_view:
            formats.append(default_view)

        if isinstance(view_order, list):
            for view in view_order:
                token = str(view or "").strip()

                if token and token not in formats:
                    formats.append(token)

        narrative_mode = str(profile.get("humanizedNarrative") or "enrich").strip().lower()
        commentary = str(commentary_profile_key or "").strip()
        has_narrative = narrative_mode != "skip" and bool(commentary)
        has_limitations = bool(ChatHumanizedDataResponseContentService.get_node("limitations"))
        has_recommendations = bool(
            ChatHumanizedDataResponseContentService.recommendation_queries(commentary)
        )
        data_shape = cls._shape_from_profile(
            profile=profile,
            commentary_profile_key=commentary_profile_key,
        )
        has_shape_test = data_shape in _HUMANIZED_SHAPE_IDS
        gap_tokens: list[str] = []

        if tier == "A":
            if narrative_mode == "enrich" and not commentary:
                gap_tokens.append("missing_commentary_profile")

            if narrative_mode == "enrich" and commentary and not has_recommendations:
                gap_tokens.append("missing_recommendation_queries")

            if narrative_mode == "enrich" and not has_shape_test:
                gap_tokens.append("missing_shape_fixture")

        return {
            "data_shape": data_shape or None,
            "supported_formats": "|".join(formats) if formats else None,
            "default_view": default_view or None,
            "has_narrative": has_narrative,
            "has_limitations": has_limitations,
            "has_recommendations": has_recommendations,
            "has_shape_test": has_shape_test,
            "humanized_gaps": "|".join(gap_tokens) if gap_tokens else None,
        }

    @classmethod
    def find_humanized_coverage_gaps(
        cls,
        rows: list[PresentationCoverageRow],
    ) -> list[str]:
        gaps: list[str] = []

        for row in rows:
            if row.tier != "A":
                continue

            for gap_code in (row.humanized_gaps or "").split("|"):
                token = gap_code.strip()

                if token:
                    gaps.append(f"{row.operation_id}: {token}")

        return gaps

    @classmethod
    def build_report(
        cls,
        *,
        baseline_path: Path | None = None,
    ) -> dict[str, Any]:
        rows = cls.build_matrix(baseline_path=baseline_path)
        summary = cls.summarize(rows)

        return {
            "summary": summary,
            "rows": [asdict(row) for row in rows],
        }

    @classmethod
    def rows_to_csv(cls, rows: list[PresentationCoverageRow]) -> str:
        header = (
            "method,path,operation_id,tags,entity,entity_routed,tier,routed_by,profile_key,"
            "commentary_profile_key,narrative_policy,data_shape,supported_formats,default_view,"
            "has_narrative,has_limitations,has_recommendations,has_shape_test,humanized_gaps"
        )
        lines = [header]

        for row in rows:
            tags = "|".join(row.tags)
            entity = row.entity or ""
            lines.append(
                ",".join(
                    [
                        row.method,
                        cls._csv_cell(row.path),
                        cls._csv_cell(row.operation_id),
                        cls._csv_cell(tags),
                        cls._csv_cell(entity),
                        "true" if row.entity_routed else "false",
                        row.tier,
                        row.routed_by,
                        row.profile_key,
                        cls._csv_cell(row.commentary_profile_key or ""),
                        cls._csv_cell(row.narrative_policy or ""),
                        cls._csv_cell(row.data_shape or ""),
                        cls._csv_cell(row.supported_formats or ""),
                        cls._csv_cell(row.default_view or ""),
                        "true" if row.has_narrative else "false",
                        "true" if row.has_limitations else "false",
                        "true" if row.has_recommendations else "false",
                        "true" if row.has_shape_test else "false",
                        cls._csv_cell(row.humanized_gaps or ""),
                    ]
                )
            )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _csv_cell(value: str) -> str:
        if any(char in value for char in (",", '"', "\n")):
            return '"' + value.replace('"', '""') + '"'

        return value
