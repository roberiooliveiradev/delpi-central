# app/infrastructure/seeds/permissions_seed.py

from app.extensions.db import db
from app.infrastructure.db.models import Permission


BASE_PERMISSIONS = [
    # =============================
    # RBAC
    # =============================
    {"code": "rbac.manage", "name": "Gerenciar RBAC", "description": "Gerenciar roles, permissões e grupos"},

    # =============================
    # Users
    # =============================
    {"code": "users.view", "name": "Visualizar usuários", "description": "Listar usuários do sistema"},
    {"code": "users.manage", "name": "Gerenciar usuários", "description": "Criar, editar e atribuir roles a usuários"},

    # =============================
    # Groups
    # =============================
    {"code": "groups.manage", "name": "Gerenciar grupos", "description": "Criar e editar grupos"},

    # =============================
    # Permissions
    # =============================
    {"code": "permissions.manage", "name": "Gerenciar permissões", "description": "Criar e editar permissões"},

    # =============================
    # Apps & Routes
    # =============================
    {"code": "apps.manage", "name": "Gerenciar apps", "description": "Criar e editar apps"},
    {"code": "routes.manage", "name": "Gerenciar rotas", "description": "Criar e editar rotas"},

    # =============================
    # Dashboard
    # =============================
    {"code": "dashboard.view", "name": "Visualizar dashboard", "description": "Acessar dashboard do sistema"},

    # =============================
    # Notifications
    # =============================
    {"code": "notifications.view", "name": "Visualizar notificações", "description": "Listar notificações do usuário"},
    {"code": "notifications.manage", "name": "Gerenciar notificações", "description": "Marcar notificações como lidas"},
]


def seed_base_permissions():

    created = 0
    updated = 0

    for perm_data in BASE_PERMISSIONS:

        existing = Permission.query.filter_by(code=perm_data["code"]).first()

        if not existing:
            permission = Permission(
                code=perm_data["code"],
                name=perm_data["name"],
                description=perm_data["description"],
            )
            db.session.add(permission)
            created += 1
        else:
            # Atualiza nome/descrição se mudar
            if existing.name != perm_data["name"] or existing.description != perm_data["description"]:
                existing.name = perm_data["name"]
                existing.description = perm_data["description"]
                updated += 1

    if created or updated:
        db.session.commit()

    print(f"[SEED] Permissões criadas: {created}, atualizadas: {updated}")
