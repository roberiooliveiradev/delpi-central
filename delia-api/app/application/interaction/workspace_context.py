"""Bounded provider-neutral workspace context for one interaction turn.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
the client may attach a bounded, untrusted view of what the user is
looking at — host application, current route/surface, and the selected
entity references (e.g. the TV Dashboard playlist + slide). It exists
to let the model resolve demonstratives ("this", "here", "current").

This context is NEVER authority: it grants nothing, never substitutes
Core/RBAC/owner authorization, and carries no credentials. Every field
is untrusted client data — syntactically bounded here, semantically
non-authoritative everywhere.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

MAX_WORKSPACE_STRING_CHARS = 200
MAX_WORKSPACE_ENTITY_REFS = 4
MAX_WORKSPACE_BLOCK_CHARS = 2000

_WORKSPACE_KEYS = frozenset(
    {"host_app_id", "route", "view_ref", "selected_entity_ref", "entity_refs"}
)
_ENTITY_KEYS = frozenset(
    {"entity_type", "entity_id", "source_system", "label"}
)


@dataclass(frozen=True, slots=True)
class WorkspaceEntityRef:
    """One untrusted entity hint: which thing the client is showing."""

    entity_type: str
    entity_id: str
    source_system: str
    label: str | None = None

    def to_projection(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "source_system": self.source_system,
        }
        if self.label:
            out["label"] = self.label
        return out


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    """Bounded untrusted client-supplied workspace view.

    ``selected_entity_ref`` is the primary "current thing" (e.g. the
    slide the user is editing); ``entity_refs`` carries additional
    ambient references (e.g. the containing playlist). All fields are
    hints only — resolution happens downstream through provider
    capabilities against authoritative sources.
    """

    host_app_id: str
    route: str | None = None
    view_ref: str | None = None
    selected_entity_ref: WorkspaceEntityRef | None = None
    entity_refs: tuple[WorkspaceEntityRef, ...] = field(
        default_factory=tuple
    )

    def to_prompt_block(self) -> str:
        """Bounded untrusted projection for the selection prompt."""
        payload: dict[str, Any] = {
            "host_app_id": self.host_app_id,
        }
        if self.route:
            payload["route"] = self.route
        if self.view_ref:
            payload["view_ref"] = self.view_ref
        if self.selected_entity_ref is not None:
            payload["selected_entity_ref"] = (
                self.selected_entity_ref.to_projection()
            )
        if self.entity_refs:
            payload["entity_refs"] = [
                ref.to_projection() for ref in self.entity_refs
            ]
        return json.dumps(payload, ensure_ascii=False, default=str)[
            :MAX_WORKSPACE_BLOCK_CHARS
        ]

    def grants_authorization(self) -> bool:
        return False


def _bounded_string(value: object, field_name: str) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, f"'workspace.{field_name}' must be a non-empty string"
    value = value.strip()
    if len(value) > MAX_WORKSPACE_STRING_CHARS:
        return None, f"'workspace.{field_name}' is too long"
    return value, None


def _parse_entity_ref(
    raw: object, field_name: str
) -> tuple[WorkspaceEntityRef | None, str | None]:
    if not isinstance(raw, dict):
        return None, f"'workspace.{field_name}' must be an object"
    extra = set(raw) - _ENTITY_KEYS
    if extra:
        return None, (
            f"'workspace.{field_name}' unsupported fields: "
            f"{sorted(extra)}"
        )
    entity_type, err = _bounded_string(raw.get("entity_type"), field_name)
    if err:
        return None, err
    entity_id, err = _bounded_string(raw.get("entity_id"), field_name)
    if err:
        return None, err
    source_system, err = _bounded_string(
        raw.get("source_system"), field_name
    )
    if err:
        return None, err
    label_raw = raw.get("label")
    label = None
    if label_raw is not None:
        label, err = _bounded_string(label_raw, f"{field_name}.label")
        if err:
            return None, err
    return (
        WorkspaceEntityRef(
            entity_type=entity_type or "",
            entity_id=entity_id or "",
            source_system=source_system or "",
            label=label,
        ),
        None,
    )


def parse_workspace_context(
    raw: object,
) -> tuple[WorkspaceContext | None, str | None]:
    """Syntactic validation of the untrusted workspace payload.

    Fail closed on malformed shape: the context is an optimization for
    resolving demonstratives, never required — but when supplied it must
    be bounded and strict so no oversized or unexpected data reaches the
    model context.
    """
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, "'workspace' must be an object"
    extra = set(raw) - _WORKSPACE_KEYS
    if extra:
        return None, f"'workspace' unsupported fields: {sorted(extra)}"

    host_app_id, err = _bounded_string(raw.get("host_app_id"), "host_app_id")
    if err:
        return None, err

    route = None
    route_raw = raw.get("route")
    if route_raw is not None:
        route, err = _bounded_string(route_raw, "route")
        if err:
            return None, err

    view_ref = None
    view_raw = raw.get("view_ref")
    if view_raw is not None:
        view_ref, err = _bounded_string(view_raw, "view_ref")
        if err:
            return None, err

    selected = None
    selected_raw = raw.get("selected_entity_ref")
    if selected_raw is not None:
        selected, err = _parse_entity_ref(
            selected_raw, "selected_entity_ref"
        )
        if err:
            return None, err

    entity_refs: list[WorkspaceEntityRef] = []
    refs_raw = raw.get("entity_refs")
    if refs_raw is not None:
        if not isinstance(refs_raw, list):
            return None, "'workspace.entity_refs' must be a list"
        if len(refs_raw) > MAX_WORKSPACE_ENTITY_REFS:
            return None, "'workspace.entity_refs' exceeds bound"
        for index, item in enumerate(refs_raw):
            ref, err = _parse_entity_ref(item, f"entity_refs[{index}]")
            if err:
                return None, err
            assert ref is not None
            entity_refs.append(ref)

    return (
        WorkspaceContext(
            host_app_id=host_app_id or "",
            route=route,
            view_ref=view_ref,
            selected_entity_ref=selected,
            entity_refs=tuple(entity_refs),
        ),
        None,
    )
