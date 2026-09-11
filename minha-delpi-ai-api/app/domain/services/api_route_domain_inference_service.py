"""Resolve apiRouteDomain from Action Catalog / OpenAPI semantic metadata.

E11.S2 — path substring maps (former Python domain-rule tables / pathMarkers)
are not authority.
Resolution order:

1. explicit ``apiRouteDomain`` (top-level or delpiMetadata / x-delpi)
2. ``entity`` exact or longest known-domain prefix match
3. ``category`` → domain via content ``semanticBindings.categoryToDomain``
4. ``generic`` (unknown / external OpenAPI without enrichment)
"""

from __future__ import annotations

from typing import Any, Mapping


class ApiRouteDomainInferenceService:
    """Semantic apiRouteDomain resolver — no path-fragment authority."""

    @classmethod
    def infer_from_action(
        cls,
        action: dict[str, Any] | None,
        *,
        known_domain_ids: frozenset[str] | None = None,
        category_to_domain: Mapping[str, str] | None = None,
        entity_to_domain: Mapping[str, str] | None = None,
    ) -> str:
        payload = action if isinstance(action, dict) else {}
        explicit = cls._explicit_domain(payload)
        if explicit:
            return explicit

        domains = known_domain_ids or frozenset()
        metadata = cls._metadata(payload)

        entity = str(metadata.get("entity") or payload.get("entity") or "").strip()
        if entity_to_domain:
            mapped_entity = str(entity_to_domain.get(entity.lower()) or "").strip().lower()
            if mapped_entity:
                return mapped_entity
        from_entity = cls._domain_from_entity(entity, domains)
        if from_entity:
            return from_entity

        category = str(metadata.get("category") or payload.get("category") or "").strip()
        from_category = cls._domain_from_category(category, category_to_domain)
        if from_category:
            return from_category

        return "generic"

    @classmethod
    def infer_from_path(cls, path: str, *, operation_id: str = "") -> str:
        """Path is not semantic authority (E11.S2). Always generic.

        Kept as a no-op stub so residual call sites fail closed instead of
        inventing domain from URL fragments.
        """
        _ = (path, operation_id)
        return "generic"

    @classmethod
    def _explicit_domain(cls, action: dict[str, Any]) -> str:
        top = str(action.get("apiRouteDomain") or action.get("api_route_domain") or "").strip()
        if top:
            return top.lower()

        metadata = cls._metadata(action)
        nested = str(
            metadata.get("apiRouteDomain") or metadata.get("api_route_domain") or ""
        ).strip()
        if nested:
            return nested.lower()

        return ""

    @classmethod
    def _metadata(cls, action: dict[str, Any]) -> dict[str, Any]:
        metadata = action.get("delpiMetadata") or action.get("delpi_metadata") or {}
        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _domain_from_entity(cls, entity: str, domains: frozenset[str]) -> str:
        token = str(entity or "").strip().lower()
        if not token or not domains:
            return ""
        if token in domains and token != "generic":
            return token

        best = ""
        for domain_id in domains:
            if not domain_id or domain_id == "generic":
                continue
            if token == domain_id or token.startswith(f"{domain_id}_"):
                if len(domain_id) > len(best):
                    best = domain_id
        return best

    @classmethod
    def _domain_from_category(
        cls,
        category: str,
        category_to_domain: Mapping[str, str] | None,
    ) -> str:
        token = str(category or "").strip().lower()
        if not token or not category_to_domain:
            return ""
        mapped = str(category_to_domain.get(token) or "").strip().lower()
        return mapped
