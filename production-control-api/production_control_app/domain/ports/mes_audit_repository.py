"""Port do repositório de auditoria MES (append-only)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MesAuditRepositoryPort(ABC):
    @abstractmethod
    def append(
        self,
        *,
        branch: str,
        work_center: str,
        action: str,
        actor_type: str,
        actor_ref: str | None = None,
        run_id: str | None = None,
        occurred_at: Any | None = None,
        details: dict[str, Any] | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """Insere evento de auditoria. Com ``conn``, participa da transação do chamador."""

    @abstractmethod
    def list_for_run(self, run_id: str) -> list[dict[str, Any]]: ...
