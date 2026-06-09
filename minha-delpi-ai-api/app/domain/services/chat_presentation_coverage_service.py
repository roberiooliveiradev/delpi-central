"""Matriz de cobertura de apresentação — OpenAPI api-delpi × perfis do chat (Fase 0)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
    ENTITY_PATH_HINTS,
    PATH_ENTITY_FALLBACKS,
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
)

_TIER_ORDER = ("A", "B", "C", "D")


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


class ChatPresentationCoverageService:
    @classmethod
    def default_openapi_baseline_path(cls) -> Path:
        repo_root = Path(__file__).resolve().parents[4]
        return repo_root / "api-delpi" / "app" / "content" / "openapi_baseline.json"

    @classmethod
    def load_openapi_operations(cls, baseline_path: Path | None = None) -> list[dict[str, Any]]:
        path = baseline_path or cls.default_openapi_baseline_path()

        if not path.is_file():
            raise FileNotFoundError(f"OpenAPI baseline não encontrado: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        operations = payload.get("operations")

        if not isinstance(operations, list):
            raise ValueError("OpenAPI baseline inválido: campo operations ausente")

        return [op for op in operations if isinstance(op, dict)]

    @classmethod
    def resolve_entity_for_path(cls, path: str) -> tuple[str | None, str]:
        profile = ChatApiDelpiResponseProfileService.resolve({}, path=path)
        return profile.entity, profile.routed_by

    @classmethod
    def classify_tier(cls, *, entity: str | None, path: str) -> str:
        lowered = str(path or "").lower()

        if entity in ChatApiDelpiResponseProfileService.SQL_PRESENT_ENTITIES:
            return "D"

        if entity in ChatApiDelpiResponseProfileService.SYSTEM_PRESENT_ENTITIES:
            return "D"

        if entity and entity in ChatApiDelpiResponseProfileService.PROFILE_PRESENT_ENTITIES:
            if any(token in lowered for token in _RICH_PRODUCT_PATH_TOKENS):
                return "A"

            if any(
                token in lowered
                for token in ("/stock", "/structure", "/parents", "/guide", "/inspection")
            ):
                return "A"

            return "A"

        if entity and (
            entity in ChatApiDelpiResponseProfileService.KPI_PRESENT_ENTITIES
            or entity in ChatApiDelpiResponseProfileService.LMP_PRESENT_ENTITIES
        ):
            return "B"

        if entity and entity in ChatApiDelpiResponseProfileService.ENTITY_ROUTED_FOR_PRESENT:
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
        entity_routed = ChatApiDelpiResponseProfileService.is_entity_routed_for_present(entity)

        return PresentationCoverageRow(
            method=method,
            path=path,
            operation_id=operation_id,
            tags=tags,
            entity=entity,
            entity_routed=entity_routed,
            tier=tier,
            routed_by=routed_by,
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

        for row in rows:
            tier_counts[row.tier] = tier_counts.get(row.tier, 0) + 1

            if row.entity_routed:
                routed_count += 1

            if row.entity:
                entity_counts[row.entity] = entity_counts.get(row.entity, 0) + 1

            for tag in row.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        unmapped = sum(1 for row in rows if not row.entity)

        return {
            "operationCount": len(rows),
            "tierCounts": tier_counts,
            "entityRoutedCount": routed_count,
            "entityRoutedRatio": round(routed_count / len(rows), 4) if rows else 0.0,
            "unmappedEntityCount": unmapped,
            "distinctEntities": len(entity_counts),
            "topTags": sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:12],
            "profileCoverageRatio": ChatApiDelpiResponseProfileService.profile_coverage_ratio(),
            "entityPathHintCount": len(ENTITY_PATH_HINTS),
            "pathEntityFallbackCount": len(PATH_ENTITY_FALLBACKS),
        }

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
            "method,path,operation_id,tags,entity,entity_routed,tier,routed_by"
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
                    ]
                )
            )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _csv_cell(value: str) -> str:
        if any(char in value for char in (",", '"', "\n")):
            return '"' + value.replace('"', '""') + '"'

        return value
