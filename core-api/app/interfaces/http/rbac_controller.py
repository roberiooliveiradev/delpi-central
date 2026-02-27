# app/interfaces/http/rbac_controller.py

from uuid import UUID
from flask import Blueprint, request, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.infrastructure.events.socket_admin_event_publisher import (
    SocketAdminEventPublisher
)

from app.application.use_cases.create_role_use_case import CreateRoleUseCase
from app.application.use_cases.list_role_permissions_use_case import ListRolePermissionsUseCase
from app.application.use_cases.replace_role_permissions_use_case import ReplaceRolePermissionsUseCase
from app.application.use_cases.add_permission_to_role_use_case import AddPermissionToRoleUseCase
from app.application.use_cases.remove_permission_from_role_use_case import RemovePermissionFromRoleUseCase

from app.application.use_cases.list_group_roles_use_case import ListGroupRolesUseCase
from app.application.use_cases.replace_group_roles_use_case import ReplaceGroupRolesUseCase
from app.application.use_cases.add_group_roles_use_case import AddRoleToGroupUseCase
from app.application.use_cases.remove_group_roles_use_case import RemoveRoleFromGroupUseCase

from app.application.use_cases.list_user_roles_use_case import ListUserRolesUseCase
from app.application.use_cases.replace_user_roles_use_case import ReplaceUserRolesUseCase
from app.application.use_cases.add_role_to_user_use_case import AddRoleToUserUseCase
from app.application.use_cases.remove_role_from_user_use_case import RemoveRoleFromUserUseCase

from app.application.use_cases.list_user_groups_use_case import ListUserGroupsUseCase
from app.application.use_cases.replace_user_groups_use_case import ReplaceUserGroupsUseCase
from app.application.use_cases.add_group_to_user_use_case import AddGroupToUserUseCase
from app.application.use_cases.remove_group_from_user_use_case import RemoveGroupFromUserUseCase

from app.application.use_cases.admin.list_users_use_case import ListUsersUseCase

from app.interfaces.http.utils.errors import unauthorized, api_error, server_error


rbac_bp = Blueprint("rbac", __name__)


def require_auth():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    return None




# ==========================================================
# ROLES
# ==========================================================

