from __future__ import annotations

import logging
from typing import Any

from tm_app.application.services.dashboard_query_cache import dashboard_query_cache
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.config import settings

logger = logging.getLogger(__name__)


class DashboardRecalcHookService:
    """Reage a mutações de CRUD do transformômetro.

    Fonte única do dashboard é o motor live (``DashboardLiveService``) com
    ``DashboardQueryCache``. Toda mutação apenas **invalida** o cache em O(1) —
    sem recálculo pesado no caminho de escrita; a próxima leitura recomputa.

    A tabela materializada legada ``dashboard_calculos`` só é atualizada quando
    ``TM_DASHBOARD_PERSIST_CACHE`` está ligado (integrações que ainda leem o
    snapshot persistido). Por padrão fica desligada.
    """

    def __init__(self) -> None:
        self._recalc = DashboardRecalcService()

    @property
    def persist_enabled(self) -> bool:
        return settings.TM_DASHBOARD_AUTO_RECALC and settings.TM_DASHBOARD_PERSIST_CACHE

    def _invalidate_cache(self) -> int:
        try:
            cleared = dashboard_query_cache.invalidate()
            logger.debug(
                "transformometro_dashboard_cache_invalidated entries=%d", cleared
            )
            return cleared
        except Exception as exc:  # pragma: no cover - invalidação nunca deve quebrar CRUD
            logger.warning(
                "transformometro_dashboard_cache_invalidate_failed err=%s", exc
            )
            return 0

    def _safe_recalculate(self, **kwargs: Any) -> dict[str, Any] | None:
        try:
            return self._recalc.recalculate(**kwargs)
        except Exception as exc:
            logger.warning(
                "transformometro_dashboard_recalc_hook_failed kwargs=%s err=%s",
                kwargs,
                exc,
                exc_info=True,
            )
            return None

    def _handle(self, **recalc_kwargs: Any) -> dict[str, Any]:
        cleared = self._invalidate_cache()
        result: dict[str, Any] = {"cache_invalidated": True, "cache_entries_cleared": cleared}
        if self.persist_enabled:
            persisted = self._safe_recalculate(**recalc_kwargs) or {}
            result["persisted"] = True
            result.update(persisted)
        else:
            result["persisted"] = False
        return result

    def after_processo(self, processo_id: str) -> dict[str, Any] | None:
        """Medição, revisão, investimento ou metadados do processo."""
        return self._handle(processo_id=str(processo_id))

    def after_revisao(
        self,
        revisao_id: str,
        *,
        processo_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Alteração em revisão; ``processo_id`` cobre ativação (revisões irmãs)."""
        if processo_id:
            return self._handle(processo_id=str(processo_id))
        return self._handle(revisao_id=str(revisao_id))

    def after_global_resource_change(self) -> dict[str, Any] | None:
        """Recursos/vínculos/custos alteram rateio global — invalida tudo."""
        return self._handle()
