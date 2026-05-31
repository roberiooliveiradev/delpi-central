"""Geração/sincronização do catálogo de funcionalidades — Playbook autoajuda, Fase 3."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.application.services.assistant_capabilities_catalog_validator import (
    AssistantCapabilitiesCatalogValidator,
)
from app.infrastructure.content.content_service import ContentService

_PRODUCT_ACTION_TOKENS: tuple[str, ...] = (
    "/products",
    "/suppliers",
    "/customers",
    "/structure",
    "/parents",
    "/purchases",
    "/prices",
    "/guide",
    "/inspection",
    "/internal-movements",
    "/inbound-invoice",
    "/outbound-invoice",
    "/search",
    "/analyser",
    "/supplies/stock-value",
    "/inventory-turnover",
    "/cpv",
    "/otd",
    "/sale-order",
    "/sales/billing",
)

_IGNORE_PATHS: frozenset[str] = frozenset({"/", "/health"})


def _path_rule(
    *,
    feature_id: str,
    markers: tuple[str, ...],
    action_token: str,
) -> dict[str, Any]:
    return {
        "featureId": feature_id,
        "pathMarkers": markers,
        "actionToken": action_token,
    }


_PATH_RULES: tuple[dict[str, Any], ...] = (
    _path_rule(
        feature_id="product_lookup",
        markers=("/products", "/product", "products"),
        action_token="/products",
    ),
    *(
        _path_rule(feature_id="product_lookup", markers=(token,), action_token=token)
        for token in _PRODUCT_ACTION_TOKENS
        if token != "/products"
    ),
    _path_rule(
        feature_id="stock_lookup",
        markers=("/stock", "estoque", "inventory"),
        action_token="/stock",
    ),
    _path_rule(
        feature_id="sales_lookup",
        markers=("/sales", "/ordens", "ordem de venda", "order"),
        action_token="/sales",
    ),
    _path_rule(
        feature_id="commercial_indicators",
        markers=("/commercial",),
        action_token="/commercial",
    ),
    _path_rule(
        feature_id="financial_indicators",
        markers=("/financial", "/finacial"),
        action_token="/financial",
    ),
    _path_rule(
        feature_id="quality_indicators",
        markers=("/quality",),
        action_token="/quality",
    ),
    _path_rule(
        feature_id="hr_indicators",
        markers=("/hr",),
        action_token="/hr",
    ),
    _path_rule(
        feature_id="engineering_lmps",
        markers=("/engineering/lmps", "/lmps/"),
        action_token="/engineering/lmps",
    ),
    _path_rule(
        feature_id="engineering_transforma",
        markers=("/engineering/transforma-mais", "transforma-mais"),
        action_token="/engineering/transforma-mais",
    ),
    _path_rule(
        feature_id="data_sql",
        markers=("/data/sql",),
        action_token="/data/sql",
    ),
    _path_rule(
        feature_id="production_indicators",
        markers=("/production",),
        action_token="/production",
    ),
    _path_rule(
        feature_id="system_metadata",
        markers=("/system",),
        action_token="/system",
    ),
)

_SKILL_TO_FEATURE: dict[str, str] = {
    "company-knowledge": "rag",
}

_CATALOG_RELATIVE_PATH = "assistant/features_catalog"


class AssistantCapabilitiesCatalogGenerator:
    @classmethod
    def load_catalog(cls) -> dict[str, Any]:
        return copy.deepcopy(ContentService.load_json(_CATALOG_RELATIVE_PATH))

    @classmethod
    def catalog_file_path(cls) -> Path:
        return ContentService._resolve_path(_CATALOG_RELATIVE_PATH, locale=None, extension=".json")

    @classmethod
    def generate(
        cls,
        *,
        actions: list[dict[str, Any]] | None = None,
        skills: list[dict[str, Any]] | None = None,
        base_catalog: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        catalog = copy.deepcopy(base_catalog or cls.load_catalog())
        resolved_actions = actions if actions is not None else []
        resolved_skills = skills if skills is not None else cls._load_skills()

        paths_by_feature: dict[str, set[str]] = {}
        unmapped_paths: list[str] = []

        for action in resolved_actions:
            if action.get("enabled") is False:
                continue

            path = str(action.get("path") or "").strip()

            if not path or path in _IGNORE_PATHS:
                continue

            feature_id = cls._resolve_feature_id(path)
            token = cls._action_token(path)

            if feature_id and token:
                paths_by_feature.setdefault(feature_id, set()).add(token)
            else:
                unmapped_paths.append(path)

        skill_keys_by_feature = cls._map_skills(resolved_skills)

        features = catalog.get("features")

        if not isinstance(features, list):
            catalog["features"] = []
            features = catalog["features"]

        for feature in features:
            if not isinstance(feature, dict):
                continue

            feature_id = str(feature.get("id") or "").strip()

            if not feature_id:
                continue

            discovered_tokens = paths_by_feature.get(feature_id)

            if discovered_tokens:
                existing = {
                    str(item).strip()
                    for item in (feature.get("requiredActions") or [])
                    if str(item).strip()
                }
                feature["requiredActions"] = sorted(existing | discovered_tokens)

            linked_skills = skill_keys_by_feature.get(feature_id)

            if linked_skills:
                feature["linkedSkills"] = linked_skills

        catalog["generation"] = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "sources": ["external_actions", "skills/catalog", _CATALOG_RELATIVE_PATH],
            "actionCount": len(resolved_actions),
            "enabledActionCount": sum(
                1 for item in resolved_actions if item.get("enabled") is not False
            ),
            "skillCount": len(resolved_skills),
            "unmappedActionPaths": sorted(set(unmapped_paths))[:40],
            "pathRulesVersion": "2026.06.03",
        }

        return catalog

    @classmethod
    def synced_snapshot(cls, catalog: dict[str, Any]) -> dict[str, Any]:
        features = catalog.get("features")

        if not isinstance(features, list):
            return {"generation": catalog.get("generation"), "features": []}

        synced_features = []

        for feature in features:
            if not isinstance(feature, dict):
                continue

            synced_features.append(
                {
                    "id": feature.get("id"),
                    "requiredActions": feature.get("requiredActions"),
                    "linkedSkills": feature.get("linkedSkills"),
                }
            )

        synced_features.sort(key=lambda item: str(item.get("id") or ""))

        generation = catalog.get("generation")

        stable_generation = None

        if isinstance(generation, dict):
            stable_generation = {
                key: value
                for key, value in generation.items()
                if key != "generatedAt"
            }

        return {
            "generation": stable_generation,
            "features": synced_features,
        }

    @classmethod
    def drift_report(cls, *, on_disk: dict[str, Any], generated: dict[str, Any]) -> list[str]:
        on_disk_snapshot = json.dumps(cls.synced_snapshot(on_disk), sort_keys=True, ensure_ascii=False)
        generated_snapshot = json.dumps(
            cls.synced_snapshot(generated),
            sort_keys=True,
            ensure_ascii=False,
        )

        if on_disk_snapshot == generated_snapshot:
            return []

        return [
            "features_catalog.json está dessincronizado com actions/skills.",
            "Execute: python scripts/generate_assistant_capabilities_catalog.py --write",
        ]

    @classmethod
    def write_catalog(cls, catalog: dict[str, Any]) -> Path:
        errors = AssistantCapabilitiesCatalogValidator.validate_catalog_dict(catalog)

        if errors:
            raise ValueError("; ".join(errors))

        path = cls.catalog_file_path()
        path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        ContentService.clear_cache()
        from app.application.services.assistant_capabilities_registry import clear_catalog_cache

        clear_catalog_cache()
        return path

    @classmethod
    def load_actions_from_database(cls) -> list[dict[str, Any]]:
        from app.composition.root_composer import create_application
        from app.infrastructure.persistence.postgres_external_action_repository import (
            PostgresExternalActionRepository,
        )

        app = create_application()

        with app.app_context():
            return PostgresExternalActionRepository().list_actions() or []

    @classmethod
    def _load_skills(cls) -> list[dict[str, Any]]:
        raw = ContentService.skills_catalog().get("skills")

        if not isinstance(raw, list):
            return []

        return [item for item in raw if isinstance(item, dict)]

    @classmethod
    def _map_skills(cls, skills: list[dict[str, Any]]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}

        for skill in skills:
            key = str(skill.get("key") or "").strip()

            if not key:
                continue

            feature_id = _SKILL_TO_FEATURE.get(key)

            if not feature_id:
                continue

            result.setdefault(feature_id, []).append(key)

        for feature_id, keys in result.items():
            result[feature_id] = sorted(set(keys))

        return result

    @classmethod
    def _best_path_match(cls, path: str) -> tuple[str | None, str | None]:
        normalized = path.lower()
        best_length = 0
        feature_id: str | None = None
        action_token: str | None = None

        for rule in _PATH_RULES:
            markers = rule.get("pathMarkers") or ()

            for marker in markers:
                token = str(marker or "").strip().lower()

                if not token or token not in normalized or len(token) <= best_length:
                    continue

                best_length = len(token)
                feature_id = str(rule.get("featureId") or "").strip() or None
                action_token = str(rule.get("actionToken") or "").strip() or None

        return feature_id, action_token

    @classmethod
    def _resolve_feature_id(cls, path: str) -> str | None:
        feature_id, _ = cls._best_path_match(path)
        return feature_id

    @classmethod
    def _action_token(cls, path: str) -> str | None:
        _, action_token = cls._best_path_match(path)

        if action_token:
            return action_token

        normalized = path.lower()
        match = re.search(r"/[a-z0-9_-]+", normalized)

        if match:
            return match.group(0)

        return None
