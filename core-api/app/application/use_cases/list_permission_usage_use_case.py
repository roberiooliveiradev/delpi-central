# app/application/use_cases/list_permission_usage_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class ListPermissionUsageUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, permission_id: str) -> dict:
        pid = UUID(permission_id)

        permission = self.uow.permissions.get(pid)

        if not permission:
            raise ValueError("Permissão não encontrada.")

        role_ids = self.uow.role_permissions.list_role_ids_by_permission_id(pid)

        roles_by_id = {}

        for role_id in role_ids:
            role = self.uow.roles.get(role_id)

            if not role:
                continue

            roles_by_id[role.id] = {
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
            }

        group_role_links = self.uow.group_roles.list_group_role_ids_by_role_ids(
            role_ids
        )

        groups_by_id = {}

        for group_id, role_id in group_role_links:
            group = self.uow.groups.get(group_id)
            role = roles_by_id.get(role_id)

            if not group or not role:
                continue

            if group.id not in groups_by_id:
                groups_by_id[group.id] = {
                    "id": str(group.id),
                    "name": group.name,
                    "description": group.description,
                    "via_roles": [],
                }

            groups_by_id[group.id]["via_roles"].append({
                "id": role["id"],
                "name": role["name"],
            })

        roles = sorted(
            roles_by_id.values(),
            key=lambda item: item["name"].lower(),
        )

        groups = sorted(
            groups_by_id.values(),
            key=lambda item: item["name"].lower(),
        )

        for group in groups:
            group["via_roles"] = sorted(
                group["via_roles"],
                key=lambda item: item["name"].lower(),
            )

        return {
            "permission": {
                "id": str(permission.id),
                "code": permission.code,
                "name": permission.name,
                "description": permission.description,
                "module": permission.module,
            },
            "roles": roles,
            "groups": groups,
        }