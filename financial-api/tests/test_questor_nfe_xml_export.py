"""Ciclo do exporter de XML NF-e. Sem Questor, sem Protheus e sem SMB."""

from __future__ import annotations

import os
import signal
import threading
from datetime import date
from pathlib import Path

import pytest

from financial_app.application.services.questor_nfe_xml_export_service import (
    QuestorNfeXmlExportService,
    validate_runtime_settings,
)
from financial_app.config import load_nfe_export_settings
from financial_app.domain.errors import NfeExportConfigurationError, QuestorUnavailable
from financial_app.domain.nfe_export import (
    STATUS_FAILED,
    STATUS_IGNORED,
    STATUS_PROCESSING,
    STATUS_SUCCESS,
    CycleResult,
    NfeExportListingPage,
    NfeExportRecord,
    NfeExportSettings,
    QuestorNfeListing,
)
from financial_app.infrastructure.filesystem.nfe_xml_export_storage import (
    NfeXmlExportStorage,
    validate_export_directory,
)
from financial_app.infrastructure.persistence.questor_nfe_xml_export_repository import (
    PostgresNfeExportLedger,
)
from financial_app.jobs.questor_nfe_xml_export import (
    execute_cycle,
    exit_code,
    request_stop,
    run_once,
    worker_loop,
)
from nfe_xml_samples import nfe_access_key, nfe_xml

START = date(2026, 10, 2)
FILE_ID = "6ab797d5ac12fe368c488f35"
ENTITY_ID = "6ab797d5ac12fe368c488f37"
KEY = nfe_access_key()
KEY_LATER = nfe_access_key(number="000085646")


def _settings(directory: Path, **overrides: object) -> NfeExportSettings:
    payload = {
        "enabled": True,
        "directory": str(directory),
        "interval_seconds": 900,
        "start_date": START,
        "page_size": 100,
        "max_pages": 20,
        "max_bytes": 100_000,
    }
    payload.update(overrides)
    return NfeExportSettings(**payload)  # type: ignore[arg-type]


def _listing(
    access_key: str = KEY,
    *,
    branch: str = "01",
    emission: str = "2026-10-02T10:00:00-03:00",
    entity: str = ENTITY_ID,
    file_id: str = FILE_ID,
) -> QuestorNfeListing:
    return QuestorNfeListing(
        provider_file_id=file_id,
        provider_entity_id=entity,
        access_key=access_key,
        invoice_number="85645",
        series="1",
        issuer_cnpj="47132675000158",
        emission_at=emission,
        branch_code=branch,
    )


class MemoryLedger:
    def __init__(self) -> None:
        self.rows: dict[str, NfeExportRecord] = {}
        self._locked = False
        self.fail_success_times = 0
        self.factories_blocked = False

    def try_lock(self) -> bool:
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self) -> None:
        self._locked = False

    def get(self, access_key: str) -> NfeExportRecord | None:
        return self.rows.get(access_key)

    def mark_processing(self, listing, *, access_key: str, filename: str, emission_date) -> NfeExportRecord:
        current = self.rows.get(access_key)
        if current is not None and current.status in {STATUS_SUCCESS, STATUS_IGNORED}:
            return current
        attempts = 1 if current is None else current.attempts + 1
        record = _record(listing, access_key, filename, emission_date, STATUS_PROCESSING, attempts)
        self.rows[access_key] = record
        return record

    def mark_success(self, listing, *, access_key: str, filename: str, emission_date) -> NfeExportRecord:
        if self.fail_success_times:
            self.fail_success_times -= 1
            raise RuntimeError("db down")
        current = self.rows.get(access_key)
        if current is not None and current.status == STATUS_SUCCESS:
            return current
        attempts = 1 if current is None else current.attempts
        record = _record(listing, access_key, filename, emission_date, STATUS_SUCCESS, attempts)
        self.rows[access_key] = record
        return record

    def mark_failed(self, *, access_key: str, code: str, message: str) -> None:
        current = self.rows.get(access_key)
        if current is None or current.status == STATUS_SUCCESS:
            return
        self.rows[access_key] = NfeExportRecord(
            access_key=current.access_key,
            branch_code=current.branch_code,
            provider_document_id=current.provider_document_id,
            provider_file_id=current.provider_file_id,
            invoice_number=current.invoice_number,
            series=current.series,
            emission_date=current.emission_date,
            filename=current.filename,
            status=STATUS_FAILED,
            attempts=current.attempts,
            last_error_code=code,
            last_error_message=message,
        )

    def mark_ignored(self, listing, *, access_key: str, filename: str, emission_date) -> None:
        current = self.rows.get(access_key)
        if current is not None and current.status == STATUS_SUCCESS:
            return
        attempts = 1 if current is None else current.attempts
        self.rows[access_key] = _record(listing, access_key, filename, emission_date, STATUS_IGNORED, attempts)


