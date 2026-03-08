# app/infrastructure/seeds/permissions_seed.py

from app.infrastructure.db.models import Permission


BASE_PERMISSIONS = [

    # RBAC
    {
        "code": "rbac.manage",
        "name": "Gerenciar RBAC",
        "description": "Gerenciar roles, permissões e grupos",
        "module": "system",
    },

    # Users
    {
        "code": "users.view",
        "name": "Visualizar usuários",
        "description": "Listar usuários do sistema",
        "module": "system",
    },
    {
        "code": "users.manage",
        "name": "Gerenciar usuários",
        "description": "Criar, editar e atribuir roles",
        "module": "system",
    },

    # Groups
    {
        "code": "groups.manage",
        "name": "Gerenciar grupos",
        "description": "Criar e editar grupos",
        "module": "system",
    },

    # Roles
    {
        "code": "roles.manage",
        "name": "Gerenciar papéis",
        "description": "Criar e editar papéis",
        "module": "system",
    },

    # Permissions
    {
        "code": "permissions.manage",
        "name": "Gerenciar permissões",
        "description": "Criar e editar permissões",
        "module": "system",
    },

    # Apps
    {
        "code": "apps.manage",
        "name": "Gerenciar apps",
        "description": "Criar e editar apps",
        "module": "system",
    },
    {
        "code": "apps.view",
        "name": "Visualizar apps",
        "description": "Listar apps plugados",
        "module": "system",
    },

    # Routes
    {
        "code": "routes.manage",
        "name": "Gerenciar rotas",
        "description": "Criar e editar rotas",
        "module": "system",
    },
]


def seed_base_permissions(session):

    created = 0
    updated = 0
    deleted = 0

    # =====================================
    # 1️⃣ REMOVE PERMISSÕES ANTIGAS SEM MODULE
    # =====================================

    old_permissions = (
        session.query(Permission)
        .filter(Permission.module.is_(None))
        .all()
    )

    for perm in old_permissions:
        session.delete(perm)
        deleted += 1

    if deleted:
        session.commit()

    # =====================================
    # 2️⃣ UPSERT DAS PERMISSÕES BASE
    # =====================================

    for perm_data in BASE_PERMISSIONS:

        existing = (
            session.query(Permission)
            .filter_by(code=perm_data["code"])
            .first()
        )

        if not existing:
            permission = Permission(
                code=perm_data["code"],
                name=perm_data["name"],
                description=perm_data["description"],
                module=perm_data["module"],
            )

            session.add(permission)
            created += 1

        else:
            if (
                existing.name != perm_data["name"]
                or existing.description != perm_data["description"]
                or existing.module != perm_data["module"]
            ):
                existing.name = perm_data["name"]
                existing.description = perm_data["description"]
                existing.module = perm_data["module"]
                updated += 1

    if created or updated:
        session.commit()

    print(
        f"[SEED] Permissões deletadas: {deleted}, criadas: {created}, atualizadas: {updated}"
    )