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
        filters = ["batch_id = %s::uuid"]
        params: list[Any] = [batch_id]
        needle = (search or "").strip()
        if needle:
            filters.append(
                "("
                "material_weg_tratado ILIKE %s OR "
                "COALESCE(codigo_referencia_weg, '') ILIKE %s OR "
                "origem_material_weg ILIKE %s OR "
                "COALESCE(documento, '') ILIKE %s"
                ")"
            )
            like = f"%{needle}%"
            params.extend([like, like, like, like])
        if remessa_from is not None:
            filters.append("data_remessa >= %s")
            params.append(remessa_from)
        if remessa_to is not None:
            filters.append("data_remessa <= %s")
            params.append(remessa_to)
        where = " AND ".join(filters)
        count_sql = f"SELECT COUNT(*) AS total FROM {_RECORDS} WHERE {where}"
        list_sql = f"""
            SELECT
                id::text AS id,
                batch_id::text AS batch_id,
                line_no,
                material_weg_tratado,
                codigo_referencia_weg,
                origem_material_weg,
                quantidade_original_un,
                quantidade_mi,
                unidade,
                data_remessa,
                documento,
                linha_fonte,
                assinatura_registro,
                rastreabilidade,
                line_fingerprint,
                sb1_status,
                sb1_protheus_product_code,
                sb1_matched_by,
                sb1_resolved_at
            FROM {_RECORDS}
            WHERE {where}
            ORDER BY line_no ASC
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
        data["sb1_resolution"] = {
            "status": data.pop("sb1_status", "pending"),
            "protheus_product_code": data.pop("sb1_protheus_product_code", None),
            "matched_by": data.pop("sb1_matched_by", None),
            "resolved_at": resolved.isoformat() if isinstance(resolved, datetime) else resolved,
        }
        if data.get("linha_fonte") is not None:
            data["linha_fonte"] = str(data["linha_fonte"])
        return data
