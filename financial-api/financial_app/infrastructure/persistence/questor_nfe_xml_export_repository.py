"""Ledger PostgreSQL da exportação de XML NF-e.

A chave de acesso é única. status success não volta a processing.
O advisory lock é de sessão e cai se a conexão morrer.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from financial_app.domain.nfe_export import (
    STATUS_IGNORED,
    STATUS_PROCESSING,
    STATUS_SUCCESS,
    NfeExportRecord,
    QuestorNfeListing,
)
from financial_app.infrastructure.persistence.plugins_postgres_connection import FIN_SCHEMA_NAME

_LOCK_CLASS = 58201955
_LOCK_OBJECT = 55
_TABLE = f'"{FIN_SCHEMA_NAME}".questor_nfe_xml_exports'
_MESSAGE_LIMIT = 500


class PostgresNfeExportLedger:
    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._locked = False

    def try_lock(self) -> bool:
        row = self._fetchone(
            "SELECT pg_try_advisory_lock(%s, %s) AS locked",
            (_LOCK_CLASS, _LOCK_OBJECT),
        )
        self._locked = bool(row and row["locked"])
        return self._locked

    def unlock(self) -> None:
        if not self._locked:
            return
        try:
            self._fetchone(
                "SELECT pg_advisory_unlock(%s, %s) AS unlocked",
                (_LOCK_CLASS, _LOCK_OBJECT),
            )
        finally:
            self._locked = False

    def close(self) -> None:
        try:
            self.unlock()
        finally:
            self._connection.close()

    def get(self, access_key: str) -> NfeExportRecord | None:
        row = self._fetchone(
            f"""
            SELECT access_key, branch_code, provider_document_id, provider_file_id,
                   invoice_number, series, emission_date, filename, status, attempts,
                   last_error_code, last_error_message
            FROM {_TABLE}
            WHERE access_key = %s
            """,
            (access_key,),
        )
        if row is None:
            return None
        return _record(row)

    def mark_processing(
        self,
        listing: QuestorNfeListing,
        *,
        access_key: str,
        filename: str,
        emission_date: date | None,
    ) -> NfeExportRecord | None:
        row = self._fetchone(
            f"""
            INSERT INTO {_TABLE} (
                access_key, branch_code, provider_document_id, provider_file_id,
                invoice_number, series, emission_date, filename, status, attempts, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW())
            ON CONFLICT (access_key) DO UPDATE SET
                branch_code = EXCLUDED.branch_code,
                provider_document_id = EXCLUDED.provider_document_id,
                provider_file_id = EXCLUDED.provider_file_id,
                invoice_number = EXCLUDED.invoice_number,
                series = EXCLUDED.series,
                emission_date = EXCLUDED.emission_date,
                filename = EXCLUDED.filename,
                status = %s,
                attempts = {_TABLE}.attempts + 1,
                last_error_code = NULL,
                last_error_message = NULL,
                updated_at = NOW()
            WHERE {_TABLE}.status NOT IN (%s, %s)
            RETURNING access_key, branch_code, provider_document_id, provider_file_id,
                      invoice_number, series, emission_date, filename, status, attempts,
                      last_error_code, last_error_message
            """,
            (
                access_key,
                listing.branch_code,
                _limit(listing.provider_entity_id, 64),
                _limit(listing.provider_file_id, 64),
                _limit(listing.invoice_number, 20),
                _limit(listing.series, 10),
                emission_date,
                filename,
                STATUS_PROCESSING,
                STATUS_PROCESSING,
                STATUS_SUCCESS,
                STATUS_IGNORED,
            ),
        )
        if row is not None:
            return _record(row)
        return self.get(access_key)

    def mark_success(
        self,
        listing: QuestorNfeListing,
        *,
        access_key: str,
        filename: str,
        emission_date: date | None,
    ) -> NfeExportRecord | None:
        row = self._fetchone(
            f"""
            INSERT INTO {_TABLE} (
                access_key, branch_code, provider_document_id, provider_file_id,
                invoice_number, series, emission_date, filename, status, attempts,
                exported_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
            ON CONFLICT (access_key) DO UPDATE SET
                branch_code = EXCLUDED.branch_code,
                provider_document_id = EXCLUDED.provider_document_id,
                provider_file_id = EXCLUDED.provider_file_id,
                invoice_number = EXCLUDED.invoice_number,
                series = EXCLUDED.series,
                emission_date = EXCLUDED.emission_date,
                filename = EXCLUDED.filename,
                status = %s,
                last_error_code = NULL,
                last_error_message = NULL,
                exported_at = NOW(),
                updated_at = NOW()
            WHERE {_TABLE}.status <> %s
            RETURNING access_key, branch_code, provider_document_id, provider_file_id,
                      invoice_number, series, emission_date, filename, status, attempts,
                      last_error_code, last_error_message
            """,
            (
                access_key,
                listing.branch_code,
                _limit(listing.provider_entity_id, 64),
                _limit(listing.provider_file_id, 64),
                _limit(listing.invoice_number, 20),
                _limit(listing.series, 10),
                emission_date,
                filename,
                STATUS_SUCCESS,
                STATUS_SUCCESS,
                STATUS_SUCCESS,
            ),
        )
        if row is not None:
            return _record(row)
        return self.get(access_key)

    def mark_failed(
        self,
        *,
        access_key: str,
        code: str,
        message: str,
    ) -> None:
        self._execute(
            f"""
            UPDATE {_TABLE}
            SET status = 'failed',
                last_error_code = %s,
                last_error_message = %s,
                updated_at = NOW()
            WHERE access_key = %s
              AND status <> %s
            """,
            (_limit(code, 64), _limit(message, _MESSAGE_LIMIT), access_key, STATUS_SUCCESS),
        )

    def mark_ignored(
        self,
        listing: QuestorNfeListing,
        *,
        access_key: str,
        filename: str,
        emission_date: date | None,
    ) -> None:
        self._execute(
            f"""
            INSERT INTO {_TABLE} (
                access_key, branch_code, provider_document_id, provider_file_id,
                invoice_number, series, emission_date, filename, status, attempts,
                last_error_code, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'before_start_date', NOW())
            ON CONFLICT (access_key) DO UPDATE SET
                emission_date = EXCLUDED.emission_date,
                filename = EXCLUDED.filename,
                status = %s,
                last_error_code = 'before_start_date',
                last_error_message = NULL,
                updated_at = NOW()
            WHERE {_TABLE}.status <> %s
            """,
            (
                access_key,
                listing.branch_code,
                _limit(listing.provider_entity_id, 64),
                _limit(listing.provider_file_id, 64),
                _limit(listing.invoice_number, 20),
                _limit(listing.series, 10),
                emission_date,
                filename,
                STATUS_IGNORED,
                STATUS_IGNORED,
                STATUS_SUCCESS,
            ),
        )

    def _fetchone(self, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone() if cursor.description else None
            self._connection.commit()
            return row
        except Exception:
            self._connection.rollback()
            raise

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(sql, params)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise


def _record(row: dict[str, Any]) -> NfeExportRecord:
    emission = row.get("emission_date")
    return NfeExportRecord(
        access_key=str(row["access_key"]),
        branch_code=str(row["branch_code"]),
        provider_document_id=row.get("provider_document_id"),
        provider_file_id=row.get("provider_file_id"),
        invoice_number=row.get("invoice_number"),
        series=row.get("series"),
        emission_date=emission,
        filename=row.get("filename"),
        status=str(row["status"]),
        attempts=int(row["attempts"] or 0),
        last_error_code=row.get("last_error_code"),
        last_error_message=row.get("last_error_message"),
    )


def _limit(value: str | None, size: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:size]
