# app/domain/ports/permission_query_port.py

from typing import Protocol, List, Tuple
from uuid import UUID


class PermissionQueryPort(Protocol):
    """
    Port responsável por consultas relacionadas à resolução de permissões.
    NÃO deve depender de ORM.
    """

    def list_all_permission_codes(self) -> List[str]:
        ...

    def list_direct_role_permissions(self, user_id: UUID) -> List[str]:
        ...

    def list_group_role_permissions(self, user_id: UUID) -> List[str]:
        ...

    def list_user_overrides(self, user_id: UUID) -> List[Tuple[str, bool]]:
        """
        Retorna lista de (permission_code, granted)
        """
        ...