# app/interfaces/http/admin/rbac_controller.py

from __future__ import annotations

from flask import Blueprint, jsonify, request, g
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from app.extensions.db import db
from app.domain.services.permission_resolver import resolve_user_permissions
from app.extensions.permission_cache import invalidate_user_permissions
from app.domain.services.audit_log_service import log_audit
from app.interfaces.http.utils.pagination import paginate_query
from app.domain.services.admin_event_service import emit_admin_event

from app.interfaces.http.utils.errors import (
    error_response,
    unauthorized,
    forbidden,
    not_found,
    bad_request,
    conflict,
)

from app.infrastructure.db.models import (
    User,
    Role,
    Group,
    Permission,
    UserPermission,
)

rbac_admin_bp = Blueprint(
    "rbac_admin",
    __name__,
    url_prefix="/core-api/admin/rbac"
)

# =========================================================
# Auth
# =========================================================

def _require_rbac_manage_or_superadmin():
    """
    ✅ Semântica correta:
    - 401 quando não autenticado
    - 403 quando autenticado mas sem permissão
    """
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    if getattr(user, "is_superadmin", False):
        return None

    perms = set(resolve_user_permissions(user))
    if "rbac.manage" not in perms:
        return forbidden("Forbidden")

    return None


@rbac_admin_bp.before_request
def guard():
    guard_resp = _require_rbac_manage_or_superadmin()
    if guard_resp:
        return guard_resp


# =========================================================
# Serializers
# =========================================================

def _json_permission(p: Permission):
    return {
        "id": str(p.id),
        "code": p.code,
        "name": p.name,
        "description": getattr(p, "description", None),
        "module": getattr(p, "module", None),
    }


def _json_role(role: Role):
    return {
        "id": str(role.id),
        "name": role.name,
        "description": getattr(role, "description", None),
        "permissions": [
            {"id": str(p.id), "code": p.code, "name": p.name}
            for p in role.permissions
        ],
    }


def _json_group(group: Group):
    return {
        "id": str(group.id),
        "name": group.name,
        "description": getattr(group, "description", None),
        "roles": [{"id": str(r.id), "name": r.name} for r in group.roles],
    }


def _json_user(user: User):
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "is_superadmin": getattr(user, "is_superadmin", False),
        "roles": [{"id": str(r.id), "name": r.name} for r in user.roles],
        "groups": [{"id": str(gr.id), "name": gr.name} for gr in user.groups],
    }


# =========================================================
# Cache invalidation helpers
# =========================================================

def _invalidate_users_for_role(role: Role):
    """
    invalida cache de todos os users que herdam a role
    diretamente e via groups.
    """
    for user in getattr(role, "users", []):
        invalidate_user_permissions(user.id)

    for group in getattr(role, "groups", []):
        for user in getattr(group, "users", []):
            invalidate_user_permissions(user.id)


def _invalidate_users_for_group(group: Group):
    for user in getattr(group, "users", []):
        invalidate_user_permissions(user.id)


def _invalidate_all_users():
    """
    ✅ safe default (mais caro, mas correto)
    """
    for row in db.session.query(User.id).all():
        invalidate_user_permissions(row[0])


def _invalidate_users_for_permission(permission_id: str):
    """
    Invalida usuários que possuem override para essa permissão.
    """
    rows = db.session.query(UserPermission.user_id).filter_by(permission_id=permission_id).all()
    for (uid,) in rows:
        invalidate_user_permissions(uid)


# =========================================================
# Helpers
# =========================================================

def _parse_ids(field_name: str = "ids"):
    ids = (request.get_json(force=True) or {}).get(field_name, [])
    if not isinstance(ids, list) or not ids:
        return None, bad_request(
            f"{field_name} list required",
            code="validation_error",
            path=field_name,
        )
    return ids, None


# =========================================================
# Permissions
# =========================================================

@rbac_admin_bp.get("/permissions")
def list_permissions():
    q = (request.args.get("q") or "").strip().lower()
    query = Permission.query
    if q:
        query = query.filter(
            or_(
                Permission.code.ilike(f"%{q}%"),
                Permission.name.ilike(f"%{q}%"),
            )
        )

    return paginate_query(
        query,
        _json_permission,
        Permission,
        allowed_sort_fields=["module", "code", "name"],
        default_sort="module",
    )


