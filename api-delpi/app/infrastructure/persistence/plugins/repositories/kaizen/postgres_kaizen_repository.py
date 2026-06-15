from __future__ import annotations

from typing import Any

from app.domain.services.kaizen.kaizen_savings_calculator import enrich_savings_fields
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

_KAIZEN_SELECT = """
    SELECT k.id,
           k.submodule_id,
           k.branch_code,
           k.title,
           k.accountable,
           k.sector,
           k.investment,
           k.savings_type,
           k.seconds_per_occurrence,
           k.occurrences_per_day,
           k.hourly_cost,
           k.quantity_saved_per_day,
           k.unit_material_cost,
           k.fixed_daily_savings,
           k.daily_savings,
           k.annual_savings,
           k.status,
           k.date_implemented,
           k.date_discontinued,
           k.notes,
           k.created_by_user_id,
           k.updated_by_user_id,
           k.created_at,
           k.updated_at
      FROM quality.kaizens k
"""


class PostgresKaizenRepository(PluginBaseRepository):
    _submodule_id_cache: str | None = None

    def _kaizen_submodule_id(self) -> str:
        if self._submodule_id_cache:
            return self._submodule_id_cache

        row = self.fetch_one(
            """
            SELECT id
              FROM quality.submodules
             WHERE code = 'kaizen'
               AND active = TRUE
            """,
        )
        if not row:
            raise PluginsRepositoryError("Submódulo kaizen não encontrado em quality.submodules.")
        self._submodule_id_cache = str(row["id"])
        return self._submodule_id_cache

    def list_records(
        self,
        *,
        branch_code: str | None = None,
        status: str | None = None,
        savings_type: str | None = None,
        title: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters = ["k.deleted_at IS NULL"]
        params: list[Any] = []

        if branch_code:
            filters.append("k.branch_code = %s")
            params.append(branch_code)
        if status:
            filters.append("k.status = %s")
            params.append(status)
        if savings_type:
            filters.append("k.savings_type = %s")
            params.append(savings_type)
        if title:
            filters.append("k.title ILIKE %s")
            params.append(f"%{title.strip()}%")
        if date_start:
            filters.append("k.date_implemented >= %s")
            params.append(date_start)
        if date_end:
            filters.append("k.date_implemented <= %s")
            params.append(date_end)

        where_clause = " AND ".join(filters)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM quality.kaizens k WHERE {where_clause}",
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0

        offset = max(page - 1, 0) * page_size
        rows = self.fetch_all(
            f"""
            {_KAIZEN_SELECT}
             WHERE {where_clause}
             ORDER BY k.date_implemented DESC NULLS LAST, k.created_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        return {
            "items": rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {_KAIZEN_SELECT}
             WHERE k.id = %s
               AND k.deleted_at IS NULL
            """,
            (record_id,),
        )

    def create_record(
        self,
        *,
        fields: dict[str, Any],
        created_by_user_id: str,
    ) -> dict[str, Any]:
        enriched = enrich_savings_fields(fields)
        submodule_id = self._kaizen_submodule_id()

        row = self.execute_returning_one(
            """
            INSERT INTO quality.kaizens (
                submodule_id,
                branch_code,
                title,
                accountable,
                sector,
                investment,
                savings_type,
                seconds_per_occurrence,
                occurrences_per_day,
                hourly_cost,
                quantity_saved_per_day,
                unit_material_cost,
                fixed_daily_savings,
                daily_savings,
                annual_savings,
                status,
                date_implemented,
                date_discontinued,
                notes,
                created_by_user_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                submodule_id,
                enriched["branch_code"],
                enriched["title"].strip(),
                enriched.get("accountable"),
                enriched.get("sector"),
                enriched.get("investment"),
                enriched["savings_type"],
                enriched.get("seconds_per_occurrence"),
                enriched.get("occurrences_per_day"),
                enriched.get("hourly_cost"),
                enriched.get("quantity_saved_per_day"),
                enriched.get("unit_material_cost"),
                enriched.get("fixed_daily_savings"),
                enriched.get("daily_savings"),
                enriched.get("annual_savings"),
                enriched.get("status", "em_andamento"),
                enriched.get("date_implemented"),
                enriched.get("date_discontinued"),
                enriched.get("notes"),
                created_by_user_id,
            ),
        )
        if not row:
            raise PluginsRepositoryError("Falha ao cadastrar kaizen.")
        created = self.get_record(str(row["id"]))
        if not created:
            raise PluginsRepositoryError("Kaizen criado mas não encontrado.")
        return created

    def update_record(
        self,
        record_id: str,
        *,
        fields: dict[str, Any],
        updated_by_user_id: str,
    ) -> dict[str, Any] | None:
        current = self.get_record(record_id)
        if not current:
            return None

        merged = {**current, **fields}
        enriched = enrich_savings_fields(merged)

        row = self.execute_returning_one(
            """
            UPDATE quality.kaizens
               SET branch_code = %s,
                   title = %s,
                   accountable = %s,
                   sector = %s,
                   investment = %s,
                   savings_type = %s,
                   seconds_per_occurrence = %s,
                   occurrences_per_day = %s,
                   hourly_cost = %s,
                   quantity_saved_per_day = %s,
                   unit_material_cost = %s,
                   fixed_daily_savings = %s,
                   daily_savings = %s,
                   annual_savings = %s,
                   status = %s,
                   date_implemented = %s,
                   date_discontinued = %s,
                   notes = %s,
                   updated_by_user_id = %s,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
            RETURNING id
            """,
            (
                enriched["branch_code"],
                str(enriched["title"]).strip(),
                enriched.get("accountable"),
                enriched.get("sector"),
                enriched.get("investment"),
                enriched["savings_type"],
                enriched.get("seconds_per_occurrence"),
                enriched.get("occurrences_per_day"),
                enriched.get("hourly_cost"),
                enriched.get("quantity_saved_per_day"),
                enriched.get("unit_material_cost"),
                enriched.get("fixed_daily_savings"),
                enriched.get("daily_savings"),
                enriched.get("annual_savings"),
                enriched.get("status", "em_andamento"),
                enriched.get("date_implemented"),
                enriched.get("date_discontinued"),
                enriched.get("notes"),
                updated_by_user_id,
                record_id,
            ),
        )
        if not row:
            return None
        return self.get_record(record_id)

    def delete_record(self, record_id: str, *, updated_by_user_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE quality.kaizens
               SET deleted_at = NOW(),
                   updated_by_user_id = %s,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
            RETURNING id
            """,
            (updated_by_user_id, record_id),
        )
        return row is not None
