# app/application/use_cases/get_plugin_access_use_case.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class GetPluginAccessResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class GetPluginAccessUseCase:
    """
    Resolve quem tem acesso efetivo às permissions do módulo (= plugin_id):
    - User → Role → Permission
    - User → Group → Role → Permission
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str) -> GetPluginAccessResult:
        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return GetPluginAccessResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.not_found",
                        "message": "Plugin não encontrado",
                        "path": "_global",
                    }
                ],
            )

        permissions = self._uow.plugin_permissions.list_by_module(plugin_id)
        perm_payload = [
            {
                "id": p["id"],
                "code": p["code"],
                "name": p["name"],
                "description": p.get("description"),
            }
            for p in permissions
        ]
        codes = {p["code"] for p in permissions if p.get("code")}

        roles_out: Dict[str, Dict[str, Any]] = {}
        groups_out: Dict[str, Dict[str, Any]] = {}
        # user_id -> paths aggregator
        user_paths: Dict[str, List[Dict[str, Any]]] = {}

        for perm in permissions:
            try:
                pid = UUID(str(perm["id"]))
            except (TypeError, ValueError):
                continue

            role_ids = self._uow.role_permissions.list_role_ids_by_permission_id(pid)
            code = perm["code"]

            for role_id in role_ids:
                role = self._uow.roles.get(role_id)
                if not role:
                    continue

                rid = str(role.id)
                if rid not in roles_out:
                    role_codes = [
                        c
                        for c in self._uow.role_permissions.list_permission_codes(role.id)
                        if c in codes
                    ]
                    roles_out[rid] = {
                        "id": rid,
                        "name": role.name,
                        "description": role.description,
                        "permissionCodes": sorted(role_codes),
                    }

                # users with direct role
                for uid in self._uow.user_roles.list_user_ids_by_role_id(role.id):
                    self._append_path(
                        user_paths,
                        str(uid),
                        {
                            "type": "role",
                            "roleId": rid,
                            "roleName": role.name,
                            "codes": [code],
                        },
                    )

            group_links = self._uow.group_roles.list_group_role_ids_by_role_ids(role_ids)
            for group_id, role_id in group_links:
                group = self._uow.groups.get(group_id)
                role = self._uow.roles.get(role_id)
                if not group or not role:
                    continue

                gid = str(group.id)
                rid = str(role.id)
                if gid not in groups_out:
                    groups_out[gid] = {
                        "id": gid,
                        "name": group.name,
                        "description": group.description,
                        "viaRoles": [],
                    }
                via = groups_out[gid]["viaRoles"]
                if not any(v.get("id") == rid for v in via):
                    via.append({"id": rid, "name": role.name})

                for uid in self._uow.user_groups.list_user_ids_by_group_id(group.id):
                    self._append_path(
                        user_paths,
                        str(uid),
                        {
                            "type": "group_role",
                            "groupId": gid,
                            "groupName": group.name,
                            "roleId": rid,
                            "roleName": role.name,
                            "codes": [code],
                        },
                    )

        # merge duplicate path keys (same role/group_role) and union codes
        users_out: List[Dict[str, Any]] = []
        user_ids = [UUID(uid) for uid in user_paths.keys()]
        users_by_id = {
            str(u.id): u for u in (self._uow.users.get_by_ids(user_ids) if user_ids else [])
        }

        for uid, paths in user_paths.items():
            merged = self._merge_paths(paths)
            user = users_by_id.get(uid)
            if not user:
                continue
            covered = sorted({c for p in merged for c in p.get("codes") or []})
            users_out.append(
                {
                    "id": uid,
                    "name": user.name,
                    "email": user.email,
                    "isSuperadmin": bool(user.is_superadmin),
                    "paths": merged,
                    "permissionCodes": covered,
                }
            )

        users_out.sort(key=lambda u: (u["name"] or "").lower())

        roles_list = sorted(roles_out.values(), key=lambda r: r["name"].lower())
        groups_list = sorted(groups_out.values(), key=lambda g: g["name"].lower())
        for g in groups_list:
            g["viaRoles"] = sorted(g["viaRoles"], key=lambda r: r["name"].lower())

        return GetPluginAccessResult(
            success=True,
            data={
                "pluginId": plugin_id,
                "permissions": perm_payload,
                "roles": roles_list,
                "groups": groups_list,
                "users": users_out,
                "summary": {
                    "permissionCount": len(perm_payload),
                    "roleCount": len(roles_list),
                    "groupCount": len(groups_list),
                    "userCount": len(users_out),
                },
            },
        )

    @staticmethod
    def _append_path(
        bucket: Dict[str, List[Dict[str, Any]]],
        user_id: str,
        path: Dict[str, Any],
    ) -> None:
        bucket.setdefault(user_id, []).append(path)

    @staticmethod
    def _merge_paths(paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        for path in paths:
            if path.get("type") == "role":
                key = f"role:{path.get('roleId')}"
            else:
                key = f"group_role:{path.get('groupId')}:{path.get('roleId')}"
            if key not in merged:
                merged[key] = {**path, "codes": list(path.get("codes") or [])}
            else:
                codes = set(merged[key].get("codes") or [])
                codes.update(path.get("codes") or [])
                merged[key]["codes"] = sorted(codes)
        return list(merged.values())
