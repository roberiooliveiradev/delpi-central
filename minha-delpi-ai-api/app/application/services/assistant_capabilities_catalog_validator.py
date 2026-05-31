"""Validação do catálogo de funcionalidades — Playbook autoajuda, Fase 3."""

from __future__ import annotations

from typing import Any

from app.infrastructure.content.content_service import ContentService


class AssistantCapabilitiesCatalogValidator:
    REQUIRED_FEATURE_FIELDS = ("id", "title", "category", "status", "summary")

    @classmethod
    def validate(cls) -> list[str]:
        try:
            catalog = ContentService.load_json("assistant/features_catalog")
        except (FileNotFoundError, OSError, ValueError) as exc:
            return [f"features_catalog.json inválido: {exc}"]

        return cls.validate_catalog_dict(catalog)

    @classmethod
    def validate_catalog_dict(cls, catalog: dict[str, Any]) -> list[str]:
        errors: list[str] = []

        version = str(catalog.get("version") or "").strip()

        if not version:
            errors.append("features_catalog: campo version ausente")

        features = catalog.get("features")

        if not isinstance(features, list) or not features:
            errors.append("features_catalog: lista features vazia")
            return errors

        seen_ids: set[str] = set()
        feature_by_id: dict[str, dict[str, Any]] = {}
        help_topic_ids: set[str] = set()

        for feature in features:
            if not isinstance(feature, dict):
                continue

            token = str(feature.get("id") or "").strip()

            if token:
                feature_by_id[token] = feature

            help_token = str(feature.get("helpTopicId") or "").strip()

            if help_token:
                help_topic_ids.add(help_token)

        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                errors.append(f"features[{index}]: entrada inválida")
                continue

            feature_id = str(feature.get("id") or "").strip()

            for field in cls.REQUIRED_FEATURE_FIELDS:
                if not str(feature.get(field) or "").strip():
                    errors.append(f"features[{feature_id or index}]: campo {field} ausente")

            if feature_id:
                if feature_id in seen_ids:
                    errors.append(f"features_catalog: id duplicado {feature_id}")
                seen_ids.add(feature_id)

            help_topic = str(feature.get("helpTopicId") or "").strip()

            if help_topic and help_topic not in help_topic_ids:
                errors.append(
                    f"features[{feature_id}]: helpTopicId {help_topic!r} sem feature correspondente"
                )

            for related_id in feature.get("relatedFeatures") or []:
                token = str(related_id or "").strip()

                if token and token not in feature_by_id:
                    errors.append(
                        f"features[{feature_id}]: relatedFeatures referencia id inexistente {token}"
                    )

        errors.extend(cls._validate_release_notes(seen_ids))

        return errors

    @classmethod
    def _validate_release_notes(cls, feature_ids: set[str]) -> list[str]:
        errors: list[str] = []

        try:
            notes = ContentService.load_json("assistant/assistant_release_notes")
        except (FileNotFoundError, OSError, ValueError) as exc:
            return [f"assistant_release_notes.json inválido: {exc}"]

        releases = notes.get("releases")

        if not isinstance(releases, list) or not releases:
            errors.append("assistant_release_notes: releases vazio")
            return errors

        for release in releases:
            if not isinstance(release, dict):
                continue

            items = release.get("items")

            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                feature_id = str(item.get("featureId") or "").strip()

                if feature_id and feature_id not in feature_ids:
                    errors.append(
                        f"release_notes: featureId {feature_id!r} ausente em features_catalog"
                    )

        return errors