def _record(listing, access_key, filename, emission_date, status, attempts) -> NfeExportRecord:
    return NfeExportRecord(
        access_key=access_key,
        branch_code=listing.branch_code,
        provider_document_id=listing.provider_entity_id,
        provider_file_id=listing.provider_file_id,
        invoice_number=listing.invoice_number,
        series=listing.series,
        emission_date=emission_date,
        filename=filename,
        status=status,
        attempts=attempts,
        last_error_code=None,
        last_error_message=None,
    )


class FakeSource:
    def __init__(self, branch: str, rows: list[QuestorNfeListing], documents: dict[str, bytes]) -> None:
        self.branch_code = branch
        self.rows = rows
        self.documents = documents
        self.pages_called: list[int] = []
        self.downloads: list[tuple[str, str]] = []
        self.list_error: Exception | None = None
        self.download_error: Exception | None = None

    def list_page(self, *, page: int, page_size: int) -> NfeExportListingPage:
        if self.list_error is not None:
            raise self.list_error
        self.pages_called.append(page)
        start = (page - 1) * page_size
        items = tuple(self.rows[start : start + page_size])
        return NfeExportListingPage(total_items=len(self.rows), items=items)

    def download_xml(self, *, provider_file_id: str, provider_entity_id: str) -> bytes:
        self.downloads.append((provider_file_id, provider_entity_id))
        if self.download_error is not None:
            raise self.download_error
        return self.documents[provider_entity_id]


def _run(directory: Path, sources: list[FakeSource], ledger: MemoryLedger | None = None, **settings_overrides):
    store = NfeXmlExportStorage(directory)
    book = ledger or MemoryLedger()
    service = QuestorNfeXmlExportService(_settings(directory, **settings_overrides))
    result = service.run(ledger=book, source_factory=lambda: tuple(sources), storage=store)
    return result, book, store


def test_disabled_and_missing_start_date_do_not_touch_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("FIN_QUESTOR_NFE_EXPORT_ENABLED", raising=False)
    monkeypatch.delenv("FIN_QUESTOR_NFE_EXPORT_START_DATE", raising=False)
    loaded = load_nfe_export_settings()
    assert loaded.enabled is False
    assert execute_cycle(loaded).status == "disabled"

    monkeypatch.setattr(
        "financial_app.jobs.questor_nfe_xml_export.run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("migration")),
    )
    missing_date = _settings(tmp_path, start_date=None)
    assert execute_cycle(missing_date).status == "invalid_configuration"
    assert exit_code(execute_cycle(missing_date)) == 2


def test_invalid_directory_fails_fast_and_is_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "ausente"
    monkeypatch.setattr(
        "financial_app.jobs.questor_nfe_xml_export.run_migrations",
        lambda: (_ for _ in ()).throw(AssertionError("migration")),
    )
    result = execute_cycle(_settings(missing))
    assert result.status == "invalid_configuration"
    assert not missing.exists()
    with pytest.raises(NfeExportConfigurationError):
        validate_export_directory("exports/relativo", application_root=tmp_path / "app")
    with pytest.raises(NfeExportConfigurationError):
        validate_export_directory("/", application_root=tmp_path / "app")
    application = tmp_path / "app"
    application.mkdir()
    with pytest.raises(NfeExportConfigurationError):
        validate_export_directory(str(application), application_root=application)
    blocked = tmp_path / "bloqueado"
    blocked.mkdir()
    monkeypatch.setattr(os, "access", lambda *_args, **_kwargs: False)
    with pytest.raises(NfeExportConfigurationError):
        validate_runtime_settings(_settings(blocked), application_root=tmp_path / "outro")


