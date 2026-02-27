# app/domain/services/permission_resolver.py

from typing import List, Set
from uuid import UUID

from app.domain.ports.permission_query_port import PermissionQueryPort
from app.domain.ports.cache_port import PermissionCachePort


class PermissionResolver:
    """
    Serviço de domínio responsável por resolver permissões efetivas de um usuário.

    Não conhece:
    - SQLAlchemy
    - Flask
    - db.session
    - cache concreto
    """

    def __init__(
        self,
        permission_query: PermissionQueryPort,
        cache: PermissionCachePort | None = None,
    ):
        self.permission_query = permission_query
        self.cache = cache

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def resolve(self, user_id: UUID, is_superadmin: bool) -> List[str]:
        """
        Retorna lista de permission codes efetivos do usuário.
        """

        # 1️⃣ Superadmin SEMPRE primeiro (bypass absoluto)
        if is_superadmin:
            permissions = self.permission_query.list_all_permission_codes()
            self._store_cache(user_id, permissions)
            return permissions

        # 2️⃣ Cache (apenas para usuários normais)
        if self.cache:
            cached = self.cache.get(str(user_id))
            if cached is not None:
                return cached

        # 3️⃣ Permissões via roles diretas
        direct_permissions = set(
            self.permission_query.list_direct_role_permissions(user_id)
        )

        # 4️⃣ Permissões via grupos
        group_permissions = set(
            self.permission_query.list_group_role_permissions(user_id)
        )

        effective: Set[str] = direct_permissions | group_permissions

        # 5️⃣ Overrides do usuário
        overrides = self.permission_query.list_user_overrides(user_id)

        for code, granted in overrides:
            if granted:
                effective.add(code)
            else:
                effective.discard(code)

        result = sorted(effective)

        self._store_cache(user_id, result)

        return result

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def invalidate(self, user_id: UUID) -> None:
        if self.cache:
            self.cache.invalidate(str(user_id))

    def _store_cache(self, user_id: UUID, permissions: List[str]) -> None:
        if self.cache:
            self.cache.set(str(user_id), permissions)