@rbac_bp.route("/admin/rbac/roles", methods=["POST"])
def create_role():
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return api_error("validation_error", "Campo 'name' é obrigatório.", path="name")

    uow = SqlAlchemyUnitOfWork()
    uc = CreateRoleUseCase(uow)

    try:
        role_id = uc.execute(name=name, description=data.get("description"))
        return jsonify({"id": str(role_id)}), 201
    except Exception as e:
        uow.rollback()
        return api_error("create_role_failed", str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions", methods=["GET"])
def list_role_permissions(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListRolePermissionsUseCase(uow)
        permissions = uc.execute(role_id)

    total = len(permissions)

    return jsonify({
        "data": permissions,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": 1,
        }
    }), 200


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions", methods=["PUT"])
def replace_role_permissions(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    permission_ids = data.get("permissionIds")

    if not isinstance(permission_ids, list):
        return api_error(
            "validation_error",
            "Campo 'permissionIds' deve ser uma lista.",
            path="permissionIds"
        )


    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceRolePermissionsUseCase(uow)

    try:
        return jsonify(
            uc.execute(role_id, permission_ids)
        ), 200
    except Exception as e:
        uow.rollback()
        return api_error("replace_role_permissions_failed", str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions", methods=["POST"])
def add_permission_to_role(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    id = (data.get("id") or "").strip()

    if not id:
        return api_error("validation_error", "Campo 'id' é obrigatório.", path="id")

    uow = SqlAlchemyUnitOfWork()
    uc = AddPermissionToRoleUseCase(uow)

    try:
        return jsonify(uc.execute(role_id, id)), 200
    except Exception as e:
        uow.rollback()
        return api_error("add_permission_to_role_failed", str(e))


@rbac_bp.route("/admin/rbac/roles/<role_id>/permissions/<permission_id>", methods=["DELETE"])
def remove_permission_from_role(role_id: str, permission_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemovePermissionFromRoleUseCase(uow)

    try:
        return jsonify(uc.execute(role_id, permission_id)), 200
    except Exception as e:
        uow.rollback()
        return api_error("remove_permission_from_role_failed", str(e))


# ==========================================================
# GROUPS
# ==========================================================

@rbac_bp.route("/admin/rbac/groups/<group_id>/roles", methods=["GET"])
def list_group_roles(group_id: str):
    guard = require_auth()
    if guard:
        return guard

    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListGroupRolesUseCase(uow)
        roles = uc.execute(group_id)

    total = len(roles)

    return jsonify({
        "data": roles,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": 1,
        }
    }), 200


@rbac_bp.route("/admin/rbac/groups/<group_id>/roles", methods=["PUT"])
def replace_group_roles(group_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    role_ids = data.get("roleIds", [])

    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceGroupRolesUseCase(uow)

    try:
        return jsonify(uc.execute(group_id, role_ids)), 200
    except Exception as e:
        uow.rollback()
        return api_error("replace_group_roles_failed", str(e))


@rbac_bp.route("/admin/rbac/groups/<group_id>/roles/<role_id>", methods=["POST"])
def add_role_to_group(group_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = AddRoleToGroupUseCase(uow)

    return jsonify(uc.execute(group_id, role_id)), 200


@rbac_bp.route("/admin/rbac/groups/<group_id>/roles/<role_id>", methods=["DELETE"])
def remove_role_from_group(group_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemoveRoleFromGroupUseCase(uow)

    return jsonify(uc.execute(group_id, role_id)), 200


# ==========================================================
# USERS
# ==========================================================

@rbac_bp.route("/admin/rbac/users", methods=["GET"])
def list_users():

    guard = require_auth()
    if guard:
        return guard

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "email")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            use_case = ListUsersUseCase(uow)
            result = use_case.execute(
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        return jsonify({
            "data": [u.__dict__ for u in result.data],
            "pagination": result.pagination.__dict__,
        }), 200

    except Exception as e:
        return server_error(str(e))


@rbac_bp.route("/admin/users/<user_id>/roles", methods=["GET"])
def list_user_roles(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    with SqlAlchemyUnitOfWork() as uow:
        role_ids = uow.user_roles.list_role_ids(user_id)

        roles = []
        for rid in role_ids:
            role = uow.roles.get(rid)
            if role:
                roles.append({
                    "id": str(role.id),
                    "name": role.name
                })

    total = len(roles)

    return jsonify({
        "data": roles,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": 1,
        }
    }), 200


@rbac_bp.route("/admin/users/<user_id>/roles", methods=["PUT"])
def replace_user_roles(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    role_ids = data.get("roleIds", [])

    uow = SqlAlchemyUnitOfWork()
    publisher = SocketAdminEventPublisher()

    uc = ReplaceUserRolesUseCase(uow, publisher)

    return jsonify(uc.execute(user_id, role_ids)), 200


@rbac_bp.route("/admin/users/<user_id>/roles/<role_id>", methods=["POST"])
def add_role_to_user(user_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = AddRoleToUserUseCase(uow)

    return jsonify(uc.execute(user_id, role_id)), 200


@rbac_bp.route("/admin/users/<user_id>/roles/<role_id>", methods=["DELETE"])
def remove_role_from_user(user_id: str, role_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemoveRoleFromUserUseCase(uow)

    return jsonify(uc.execute(user_id, role_id)), 200


@rbac_bp.route("/admin/users/<user_id>/groups", methods=["GET"])
def list_user_groups(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 999))

    with SqlAlchemyUnitOfWork() as uow:
        group_ids = uow.user_groups.list_group_ids(user_id)

        groups = []
        for gid in group_ids:
            group = uow.groups.get(gid)
            if group:
                groups.append({
                    "id": str(group.id),
                    "name": group.name
                })

    total = len(groups)

    return jsonify({
        "data": groups,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": 1,
        }
    }), 200


@rbac_bp.route("/admin/users/<user_id>/groups", methods=["PUT"])
def replace_user_groups(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    group_ids = data.get("groupIds", [])

    uow = SqlAlchemyUnitOfWork()
    uc = ReplaceUserGroupsUseCase(uow)

    return jsonify(uc.execute(user_id, group_ids)), 200


@rbac_bp.route("/admin/users/<user_id>/groups/<group_id>", methods=["POST"])
def add_group_to_user(user_id: str, group_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = AddGroupToUserUseCase(uow)

    return jsonify(uc.execute(user_id, group_id)), 200


@rbac_bp.route("/admin/users/<user_id>/groups/<group_id>", methods=["DELETE"])
def remove_group_from_user(user_id: str, group_id: str):
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    uc = RemoveGroupFromUserUseCase(uow)

    return jsonify(uc.execute(user_id, group_id)), 200

# ==========================================================
# ROLES - LIST PAGINATED
# ==========================================================

@rbac_bp.route("/admin/rbac/roles", methods=["GET"])
def list_roles():
    guard = require_auth()
    if guard:
        return guard

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "name")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            data, total = uow.roles.list_paginated(
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        total_pages = (total + page_size - 1) // page_size

        return jsonify({
            "data": [r.__dict__ for r in data],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            }
        }), 200

    except Exception as e:
        return server_error(str(e))
    

# ==========================================================
# GROUPS - LIST PAGINATED
# ==========================================================

@rbac_bp.route("/admin/rbac/groups", methods=["GET"])
def list_groups():
    guard = require_auth()
    if guard:
        return guard

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "name")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            data, total = uow.groups.list_paginated(
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        total_pages = (total + page_size - 1) // page_size

        return jsonify({
            "data": [g.__dict__ for g in data],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            }
        }), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# UPDATE USER
# ==========================================================

@rbac_bp.route("/admin/rbac/users/<user_id>", methods=["PUT"])
def update_user(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    role_ids = data.get("roleIds", None)
    group_ids = data.get("groupIds", None)
    is_superadmin = data.get("is_superadmin", None)

    # validações
    if role_ids is not None and not isinstance(role_ids, list):
        return api_error("validation_error", "Campo 'roleIds' deve ser uma lista.", path="roleIds")

    if group_ids is not None and not isinstance(group_ids, list):
        return api_error("validation_error", "Campo 'groupIds' deve ser uma lista.", path="groupIds")

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uid = UUID(user_id)

            # atualiza flag superadmin se vier
            if is_superadmin is not None:
                # precisa existir esse método no repo (ou equivalente)
                uow.users.set_superadmin(uid, bool(is_superadmin))

            # troca roles se vier
            if role_ids is not None:
                rid_list = [UUID(r) for r in role_ids]
                uow.user_roles.replace_roles(uid, rid_list)

            # troca grupos se vier
            if group_ids is not None:
                gid_list = [UUID(g) for g in group_ids]
                uow.user_groups.replace_groups(uid, gid_list)

            uow.commit()
            from app.infrastructure.events.socket_admin_event_publisher import SocketAdminEventPublisher
            from app.domain.ports.admin_event_publicher import AdminChangedEvent
            publisher = SocketAdminEventPublisher()
            publisher.publish(AdminChangedEvent(
                entity="rbac",
                action="update",
                payload={"userId": user_id},
            ))
            # invalida cache se existir
            if hasattr(uow, "cache") and uow.cache:
                uow.cache.invalidate(user_id)

        return jsonify({"ok": True}), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# PERMISSIONS - LIST PAGINATED
# ==========================================================

@rbac_bp.route("/admin/rbac/permissions", methods=["GET"])
def list_permissions():
    guard = require_auth()
    if guard:
        return guard

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        sort = request.args.get("sort", "code")
        direction = request.args.get("direction", "asc")

        with SqlAlchemyUnitOfWork() as uow:
            data, total = uow.permissions.list_paginated(
                page=page,
                page_size=page_size,
                sort=sort,
                direction=direction,
            )

        total_pages = (total + page_size - 1) // page_size

        return jsonify({
            "data": [
                {
                    "id": str(p.id),
                    "code": p.code,
                    "name": p.name,
                    "module": p.module,
                }
                for p in data
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            }
        }), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# UPDATE GROUP
# ==========================================================

@rbac_bp.route("/admin/rbac/groups/<group_id>", methods=["PUT"])
def update_group(group_id: str):
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return api_error("validation_error", "Campo 'name' é obrigatório.", path="name")

    try:
        with SqlAlchemyUnitOfWork() as uow:
            gid = UUID(group_id)

            group = uow.groups.get(gid)
            if not group:
                return api_error("not_found", "Grupo não encontrado.")

            uow.groups.update(
                group_id=gid,
                name=name,
                description=description,
            )

            uow.commit()

        return jsonify({"ok": True}), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# DELETE ROLE
# ==========================================================

@rbac_bp.route("/admin/rbac/roles/<role_id>", methods=["DELETE"])
def delete_role(role_id: str):
    guard = require_auth()
    if guard:
        return guard

    try:
        with SqlAlchemyUnitOfWork() as uow:
            rid = UUID(role_id)

            # limpa relacionamentos
            uow.role_permissions.delete_by_role_id(rid)
            uow.user_roles.delete_by_role_id(rid)
            uow.group_roles.delete_by_role_id(rid)

            # remove role
            uow.roles.delete(rid)

            uow.commit()

        return jsonify({"ok": True}), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# BULK DELETE ROLES
# ==========================================================

@rbac_bp.route("/admin/rbac/roles/bulk-delete", methods=["POST"])
def bulk_delete_roles():
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    ids = data.get("ids")

    if not isinstance(ids, list):
        return api_error("validation_error", "Campo 'ids' deve ser uma lista.", path="ids")

    deleted = 0

    try:
        with SqlAlchemyUnitOfWork() as uow:
            for role_id in ids:
                rid = UUID(role_id)

                role = uow.roles.get(rid)
                if not role:
                    continue

                uow.role_permissions.delete_by_role_id(rid)
                uow.roles.delete(rid)
                deleted += 1

            uow.commit()

        return jsonify({"ok": True, "deleted": deleted}), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# DELETE GROUP
# ==========================================================
@rbac_bp.route("/admin/rbac/groups/<group_id>", methods=["DELETE"])
def delete_group(group_id: str):
    guard = require_auth()
    if guard:
        return guard

    try:
        with SqlAlchemyUnitOfWork() as uow:
            gid = UUID(group_id)

            uow.user_groups.delete_by_group_id(gid)
            uow.group_roles.delete_by_group_id(gid)

            uow.groups.delete(gid)

            uow.commit()

        return jsonify({"ok": True}), 200

    except Exception as e:
        return server_error(str(e))

# ==========================================================
# DELETE GROUP
# ==========================================================
@rbac_bp.route("/admin/rbac/users/<user_id>", methods=["DELETE"])
def delete_user(user_id: str):
    guard = require_auth()
    if guard:
        return guard

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uid = UUID(user_id)

            uow.user_roles.delete_by_user_id(uid)
            uow.user_groups.delete_by_user_id(uid)

            uow.users.delete(uid)

            uow.commit()

        return jsonify({"ok": True}), 200

    except Exception as e:
        return server_error(str(e))
    
# ==========================================================
# CREATE GROUP
# ==========================================================

@rbac_bp.route("/admin/rbac/groups", methods=["POST"])
def create_group():
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    description = data.get("description")

    if not name:
        return api_error("validation_error", "Campo 'name' é obrigatório.", path="name")

    try:
        with SqlAlchemyUnitOfWork() as uow:
            gid = uow.groups.create(
                name=name,
                description=description,
            )

            uow.commit()

        return jsonify({"id": str(gid)}), 201

    except Exception as e:
        return server_error(str(e))