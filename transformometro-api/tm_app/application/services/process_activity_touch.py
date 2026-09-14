"""Bump ``processos.updated_at`` after any process-family mutation.

Single owner for list ordering ("Data de atualização"). Call after successful
writes of process children (revisão, instância, diagrama, decomposição,
arquivo, evidência, vínculo, etc.). Safe no-op on blank id / persistence errors.
"""

from __future__ import annotations

import logging

from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)

logger = logging.getLogger(__name__)


def touch_processo_updated_at(processo_id: str | None) -> bool:
    pid = str(processo_id or "").strip()
    if not pid:
        return False
    try:
        return bool(ProcessoRepository().touch_updated_at(pid))
    except Exception as exc:  # pragma: no cover - never break write path
        logger.warning(
            "transformometro_processo_touch_updated_at_failed processo_id=%s err=%s",
            pid,
            exc,
        )
        return False


def resolve_processo_id_for_revisao(
    revisao_id: str,
    *,
    processo_id: str | None = None,
) -> str | None:
    pid = str(processo_id or "").strip() or None
    if pid:
        return pid
    try:
        row = RevisaoRepository().get(str(revisao_id))
        return str((row or {}).get("processo_id") or "").strip() or None
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "transformometro_processo_touch_lookup_failed revisao_id=%s err=%s",
            revisao_id,
            exc,
        )
        return None


def touch_processo_for_revisao(
    revisao_id: str,
    *,
    processo_id: str | None = None,
) -> str | None:
    """Touch parent process; returns resolved ``processo_id`` when known."""
    pid = resolve_processo_id_for_revisao(revisao_id, processo_id=processo_id)
    touch_processo_updated_at(pid)
    return pid
