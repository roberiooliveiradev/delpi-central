"""Worker da exportação de XML NF-e.

Não roda dentro do processo HTTP. Comandos:

    python -m financial_app.jobs.questor_nfe_xml_export run-once
    python -m financial_app.jobs.questor_nfe_xml_export worker

Enabled false é o default. Nesse estado o worker não baixa nem grava XML.
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
from collections.abc import Callable

from financial_app.application.services.questor_nfe_xml_export_service import (
    QuestorNfeXmlExportService,
    application_root,
    error_code,
    validate_runtime_settings,
)
from financial_app.config import load_nfe_export_settings, settings
from financial_app.domain.errors import NfeExportConfigurationError
from financial_app.domain.nfe_export import BranchExportResult, CycleResult, NfeExportSettings
from financial_app.infrastructure.filesystem.nfe_xml_export_storage import NfeXmlExportStorage
from financial_app.infrastructure.gateways.questor_branch_fiscal_client import (
    QuestorBranchFiscalClient,
)
from financial_app.infrastructure.gateways.questor_company_registry import QuestorCompanyRegistry
from financial_app.infrastructure.gateways.questor_company_session import QuestorCompanySession
from financial_app.infrastructure.gateways.questor_nfe_export_source import QuestorNfeExportSource
from financial_app.infrastructure.persistence.migrations_runner import run_migrations
from financial_app.infrastructure.persistence.plugins_postgres_connection import get_connection
from financial_app.infrastructure.persistence.questor_nfe_xml_export_repository import (
    PostgresNfeExportLedger,
)

logger = logging.getLogger(__name__)
_BRANCHES = ("01", "02")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(level=getattr(logging, (settings.LOG_LEVEL or "INFO").upper(), logging.INFO))
    if args == ["run-once"]:
        return run_once()
    if args == ["worker"]:
        return run_worker()
    print(
        "uso: python -m financial_app.jobs.questor_nfe_xml_export run-once|worker",
        file=sys.stderr,
    )
    return 2


def run_once() -> int:
    try:
        loaded = load_nfe_export_settings()
        result = execute_cycle(loaded)
    except NfeExportConfigurationError as exc:
        logger.info(
            "provider=questor job=nfe_xml_export status=invalid_configuration error_code=invalid_configuration"
        )
        print(f"job=nfe_xml_export status=invalid_configuration error_code=invalid_configuration")
        _ = exc
        return 2
    emit_result(result)
    return exit_code(result)


def run_worker() -> int:
    stop_event = threading.Event()
    previous_term = signal.signal(signal.SIGTERM, lambda signum, frame: request_stop(stop_event, signum))
    previous_int = signal.signal(signal.SIGINT, lambda signum, frame: request_stop(stop_event, signum))
    try:
        return worker_loop(
            load_settings=load_nfe_export_settings,
            run_cycle=execute_cycle,
            stop_event=stop_event,
        )
    except NfeExportConfigurationError:
        logger.info(
            "provider=questor job=nfe_xml_export status=invalid_configuration error_code=invalid_configuration"
        )
        return 2
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)


def request_stop(stop_event: threading.Event, signum: int) -> None:
    logger.info("provider=questor job=nfe_xml_export status=stopping signal=%s", signum)
    stop_event.set()


def worker_loop(
    *,
    load_settings: Callable[[], NfeExportSettings],
    run_cycle: Callable[[NfeExportSettings], CycleResult],
    stop_event: threading.Event,
) -> int:
    announced_disabled = False
    while not stop_event.is_set():
        loaded = load_settings()
        if not loaded.enabled:
            if not announced_disabled:
                logger.info("provider=questor job=nfe_xml_export status=disabled")
                announced_disabled = True
        else:
            announced_disabled = False
            result = run_cycle(loaded)
            emit_result(result)
            if result.status == "invalid_configuration":
                return 2
        wait_seconds = loaded.interval_seconds if loaded.interval_seconds >= 1 else 900
        if stop_event.wait(wait_seconds):
            logger.info("provider=questor job=nfe_xml_export status=stopped")
            return 0
    logger.info("provider=questor job=nfe_xml_export status=stopped")
    return 0


def execute_cycle(loaded: NfeExportSettings) -> CycleResult:
    if not loaded.enabled:
        logger.info("provider=questor job=nfe_xml_export status=disabled")
        return CycleResult(status="disabled")
    try:
        directory = validate_runtime_settings(loaded, application_root=application_root())
    except NfeExportConfigurationError:
        logger.info(
            "provider=questor job=nfe_xml_export status=invalid_configuration error_code=invalid_configuration"
        )
        return CycleResult(status="invalid_configuration", error_code="invalid_configuration")
    run_migrations()
    connection = get_connection()
    ledger = PostgresNfeExportLedger(connection)
    registry: QuestorCompanyRegistry | None = None
    try:
        def source_factory():
            nonlocal registry
            registry = _build_registry(loaded.max_bytes)
            companies = registry.companies()
            return tuple(
                QuestorNfeExportSource(companies[branch].nfe) for branch in _BRANCHES
            )

        result = QuestorNfeXmlExportService(loaded).run(
            ledger=ledger,
            source_factory=source_factory,
            storage=NfeXmlExportStorage(directory),
        )
    except Exception as exc:
        logger.info(
            "provider=questor job=nfe_xml_export status=failed error_code=%s",
            error_code(exc),
        )
        result = CycleResult(status="failed", error_code=error_code(exc))
    finally:
        if registry is not None:
            registry.close()
        ledger.close()
    return result


def exit_code(result: CycleResult) -> int:
    if result.status == "invalid_configuration":
        return 2
    if result.status in {"disabled", "skipped_lock"}:
        return 0
    if result.status != "completed":
        return 1
    for branch in result.branches:
        if branch.status != "completed" or branch.failed:
            return 1
    return 0


def emit_result(result: CycleResult) -> None:
    print(f"job=nfe_xml_export status={result.status} duration_ms={result.duration_ms}")
    for branch in result.branches:
        print(_branch_line(branch))


def _branch_line(branch: BranchExportResult) -> str:
    return (
        f"job=nfe_xml_export branch={branch.branch_code} status={branch.status} "
        f"found={branch.found} eligible={branch.eligible} already_success={branch.already_success} "
        f"exported={branch.exported} ignored={branch.ignored} failed={branch.failed} "
        f"reconciled={branch.reconciled} duration_ms={branch.duration_ms}"
    )


def _build_registry(max_bytes: int) -> QuestorCompanyRegistry:
    company_ids = {
        "01": settings.FIN_QUESTOR_COMPANY_01_ID,
        "02": settings.FIN_QUESTOR_COMPANY_02_ID,
    }
    return QuestorCompanyRegistry(
        company_ids=company_ids,
        factory=lambda branch, company_id: QuestorBranchFiscalClient(
            QuestorCompanySession(
                branch_code=branch,
                company_id=company_id,
                max_bytes=max_bytes,
            )
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
