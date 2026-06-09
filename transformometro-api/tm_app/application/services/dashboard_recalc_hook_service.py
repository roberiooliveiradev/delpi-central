from __future__ import annotations

import logging
from typing import Any

from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.config import settings

logger = logging.getLogger(__name__)


class DashboardRecalcHookService:
    """Dispara recálculo incremental do cache ``dashboard_calculos`` após mutações CRUD."""

    def __init__(self) -> None:
        self._recalc = DashboardRecalcService()

    @property
    def enabled(self) -> bool:
        return settings.TM_DASHBOARD_AUTO_RECALC

    def _safe_recalculate(self, **kwargs: Any) -> dict[str, Any] | None:
        if not self.enabled:
            return None
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

    def after_processo(self, processo_id: str) -> dict[str, Any] | None:
        """Medição, revisão, investimento ou metadados do processo."""
        return self._safe_recalculate(processo_id=str(processo_id))

    def after_revisao(
        self,
        revisao_id: str,
        *,
        processo_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Alteração em revisão; ``processo_id`` cobre ativação (revisões irmãs)."""
        if processo_id:
            return self._safe_recalculate(processo_id=str(processo_id))
        return self._safe_recalculate(revisao_id=str(revisao_id))

    def after_global_resource_change(self) -> dict[str, Any] | None:
        """Recursos/vínculos/custos alteram rateio global — recálculo completo."""
        return self._safe_recalculate()
