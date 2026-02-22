# app/tests/unit/test_permission_resolver.py

import uuid
import pytest
from app.domain.services.permission_resolver import resolve_user_permissions
from app.extensions.permission_cache import invalidate_user_permissions
from app.infrastructure.db.models import (
    User, Role, Permission, Group, UserPermission
)
from app.extensions.db import db


def test_superadmin_bypass(app):
    with app.app_context():
        p1 = Permission(code="a.view", name="A")
        p2 = Permission(code="b.view", name="B")
        db.session.add_all([p1, p2])

        user = User(
            id=str(uuid.uuid4()),
            email="root@test.com",
            name="Root",
            is_superadmin=True
        )
        db.session.add(user)
        db.session.commit()

        perms = resolve_user_permissions(user)
        assert set(perms) == {"a.view", "b.view"}


def test_role_permission_resolution(app):
    with app.app_context():
        p = Permission(code="reports.view", name="Reports")
        role = Role(name="Analyst")
        role.permissions.append(p)

        user = User(
            id=str(uuid.uuid4()),
            email="a@test.com",
            name="A"
        )
        user.roles.append(role)

        db.session.add_all([p, role, user])
        db.session.commit()

        perms = resolve_user_permissions(user)
        assert "reports.view" in perms


def test_group_permission_resolution(app):
    with app.app_context():
        p = Permission(code="group.view", name="Group")
        role = Role(name="GroupRole")
        role.permissions.append(p)

        group = Group(name="Team")
        group.roles.append(role)

        user = User(
            id=str(uuid.uuid4()),
            email="g@test.com",
            name="G"
        )
        user.groups.append(group)

        db.session.add_all([p, role, group, user])
        db.session.commit()

        perms = resolve_user_permissions(user)
        assert "group.view" in perms


def test_user_override_grant_and_revoke(app):
    with app.app_context():
        p = Permission(code="override.view", name="Override")
        user = User(
            id=str(uuid.uuid4()),
            email="o@test.com",
            name="O"
        )

        db.session.add_all([p, user])
        db.session.commit()

        # grant
        db.session.add(UserPermission(
            user_id=user.id,
            permission_id=p.id,
            granted=True
        ))
        db.session.commit()

        perms = resolve_user_permissions(user)
        assert "override.view" in perms

        # revoke
        invalidate_user_permissions(user.id)
        db.session.query(UserPermission).delete()
        db.session.add(UserPermission(
            user_id=user.id,
            permission_id=p.id,
            granted=False
        ))
        db.session.commit()

        perms = resolve_user_permissions(user)
        assert "override.view" not in perms