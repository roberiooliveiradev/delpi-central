# app/application/workspace_context/workspace_context_contract.py
"""Canonical ``workspace_context_v1`` contract — bounded validation.

This payload is a *navigation hint*: it tells conversational surfaces where
the user's screen currently is. It is never authorization, never domain
truth and never persisted business state. Identity always comes from the
authenticated token — never from the payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

WORKSPACE_CONTEXT_VERSION = 1

MAX_APP_ID_CHARS = 64
MAX_STRING_CHARS = 200
MAX_CANONICAL_PATH_CHARS = 500
MAX_ENTITY_REFS = 4
MAX_PRESENTATION_KEYS = 16

_ALLOWED_TOP_LEVEL = {
    "version",
    "app_id",
    "route_id",
    "client_instance_id",
    "entity_refs",
    "presentation_state",
    "canonical_path",
    "active",
    "focused",
    "source",
}
_ALLOWED_REF_KEYS = {"entity_type", "entity_id", "source_system", "label"}
# Never accept credentials-like keys anywhere in the payload.
_FORBIDDEN_TOKENS = ("token", "authorization", "cookie", "secret", "password", "jwt")


class WorkspaceContextValidationError(ValueError):
    """Raised when a workspace-context payload violates the bounded contract."""


@dataclass(frozen=True)
class WorkspaceEntityRef:
    entity_type: str
    entity_id: str
    source_system: str | None = None
    label: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
        }
        if self.source_system:
            out["source_system"] = self.source_system
        if self.label:
            out["label"] = self.label
        return out


@dataclass(frozen=True)
class WorkspaceContextPayload:
    """Validated, bounded publish payload (identity excluded by design)."""

    app_id: str
    client_instance_id: str
    route_id: str | None = None
    entity_refs: tuple[WorkspaceEntityRef, ...] = ()
    presentation_state: Mapping[str, Any] = field(default_factory=dict)
    canonical_path: str | None = None
    active: bool = True
    focused: bool = False
    source: str = "mfe"

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": WORKSPACE_CONTEXT_VERSION,
            "app_id": self.app_id,
            "route_id": self.route_id,
            "client_instance_id": self.client_instance_id,
            "entity_refs": [r.as_dict() for r in self.entity_refs],
            "presentation_state": dict(self.presentation_state),
            "canonical_path": self.canonical_path,
            "active": self.active,
            "focused": self.focused,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkspaceContextPayload":
        """Rehydrate a stored payload (already validated at publish time)."""
        refs = tuple(
            WorkspaceEntityRef(
                entity_type=str(r.get("entity_type") or ""),
                entity_id=str(r.get("entity_id") or ""),
                source_system=r.get("source_system"),
                label=r.get("label"),
            )
            for r in raw.get("entity_refs") or ()
            if isinstance(r, Mapping) and r.get("entity_type") and r.get("entity_id")
        )
        return cls(
            app_id=str(raw.get("app_id") or ""),
            client_instance_id=str(raw.get("client_instance_id") or ""),
            route_id=raw.get("route_id"),
            entity_refs=refs,
            presentation_state=dict(raw.get("presentation_state") or {}),
            canonical_path=raw.get("canonical_path"),
            active=bool(raw.get("active", True)),
            focused=bool(raw.get("focused", False)),
            source=str(raw.get("source") or "mfe"),
        )


def _fail(message: str) -> WorkspaceContextValidationError:
    return WorkspaceContextValidationError(message)


def _bounded_string(value: Any, field_name: str, max_chars: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _fail(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_chars:
        raise _fail(f"{field_name} exceeds {max_chars} chars")
    return normalized


def _assert_no_forbidden_keys(value: Any, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(bad in lowered for bad in _FORBIDDEN_TOKENS):
                raise _fail(f"forbidden credential-like key at {path or '<root>'}: {key}")
            _assert_no_forbidden_keys(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _assert_no_forbidden_keys(item, f"{path}[{idx}]")


def _parse_entity_ref(raw: Any) -> WorkspaceEntityRef:
    if not isinstance(raw, Mapping):
        raise _fail("entity_refs entries must be objects")
    unknown = set(raw) - _ALLOWED_REF_KEYS
    if unknown:
        raise _fail(f"entity_refs has unknown keys: {sorted(unknown)}")
    entity_type = _bounded_string(raw.get("entity_type"), "entity_refs.entity_type", MAX_STRING_CHARS)
    entity_id = _bounded_string(raw.get("entity_id"), "entity_refs.entity_id", MAX_STRING_CHARS)
    if not entity_type or not entity_id:
        raise _fail("entity_refs requires entity_type and entity_id")
    return WorkspaceEntityRef(
        entity_type=entity_type,
        entity_id=entity_id,
        source_system=_bounded_string(raw.get("source_system"), "entity_refs.source_system", MAX_STRING_CHARS),
        label=_bounded_string(raw.get("label"), "entity_refs.label", MAX_STRING_CHARS),
    )


def parse_workspace_context_payload(raw: Any) -> WorkspaceContextPayload:
    """Validate a bounded ``workspace_context_v1`` publish payload.

    Raises ``WorkspaceContextValidationError`` on any violation — fail-closed.
    """
    if not isinstance(raw, Mapping):
        raise _fail("workspace context must be a JSON object")
    _assert_no_forbidden_keys(raw)
    unknown = set(raw) - _ALLOWED_TOP_LEVEL
    if unknown:
        raise _fail(f"unknown workspace context keys: {sorted(unknown)}")

    version = raw.get("version")
    if version != WORKSPACE_CONTEXT_VERSION:
        raise _fail(f"unsupported workspace context version: {version!r}")

    app_id = _bounded_string(raw.get("app_id"), "app_id", MAX_APP_ID_CHARS)
    if not app_id or not all(ch.isalnum() or ch in "-_" for ch in app_id):
        raise _fail("app_id is required and must be alphanumeric/-/_")
    client_instance_id = _bounded_string(
        raw.get("client_instance_id"), "client_instance_id", MAX_APP_ID_CHARS
    )
    if not client_instance_id:
        raise _fail("client_instance_id is required (per tab/publisher instance)")

    entity_refs_raw = raw.get("entity_refs") or ()
    if not isinstance(entity_refs_raw, (list, tuple)):
        raise _fail("entity_refs must be a list")
    if len(entity_refs_raw) > MAX_ENTITY_REFS:
        raise _fail(f"entity_refs exceeds {MAX_ENTITY_REFS} entries")
    entity_refs = tuple(_parse_entity_ref(item) for item in entity_refs_raw)

    presentation = raw.get("presentation_state") or {}
    if not isinstance(presentation, Mapping):
        raise _fail("presentation_state must be an object")
    if len(presentation) > MAX_PRESENTATION_KEYS:
        raise _fail(f"presentation_state exceeds {MAX_PRESENTATION_KEYS} keys")
    for key, value in presentation.items():
        if isinstance(value, (dict, list, tuple)):
            raise _fail("presentation_state values must be scalars")
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise _fail("presentation_state values must be scalars")
        if isinstance(value, str) and len(value) > MAX_STRING_CHARS:
            raise _fail("presentation_state value exceeds bounds")

    return WorkspaceContextPayload(
        app_id=app_id,
        client_instance_id=client_instance_id,
        route_id=_bounded_string(raw.get("route_id"), "route_id", MAX_STRING_CHARS),
        entity_refs=entity_refs,
        presentation_state=dict(presentation),
        canonical_path=_bounded_string(
            raw.get("canonical_path"), "canonical_path", MAX_CANONICAL_PATH_CHARS
        ),
        active=bool(raw.get("active", True)),
        focused=bool(raw.get("focused", False)),
        source=_bounded_string(raw.get("source"), "source", MAX_APP_ID_CHARS) or "mfe",
    )
