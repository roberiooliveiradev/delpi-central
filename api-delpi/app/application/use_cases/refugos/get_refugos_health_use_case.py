from __future__ import annotations

from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort


class GetRefugosHealthUseCase:
    def __init__(self, repository: RefugosRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> dict:
        row = self._repository.check_health()
        return {
            "ok": bool(row),
            "filial": (row.get("filial") or "").strip() if row else None,
            "ultimaData": (row.get("ultima_data") or None) if row else None,
        }
