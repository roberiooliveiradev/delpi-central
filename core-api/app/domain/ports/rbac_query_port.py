# app/domain/ports/rbac_query_port.py

from typing import Protocol, List
from uuid import UUID


class RbacQueryPort(Protocol):
    def list_user_ids_by_role(self, role_id: UUID) -> List[str]:
        """
        Retorna user_ids (string UUID) com a role atribuída diretamente.
        """
        ...

    def list_user_ids_by_group_role(self, role_id: UUID) -> List[str]:
        """
        Retorna user_ids (string UUID) que ganham a role via grupos.
        """
        ...

    def list_user_ids_by_group(self, group_id: UUID) -> List[str]:
        """
        """
        ...

    def list_user_ids_by_permission_code(self, permission_code: str) -> List[str]:
        """
        Retorna user_ids (string UUID) com a permissão via role direta ou grupo.
        """
        ...