def test_exports_branch_01_and_branch_02_including_the_cutoff(tmp_path: Path) -> None:
    key_02 = nfe_access_key(number="000011111")
    source_01 = FakeSource(
        "01",
        [_listing(KEY, branch="01", emission="2026-10-02T00:00:00-03:00")],
        {ENTITY_ID: nfe_xml(KEY, dh_emi="2026-10-02T00:00:00-03:00")},
    )
    source_02 = FakeSource(
        "02",
        [_listing(key_02, branch="02", emission="2026-10-05T08:00:00-03:00", entity="6ab797d5ac12fe368c488f38", file_id="6ab797d5ac12fe368c488f39")],
        {"6ab797d5ac12fe368c488f38": nfe_xml(key_02, dh_emi="2026-10-05T08:00:00-03:00")},
    )
    result, ledger, _store = _run(tmp_path, [source_01, source_02])
    assert [branch.branch_code for branch in result.branches] == ["01", "02"]
    assert all(branch.exported == 1 and branch.failed == 0 for branch in result.branches)
    assert (tmp_path / f"NFe-{KEY}.xml").read_bytes().startswith(b"<?xml")
    assert (tmp_path / f"NFe-{key_02}.xml").is_file()
    assert ledger.rows[KEY].status == STATUS_SUCCESS
    assert ledger.rows[key_02].branch_code == "02"
    assert source_01.downloads == [(FILE_ID, ENTITY_ID)]


def test_dates_before_the_cutoff_are_ignored_and_later_dates_are_exported(tmp_path: Path) -> None:
    old = nfe_access_key(number="000000001")
    boundary = KEY
    later = KEY_LATER
    source = FakeSource(
        "01",
        [
            _listing(old, emission="2026-10-01T12:00:00-03:00", entity="6ab797d5ac12fe368c488f31", file_id="6ab797d5ac12fe368c488f32"),
            _listing(boundary, emission="2026-10-02T00:00:00-03:00"),
            _listing(later, emission="2026-10-03T09:00:00-03:00", entity="6ab797d5ac12fe368c488f33", file_id="6ab797d5ac12fe368c488f34"),
        ],
        {
            ENTITY_ID: nfe_xml(boundary, dh_emi="2026-10-02T00:00:00-03:00"),
            "6ab797d5ac12fe368c488f33": nfe_xml(later, dh_emi="2026-10-03T09:00:00-03:00"),
        },
    )
    result, _ledger, _store = _run(tmp_path, [source], page_size=1)
    assert result.branches[0].ignored == 1
    assert result.branches[0].exported == 2
    assert source.pages_called == [1, 2, 3, 4]
    assert "6ab797d5ac12fe368c488f31" not in {entity for _file, entity in source.downloads}
    assert not (tmp_path / f"NFe-{old}.xml").exists()


def test_xml_emission_before_the_cutoff_is_ignored_after_download(tmp_path: Path) -> None:
    source = FakeSource(
        "01",
        [_listing(emission="2026-10-02T10:00:00Z")],
        {ENTITY_ID: nfe_xml(KEY, dh_emi="2026-10-01T22:00:00-03:00")},
    )
    result, ledger, _store = _run(tmp_path, [source])
    assert result.branches[0].exported == 0
    assert result.branches[0].ignored == 1
    assert ledger.rows[KEY].status == STATUS_IGNORED
    assert not (tmp_path / f"NFe-{KEY}.xml").exists()


def test_portal_total_that_grows_with_the_offset_does_not_stop_the_scan(tmp_path: Path) -> None:
    rows = [
        _listing(
            nfe_access_key(number=f"{index:09d}"),
            emission="2026-09-01T10:00:00-03:00" if index < 250 else "2026-10-03T10:00:00-03:00",
            entity=f"{index:024x}",
            file_id=f"{index + 1:024x}",
        )
        for index in range(1, 251)
    ]
    late = rows[-1]
    source = FakeSource(
        "01",
        rows,
        {late.provider_entity_id: nfe_xml(late.access_key, dh_emi="2026-10-03T10:00:00-03:00")},
    )
    original = source.list_page

    def list_page(*, page: int, page_size: int) -> NfeExportListingPage:
        current = original(page=page, page_size=page_size)
        start = (page - 1) * page_size
        return NfeExportListingPage(total_items=start + page_size + 1, items=current.items)

    source.list_page = list_page  # type: ignore[method-assign]
    result, ledger, _store = _run(tmp_path, [source], page_size=100)
    assert source.pages_called == [1, 2, 3]
    assert result.branches[0].found == 250
    assert result.branches[0].exported == 1
    assert ledger.rows[late.access_key].status == STATUS_SUCCESS


