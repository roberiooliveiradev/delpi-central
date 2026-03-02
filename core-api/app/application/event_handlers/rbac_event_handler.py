# app/application/event_handlers/rbac_event_handler.py

from uuid import UUID

from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.iam_sync_service import IamSyncService


class RbacEventHandler:

    def __init__(self, uow):
        self.uow = uow
        self.iam = IamSyncService(uow)

    # =========================================================

    def handle(self, event: AdminChangedEvent):

        if event.entity != "rbac":
            return

        # =====================================================
        # 1️⃣ Evento direcionado (um usuário)
        # =====================================================

        if event.target_user_id:
            self._sync_user(UUID(event.target_user_id))
            return

        # =====================================================
        # 2️⃣ Eventos que afetam ROLE
        # =====================================================

        if event.action in (
            "permission_added_to_role",
            "permission_removed_from_role",
            "role_permissions_replaced",
        ):
            role_id = UUID(event.payload["roleId"])
            user_ids = self._get_users_by_role(role_id)
            self._sync_users(user_ids)
            return

        # =====================================================
        # 3️⃣ Eventos que afetam GROUP
        # =====================================================

        if event.action in (
            "role_added_to_group",
            "role_removed_from_group",
            "group_roles_replaced",
        ):
            group_id = UUID(event.payload["groupId"])
            user_ids = self.uow.rbac_queries.list_user_ids_by_group(group_id)
            self._sync_users(user_ids)
            return

    # =========================================================
    # Helpers
    # =========================================================

    def _get_users_by_role(self, role_id):
        user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(role_id))
        user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(role_id))
        return user_ids

    def _sync_users(self, user_ids):
        for uid in user_ids:
            self._sync_user(uid)

    def _sync_user(self, user_id):

        if self.uow.cache:
            self.uow.cache.invalidate(str(user_id))

        user = self.uow.users.get_by_id(user_id)
        if not user:
            return

        self.iam.sync_user(
            user_id=user.id,
            is_superadmin=bool(user.is_superadmin),
        )