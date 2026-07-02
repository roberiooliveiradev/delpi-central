from __future__ import annotations

import json
from typing import Any

from app.domain.services.kaizen import kaizen_revision_service as revision_service
from app.domain.services.kaizen import kaizen_savings_validity
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
           k.realized_daily_savings,
           k.realized_annual_savings,
           k.status,
           k.date_implemented,
           k.date_discontinued,
           k.notes,
           k.process_description,
           k.problem_description,
           k.improvement_description,
           k.expected_result,
           k.category,
           k.current_revision_number,
           k.created_by_user_id,
           k.updated_by_user_id,
           k.created_at,
           k.updated_at
      FROM quality.kaizens k
"""

_VALID_PARTICIPANT_ROLES = {"responsavel", "participante", "apoio"}


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

    # ------------------------------------------------------------------ validade da economia

    @staticmethod
    def _enrich_savings_validity(record: dict[str, Any] | None) -> dict[str, Any] | None:
        """Anexa a validade da economia (regra de 1 ano) ao registro lido."""
        if record is None:
            return None
        implemented = record.get("date_implemented")
        record["savings_valid_until"] = kaizen_savings_validity.savings_valid_until(implemented)
        record["savings_active"] = kaizen_savings_validity.is_savings_active(
            implemented,
            status=record.get("status"),
        )
        return record

    # ------------------------------------------------------------------ listagem

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
            "items": [self._enrich_savings_validity(row) for row in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def get_record(self, record_id: str, *, with_participants: bool = True) -> dict[str, Any] | None:
        record = self.fetch_one(
            f"""
            {_KAIZEN_SELECT}
             WHERE k.id = %s
               AND k.deleted_at IS NULL
            """,
            (record_id,),
        )
        if record and with_participants:
            record["participants"] = self._load_participants(record_id)
        return self._enrich_savings_validity(record)

    # ------------------------------------------------------------------ participantes

    def _load_participants(self, kaizen_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, name, role, user_id
              FROM quality.kaizen_participants
             WHERE kaizen_id = %s
             ORDER BY CASE role WHEN 'responsavel' THEN 0 WHEN 'participante' THEN 1 ELSE 2 END,
                      created_at
            """,
            (kaizen_id,),
        )

    @staticmethod
    def _normalize_participants(raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        cleaned: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            role = str(item.get("role") or "participante").strip()
            if role not in _VALID_PARTICIPANT_ROLES:
                role = "participante"
            cleaned.append(
                {
                    "name": name[:200],
                    "role": role,
                    "user_id": (str(item["user_id"]).strip() if item.get("user_id") else None),
                }
            )
        return cleaned

    def _replace_participants(self, kaizen_id: str, participants: list[dict[str, Any]]) -> None:
        self.execute(
            "DELETE FROM quality.kaizen_participants WHERE kaizen_id = %s",
            (kaizen_id,),
            auto_commit=False,
        )
        if participants:
            self.execute_many(
                """
                INSERT INTO quality.kaizen_participants (kaizen_id, name, role, user_id)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (kaizen_id, p["name"], p["role"], p.get("user_id"))
                    for p in participants
                ],
                auto_commit=False,
            )

    @staticmethod
    def _principal_accountable(
        participants: list[dict[str, Any]],
        fallback: str | None,
    ) -> str | None:
        for p in participants:
            if p["role"] == "responsavel":
                return p["name"]
        if participants:
            return participants[0]["name"]
        return fallback

    # ------------------------------------------------------------------ revisões

    def _create_revision(
        self,
        *,
        kaizen_id: str,
        record: dict[str, Any],
        revision_number: int,
        change_type: str,
        change_summary: str | None,
        change_reason: str | None,
        effective_from: str,
        created_by_user_id: str,
    ) -> None:
        snapshot = revision_service.build_snapshot(record)
        self.execute(
            """
            INSERT INTO quality.kaizen_revisions (
                kaizen_id, revision_number, change_type, change_summary, change_reason,
                effective_from, effective_until, snapshot, created_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, NULL, %s::jsonb, %s)
            """,
            (
                kaizen_id,
                revision_number,
                change_type,
                change_summary,
                change_reason,
                effective_from,
                json.dumps(snapshot),
                created_by_user_id,
            ),
            auto_commit=False,
        )

    def _close_current_revision(self, kaizen_id: str, effective_until: str) -> None:
        self.execute(
            """
            UPDATE quality.kaizen_revisions
               SET effective_until = %s
             WHERE kaizen_id = %s
               AND effective_until IS NULL
            """,
            (effective_until, kaizen_id),
            auto_commit=False,
        )

    def list_revisions(self, kaizen_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, kaizen_id, revision_number, change_type, change_summary, change_reason,
                   effective_from, effective_until, snapshot, snapshot_schema_version,
                   created_by_user_id, created_at
              FROM quality.kaizen_revisions
             WHERE kaizen_id = %s
             ORDER BY revision_number DESC
            """,
            (kaizen_id,),
        )

    def get_revision(self, kaizen_id: str, revision_number: int) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT id, kaizen_id, revision_number, change_type, change_summary, change_reason,
                   effective_from, effective_until, snapshot, snapshot_schema_version,
                   created_by_user_id, created_at
              FROM quality.kaizen_revisions
             WHERE kaizen_id = %s
               AND revision_number = %s
            """,
            (kaizen_id, revision_number),
        )

    def get_revision_at(self, kaizen_id: str, as_of: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT id, kaizen_id, revision_number, change_type, change_summary, change_reason,
                   effective_from, effective_until, snapshot, snapshot_schema_version,
                   created_by_user_id, created_at
              FROM quality.kaizen_revisions
             WHERE kaizen_id = %s
               AND effective_from <= %s
               AND (effective_until IS NULL OR effective_until >= %s)
             ORDER BY revision_number DESC
             LIMIT 1
            """,
            (kaizen_id, as_of, as_of),
        )

    # ------------------------------------------------------------------ create

    def create_record(
        self,
        *,
        fields: dict[str, Any],
        created_by_user_id: str,
    ) -> dict[str, Any]:
        participants = self._normalize_participants(fields.get("participants"))
        fields = {k: v for k, v in fields.items() if k != "participants"}
        if participants:
            fields["accountable"] = self._principal_accountable(participants, fields.get("accountable"))

        enriched = enrich_savings_fields(fields)
        submodule_id = self._kaizen_submodule_id()
        effective_from = revision_service.resolve_effective_from(
            enriched, provided=fields.get("effective_from")
        )

        row = self.execute_returning_one(
            """
            INSERT INTO quality.kaizens (
                submodule_id, branch_code, title, accountable, sector, investment,
                savings_type, seconds_per_occurrence, occurrences_per_day, hourly_cost,
                quantity_saved_per_day, unit_material_cost, fixed_daily_savings,
                daily_savings, annual_savings, realized_daily_savings, realized_annual_savings,
                status, date_implemented, date_discontinued,
                notes, process_description, problem_description, improvement_description,
                expected_result, category, current_revision_number, created_by_user_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, 1, %s
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
                enriched.get("realized_daily_savings"),
                enriched.get("realized_annual_savings"),
                enriched.get("status", "em_andamento"),
                enriched.get("date_implemented"),
                enriched.get("date_discontinued"),
                enriched.get("notes"),
                enriched.get("process_description"),
                enriched.get("problem_description"),
                enriched.get("improvement_description"),
                enriched.get("expected_result"),
                enriched.get("category"),
                created_by_user_id,
            ),
            auto_commit=False,
        )
        if not row:
            self.rollback()
            raise PluginsRepositoryError("Falha ao cadastrar kaizen.")

        kaizen_id = str(row["id"])
        if participants:
            self._replace_participants(kaizen_id, participants)

        change_type = revision_service.resolve_change_type(None, enriched, is_creation=True)
        self._create_revision(
            kaizen_id=kaizen_id,
            record=enriched,
            revision_number=1,
            change_type=change_type,
            change_summary="Revisão inicial",
            change_reason=fields.get("change_reason"),
            effective_from=effective_from,
            created_by_user_id=created_by_user_id,
        )
        self.commit()

        created = self.get_record(kaizen_id)
        if not created:
            raise PluginsRepositoryError("Kaizen criado mas não encontrado.")
        return created

    # ------------------------------------------------------------------ update

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

        effective_from_input = fields.pop("effective_from", None)
        change_reason = fields.pop("change_reason", None)
        participants_input = fields.pop("participants", None)
        participants = (
            self._normalize_participants(participants_input)
            if participants_input is not None
            else None
        )

        merged = {**current, **fields}
        if participants is not None:
            merged["accountable"] = self._principal_accountable(
                participants, merged.get("accountable")
            )
        enriched = enrich_savings_fields(merged)

        changed_fields = revision_service.changed_trigger_fields(current, enriched)
        needs_revision = bool(changed_fields)

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
                   realized_daily_savings = %s,
                   realized_annual_savings = %s,
                   status = %s,
                   date_implemented = %s,
                   date_discontinued = %s,
                   notes = %s,
                   process_description = %s,
                   problem_description = %s,
                   improvement_description = %s,
                   expected_result = %s,
                   category = %s,
                   current_revision_number = current_revision_number + %s,
                   updated_by_user_id = %s,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
            RETURNING id, current_revision_number
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
                enriched.get("realized_daily_savings"),
                enriched.get("realized_annual_savings"),
                enriched.get("status", "em_andamento"),
                enriched.get("date_implemented"),
                enriched.get("date_discontinued"),
                enriched.get("notes"),
                enriched.get("process_description"),
                enriched.get("problem_description"),
                enriched.get("improvement_description"),
                enriched.get("expected_result"),
                enriched.get("category"),
                1 if needs_revision else 0,
                updated_by_user_id,
                record_id,
            ),
            auto_commit=False,
        )
        if not row:
            self.rollback()
            return None

        if participants is not None:
            self._replace_participants(record_id, participants)

        if needs_revision:
            new_revision_number = int(row["current_revision_number"])
            effective_from = revision_service.resolve_effective_from(
                enriched, provided=effective_from_input
            )
            self._close_current_revision(record_id, effective_from)
            change_type = revision_service.resolve_change_type(
                current, enriched, is_creation=False
            )
            change_summary = revision_service.build_change_summary(
                current, enriched, changed_fields
            )
            self._create_revision(
                kaizen_id=record_id,
                record=enriched,
                revision_number=new_revision_number,
                change_type=change_type,
                change_summary=change_summary,
                change_reason=change_reason,
                effective_from=effective_from,
                created_by_user_id=updated_by_user_id,
            )

        self.commit()
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
