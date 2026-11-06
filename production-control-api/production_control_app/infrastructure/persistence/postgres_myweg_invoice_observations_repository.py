"""Repositório Postgres — observações imutáveis MyWEG NF Emitidas (filial 02)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from production_control_app.domain.myweg_invoice_observations_contract import (
    decimal_to_canonical_str,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_OBSERVATIONS = f"{PC_SCHEMA_NAME}.myweg_invoice_observations"
_ITEMS = f"{PC_SCHEMA_NAME}.myweg_invoice_observation_items"

_OBS_COLUMNS = """
    id::text AS id,
    collection_id,
    branch,
    myweg_company_code,
    myweg_work_center,
    myweg_supplier_code,
    contract_version,
    document_date,
    observation_status,
    observed_at,
    source_prepared_at,
    imported_at,
    source_sha256,
    payload_sha256,
    semantic_sha256,
    record_count,
    total_quantity_un,
    manifesto_json,
    status,
    idempotency_key,
    caller_app
"""


class MyWegInvoiceObservationCollectionConflict(Exception):
    """UNIQUE(collection_id) violado — caller resolve idempotência vs 409."""


class PostgresMyWegInvoiceObservationsRepository:
    def find_by_collection_id(self, collection_id: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_OBS_COLUMNS}
            FROM {_OBSERVATIONS}
            WHERE collection_id = %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (collection_id,))
                row = cursor.fetchone()
        return self._map_observation(row) if row else None

    def find_by_id(self, observation_id: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_OBS_COLUMNS}
            FROM {_OBSERVATIONS}
            WHERE id = %s::uuid
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (observation_id,))
                row = cursor.fetchone()
        return self._map_observation(row) if row else None

    def insert_accepted_observation(
        self,
        *,
        collection_id: str,
        branch: str,
        myweg_company_code: str,
        myweg_work_center: str,
        myweg_supplier_code: str,
        contract_version: str,
        document_date: date,
        observation_status: str,
        observed_at: datetime | None,
        source_prepared_at: datetime,
        source_sha256: str | None,
        payload_sha256: str,
        semantic_sha256: str,
        record_count: int,
        total_quantity_un: Decimal,
        manifesto: dict[str, Any],
        idempotency_key: str,
        caller_app: str | None,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if record_count != len(records):
            raise ValueError("record_count diverge de len(records).")
        if observation_status == "empty_signaled_by_sap":
            if records or source_sha256:
                raise ValueError("Observação vazia inválida.")
        elif observation_status == "with_records":
            if not records or not source_sha256:
                raise ValueError("Observação com registros incompleta.")
        else:
            raise ValueError(f"observation_status inválido: {observation_status}")

        insert_obs = f"""
            INSERT INTO {_OBSERVATIONS} (
                collection_id, branch, myweg_company_code, myweg_work_center,
                myweg_supplier_code, contract_version, document_date,
                observation_status, observed_at, source_prepared_at,
                source_sha256, payload_sha256, semantic_sha256, record_count,
                total_quantity_un, manifesto_json, status,
                idempotency_key, caller_app
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, 'accepted',
                %s, %s
            )
            RETURNING {_OBS_COLUMNS}
        """
        insert_item = f"""
            INSERT INTO {_ITEMS} (
                observation_id, source_line_no, invoice_number, invoice_series,
                material_weg, material_description, quantity_original, source_unit,
                quantity_un, unit_comparability, departure_date
            ) VALUES (
                %s::uuid, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
        """

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        insert_obs,
                        (
                            collection_id,
                            branch,
                            myweg_company_code,
                            myweg_work_center,
                            myweg_supplier_code,
                            contract_version,
                            document_date,
                            observation_status,
                            observed_at,
                            source_prepared_at,
                            source_sha256,
                            payload_sha256,
                            semantic_sha256,
                            record_count,
                            total_quantity_un,
                            Jsonb(manifesto or {}),
                            idempotency_key,
                            caller_app,
                        ),
                    )
                    observation = cursor.fetchone()
                    if observation is None:
                        raise RuntimeError("Falha ao persistir observação MyWEG NF.")
                    observation_id = observation["id"]
                    for record in records:
                        departure = record["departure_date"]
                        if isinstance(departure, str):
                            departure_date = date.fromisoformat(departure[:10])
                        else:
                            departure_date = departure
                        qty_un = record.get("quantity_un")
                        cursor.execute(
                            insert_item,
                            (
                                observation_id,
                                int(record["source_line_no"]),
                                record["invoice_number"],
                                record["invoice_series"],
                                record["material_weg"],
                                record.get("material_description") or "",
                                Decimal(str(record["quantity_original"])),
                                record["source_unit"],
                                Decimal(str(qty_un)) if qty_un is not None else None,
                                record["unit_comparability"],
                                departure_date,
                            ),
                        )
                connection.commit()
            except UniqueViolation as exc:
                connection.rollback()
                raise MyWegInvoiceObservationCollectionConflict(str(exc)) from exc
            except Exception:
                connection.rollback()
                raise

        mapped = self._map_observation(observation)
        assert mapped is not None
        return mapped

    def list_observations(
        self,
        *,
        document_date: date | None,
        observation_status: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        offset = (page - 1) * page_size
        filters: list[str] = []
        params: list[Any] = []
        if document_date is not None:
            filters.append("document_date = %s")
            params.append(document_date)
        if observation_status:
            filters.append("observation_status = %s")
            params.append(observation_status)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        count_query = f"SELECT COUNT(*) AS total FROM {_OBSERVATIONS} {where}"
        list_query = f"""
            SELECT {_OBS_COLUMNS}
            FROM {_OBSERVATIONS}
            {where}
            ORDER BY document_date DESC, imported_at DESC
            LIMIT %s OFFSET %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(count_query, params)
                total = int(cursor.fetchone()["total"])
                cursor.execute(list_query, [*params, page_size, offset])
                rows = cursor.fetchall()
        return {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": [self._map_observation(row) for row in rows],
        }

    def list_observation_items(
        self,
        *,
        observation_id: str,
        search: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        offset = (page - 1) * page_size
        search_text = (search or "").strip()
        filters = ["observation_id = %s::uuid"]
        params: list[Any] = [observation_id]
        if search_text:
            filters.append(
                "("
                "invoice_number ILIKE %s OR invoice_series ILIKE %s OR "
                "material_weg ILIKE %s OR material_description ILIKE %s"
                ")"
            )
            like = f"%{search_text}%"
            params.extend([like, like, like, like])
        where = " AND ".join(filters)

        count_query = f"SELECT COUNT(*) AS total FROM {_ITEMS} WHERE {where}"
        list_query = f"""
            SELECT
                id::text AS id,
                source_line_no,
                invoice_number,
                invoice_series,
                material_weg,
                material_description,
                quantity_original,
                source_unit,
                quantity_un,
                unit_comparability,
                departure_date
            FROM {_ITEMS}
            WHERE {where}
            ORDER BY source_line_no ASC
            LIMIT %s OFFSET %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(count_query, params)
                total = int(cursor.fetchone()["total"])
                cursor.execute(list_query, [*params, page_size, offset])
                rows = cursor.fetchall()
        return {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": [self._map_item(row) for row in rows],
        }

    def count_by_semantic_sha256(
        self, *, semantic_sha256: str, exclude_collection_id: str | None = None
    ) -> int:
        query = f"""
            SELECT COUNT(*) AS total
            FROM {_OBSERVATIONS}
            WHERE semantic_sha256 = %s
        """
        params: list[Any] = [semantic_sha256.lower()]
        if exclude_collection_id:
            query += " AND collection_id <> %s"
            params.append(exclude_collection_id)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return int(cursor.fetchone()["total"])

    @staticmethod
    def _map_observation(row: Any | None) -> dict[str, Any] | None:
        if row is None:
            return None
        manifesto = row.get("manifesto_json") or {}
        return {
            "id": row["id"],
            "collection_id": row["collection_id"],
            "branch": row["branch"],
            "myweg_company_code": row["myweg_company_code"],
            "myweg_work_center": row["myweg_work_center"],
            "myweg_supplier_code": row["myweg_supplier_code"],
            "contract_version": row["contract_version"],
            "document_date": (
                row["document_date"].isoformat()
                if hasattr(row["document_date"], "isoformat")
                else str(row["document_date"])
            ),
            "observation_status": row["observation_status"],
            "observed_at": (
                row["observed_at"].isoformat() if row.get("observed_at") else None
            ),
            "source_prepared_at": (
                row["source_prepared_at"].isoformat()
                if row.get("source_prepared_at")
                else None
            ),
            "imported_at": (
                row["imported_at"].isoformat() if row.get("imported_at") else None
            ),
            "source_sha256": row.get("source_sha256"),
            "payload_sha256": row["payload_sha256"],
            "semantic_sha256": row["semantic_sha256"],
            "record_count": int(row["record_count"]),
            "total_quantity_un": row["total_quantity_un"],
            "manifesto": manifesto if isinstance(manifesto, dict) else {},
            "status": row["status"],
            "idempotency_key": row.get("idempotency_key"),
            "caller_app": row.get("caller_app"),
        }

    @staticmethod
    def _map_item(row: Any) -> dict[str, Any]:
        qty_orig = Decimal(str(row["quantity_original"]))
        qty_un = row.get("quantity_un")
        return {
            "id": row["id"],
            "sourceLineNo": int(row["source_line_no"]),
            "invoiceNumber": row["invoice_number"],
            "invoiceSeries": row["invoice_series"],
            "materialWeg": row["material_weg"],
            "materialDescription": row["material_description"],
            "quantityOriginal": decimal_to_canonical_str(qty_orig),
            "sourceUnit": row["source_unit"],
            "quantityUn": (
                decimal_to_canonical_str(Decimal(str(qty_un)))
                if qty_un is not None
                else None
            ),
            "unitComparability": row["unit_comparability"],
            "departureDate": (
                row["departure_date"].isoformat()
                if hasattr(row["departure_date"], "isoformat")
                else str(row["departure_date"])
            ),
        }
