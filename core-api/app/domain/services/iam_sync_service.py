# app/domain/services/iam_sync_service.py

from app.domain.services.permission_resolver import PermissionResolver


class IamSyncService:
    """
    Serviço responsável por manter coerência do RBAC interno
    após alterações administrativas.

    ⚠️ Não sincroniza mais roles com Keycloak.
    A DELPI Central resolve autorização internamente.
    """

    def __init__(self, uow):
        self.uow = uow

    # =========================================================
    # Public API
    # =========================================================

    def sync_user(self, user_id, is_superadmin: bool) -> None:
        """
        Recalcula permissões efetivas do usuário
        e garante invalidação de cache.
        """

        resolver = PermissionResolver(
            permission_query=self.uow.permission_queries,
            cache=self.uow.cache,
        )

        # Recalcula permissões (efeito colateral: cache)
        resolver.resolve(
            user_id=user_id,
            is_superadmin=is_superadmin,
        )

        # Segurança adicional: invalidação explícita
        if self.uow.cache:
            self.uow.cache.invalidate(str(user_id))