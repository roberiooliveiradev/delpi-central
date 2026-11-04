"""Repositório Postgres — lotes imutáveis MyWEG Necessidades (filial 02)."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from production_control_app.domain.myweg_needs_contract import decimal_to_canonical_str
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_BATCHES = f"{PC_SCHEMA_NAME}.myweg_need_batches"
_RECORDS = f"{PC_SCHEMA_NAME}.myweg_need_records"
_SB1_RUNS = f"{PC_SCHEMA_NAME}.myweg_need_sb1_resolution_runs"
_SB1_RESOLUTIONS = f"{PC_SCHEMA_NAME}.myweg_need_sb1_resolutions"

_BATCH_COLUMNS = """
    id::text AS id,
    collection_id,
    branch,
    myweg_company_code,
    myweg_work_center,
    contract_version,
    collected_at,
    exported_at,
    collection_date,
    imported_at,
    payload_sha256,
    source_files_json,
    record_count,
    total_quantidade_un,
    total_quantidade_mi,
    status,
    idempotency_key,
    caller_app
"""


class MyWegNeedsCollectionConflict(Exception):
    """UNIQUE(collection_id) violado — caller resolve idempotência vs 409."""


class PostgresMyWegNeedsRepository:
    def find_by_collection_id(self, collection_id: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_BATCH_COLUMNS}
            FROM {_BATCHES}
            WHERE collection_id = %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (collection_id,))
                row = cursor.fetchone()
        return self._map_batch(row) if row else None

    def find_by_id(self, batch_id: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_BATCH_COLUMNS}
            FROM {_BATCHES}
            WHERE id = %s::uuid
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (batch_id,))
                row = cursor.fetchone()
        return self._map_batch(row) if row else None

    def insert_accepted_batch(
        self,
        *,
        collection_id: str,
        branch: str,
        myweg_company_code: str,
        myweg_work_center: str,
        contract_version: str,
        collected_at: datetime,
        exported_at: datetime,
        collection_date: date,
        payload_sha256: str,
        source_files: dict[str, Any],
        record_count: int,
        total_quantidade_un: Decimal,
        total_quantidade_mi: Decimal,
        idempotency_key: str,
        caller_app: str | None,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if record_count <= 0 or not records:
            raise ValueError("Lote vazio não é aceito.")

        insert_batch = f"""
            INSERT INTO {_BATCHES} (
                collection_id, branch, myweg_company_code, myweg_work_center,
                contract_version, collected_at, exported_at, collection_date,
                payload_sha256, source_files_json, record_count,
                total_quantidade_un, total_quantidade_mi, status,
                idempotency_key, caller_app
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, 'accepted',
                %s, %s
            )
            RETURNING {_BATCH_COLUMNS}
        """
        insert_record = f"""
            INSERT INTO {_RECORDS} (
                batch_id, line_no, material_weg_tratado, codigo_referencia_weg,
                origem_material_weg, quantidade_original_un, quantidade_mi, unidade,
                data_remessa, documento, linha_fonte, assinatura_registro,
                rastreabilidade, line_fingerprint,
                sb1_status, sb1_protheus_product_code, sb1_matched_by, sb1_resolved_at
            ) VALUES (
                %s::uuid, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s
            )
        """

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        insert_batch,
                        (
                            collection_id,
                            branch,
                            myweg_company_code,
                            myweg_work_center,
                            contract_version,
                            collected_at,
                            exported_at,
                            collection_date,
                            payload_sha256,
                            Jsonb(source_files),
                            record_count,
                            total_quantidade_un,
                            total_quantidade_mi,
                            idempotency_key,
                            caller_app,
                        ),
                    )
                    batch = cursor.fetchone()
                    if batch is None:
                        raise RuntimeError("Falha ao persistir lote MyWEG.")
                    batch_id = batch["id"]
                    for index, record in enumerate(records, start=1):
                        sb1 = record.get("sb1_resolution") or {}
                        remessa = record["data_remessa"]
                        if isinstance(remessa, str):
                            remessa_date = date.fromisoformat(remessa[:10])
                        else:
                            remessa_date = remessa
                        cursor.execute(
                            insert_record,
                            (
                                batch_id,
                                index,
                                record["material_weg_tratado"],
                                record.get("codigo_referencia_weg"),
                                record["origem_material_weg"],
                                Decimal(str(record["quantidade_original_un"])),
                                Decimal(str(record["quantidade_mi"])),
                                record["unidade"],
                                remessa_date,
                                record.get("documento"),
                                record.get("linha_fonte"),
                                record.get("assinatura_registro"),
                                record["rastreabilidade"],
                                record["line_fingerprint"],
                                sb1.get("status") or "pending",
                                sb1.get("protheus_product_code"),
                                sb1.get("matched_by"),
                                sb1.get("resolved_at"),
                            ),
                        )
                connection.commit()
            except UniqueViolation as exc:
                connection.rollback()
                raise MyWegNeedsCollectionConflict(str(exc)) from exc
            except Exception:
                connection.rollback()
                raise

        mapped = self._map_batch(batch)
        assert mapped is not None
        return mapped

    def list_batches(self, *, page: int, page_size: int) -> dict[str, Any]:
        offset = (page - 1) * page_size
        count_sql = f"SELECT COUNT(*) AS total FROM {_BATCHES}"
        list_sql = f"""
            SELECT {_BATCH_COLUMNS}
            FROM {_BATCHES}
            ORDER BY collected_at DESC, imported_at DESC, collection_id ASC
            LIMIT %s OFFSET %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(count_sql)
                total = int(cursor.fetchone()["total"])
                cursor.execute(list_sql, (page_size, offset))
                rows = cursor.fetchall()
        return {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": [self._map_batch(row) for row in rows],
        }

    def get_latest_batch(self) -> dict[str, Any] | None:
        """Última coleta pela data real da coleta (collected_at), não pelo import."""
        query = f"""
            SELECT {_BATCH_COLUMNS}
            FROM {_BATCHES}
            ORDER BY collected_at DESC, imported_at DESC, collection_id ASC
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
        return self._map_batch(row) if row else None

    def list_all_batch_records(self, *, batch_id: str) -> list[dict[str, Any]]:
        """Todas as linhas do lote (resolução SB1) — sem paginação."""
        query = f"""
            SELECT
                id::text AS id,
                batch_id::text AS batch_id,
                line_no,
                material_weg_tratado,
                codigo_referencia_weg,
                line_fingerprint
            FROM {_RECORDS}
            WHERE batch_id = %s::uuid
            ORDER BY line_no ASC
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (batch_id,))
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_sb1_resolution_run(
        self,
        *,
        run_id: str,
        batch_id: str,
        dry_run: bool,
        caller_app: str | None,
        status: str,
        counts: dict[str, Any],
        semantics_proven: bool,
        semantics_notes: str,
    ) -> None:
        query = f"""
            INSERT INTO {_SB1_RUNS} (
                id, batch_id, dry_run, caller_app, started_at, finished_at,
                status, counts_json, semantics_proven, semantics_notes
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, NOW(), NOW(),
                %s, %s::jsonb, %s, %s
            )
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        run_id,
                        batch_id,
                        dry_run,
                        caller_app,
                        status,
                        Jsonb(counts),
                        semantics_proven,
                        semantics_notes,
                    ),
                )
                connection.commit()

    def upsert_sb1_resolutions(
        self,
        *,
        resolution_run_id: str,
        rows: list[dict[str, Any]],
    ) -> None:
        if not rows:
            return
        query = f"""
            INSERT INTO {_SB1_RESOLUTIONS} (
                batch_id, record_id, line_fingerprint, status,
                informed_product_code, customer_reference,
                verified_product_code, verified_description,
                matched_by, reason, candidates_json, source,
                resolution_run_id, verified_at, created_at, updated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s::jsonb, %s,
                %s::uuid, %s, NOW(), NOW()
            )
            ON CONFLICT (record_id) DO UPDATE SET
                status = EXCLUDED.status,
                informed_product_code = EXCLUDED.informed_product_code,
                customer_reference = EXCLUDED.customer_reference,
                verified_product_code = EXCLUDED.verified_product_code,
                verified_description = EXCLUDED.verified_description,
                matched_by = EXCLUDED.matched_by,
                reason = EXCLUDED.reason,
                candidates_json = EXCLUDED.candidates_json,
                source = EXCLUDED.source,
                resolution_run_id = EXCLUDED.resolution_run_id,
                verified_at = EXCLUDED.verified_at,
                line_fingerprint = EXCLUDED.line_fingerprint,
                updated_at = NOW()
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                for row in rows:
                    verified_at = row["verified_at"]
                    cursor.execute(
                        query,
                        (
                            row["batch_id"],
                            row["record_id"],
                            row["line_fingerprint"],
                            row["status"],
                            row.get("informed_product_code"),
                            row.get("customer_reference"),
                            row.get("verified_product_code"),
                            row.get("verified_description"),
                            row.get("matched_by"),
                            row.get("reason"),
                            Jsonb(row.get("candidates") or []),
                            row.get("source") or "api-delpi.lookup_products_sb1_identity",
                            resolution_run_id,
                            verified_at,
                        ),
                    )
                connection.commit()

    def list_batch_items(
        self,
        *,
        batch_id: str,
        search: str,
        remessa_from: date | None,
        remessa_to: date | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        filters = ["r.batch_id = %s::uuid"]
        params: list[Any] = [batch_id]
        needle = (search or "").strip()
        if needle:
            filters.append(
                "("
                "r.material_weg_tratado ILIKE %s OR "
                "COALESCE(r.codigo_referencia_weg, '') ILIKE %s OR "
                "r.origem_material_weg ILIKE %s OR "
                "COALESCE(r.documento, '') ILIKE %s OR "
                "COALESCE(res.verified_product_code, '') ILIKE %s"
                ")"
            )
            like = f"%{needle}%"
            params.extend([like, like, like, like, like])
        if remessa_from is not None:
            filters.append("r.data_remessa >= %s")
            params.append(remessa_from)
        if remessa_to is not None:
            filters.append("r.data_remessa <= %s")
            params.append(remessa_to)
        where = " AND ".join(filters)
        count_sql = f"SELECT COUNT(*) AS total FROM {_RECORDS} r WHERE {where}"
        list_sql = f"""
            SELECT
                r.id::text AS id,
                r.batch_id::text AS batch_id,
                r.line_no,
                r.material_weg_tratado,
                r.codigo_referencia_weg,
                r.origem_material_weg,
                r.quantidade_original_un,
                r.quantidade_mi,
                r.unidade,
                r.data_remessa,
                r.documento,
                r.linha_fonte,
                r.assinatura_registro,
                r.rastreabilidade,
                r.line_fingerprint,
                COALESCE(res.status, r.sb1_status) AS sb1_status,
                COALESCE(res.verified_product_code, r.sb1_protheus_product_code)
                    AS sb1_protheus_product_code,
                COALESCE(res.matched_by, r.sb1_matched_by) AS sb1_matched_by,
                COALESCE(res.verified_at, r.sb1_resolved_at) AS sb1_resolved_at,
                res.verified_description AS sb1_verified_description,
                res.reason AS sb1_reason,
                res.informed_product_code AS sb1_informed_product_code,
                res.candidates_json AS sb1_candidates_json
            FROM {_RECORDS} r
            LEFT JOIN {_SB1_RESOLUTIONS} res ON res.record_id = r.id
            WHERE {where}
            ORDER BY r.line_no ASC
            LIMIT %s OFFSET %s
        """
        offset = (page - 1) * page_size
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(count_sql, params)
                total = int(cursor.fetchone()["total"])
                cursor.execute(list_sql, [*params, page_size, offset])
                rows = cursor.fetchall()
        return {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": [self._map_record(row) for row in rows],
        }

    @staticmethod
    def _map_batch(row: Any | None) -> dict[str, Any] | None:
        if row is None:
            return None
        data = dict(row)
        source = data.pop("source_files_json", {}) or {}
        if isinstance(source, str):
            source = json.loads(source)
        data["source_files"] = dict(source)
        for key in ("total_quantidade_un", "total_quantidade_mi"):
            if data.get(key) is not None:
                data[key] = decimal_to_canonical_str(Decimal(str(row[key])))
        for key in ("collected_at", "exported_at", "imported_at"):
            value = data.get(key)
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        value = data.get("collection_date")
        if isinstance(value, date):
            data["collection_date"] = value.isoformat()
        return data

    @staticmethod
    def _map_record(row: Any) -> dict[str, Any]:
        data = dict(row)
        for key in ("quantidade_original_un", "quantidade_mi"):
            data[key] = decimal_to_canonical_str(Decimal(str(row[key])))
        remessa = data.get("data_remessa")
        if isinstance(remessa, date):
            data["data_remessa"] = remessa.isoformat()
        resolved = data.pop("sb1_resolved_at", None)
        candidates = data.pop("sb1_candidates_json", None) or []
        if isinstance(candidates, str):
            candidates = json.loads(candidates)
        data["sb1_resolution"] = {
            "status": data.pop("sb1_status", "pending"),
            "protheus_product_code": data.pop("sb1_protheus_product_code", None),
            "matched_by": data.pop("sb1_matched_by", None),
            "resolved_at": resolved.isoformat() if isinstance(resolved, datetime) else resolved,
            "verified_description": data.pop("sb1_verified_description", None),
            "reason": data.pop("sb1_reason", None),
            "informed_product_code": data.pop("sb1_informed_product_code", None),
            "candidates": list(candidates) if isinstance(candidates, list) else [],
        }
        if data.get("linha_fonte") is not None:
            data["linha_fonte"] = str(data["linha_fonte"])
        return data
