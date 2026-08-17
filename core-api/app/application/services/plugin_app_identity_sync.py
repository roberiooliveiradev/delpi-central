# app/application/services/plugin_app_identity_sync.py
"""Fonte única: campos de identidade do manifesto → linha `apps`."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional


IdentitySyncMode = Literal["full", "cosmetic"]


def resolve_manifest_base_path(manifest: Dict[str, Any]) -> Optional[str]:
    raw = manifest.get("basePath") or manifest.get("base_path")
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def resolve_manifest_display_name(
    manifest: Dict[str, Any],
    *,
    existing_name: str = "",
) -> str:
    return str(manifest.get("name") or "").strip() or str(existing_name or "").strip()


def app_identity_from_manifest(
    manifest: Dict[str, Any],
    *,
    existing_name: str = "",
    mode: IdentitySyncMode = "full",
) -> Dict[str, Any]:
    """
    Extrai identidade exibida no Portal (sidebar/launcher/favorites).

    - full: name, description, icon, type, base_path (register/rollback)
    - cosmetic: name, description, icon (update sem nova versão)
    """
    fields: Dict[str, Any] = {
        "name": resolve_manifest_display_name(manifest, existing_name=existing_name),
        "description": manifest.get("description"),
        "icon": manifest.get("icon"),
    }
    if mode == "full":
        fields["app_type"] = manifest.get("type")
        fields["base_path"] = resolve_manifest_base_path(manifest)
    return fields


def build_app_create_payload(
    manifest: Dict[str, Any],
    *,
    plugin_id: str,
    version: str,
    active: bool = True,
) -> Dict[str, Any]:
    """Payload de `plugins.create` — mesma fonte que o sync full."""
    identity = app_identity_from_manifest(manifest, mode="full")
    base_path = identity.get("base_path")
    if not base_path:
        raise ValueError("basePath é obrigatório")
    return {
        "id": plugin_id,
        "name": identity["name"] or str(manifest.get("name") or plugin_id),
        "description": identity.get("description"),
        "base_path": base_path,
        "icon": identity.get("icon"),
        "type": identity.get("app_type"),
        "version": version,
        "active": active,
    }


def sync_app_row_from_manifest(
    plugins,
    plugin_id: str,
    manifest: Dict[str, Any],
    *,
    existing_name: str = "",
    version: str | None = None,
    mode: IdentitySyncMode = "full",
    actor_user_id: str | None = None,
    actor_name: str | None = None,
) -> None:
    """
    Mantém `apps` alinhado ao manifesto.

    Sidebar/favorites leem `apps.icon` (e name/base_path), não só o JSON em
    plugin_manifests — create/register/update/rollback devem usar este caminho.
    """
    if version is not None:
        plugins.update_version(
            plugin_id,
            version,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
        )

    identity = app_identity_from_manifest(
        manifest,
        existing_name=existing_name,
        mode=mode,
    )
    plugins.update_metadata(
        plugin_id,
        name=identity["name"],
        description=identity.get("description"),
        icon=identity.get("icon"),
        app_type=identity.get("app_type") if mode == "full" else None,
        base_path=identity.get("base_path") if mode == "full" else None,
        actor_user_id=actor_user_id,
        actor_name=actor_name,
    )
