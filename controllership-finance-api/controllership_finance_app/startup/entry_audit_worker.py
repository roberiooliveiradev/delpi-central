"""Worker da auditoria. Ao subir, devolve para a fila as execuções que ficaram running."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger("controllership_finance.entry_audit")


async def run_entry_audit_loop(service_factory) -> None:
    service = service_factory()
    try:
        service.recover_orphans()
    except Exception:
        logger.exception("entry_audit_orphan_recovery_failed")
    while True:
        try:
            worked = await asyncio.to_thread(service.claim_and_execute)
        except Exception:
            logger.exception("entry_audit_worker_failed")
            worked = False
        await asyncio.sleep(0.2 if worked else 2)
