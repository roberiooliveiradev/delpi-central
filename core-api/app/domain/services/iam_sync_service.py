# app/domain/services/iam_sync_service.py

class IamSyncService:

    def __init__(self, uow):
        self.uow = uow

        from app.infrastructure.iam.keycloak_admin_client import KeycloakAdminClient
        self.kc = KeycloakAdminClient()

    # =========================================================

    def sync_user(self, user_id, is_superadmin: bool):

        # =====================================================
        # 1️⃣ Recalcula permissões via RBAC interno
        # =====================================================

        from app.domain.services.permission_resolver import PermissionResolver

        resolver = PermissionResolver(
            permission_query=self.uow.permission_queries,
            cache=self.uow.cache,
        )

        permissions = resolver.resolve(
            user_id=user_id,
            is_superadmin=is_superadmin,
        )

        # =====================================================
        # 2️⃣ Descobre roles atuais no Keycloak
        # =====================================================

        current_roles = self.kc.get_user_realm_roles(str(user_id))
        current_role_names = {r["name"] for r in current_roles}

        new_roles = set(permissions)

        to_add = new_roles - current_role_names
        to_remove = current_role_names - new_roles

        # =====================================================
        # 3️⃣ Aplica delta no Keycloak
        # =====================================================

        if to_add:
            self.kc.add_realm_roles_to_user(str(user_id), list(to_add))

        if to_remove:
            self.kc.remove_realm_roles_from_user(str(user_id), list(to_remove))