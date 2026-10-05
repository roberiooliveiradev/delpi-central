"""Ciclo de exportação das NF-e novas do Questor para o diretório do Protheus.

O ledger success é definitivo: arquivo ausente não reexporta.
A data de corte usa a emissão fiscal, não a data de descoberta.
Não há parada antecipada por data: a ordenação da listagem não está comprovada.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Protocol

from financial_app.domain.errors import (
    NfeExportConfigurationError,
    NfeXmlRejected,
    QuestorAuthenticationError,
    QuestorDocumentNotFound,
    QuestorInvalidResponse,
    QuestorNotConfigured,
    QuestorUnavailable,
)
from financial_app.domain.fiscal_access_key import (
    access_key_check_digit_ok,
    access_key_digits,
    access_key_model,
)
from financial_app.domain.nfe_export import (
    STATUS_IGNORED,
    STATUS_SUCCESS,
    BranchExportResult,
    CycleResult,
    NfeExportListingPage,
    NfeExportRecord,
    NfeExportSettings,
    QuestorNfeListing,
)
from financial_app.domain.services.fiscal_calendar_date import fiscal_calendar_date
from financial_app.infrastructure.filesystem.nfe_xml_export_storage import (
    NfeXmlExportStorage,
    validate_export_directory,
)
from financial_app.infrastructure.xml.nfe_xml import parse_nfe_xml

logger = logging.getLogger(__name__)


class NfeExportLedgerPort(Protocol):
    def try_lock(self) -> bool: ...

    def unlock(self) -> None: ...

    def get(self, access_key: str) -> NfeExportRecord | None: ...

    def mark_processing(
        self,
        listing: QuestorNfeListing,
        *,
        access_key: str,
        filename: str,
        emission_date: object,
    ) -> NfeExportRecord | None: ...

    def mark_success(
        self,
        listing: QuestorNfeListing,
        *,
        access_key: str,
        filename: str,
        emission_date: object,
    ) -> NfeExportRecord | None: ...

    def mark_failed(self, *, access_key: str, code: str, message: str) -> None: ...

    def mark_ignored(
        self,
        listing: QuestorNfeListing,
        *,
        access_key: str,
        filename: str,
        emission_date: object,
    ) -> None: ...


class NfeExportSourcePort(Protocol):
    branch_code: str

    def list_page(self, *, page: int, page_size: int) -> NfeExportListingPage: ...

    def download_xml(self, *, provider_file_id: str, provider_entity_id: str) -> bytes: ...


class QuestorNfeXmlExportService:
    def __init__(self, settings: NfeExportSettings) -> None:
        self._settings = settings

    def run(
        self,
        *,
        ledger: NfeExportLedgerPort,
        source_factory: Callable[[], Iterable[NfeExportSourcePort]],
        storage: NfeXmlExportStorage,
    ) -> CycleResult:
        started = time.perf_counter()
        if self._settings.start_date is None:
            raise NfeExportConfigurationError("Data inicial de exportação ausente.")
        if not ledger.try_lock():
            logger.info("provider=questor job=nfe_xml_export status=skipped_lock")
            return CycleResult(status="skipped_lock", duration_ms=_elapsed_ms(started))
        try:
            branches = tuple(
                self._export_branch(source, ledger, storage) for source in source_factory()
            )
            return CycleResult(
                status="completed",
                branches=branches,
                duration_ms=_elapsed_ms(started),
            )
        finally:
            ledger.unlock()

    def _export_branch(
        self,
        source: NfeExportSourcePort,
        ledger: NfeExportLedgerPort,
        storage: NfeXmlExportStorage,
    ) -> BranchExportResult:
        started = time.perf_counter()
        branch = source.branch_code
        try:
            rows, truncated = self._collect(source)
            counts = _Counts()
            seen: set[str] = set()
            for listing in rows:
                self._export_one(source, listing, ledger, storage, counts, seen)
            status = "truncated" if truncated else "completed"
            if counts.failed and status == "completed":
                status = "completed_with_failures"
            result = BranchExportResult(
                branch_code=branch,
                status=status,
                found=len(rows),
                eligible=counts.eligible,
                already_success=counts.already_success,
                exported=counts.exported,
                ignored=counts.ignored,
                failed=counts.failed,
                reconciled=counts.reconciled,
                rejected=counts.rejected,
                duration_ms=_elapsed_ms(started),
            )
        except Exception as exc:
            code = error_code(exc)
            logger.info(
                "provider=questor job=nfe_xml_export branch=%s status=failed error_code=%s duration_ms=%s",
                branch,
                code,
                _elapsed_ms(started),
            )
            return BranchExportResult(
                branch_code=branch,
                status="failed",
                error_code=code,
                duration_ms=_elapsed_ms(started),
            )
        logger.info(
            "provider=questor job=nfe_xml_export branch=%s status=%s found=%s eligible=%s "
            "already_success=%s exported=%s ignored=%s failed=%s reconciled=%s duration_ms=%s",
            result.branch_code,
            result.status,
            result.found,
            result.eligible,
            result.already_success,
            result.exported,
            result.ignored,
            result.failed,
            result.reconciled,
            result.duration_ms,
        )
        return result

    def _collect(self, source: NfeExportSourcePort) -> tuple[list[QuestorNfeListing], bool]:
        """Pagina até uma página vazia ou incompleta.

        O total informado pelo portal cresce com o offset (página 1 reporta 101,
        página 3 reporta 301). Não é contagem real e não pode encerrar o ciclo.
        """

        found: list[QuestorNfeListing] = []
        page = 1
        while page <= self._settings.max_pages:
            current = source.list_page(page=page, page_size=self._settings.page_size)
            found.extend(current.items)
            if len(current.items) < self._settings.page_size:
                return found, False
            page += 1
        return found, True

    def _export_one(
        self,
        source: NfeExportSourcePort,
        listing: QuestorNfeListing,
        ledger: NfeExportLedgerPort,
        storage: NfeXmlExportStorage,
        counts: _Counts,
        seen: set[str],
    ) -> None:
        access_key = exportable_access_key(listing.access_key)
        if access_key is None:
            counts.rejected += 1
            logger.info(
                "provider=questor job=nfe_xml_export branch=%s status=skipped_invalid",
                listing.branch_code,
            )
            return
        suffix = access_key[-4:]
        listed_on = fiscal_calendar_date(listing.emission_at)
        start = self._settings.start_date
        assert start is not None
        if listed_on is not None and listed_on < start:
            counts.ignored += 1
            return
        if access_key in seen:
            return
        seen.add(access_key)
        counts.eligible += 1
        filename = storage.filename(access_key)
        current = ledger.get(access_key)
        if current is not None and current.status == STATUS_SUCCESS:
            counts.already_success += 1
            logger.info(
                "provider=questor job=nfe_xml_export branch=%s status=already_success access_key_suffix=%s",
                listing.branch_code,
                suffix,
            )
            return
        if current is not None and current.status == STATUS_IGNORED:
            counts.ignored += 1
            return
        if storage.exists(access_key):
            self._reconcile_existing(
                listing,
                access_key,
                filename,
                suffix,
                ledger,
                storage,
                counts,
            )
            return
        try:
            processing = ledger.mark_processing(
                listing,
                access_key=access_key,
                filename=filename,
                emission_date=listed_on,
            )
        except Exception as exc:
            self._count_failure(counts, listing.branch_code, suffix, exc)
            return
        if processing is not None and processing.status == STATUS_SUCCESS:
            counts.already_success += 1
            return
        if processing is not None and processing.status == STATUS_IGNORED:
            counts.ignored += 1
            return
        try:
            payload = source.download_xml(
                provider_file_id=listing.provider_file_id,
                provider_entity_id=listing.provider_entity_id,
            )
            parsed = parse_nfe_xml(
                payload,
                max_bytes=self._settings.max_bytes,
                expected_access_key=access_key,
            )
        except Exception as exc:
            self._mark_document_failed(ledger, access_key, listing.branch_code, suffix, counts, exc)
            return
        if parsed.emission_date < start:
            ledger.mark_ignored(
                listing,
                access_key=access_key,
                filename=filename,
                emission_date=parsed.emission_date,
            )
            counts.ignored += 1
            logger.info(
                "provider=questor job=nfe_xml_export branch=%s status=ignored "
                "reason=before_start_date access_key_suffix=%s",
                listing.branch_code,
                suffix,
            )
            return
        try:
            storage.write_atomic(access_key, payload)
        except Exception as exc:
            self._mark_document_failed(
                ledger,
                access_key,
                listing.branch_code,
                suffix,
                counts,
                exc,
                code="storage_failed",
            )
            return
        try:
            ledger.mark_success(
                listing,
                access_key=access_key,
                filename=filename,
                emission_date=parsed.emission_date,
            )
        except Exception as exc:
            counts.failed += 1
            logger.info(
                "provider=questor job=nfe_xml_export branch=%s status=reconcile_pending "
                "error_code=%s access_key_suffix=%s",
                listing.branch_code,
                error_code(exc),
                suffix,
            )
            return
        counts.exported += 1
        logger.info(
            "provider=questor job=nfe_xml_export branch=%s status=success access_key_suffix=%s",
            listing.branch_code,
            suffix,
        )

    def _reconcile_existing(
        self,
        listing: QuestorNfeListing,
        access_key: str,
        filename: str,
        suffix: str,
        ledger: NfeExportLedgerPort,
        storage: NfeXmlExportStorage,
        counts: _Counts,
    ) -> None:
        start = self._settings.start_date
        assert start is not None
        try:
            parsed = parse_nfe_xml(
                storage.read(access_key),
                max_bytes=self._settings.max_bytes,
                expected_access_key=access_key,
            )
        except Exception as exc:
            try:
                ledger.mark_processing(
                    listing,
                    access_key=access_key,
                    filename=filename,
                    emission_date=parsed_emission_or_none(listing),
                )
            except Exception:
                self._count_failure(counts, listing.branch_code, suffix, exc)
                return
            self._mark_document_failed(
                ledger,
                access_key,
                listing.branch_code,
                suffix,
                counts,
                exc,
                code="invalid_existing_file",
            )
            return
        if parsed.emission_date < start:
            storage.remove(access_key)
            ledger.mark_ignored(
                listing,
                access_key=access_key,
                filename=filename,
                emission_date=parsed.emission_date,
            )
            counts.ignored += 1
            return
        try:
            ledger.mark_success(
                listing,
                access_key=access_key,
                filename=filename,
                emission_date=parsed.emission_date,
            )
        except Exception as exc:
            self._count_failure(counts, listing.branch_code, suffix, exc)
            return
        counts.reconciled += 1
        logger.info(
            "provider=questor job=nfe_xml_export branch=%s status=reconciled access_key_suffix=%s",
            listing.branch_code,
            suffix,
        )

    def _mark_document_failed(
        self,
        ledger: NfeExportLedgerPort,
        access_key: str,
        branch: str,
        suffix: str,
        counts: _Counts,
        exc: BaseException,
        *,
        code: str | None = None,
    ) -> None:
        resolved = code or error_code(exc)
        try:
            ledger.mark_failed(access_key=access_key, code=resolved, message=safe_message(exc))
        except Exception:
            logger.info(
                "provider=questor job=nfe_xml_export branch=%s status=failed error_code=ledger_failed "
                "access_key_suffix=%s",
                branch,
                suffix,
            )
        counts.failed += 1
        logger.info(
            "provider=questor job=nfe_xml_export branch=%s status=failed error_code=%s access_key_suffix=%s",
            branch,
            resolved,
            suffix,
        )

    def _count_failure(self, counts: _Counts, branch: str, suffix: str, exc: BaseException) -> None:
        counts.failed += 1
        logger.info(
            "provider=questor job=nfe_xml_export branch=%s status=failed error_code=%s access_key_suffix=%s",
            branch,
            error_code(exc),
            suffix,
        )


class _Counts:
    def __init__(self) -> None:
        self.eligible = 0
        self.already_success = 0
        self.exported = 0
        self.ignored = 0
        self.failed = 0
        self.reconciled = 0
        self.rejected = 0


def parsed_emission_or_none(listing: QuestorNfeListing):
    return fiscal_calendar_date(listing.emission_at)


def error_code(exc: BaseException) -> str:
    if isinstance(exc, NfeXmlRejected):
        return exc.code
    if isinstance(exc, QuestorNotConfigured):
        return "questor_not_configured"
    if isinstance(exc, QuestorUnavailable):
        return "questor_unavailable"
    if isinstance(exc, QuestorAuthenticationError):
        return "questor_auth"
    if isinstance(exc, QuestorDocumentNotFound):
        return "document_not_found"
    if isinstance(exc, QuestorInvalidResponse):
        return "invalid_xml"
    if isinstance(exc, NfeExportConfigurationError):
        return "invalid_configuration"
    return "export_failed"


def safe_message(exc: BaseException) -> str:
    text = " ".join(str(exc).split())
    lowered = text.lower()
    if "<" in text or "token=" in lowered or "cookie" in lowered or "password" in lowered:
        return "falha sanitizada"
    return text[:240]


def exportable_access_key(value: str) -> str | None:
    digits = access_key_digits(value)
    if len(digits) != 44 or access_key_model(digits) != "55" or not access_key_check_digit_ok(digits):
        return None
    return digits


def validate_runtime_settings(settings: NfeExportSettings, *, application_root: Path) -> Path:
    if settings.start_date is None:
        raise NfeExportConfigurationError("Data inicial de exportação ausente.")
    if settings.interval_seconds < 30 or settings.interval_seconds > 86400:
        raise NfeExportConfigurationError("Intervalo de exportação inválido.")
    if not 1 <= settings.page_size <= 500:
        raise NfeExportConfigurationError("Tamanho de página inválido.")
    if not 1 <= settings.max_pages <= 5000:
        raise NfeExportConfigurationError("Limite de páginas inválido.")
    if not 1024 <= settings.max_bytes <= 52_428_800:
        raise NfeExportConfigurationError("Limite de XML inválido.")
    return validate_export_directory(settings.directory, application_root=application_root)


def application_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
