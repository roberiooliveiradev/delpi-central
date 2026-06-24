"""Dispatch declarativo de presenters por profileKey — Playbook 21 W1c."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
    OperationalResponseProfile,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)


class ChatPresentationEntityRouteDispatchService:
    @classmethod
    def resolve_spec(cls, *, entity: str, path: str) -> dict[str, Any] | None:
        token = str(entity or "").strip()

        if not token:
            return None

        routing = ChatPresentationProfileService.entity_presentation_routing()
        overrides = routing.get("entityPresentOverrides")

        if isinstance(overrides, dict):
            override = overrides.get(token)

            if isinstance(override, dict):
                return dict(override)

        profile_key = ChatPresentationProfileService.resolve_profile_key(path, token)
        dispatch = routing.get("profilePresentDispatch")

        if not isinstance(dispatch, dict) or not profile_key:
            return None

        spec = dispatch.get(profile_key)

        return dict(spec) if isinstance(spec, dict) else None

    @classmethod
    def try_present(
        cls,
        host: Any,
        root: dict[str, Any],
        *,
        path: str,
        entity: str,
        profile: OperationalResponseProfile,
        normalize_root: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        spec = cls.resolve_spec(entity=entity, path=path)

        if not spec:
            return False, None

        method_name = str(spec.get("presenterMethod") or "").strip()

        if not method_name:
            return False, None

        payload = dict(root)

        if spec.get("normalizeRoot") and normalize_root is not None:
            payload = normalize_root(payload)

        method = getattr(host, f"_{method_name}", None)

        if not callable(method):
            wrapped: dict[str, Any] = {"data": payload}

            if entity:
                wrapped["meta"] = {"entity": entity}

            return True, host.present(wrapped, path=path)

        if spec.get("requiresProduct"):
            product = payload.get("product")

            if not isinstance(product, dict):
                return True, None

            normalized_product = host._normalize_api_section(product)

            if method_name == "present_product":
                return True, method(payload, normalized_product)

            effective_path = ChatOperationalResponseProfileService.presentation_path(
                path=path,
                entity=entity,
            )
            return True, method(payload, normalized_product, effective_path)

        result = method(payload, path)

        if result is None and spec.get("allowEmpty"):
            return True, None

        return True, result
