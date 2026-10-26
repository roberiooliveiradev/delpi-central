"""Market data repository — psycopg adapter for the external_data schema.

All access is parameterized; money flows as ``Decimal``. Upserts are
idempotent on the economic identity (instrument/pair + date + source):
re-running an ingestion updates the value only when it actually changed.
"""

from __future__ import annotations

import base64
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Iterable

from app.domain.market_data import (
    FeedStatus,
    FxObservation,
    IngestionRun,
    MarketDataSource,
    MetalInstrument,
    MetalObservation,
)


def _encode_cursor(obs_date: date, row_id: int) -> str:
    raw = f"{obs_date.isoformat()}|{row_id}"
    return base64.urlsafe_b64encode(raw.encode("ascii")).decode("ascii")


def decode_cursor(cursor: str) -> tuple[date, int]:
    """Parse an opaque cursor. Raises ``ValueError`` when malformed."""
    raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("ascii")
    date_part, _, id_part = raw.partition("|")
    return date.fromisoformat(date_part), int(id_part)


def _source_from_row(row: dict[str, Any]) -> MarketDataSource:
    return MarketDataSource(
        source_id=row["source_id"],
        provider_id=row["provider_id"],
        source_kind=row["source_kind"],
        attribution=row["attribution"],
        license_reference=row["license_reference"],
        license_reviewed_at=row["license_reviewed_at"],
        allowed_use_scope=row["allowed_use_scope"],
        active=row["active"],
    )


def _instrument_from_row(row: dict[str, Any]) -> MetalInstrument:
    return MetalInstrument(
        instrument_id=row["instrument_id"],
        instrument_code=row["instrument_code"],
        metal_code=row["metal_code"],
        label=row["label"],
        market=row["market"],
        quotation_basis=row["quotation_basis"],
        native_currency=row["native_currency"],
        unit_code=row["unit_code"],
        unit_label=row["unit_label"],
        source_id=row["source_id"],
        source_series_key=row["source_series_key"],
        granularity=row["granularity"],
        active=row["active"],
    )


