# app/domain/ports/plugin_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class PluginRepositoryPort(ABC):

    @abstractmethod
    def get_by_id(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def create(
        self,
        data: Dict[str, Any],
        *,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> None:
        ...

    @abstractmethod
    def update_version(
        self,
        plugin_id: str,
        version: str,
        *,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> None:
        ...

    @abstractmethod
    def update_metadata(
        self,
        plugin_id: str,
        *,
        name: str,
        description: Optional[str],
        icon: Optional[str],
        app_type: Optional[str] = None,
        base_path: Optional[str] = None,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> None:
        """
        Atualiza identidade do app (sidebar/launcher leem estes campos).

        `app_type` / `base_path` são opcionais — usados no register/rollback de
        nova versão; o update cosmético do manifesto pode omiti-los.
        """
        ...

    @abstractmethod
    def delete(self, plugin_id: str) -> None:
        ...