def test_divergent_key_and_invalid_model_do_not_create_the_final_file(tmp_path: Path) -> None:
    other = nfe_access_key(number="000085646")
    mismatch = FakeSource(
        "01",
        [_listing()],
        {ENTITY_ID: nfe_xml(KEY, protocol_key=other)},
    )
    result, ledger, _store = _run(tmp_path, [mismatch])
    assert result.branches[0].failed == 1
    assert ledger.rows[KEY].last_error_code == "access_key_mismatch"
    assert not (tmp_path / f"NFe-{KEY}.xml").exists()

    invalid_model = FakeSource(
        "02",
        [_listing(KEY_LATER, branch="02", entity="6ab797d5ac12fe368c488f41", file_id="6ab797d5ac12fe368c488f42")],
        {"6ab797d5ac12fe368c488f41": nfe_xml(KEY_LATER, model="65")},
    )
    result, ledger, _store = _run(tmp_path, [invalid_model])
    assert ledger.rows[KEY_LATER].last_error_code == "invalid_model"
    assert result.branches[0].failed == 1
    assert list(tmp_path.glob("*.xml")) == []


def test_atomic_rename_hides_the_partial_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []
    original = os.replace

    def spy(source: str, destination: str) -> None:
        seen.append(sorted(path.name for path in tmp_path.iterdir()))
        original(source, destination)

    monkeypatch.setattr(os, "replace", spy)
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    _run(tmp_path, [source])
    assert seen
    assert all(not name.endswith(".xml") for name in seen[0])
    assert any(name.endswith(".part") for name in seen[0])
    assert (tmp_path / f"NFe-{KEY}.xml").is_file()
    assert list(tmp_path.glob("*.part")) == []


def test_second_run_and_missing_file_do_not_export_again(tmp_path: Path) -> None:
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    ledger = MemoryLedger()
    first, ledger, _store = _run(tmp_path, [source], ledger)
    assert first.branches[0].exported == 1
    (tmp_path / f"NFe-{KEY}.xml").unlink()
    second, ledger, _store = _run(tmp_path, [source], ledger)
    assert second.branches[0].exported == 0
    assert second.branches[0].already_success == 1
    assert source.downloads == [(FILE_ID, ENTITY_ID)]
    assert ledger.rows[KEY].status == STATUS_SUCCESS
    assert len(ledger.rows) == 1


def test_existing_valid_file_is_reconciled_without_a_second_copy(tmp_path: Path) -> None:
    storage = NfeXmlExportStorage(tmp_path)
    storage.write_atomic(KEY, nfe_xml(KEY))
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    result, ledger, _store = _run(tmp_path, [source])
    assert result.branches[0].reconciled == 1
    assert result.branches[0].exported == 0
    assert source.downloads == []
    assert ledger.rows[KEY].status == STATUS_SUCCESS
    assert list(tmp_path.glob("NFe-*.xml")) == [tmp_path / f"NFe-{KEY}.xml"]


def test_failed_download_is_retried_on_the_next_cycle(tmp_path: Path) -> None:
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    source.download_error = QuestorUnavailable("indisponível")
    ledger = MemoryLedger()
    first, ledger, _store = _run(tmp_path, [source], ledger)
    assert first.branches[0].failed == 1
    assert ledger.rows[KEY].status == STATUS_FAILED
    assert ledger.rows[KEY].attempts == 1
    source.download_error = None
    second, ledger, _store = _run(tmp_path, [source], ledger)
    assert second.branches[0].exported == 1
    assert ledger.rows[KEY].status == STATUS_SUCCESS
    assert ledger.rows[KEY].attempts == 2


def test_one_branch_failure_does_not_block_the_other(tmp_path: Path) -> None:
    broken = FakeSource("01", [], {})
    broken.list_error = QuestorUnavailable("filial 01")
    healthy = FakeSource(
        "02",
        [_listing(KEY, branch="02")],
        {ENTITY_ID: nfe_xml(KEY)},
    )
    result, ledger, _store = _run(tmp_path, [broken, healthy])
    assert result.status == "completed"
    assert result.branches[0].status == "failed"
    assert result.branches[0].error_code == "questor_unavailable"
    assert result.branches[1].exported == 1
    assert ledger.rows[KEY].branch_code == "02"
    assert exit_code(result) == 1


