from __future__ import annotations

from si_app.application.dto.transforma_mais.raw_data import TransformaMaisRawData
from si_app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from transformometro_read.loader import load_transformometro_raw


class TransformometroProcessRepository(ProcessQueryRepositoryPort):
    """Lê Transforma+ do schema Postgres transformometro (fonte oficial pós-migração)."""

    def __init__(self, base: PluginBaseRepository | None = None) -> None:
        self._base = base or PluginBaseRepository()

    def load_raw_data(self) -> TransformaMaisRawData:
        payload = load_transformometro_raw(self._base.fetch_all)
        return TransformaMaisRawData(
            processos=payload.processos,
            revisoes=payload.revisoes,
            medicoes=payload.medicoes,
            investimentos=payload.investimentos,
            recursos_compartilhados=payload.recursos_compartilhados,
            revisao_recursos_compartilhados=payload.revisao_recursos_compartilhados,
        )
