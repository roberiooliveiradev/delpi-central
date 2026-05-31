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

_PATH_RULES: tuple[dict[str, Any], ...] = (
    {
        "featureId": "product_lookup",
        "pathMarkers": ("/products", "/product", "products"),
        "actionToken": "/products",
    },
    {
        "featureId": "stock_lookup",
        "pathMarkers": ("/stock", "estoque", "inventory"),
        "actionToken": "/stock",
    },
    {
        "featureId": "sales_lookup",
        "pathMarkers": ("/sales", "/ordens", "ordem de venda", "order"),
        "actionToken": "/sales",
    },
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

            if not path:
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
            "pathRulesVersion": "2026.06.01",
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
    def _resolve_feature_id(cls, path: str) -> str | None:
        normalized = path.lower()

        for rule in _PATH_RULES:
            markers = rule.get("pathMarkers") or ()

            if any(marker.lower() in normalized for marker in markers):
                return str(rule.get("featureId") or "").strip() or None

        return None

    @classmethod
    def _action_token(cls, path: str) -> str | None:
        normalized = path.lower()

        for rule in _PATH_RULES:
            markers = rule.get("pathMarkers") or ()

            if any(marker.lower() in normalized for marker in markers):
                return str(rule.get("actionToken") or "").strip() or None

        match = re.search(r"/[a-z0-9_-]+", normalized)

        if match:
            return match.group(0)

        return None