def test_advisory_lock_skips_the_cycle_and_unique_key_stays_single(tmp_path: Path) -> None:
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    ledger = MemoryLedger()
    ledger._locked = True
    called = {"sources": 0}

    def factory():
        called["sources"] += 1
        return (source,)

    result = QuestorNfeXmlExportService(_settings(tmp_path)).run(
        ledger=ledger,
        source_factory=factory,
        storage=NfeXmlExportStorage(tmp_path),
    )
    assert result.status == "skipped_lock"
    assert called["sources"] == 0
    assert source.downloads == []

    ledger.unlock()
    _run(tmp_path, [source], ledger)
    again = ledger.mark_processing(
        _listing(),
        access_key=KEY,
        filename=f"NFe-{KEY}.xml",
        emission_date=START,
    )
    assert again.status == STATUS_SUCCESS
    assert len(ledger.rows) == 1


def test_database_failure_after_rename_is_reconciled_later(tmp_path: Path) -> None:
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    ledger = MemoryLedger()
    ledger.fail_success_times = 1
    first, ledger, _store = _run(tmp_path, [source], ledger)
    assert first.branches[0].failed == 1
    assert (tmp_path / f"NFe-{KEY}.xml").is_file()
    assert ledger.rows[KEY].status == STATUS_PROCESSING
    second, ledger, _store = _run(tmp_path, [source], ledger)
    assert second.branches[0].reconciled == 1
    assert second.branches[0].exported == 0
    assert len(source.downloads) == 1
    assert ledger.rows[KEY].status == STATUS_SUCCESS


def test_replace_failure_removes_the_partial_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_source: str, _destination: str) -> None:
        raise OSError("disco")

    monkeypatch.setattr(os, "replace", boom)
    source = FakeSource("01", [_listing()], {ENTITY_ID: nfe_xml(KEY)})
    result, ledger, _store = _run(tmp_path, [source])
    assert result.branches[0].failed == 1
    assert ledger.rows[KEY].last_error_code == "storage_failed"
    assert list(tmp_path.iterdir()) == []


def test_repository_lock_sql_and_success_guard() -> None:
    connection = _FakeConnection()
    repository = PostgresNfeExportLedger(connection)
    assert repository.try_lock() is True
    second = PostgresNfeExportLedger(connection)
    assert second.try_lock() is False
    repository.unlock()
    rendered = "\n".join(connection.statements)
    assert "pg_try_advisory_lock" in rendered
    assert "pg_advisory_unlock" in rendered
    repository.mark_processing(
        _listing(),
        access_key=KEY,
        filename=f"NFe-{KEY}.xml",
        emission_date=START,
    )
    assert any("ON CONFLICT (access_key)" in sql and "NOT IN" in sql for sql in connection.statements)
    migration = Path(__file__).resolve().parents[1] / "migrations" / "V002__questor_nfe_xml_exports.sql"
    sql = migration.read_text(encoding="utf-8")
    assert "UNIQUE (access_key)" in sql
    assert "questor_nfe_xml_exports" in sql
    assert "CREATE SCHEMA" not in sql


def test_sigterm_stops_the_worker_after_the_current_cycle() -> None:
    stop = threading.Event()
    ran: list[int] = []
    previous = signal.getsignal(signal.SIGTERM)

    def handler(signum: int, frame) -> None:
        request_stop(stop, signum)

    def cycle(_settings_obj: NfeExportSettings) -> CycleResult:
        ran.append(1)
        os.kill(os.getpid(), signal.SIGTERM)
        return CycleResult(status="completed")

    signal.signal(signal.SIGTERM, handler)
    timer = threading.Timer(2, stop.set)
    timer.start()
    try:
        code = worker_loop(
            load_settings=lambda: _settings(Path("/tmp"), interval_seconds=1),
            run_cycle=cycle,
            stop_event=stop,
        )
    finally:
        timer.cancel()
        signal.signal(signal.SIGTERM, previous)

    assert code == 0
    assert ran == [1]
    assert stop.is_set()


def test_run_once_disabled_exits_zero(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("FIN_QUESTOR_NFE_EXPORT_ENABLED", raising=False)
    assert run_once() == 0
    assert "status=disabled" in capsys.readouterr().out


class _FakeConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []
        self.lock_held = False

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


class _FakeCursor:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection
        self.description = None
        self._sql = ""

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *_args) -> bool:
        return False

    def execute(self, sql: str, _params=None) -> None:
        self.connection.statements.append(sql)
        self._sql = sql
        self.description = ("locked",) if "pg_" in sql else ("access_key",)

    def fetchone(self):
        if "pg_try_advisory_lock" in self._sql:
            if self.connection.lock_held:
                return {"locked": False}
            self.connection.lock_held = True
            return {"locked": True}
        if "pg_advisory_unlock" in self._sql:
            self.connection.lock_held = False
            return {"unlocked": True}
        return None