class MarketDataRepository:
    """Read/write adapter — one connection per instance lifecycle."""

    def __init__(self, conn: Any, *, schema: str) -> None:
        self._conn = conn
        self._schema = schema

    def _t(self, table: str) -> str:
        return f'"{self._schema}".{table}'

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    # --- catalog -----------------------------------------------------------

    def list_sources(self) -> list[MarketDataSource]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('market_data_sources')} "
                "ORDER BY source_id"
            )
            return [_source_from_row(r) for r in cur.fetchall()]

    def get_source(self, source_id: str) -> MarketDataSource | None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('market_data_sources')} "
                "WHERE source_id = %s",
                (source_id,),
            )
            row = cur.fetchone()
        return _source_from_row(row) if row else None

    def list_instruments(self) -> list[MetalInstrument]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('metal_instruments')} "
                "ORDER BY instrument_code"
            )
            return [_instrument_from_row(r) for r in cur.fetchall()]

    def get_instrument(self, instrument_code: str) -> MetalInstrument | None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('metal_instruments')} "
                "WHERE instrument_code = %s",
                (instrument_code,),
            )
            row = cur.fetchone()
        return _instrument_from_row(row) if row else None

    # --- reads -------------------------------------------------------------

    def list_metal_observations(
        self,
        *,
        instrument_id: int,
        date_from: date,
        date_to: date,
        limit: int,
        cursor: tuple[date, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Rows ordered by (observation_date, observation_id) ascending."""
        sql = f"""
            SELECT o.observation_id, o.observation_date, o.native_price,
                   o.native_currency, o.unit_code, o.quote_basis,
                   o.quality_status, o.source_id, o.source_record_key,
                   o.retrieved_at, o.revised_at
            FROM {self._t('metal_quote_observations')} o
            WHERE o.instrument_id = %s
              AND o.observation_date BETWEEN %s AND %s
        """
        params: list[Any] = [instrument_id, date_from, date_to]
        if cursor is not None:
            sql += " AND (o.observation_date, o.observation_id) > (%s, %s)"
            params.extend([cursor[0], cursor[1]])
        sql += " ORDER BY o.observation_date ASC, o.observation_id ASC LIMIT %s"
        params.append(limit + 1)
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    # --- R2: Comex / IPP ---------------------------------------------------

    def list_ncm_allowlist(self) -> list[dict[str, Any]]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('comex_ncm_allowlist')} "
                "ORDER BY ncm_code"
            )
            return cur.fetchall()

    def get_ncm_allowlist(self, ncm_code: str) -> dict[str, Any] | None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('comex_ncm_allowlist')} "
                "WHERE ncm_code = %s",
                (ncm_code,),
            )
            return cur.fetchone()

    def list_comex_observations(
        self,
        *,
        ncm_code: str,
        date_from: date,
        date_to: date,
        country_code: str | None,
        state_code: str | None,
        limit: int,
        cursor: tuple[date, int] | None = None,
    ) -> list[dict[str, Any]]:
        sql = f"""
            SELECT o.observation_id, o.reference_month, o.ncm_code,
                   o.ncm_version, o.country_code, o.state_code,
                   o.fob_usd_total, o.net_weight_kg_total,
                   o.unit_value_usd_per_t, o.contributing_rows,
                   o.quality_status, o.dataset_year, o.dataset_revision,
                   o.source_checksum, o.source_id, o.retrieved_at,
                   o.revised_at
            FROM {self._t('comex_import_monthly_observations')} o
            WHERE o.ncm_code = %s
              AND o.reference_month BETWEEN %s AND %s
        """
        params: list[Any] = [ncm_code, date_from, date_to]
        if country_code:
            sql += " AND o.country_code = %s"
            params.append(country_code)
        if state_code:
            sql += " AND o.state_code = %s"
            params.append(state_code.upper())
        if cursor is not None:
            sql += " AND (o.reference_month, o.observation_id) > (%s, %s)"
            params.extend([cursor[0], cursor[1]])
        sql += (
            " ORDER BY o.reference_month ASC, o.observation_id ASC LIMIT %s"
        )
        params.append(limit + 1)
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def upsert_comex_observation(
        self,
        *,
        reference_month: date,
        ncm_code: str,
        ncm_version: str,
        country_code: str,
        state_code: str,
        fob_usd_total: Decimal,
        net_weight_kg_total: Decimal,
        unit_value_usd_per_t: Decimal | None,
        contributing_rows: int,
        quality_status: str,
        dataset_year: int,
        dataset_revision: str | None,
        source_checksum: str | None,
        source_id: str,
        retrieved_at: datetime,
    ) -> str:
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._t('comex_import_monthly_observations')}
                    (reference_month, ncm_code, ncm_version, country_code,
                     state_code, fob_usd_total, net_weight_kg_total,
                     unit_value_usd_per_t, contributing_rows,
                     quality_status, dataset_year, dataset_revision,
                     source_checksum, source_id, retrieved_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s)
                ON CONFLICT (reference_month, ncm_code, country_code,
                             state_code, dataset_year, source_id)
                DO UPDATE SET ncm_version = EXCLUDED.ncm_version,
                    fob_usd_total = EXCLUDED.fob_usd_total,
                    net_weight_kg_total = EXCLUDED.net_weight_kg_total,
                    unit_value_usd_per_t = EXCLUDED.unit_value_usd_per_t,
                    contributing_rows = EXCLUDED.contributing_rows,
                    quality_status = EXCLUDED.quality_status,
                    dataset_revision = EXCLUDED.dataset_revision,
                    source_checksum = EXCLUDED.source_checksum,
                    retrieved_at = EXCLUDED.retrieved_at,
                    revised_at = NOW()
                WHERE {self._t('comex_import_monthly_observations')}
                      .fob_usd_total IS DISTINCT FROM
                      EXCLUDED.fob_usd_total
                   OR {self._t('comex_import_monthly_observations')}
                      .net_weight_kg_total IS DISTINCT FROM
                      EXCLUDED.net_weight_kg_total
                   OR {self._t('comex_import_monthly_observations')}
                      .source_checksum IS DISTINCT FROM
                      EXCLUDED.source_checksum
                RETURNING (xmax = 0) AS inserted
                """,
                (
                    reference_month, ncm_code, ncm_version, country_code,
                    state_code, fob_usd_total, net_weight_kg_total,
                    unit_value_usd_per_t, contributing_rows,
                    quality_status, dataset_year, dataset_revision,
                    source_checksum, source_id, retrieved_at,
                ),
            )
            row = cur.fetchone()
        if row is None:
            return "unchanged"
        return "inserted" if row["inserted"] else "updated"

    def list_producer_price_series(self) -> list[dict[str, Any]]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('producer_price_series')} "
                "ORDER BY series_id"
            )
            return cur.fetchall()

    def get_producer_price_series(
        self, series_id: str
    ) -> dict[str, Any] | None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self._t('producer_price_series')} "
                "WHERE series_id = %s",
                (series_id,),
            )
            return cur.fetchone()

    def list_producer_price_observations(
        self,
        *,
        series_id: str,
        date_from: date,
        date_to: date,
        limit: int,
        cursor: tuple[date, int] | None = None,
    ) -> list[dict[str, Any]]:
        sql = f"""
            SELECT o.observation_id, o.series_id, o.reference_month,
                   o.value, o.quality_status, o.source_id,
                   o.source_record_key, o.published_at, o.retrieved_at,
                   o.revised_at
            FROM {self._t('producer_price_index_observations')} o
            WHERE o.series_id = %s
              AND o.reference_month BETWEEN %s AND %s
        """
        params: list[Any] = [series_id, date_from, date_to]
        if cursor is not None:
            sql += " AND (o.reference_month, o.observation_id) > (%s, %s)"
            params.extend([cursor[0], cursor[1]])
        sql += (
            " ORDER BY o.reference_month ASC, o.observation_id ASC LIMIT %s"
        )
        params.append(limit + 1)
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def upsert_producer_price_observation(
        self,
        *,
        series_id: str,
        reference_month: date,
        value: Decimal,
        source_id: str,
        source_record_key: str | None,
        published_at: datetime | None,
        retrieved_at: datetime,
        quality_status: str = "validated",
    ) -> str:
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._t('producer_price_index_observations')}
                    (series_id, reference_month, value, source_id,
                     source_record_key, published_at, retrieved_at,
                     quality_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_id, reference_month, source_id)
                DO UPDATE SET value = EXCLUDED.value,
                              retrieved_at = EXCLUDED.retrieved_at,
                              revised_at = NOW(),
                              quality_status = EXCLUDED.quality_status,
                              source_record_key =
                                  EXCLUDED.source_record_key,
                              published_at = EXCLUDED.published_at
                WHERE {self._t('producer_price_index_observations')}.value
                      IS DISTINCT FROM EXCLUDED.value
                RETURNING (xmax = 0) AS inserted
                """,
                (
                    series_id, reference_month, value, source_id,
                    source_record_key, published_at, retrieved_at,
                    quality_status,
                ),
            )
            row = cur.fetchone()
        if row is None:
            return "unchanged"
        return "inserted" if row["inserted"] else "updated"

    def list_fx_observations(
        self,
        *,
        pair_code: str,
        rate_kind: str,
        date_from: date,
        date_to: date,
        limit: int,
        cursor: tuple[date, int] | None = None,
    ) -> list[dict[str, Any]]:
        sql = f"""
            SELECT f.fx_id, f.pair_code, f.rate_kind, f.reference_date,
                   f.value, f.quality_status, f.source_id,
                   f.retrieved_at, f.revised_at
            FROM {self._t('fx_rate_observations')} f
            WHERE f.pair_code = %s AND f.rate_kind = %s
              AND f.reference_date BETWEEN %s AND %s
        """
        params: list[Any] = [pair_code, rate_kind, date_from, date_to]
        if cursor is not None:
            sql += " AND (f.reference_date, f.fx_id) > (%s, %s)"
            params.extend([cursor[0], cursor[1]])
        sql += " ORDER BY f.reference_date ASC, f.fx_id ASC LIMIT %s"
        params.append(limit + 1)
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def latest_observation_dates(self) -> dict[str, date]:
        """Latest persisted date per feed identity (instrument/pair+kind)."""
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT i.instrument_code AS key, MAX(o.observation_date) AS d
                FROM {self._t('metal_quote_observations')} o
                JOIN {self._t('metal_instruments')} i
                  ON i.instrument_id = o.instrument_id
                GROUP BY i.instrument_code
                UNION ALL
                SELECT pair_code || '|' || rate_kind AS key,
                       MAX(reference_date) AS d
                FROM {self._t('fx_rate_observations')}
                GROUP BY pair_code, rate_kind
                """
            )
            rows = {r["key"]: r["d"] for r in cur.fetchall()}
            # R2 feeds live in their own tables — the base UNION predates
            # them, so absence is tolerated for pre-V005 databases.
            for table, key_expr in (
                (
                    "comex_import_monthly_observations",
                    "'comex|' || ncm_code",
                ),
                ("producer_price_index_observations", "'ipp|' || series_id"),
            ):
                if not self._table_exists(table):
                    continue
                cur.execute(
                    f"SELECT {key_expr} AS key, MAX(reference_month) AS d "
                    f"FROM {self._t(table)} GROUP BY 1"
                )
                rows.update({r["key"]: r["d"] for r in cur.fetchall()})
            return rows

    def _table_exists(self, table: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT to_regclass(%s) AS regclass",
                (f"{self._schema}.{table}",),
            )
            return cur.fetchone()["regclass"] is not None

    # --- writes (ingestion) ------------------------------------------------

    def upsert_metal_observation(
        self,
        *,
        instrument_id: int,
        observation_date: date,
        native_price: Decimal,
        native_currency: str,
        unit_code: str,
        quote_basis: str,
        source_id: str,
        source_record_key: str | None,
        retrieved_at: datetime,
        quality_status: str = "validated",
    ) -> str:
        """Insert or revise. Returns 'inserted' | 'updated' | 'unchanged'."""
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._t('metal_quote_observations')}
                    (instrument_id, observation_date, native_price,
                     native_currency, unit_code, quote_basis, source_id,
                     source_record_key, retrieved_at, quality_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (instrument_id, observation_date, source_id)
                DO UPDATE SET native_price = EXCLUDED.native_price,
                              retrieved_at = EXCLUDED.retrieved_at,
                              revised_at = NOW(),
                              quality_status = EXCLUDED.quality_status,
                              source_record_key = EXCLUDED.source_record_key
                WHERE {self._t('metal_quote_observations')}.native_price
                      IS DISTINCT FROM EXCLUDED.native_price
                RETURNING (xmax = 0) AS inserted
                """,
                (
                    instrument_id,
                    observation_date,
                    native_price,
                    native_currency,
                    unit_code,
                    quote_basis,
                    source_id,
                    source_record_key,
                    retrieved_at,
                    quality_status,
                ),
            )
            row = cur.fetchone()
        if row is None:
            return "unchanged"
        return "inserted" if row["inserted"] else "updated"

    def upsert_fx_observation(
        self,
        *,
        pair_code: str,
        rate_kind: str,
        reference_date: date,
        value: Decimal,
        source_id: str,
        source_record_key: str | None,
        retrieved_at: datetime,
        quality_status: str = "validated",
    ) -> str:
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._t('fx_rate_observations')}
                    (pair_code, rate_kind, reference_date, value, source_id,
                     source_record_key, retrieved_at, quality_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pair_code, rate_kind, reference_date, source_id)
                DO UPDATE SET value = EXCLUDED.value,
                              retrieved_at = EXCLUDED.retrieved_at,
                              revised_at = NOW(),
                              quality_status = EXCLUDED.quality_status,
                              source_record_key = EXCLUDED.source_record_key
                WHERE {self._t('fx_rate_observations')}.value
                      IS DISTINCT FROM EXCLUDED.value
                RETURNING (xmax = 0) AS inserted
                """,
                (
                    pair_code,
                    rate_kind,
                    reference_date,
                    value,
                    source_id,
                    source_record_key,
                    retrieved_at,
                    quality_status,
                ),
            )
            row = cur.fetchone()
        if row is None:
            return "unchanged"
        return "inserted" if row["inserted"] else "updated"

    # --- ingestion runs ----------------------------------------------------

    def create_ingestion_run(
        self,
        *,
        provider_id: str,
        feed: str,
        correlation_id: str | None,
        version: str,
    ) -> str:
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self._t('market_data_ingestion_runs')}
                    (provider_id, feed, correlation_id, version)
                VALUES (%s, %s, %s, %s)
                RETURNING run_id::text AS run_id
                """,
                (provider_id, feed, correlation_id, version),
            )
            return cur.fetchone()["run_id"]

    def finish_ingestion_run(
        self,
        run_id: str,
        *,
        outcome: str,
        fetched_count: int,
        inserted_count: int,
        updated_count: int,
        skipped_count: int,
        safe_error_code: str | None,
    ) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {self._t('market_data_ingestion_runs')}
                SET finished_at = NOW(), outcome = %s,
                    fetched_count = %s, inserted_count = %s,
                    updated_count = %s, skipped_count = %s,
                    safe_error_code = %s
                WHERE run_id = %s
                """,
                (
                    outcome,
                    fetched_count,
                    inserted_count,
                    updated_count,
                    skipped_count,
                    safe_error_code,
                    run_id,
                ),
            )

    def feed_statuses(self) -> list[dict[str, Any]]:
        """Latest run + freshness per feed, for the status endpoint."""
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT DISTINCT ON (feed)
                       feed, provider_id, started_at, finished_at,
                       outcome, safe_error_code
                FROM {self._t('market_data_ingestion_runs')}
                ORDER BY feed, started_at DESC
                """
            )
            last_runs = {r["feed"]: r for r in cur.fetchall()}
            cur.execute(
                f"""
                SELECT feed, MAX(finished_at) AS ok_at
                FROM {self._t('market_data_ingestion_runs')}
                WHERE outcome IN ('success', 'partial')
                GROUP BY feed
                """
            )
            last_ok = {r["feed"]: r["ok_at"] for r in cur.fetchall()}
            freshness_sql = f"""
                SELECT 'metals-monthly' AS feed,
                       MAX(o.observation_date) AS latest,
                       COUNT(*) AS n
                FROM {self._t('metal_quote_observations')} o
                UNION ALL
                SELECT 'fx-daily' AS feed, MAX(f.reference_date),
                       COUNT(*)
                FROM {self._t('fx_rate_observations')} f
            """
            feeds = ["metals-monthly", "fx-daily"]
            # R2 feeds — tolerate absence on pre-V005 databases.
            if self._table_exists("comex_import_monthly_observations"):
                freshness_sql += f"""
                UNION ALL
                SELECT 'comex-import-monthly' AS feed,
                       MAX(c.reference_month), COUNT(*)
                FROM {self._t('comex_import_monthly_observations')} c
                """
                feeds.append("comex-import-monthly")
            if self._table_exists("producer_price_index_observations"):
                freshness_sql += f"""
                UNION ALL
                SELECT 'ipp-monthly' AS feed, MAX(p.reference_month),
                       COUNT(*)
                FROM {self._t('producer_price_index_observations')} p
                """
                feeds.append("ipp-monthly")
            cur.execute(freshness_sql)
            freshness = {r["feed"]: r for r in cur.fetchall()}

        feeds_out = []
        for feed in feeds:
            run = last_runs.get(feed)
            fresh = freshness.get(feed) or {}
            feeds_out.append(
                {
                    "feed": feed,
                    "last_run_started_at": run["started_at"] if run else None,
                    "last_run_finished_at": run["finished_at"] if run else None,
                    "last_outcome": run["outcome"] if run else None,
                    "last_error_code": run["safe_error_code"] if run else None,
                    "last_successful_at": last_ok.get(feed),
                    "latest_observation_date": fresh.get("latest"),
                    "observation_count": fresh.get("n") or 0,
                }
            )
        return feeds_out

    # --- advisory lock -----------------------------------------------------

    def try_advisory_lock(self, lock_key: int) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(%s) AS ok", (lock_key,))
            return bool(cur.fetchone()["ok"])

    def release_advisory_lock(self, lock_key: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))


def rows_to_page(
    rows: list[dict[str, Any]],
    *,
    limit: int,
    date_key: str,
    id_key: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Trim over-fetched rows and emit the next cursor when truncated."""
    items = rows[:limit]
    has_more = len(rows) > limit
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(last[date_key], last[id_key])
    return items, next_cursor


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
