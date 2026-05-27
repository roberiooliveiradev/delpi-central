from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.domain.entities.chat_agent import ChatAgent


def build_agent_config_snapshot(agent: ChatAgent) -> dict[str, Any]:
    return {
        "version": int(getattr(agent, "published_version", 0) or 0) + 1,
        "name": agent.name,
        "description": agent.description,
        "systemPrompt": agent.system_prompt,
        "responseStyle": agent.response_style,
        "category": agent.category,
        "icon": agent.icon,
        "maxToolCalls": agent.max_tool_calls,
        "requiresConfirmationForWrite": agent.requires_confirmation_for_write,
        "metadata": deepcopy(agent.metadata or {}),
    }


def snapshot_from_fields(
    *,
    name: str,
    description: str | None,
    system_prompt: str | None,
    response_style: str | None,
    category: str | None,
    icon: str | None,
    max_tool_calls: int,
    requires_confirmation_for_write: bool,
    metadata: dict | None,
    version: int | None = None,
) -> dict[str, Any]:
    return {
        "version": version,
        "name": name,
        "description": description,
        "systemPrompt": system_prompt,
        "responseStyle": response_style,
        "category": category,
        "icon": icon,
        "maxToolCalls": max_tool_calls,
        "requiresConfirmationForWrite": requires_confirmation_for_write,
        "metadata": deepcopy(metadata or {}),
    }


def normalize_draft_payload(draft: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(draft, dict):
        return None

    metadata = draft.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        metadata = {}

    max_tool_calls = draft.get("maxToolCalls", draft.get("max_tool_calls", 5))

    try:
        max_tool_calls = max(1, min(int(max_tool_calls), 20))
    except (TypeError, ValueError):
        max_tool_calls = 5

    return snapshot_from_fields(
        name=str(draft.get("name") or "").strip(),
        description=_optional_str(draft.get("description")),
        system_prompt=_optional_str(draft.get("systemPrompt", draft.get("system_prompt"))),
        response_style=_optional_str(draft.get("responseStyle", draft.get("response_style"))),
        category=_optional_str(draft.get("category")),
        icon=_optional_str(draft.get("icon")),
        max_tool_calls=max_tool_calls,
        requires_confirmation_for_write=bool(
            draft.get(
                "requiresConfirmationForWrite",
                draft.get("requires_confirmation_for_write", True),
            )
        ),
        metadata=metadata if isinstance(metadata, dict) else {},
        version=None,
    )


def apply_snapshot_to_agent(agent: ChatAgent, snapshot: dict[str, Any]) -> ChatAgent:
    return ChatAgent(
        id=agent.id,
        key=agent.key,
        name=str(snapshot.get("name") or agent.name),
        description=snapshot.get("description", agent.description),
        system_prompt=snapshot.get("systemPrompt", agent.system_prompt),
        enabled=agent.enabled,
        metadata=deepcopy(snapshot.get("metadata") or agent.metadata or {}),
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        owner_user_id=agent.owner_user_id,
        visibility=agent.visibility,
        category=snapshot.get("category", agent.category),
        icon=snapshot.get("icon", agent.icon),
        response_style=snapshot.get("responseStyle", agent.response_style),
        max_tool_calls=int(snapshot.get("maxToolCalls", agent.max_tool_calls) or 5),
        requires_confirmation_for_write=bool(
            snapshot.get(
                "requiresConfirmationForWrite",
                agent.requires_confirmation_for_write,
            )
        ),
        published_version=getattr(agent, "published_version", 0),
        published_at=getattr(agent, "published_at", None),
        published_config=getattr(agent, "published_config", None),
    )


def has_unpublished_changes(agent: ChatAgent) -> bool:
    published = getattr(agent, "published_config", None)

    if not published or not isinstance(published, dict):
        return int(getattr(agent, "published_version", 0) or 0) < 1

    current = build_agent_config_snapshot(agent)
    current["version"] = published.get("version")

    published_compare = {key: published.get(key) for key in current if key != "version"}
    current_compare = {key: current.get(key) for key in current if key != "version"}

    return published_compare != current_compare


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None