@rbac_admin_bp.post("/permissions")
def create_permission():
    data = request.get_json(force=True) or {}
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()

    if not code or not name:
        return bad_request(
            "code and name are required",
            code="validation_error",
            path="_global",
        )

    p = Permission(code=code, name=name, description=data.get("description"))
    db.session.add(p)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return conflict("permission code already exists", code="conflict")

    log_audit("permissions.create", "permission", p.id, {"payload": data})
    emit_admin_event("rbac", "permissions_changed", {})

    return jsonify(_json_permission(p)), 201


@rbac_admin_bp.put("/permissions/<permission_id>")
def update_permission(permission_id: str):
    p = Permission.query.get(permission_id)
    if not p:
        return not_found("Not found")

    data = request.get_json(force=True) or {}

    code_before = p.code

    for field in ["code", "name", "description"]:
        if field in data:
            setattr(p, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return conflict("permission code already exists", code="conflict")

    if "code" in data and (data.get("code") or "").strip() and p.code != code_before:
        _invalidate_all_users()
    else:
        _invalidate_users_for_permission(permission_id)

    log_audit("permissions.update", "permission", permission_id, {"payload": data})
    emit_admin_event("rbac", "permissions_changed", {})

    return jsonify(_json_permission(p))


@rbac_admin_bp.delete("/permissions/<permission_id>")
def delete_permission(permission_id: str):
    p = Permission.query.get(permission_id)
    if not p:
        return not_found("Not found")

    _invalidate_users_for_permission(permission_id)

    db.session.delete(p)
    db.session.commit()

    log_audit("permissions.delete", "permission", permission_id, {})
    emit_admin_event("rbac", "permissions_changed", {})

    return jsonify({"ok": True})


@rbac_admin_bp.post("/permissions/bulk-delete")
def bulk_delete_permissions():
    ids, err = _parse_ids("ids")
    if err:
        return err

    rows = Permission.query.filter(Permission.id.in_(ids)).all()

    for pid in ids:
        _invalidate_users_for_permission(str(pid))
    _invalidate_all_users()

    for r in rows:
        db.session.delete(r)

    db.session.commit()
    log_audit("permissions.bulk_delete", "permission", None, {"ids": ids})
    emit_admin_event("rbac", "permissions_changed", {})

    return jsonify({"ok": True, "deleted": len(rows)})


# =========================================================
# Roles
# =========================================================

@rbac_admin_bp.get("/roles")
def list_roles():
    q = (request.args.get("q") or "").strip().lower()
    query = Role.query
    if q:
        query = query.filter(
            or_(
                Role.name.ilike(f"%{q}%"),
                Role.description.ilike(f"%{q}%"),
            )
        )

    return paginate_query(
        query,
        _json_role,
        Role,
        allowed_sort_fields=["name", "description"],
        default_sort="name",
    )


@rbac_admin_bp.post("/roles")
def create_role():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return bad_request("name is required", code="validation_error", path="name")

    role = Role(name=name, description=data.get("description"))
    db.session.add(role)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return conflict("role name already exists", code="conflict")

    log_audit("roles.create", "role", role.id, {"payload": data})
    emit_admin_event("rbac", "roles_changed", {})

    return jsonify(_json_role(role)), 201


@rbac_admin_bp.put("/roles/<role_id>")
def update_role(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return not_found("Not found")

    data = request.get_json(force=True) or {}

    if "name" in data:
        role.name = data["name"]

    if "description" in data:
        role.description = data["description"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return conflict("role name already exists", code="conflict")

    log_audit("roles.update", "role", role_id, {"payload": data})
    emit_admin_event("rbac", "roles_changed", {})

    return jsonify(_json_role(role))


@rbac_admin_bp.delete("/roles/<role_id>")
def delete_role(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return not_found("Not found")

    if getattr(role, "system_role", False):
        return error_response(
            code="system_role_delete_blocked",
            message="Cannot delete system role",
            status=400,
        )

    _invalidate_users_for_role(role)

    db.session.delete(role)
    db.session.commit()

    log_audit("roles.delete", "role", role_id, {})
    emit_admin_event("rbac", "roles_changed", {})

    return jsonify({"ok": True})


@rbac_admin_bp.post("/roles/bulk-delete")
def bulk_delete_roles():
    ids, err = _parse_ids("ids")
    if err:
        return err

    roles = Role.query.filter(Role.id.in_(ids)).all()

    system_roles = [r for r in roles if getattr(r, "system_role", False)]
    if system_roles:
        return error_response(
            code="system_role_delete_blocked",
            message="Cannot delete system role(s)",
            status=400,
            extra={"ids": [str(r.id) for r in system_roles]},
        )

    for role in roles:
        _invalidate_users_for_role(role)

    for role in roles:
        db.session.delete(role)

    db.session.commit()
    log_audit("roles.bulk_delete", "role", None, {"ids": ids})
    emit_admin_event("rbac", "roles_changed", {})

    return jsonify({"ok": True, "deleted": len(roles)})


@rbac_admin_bp.put("/roles/<role_id>/permissions")
def set_role_permissions(role_id: str):
    role = Role.query.get(role_id)
    if not role:
        return not_found("Not found")

    data = request.get_json(force=True) or {}
    permission_ids = data.get("permissionIds", [])

    if not isinstance(permission_ids, list):
        return bad_request(
            "permissionIds must be a list",
            code="validation_error",
            path="permissionIds",
        )

    role.permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
    db.session.commit()

    _invalidate_users_for_role(role)
    log_audit("roles.set_permissions", "role", role_id, {"permissionIds": permission_ids})
    emit_admin_event("rbac", "roles_changed", {})

    return jsonify(_json_role(role))


# =========================================================
# Groups
# =========================================================

@rbac_admin_bp.get("/groups")
def list_groups():
    q = (request.args.get("q") or "").strip().lower()
    query = Group.query
    if q:
        query = query.filter(
            or_(
                Group.name.ilike(f"%{q}%"),
                Group.description.ilike(f"%{q}%"),
            )
        )

    return paginate_query(
        query,
        _json_group,
        Group,
        allowed_sort_fields=["name", "description"],
        default_sort="name",
    )


@rbac_admin_bp.post("/groups")
def create_group():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return bad_request("name is required", code="validation_error", path="name")

    group = Group(name=name, description=data.get("description"))
    db.session.add(group)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return conflict("group name already exists", code="conflict")

    log_audit("groups.create", "group", group.id, {"payload": data})
    emit_admin_event("rbac", "groups_changed", {})

    return jsonify(_json_group(group)), 201


@rbac_admin_bp.put("/groups/<group_id>")
def update_group(group_id: str):
    group = Group.query.get(group_id)
    if not group:
        return not_found("Not found")

    data = request.get_json(force=True) or {}
    for field in ["name", "description"]:
        if field in data:
            setattr(group, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return conflict("group name already exists", code="conflict")

    log_audit("groups.update", "group", group_id, {"payload": data})
    emit_admin_event("rbac", "groups_changed", {})

    return jsonify(_json_group(group))


@rbac_admin_bp.delete("/groups/<group_id>")
def delete_group(group_id: str):
    group = Group.query.get(group_id)
    if not group:
        return not_found("Not found")

    _invalidate_users_for_group(group)

    db.session.delete(group)
    db.session.commit()

    log_audit("groups.delete", "group", group_id, {})
    emit_admin_event("rbac", "groups_changed", {})

    return jsonify({"ok": True})


@rbac_admin_bp.post("/groups/bulk-delete")
def bulk_delete_groups():
    ids, err = _parse_ids("ids")
    if err:
        return err

    rows = Group.query.filter(Group.id.in_(ids)).all()

    for group in rows:
        _invalidate_users_for_group(group)

    for r in rows:
        db.session.delete(r)

    db.session.commit()
    log_audit("groups.bulk_delete", "group", None, {"ids": ids})
    emit_admin_event("rbac", "groups_changed", {})

    return jsonify({"ok": True, "deleted": len(rows)})


@rbac_admin_bp.put("/groups/<group_id>/roles")
def set_group_roles(group_id: str):
    group = Group.query.get(group_id)
    if not group:
        return not_found("Not found")

    data = request.get_json(force=True) or {}
    role_ids = data.get("roleIds", [])

    if not isinstance(role_ids, list):
        return bad_request("roleIds must be a list", code="validation_error", path="roleIds")

    group.roles = Role.query.filter(Role.id.in_(role_ids)).all()
    db.session.commit()

    _invalidate_users_for_group(group)
    log_audit("groups.set_roles", "group", group_id, {"roleIds": role_ids})
    emit_admin_event("rbac", "groups_changed", {})

    return jsonify(_json_group(group))


# =========================================================
# Users
# =========================================================

@rbac_admin_bp.get("/users")
def list_users():
    q = (request.args.get("q") or "").strip().lower()
    query = User.query

    if q:
        query = query.filter(
            or_(
                User.email.ilike(f"%{q}%"),
                User.name.ilike(f"%{q}%"),
            )
        )

    return paginate_query(
        query,
        _json_user,
        User,
        allowed_sort_fields=["email", "name", "is_superadmin"],
        default_sort="email",
    )


@rbac_admin_bp.get("/users/<user_id>")
def get_user(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return not_found("Not found")
    return jsonify(_json_user(user))


@rbac_admin_bp.put("/users/<user_id>")
def update_user(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return not_found("Not found")

    data = request.get_json(force=True) or {}

    if "name" in data:
        user.name = data["name"]

    if "is_superadmin" in data:
        if not getattr(g.current_user, "is_superadmin", False):
            return forbidden("Only superadmin can change superadmin flag")
        user.is_superadmin = bool(data["is_superadmin"])

    role_ids = data.get("roleIds", None)
    group_ids = data.get("groupIds", None)

    if role_ids is not None:
        if not isinstance(role_ids, list):
            return bad_request("roleIds must be a list", code="validation_error", path="roleIds")
        user.roles = Role.query.filter(Role.id.in_(role_ids)).all()

    if group_ids is not None:
        if not isinstance(group_ids, list):
            return bad_request("groupIds must be a list", code="validation_error", path="groupIds")
        user.groups = Group.query.filter(Group.id.in_(group_ids)).all()

    db.session.commit()

    invalidate_user_permissions(user.id)
    log_audit("users.update", "user", user_id, {"payload": data})
    emit_admin_event("rbac", "users_changed", {"userId": user_id})

    return jsonify(_json_user(user))


@rbac_admin_bp.delete("/users/<user_id>")
def delete_user(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return not_found("Not found")

    db.session.delete(user)
    db.session.commit()

    invalidate_user_permissions(user_id)
    log_audit("users.delete", "user", user_id, {})
    emit_admin_event("rbac", "users_changed", {"userId": user_id})

    return jsonify({"ok": True})


@rbac_admin_bp.post("/users/bulk-delete")
def bulk_delete_users():
    ids, err = _parse_ids("ids")
    if err:
        return err

    rows = User.query.filter(User.id.in_(ids)).all()
    for u in rows:
        invalidate_user_permissions(u.id)
        db.session.delete(u)

    db.session.commit()
    log_audit("users.bulk_delete", "user", None, {"ids": ids})
    emit_admin_event("rbac", "users_changed", {"userId": ids})

    return jsonify({"ok": True, "deleted": len(rows)})


# =========================================================
# User Overrides
# =========================================================

@rbac_admin_bp.get("/users/<user_id>/overrides")
def list_user_overrides(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return not_found("Not found")

    query = UserPermission.query.filter_by(user_id=user.id)

    def serializer(up):
        p = Permission.query.get(up.permission_id)
        if not p:
            return None
        return {
            "id": str(up.id),
            "permission": _json_permission(p),
            "granted": bool(up.granted),
        }

    return paginate_query(query, serializer, UserPermission)


@rbac_admin_bp.put("/users/<user_id>/overrides")
def set_user_overrides(user_id: str):
    user = User.query.get(user_id)
    if not user:
        return not_found("Not found")

    data = request.get_json(force=True) or {}
    items = data.get("items", [])

    if not isinstance(items, list):
        return bad_request("items must be a list", code="validation_error", path="items")

    UserPermission.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    created = 0
    for it in items:
        pid = it.get("permissionId")
        if not pid:
            continue

        if not Permission.query.get(pid):
            continue

        granted = bool(it.get("granted", True))
        db.session.add(UserPermission(user_id=user.id, permission_id=pid, granted=granted))
        created += 1

    db.session.commit()

    invalidate_user_permissions(user.id)
    log_audit("users.set_overrides", "user", user_id, {"count": created})
    emit_admin_event("rbac", "users_changed", {"userId": user_id})

    return jsonify({"ok": True, "updated": created})