"""Repositório Postgres — modelo 3D vigente por produto da OP."""

from __future__ import annotations

from production_control_app.domain.ports.product_3d_model_repository import (
    Product3DModelRepositoryPort,
)
from production_control_app.domain.product_3d_model import Product3DModel
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_TABLE = f"{PC_SCHEMA_NAME}.product_3d_models"
_COLUMNS = """
    product_code,
    original_filename,
    stored_filename,
    content_type,
    byte_size,
    uploaded_by,
    uploaded_at
"""


def _from_row(row: dict) -> Product3DModel:
    return Product3DModel(
        product_code=str(row.get("product_code") or "").strip(),
        original_filename=str(row.get("original_filename") or "").strip(),
        stored_filename=str(row.get("stored_filename") or "").strip(),
        content_type=str(row.get("content_type") or "").strip() or "model/gltf-binary",
        byte_size=int(row.get("byte_size") or 0),
        uploaded_by=str(row.get("uploaded_by") or "").strip() or None,
        uploaded_at=row.get("uploaded_at"),
    )


class PostgresProduct3DModelRepository(Product3DModelRepositoryPort):
    def get(self, *, product_code: str) -> Product3DModel | None:
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            WHERE product_code = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (product_code,))
                row = cursor.fetchone()
        return _from_row(row) if row else None

    def list(self, *, search: str | None = None) -> list[Product3DModel]:
        wanted = str(search or "").strip().upper()
        params: tuple[object, ...] = ()
        where = ""
        if wanted:
            where = "WHERE product_code LIKE %s OR original_filename ILIKE %s"
            like = f"%{wanted}%"
            params = (like, f"%{search.strip()}%")
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            {where}
            ORDER BY uploaded_at DESC, product_code ASC
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [_from_row(row) for row in rows]

    def existing_codes(self, codes: set[str]) -> set[str]:
        wanted = sorted({str(code or "").strip().upper() for code in codes if str(code or "").strip()})
        if not wanted:
            return set()
        query = f"""
            SELECT product_code
            FROM {_TABLE}
            WHERE product_code = ANY(%s)
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (wanted,))
                rows = cursor.fetchall()
        return {str(row.get("product_code") or "").strip() for row in rows if row}

    def upsert(self, model: Product3DModel) -> Product3DModel:
        query = f"""
            INSERT INTO {_TABLE} (
                product_code,
                original_filename,
                stored_filename,
                content_type,
                byte_size,
                uploaded_by,
                uploaded_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (product_code) DO UPDATE SET
                original_filename = EXCLUDED.original_filename,
                stored_filename = EXCLUDED.stored_filename,
                content_type = EXCLUDED.content_type,
                byte_size = EXCLUDED.byte_size,
                uploaded_by = EXCLUDED.uploaded_by,
                uploaded_at = NOW()
            RETURNING {_COLUMNS}
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        model.product_code,
                        model.original_filename,
                        model.stored_filename,
                        model.content_type,
                        model.byte_size,
                        model.uploaded_by,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        return _from_row(row) if row else model

    def delete(self, *, product_code: str) -> Product3DModel | None:
        query = f"""
            DELETE FROM {_TABLE}
            WHERE product_code = %s
            RETURNING {_COLUMNS}
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (product_code,))
                row = cursor.fetchone()
            connection.commit()
        return _from_row(row) if row else None
