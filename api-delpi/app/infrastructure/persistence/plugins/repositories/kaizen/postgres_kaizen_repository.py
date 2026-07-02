from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.domain.services.kaizen import kaizen_revision_service as revision_service
from app.domain.services.kaizen import kaizen_savings_timeline as savings_timeline_service
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
_VERSION_STATUSES = {"em_andamento", "implantado", "descontinuado", "cancelado", "substituido"}


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

    # ------------------------------------------------------------------ indicadores (painel)

    _EXPIRING_WINDOW_DAYS = 90

    @staticmethod
    def _as_date(value: Any) -> date | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    @staticmethod
    def _as_float(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def summary(
        self,
        *,
        branch_code: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> dict[str, Any]:
        """Indicadores agregados do painel de kaizens, direto do Postgres.

        Regras de negócio (espelham `kaizen_savings_validity` e o painel do MFE):

        - **Ganhos financeiros no período**: soma de ``daily_savings × dias ativos`` de
          TODOS os kaizens implantados (inclui os implantados antes do período que ainda
          contabilizam), com o teto de 1 ano de validade.
        - **Contagens/distribuições/série mensal**: escopadas pela ``date_implemented``
          dentro do período (quando informado).
        - **Run-rate vigente**: kaizens implantados ainda dentro da validade hoje.
        """
        filters = ["k.deleted_at IS NULL"]
        params: list[Any] = []
        if branch_code:
            filters.append("k.branch_code = %s")
            params.append(branch_code)
        where_clause = " AND ".join(filters)

        rows = self.fetch_all(
            f"{_KAIZEN_SELECT} WHERE {where_clause} ORDER BY k.created_at DESC",
            tuple(params),
        )

        start = self._as_date(date_start)
        end = self._as_date(date_end)
        has_period = bool(date_start or date_end)
        today = date.today()

        def implemented_date(row: dict[str, Any]) -> date | None:
            return self._as_date(row.get("date_implemented"))

        def is_implanted(row: dict[str, Any]) -> bool:
            return row.get("status") == "implantado"

        def in_period(row: dict[str, Any]) -> bool:
            if not has_period:
                return True
            day = implemented_date(row)
            if day is None:
                return False
            if start and day < start:
                return False
            if end and day > end:
                return False
            return True

        period_rows = [row for row in rows if in_period(row)]

        # Indicador 1 — ganhos financeiros no período (sobre TODOS os registros).
        period_savings = 0.0
        for row in rows:
            if not is_implanted(row):
                continue
            daily = self._as_float(row.get("daily_savings"))
            if not daily:
                continue
            days = kaizen_savings_validity.active_days_in_range(
                implemented_date(row), start, end
            )
            period_savings += daily * days

        # Indicador 2 — novos implantados por mês (pela date_implemented, no período).
        implanted_period = [
            row for row in period_rows if is_implanted(row) and implemented_date(row)
        ]
        month_counts: dict[str, int] = {}
        for row in implanted_period:
            day = implemented_date(row)
            if day is None:
                continue
            key = f"{day.year:04d}-{day.month:02d}"
            month_counts[key] = month_counts.get(key, 0) + 1
        implanted_by_month = [
            {"key": key, "value": value} for key, value in sorted(month_counts.items())
        ]

        # Run-rate vigente (implantados ainda dentro da validade hoje).
        active_rows = [
            row
            for row in period_rows
            if is_implanted(row)
            and kaizen_savings_validity.is_savings_active(
                implemented_date(row), status=row.get("status")
            )
        ]

        def tally(items: list[dict[str, Any]], key_of) -> list[dict[str, Any]]:
            counts: dict[str, int] = {}
            for item in items:
                key = key_of(item)
                counts[key] = counts.get(key, 0) + 1
            return [
                {"key": key, "value": value}
                for key, value in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
            ]

        expiring_soon = []
        for row in active_rows:
            valid_until = kaizen_savings_validity.savings_valid_until(implemented_date(row))
            if valid_until is None:
                continue
            days_left = (valid_until - today).days
            if days_left <= self._EXPIRING_WINDOW_DAYS:
                expiring_soon.append(
                    {
                        "id": str(row.get("id")),
                        "title": row.get("title"),
                        "branch_code": row.get("branch_code"),
                        "valid_until": valid_until.isoformat(),
                        "days_left": days_left,
                    }
                )
        expiring_soon.sort(key=lambda item: item["days_left"])

        expired_but_implanted = sum(
            1
            for row in period_rows
            if is_implanted(row)
            and implemented_date(row) is not None
            and not kaizen_savings_validity.is_savings_active(
                implemented_date(row), status=row.get("status")
            )
        )

        def status_count(status: str) -> int:
            return sum(1 for row in period_rows if row.get("status") == status)

        recent_rows = sorted(
            period_rows, key=lambda row: str(row.get("created_at") or ""), reverse=True
        )[:6]
        recent = [
            {
                "id": str(row.get("id")),
                "title": row.get("title"),
                "branch_code": row.get("branch_code"),
                "status": row.get("status"),
                "date_implemented": (
                    implemented_date(row).isoformat() if implemented_date(row) else None
                ),
                "updated_at": (
                    row["updated_at"].isoformat()
                    if hasattr(row.get("updated_at"), "isoformat")
                    else row.get("updated_at")
                ),
            }
            for row in recent_rows
        ]

        return {
            "filters": {
                "branch_code": branch_code,
                "date_start": date_start,
                "date_end": date_end,
            },
            "has_period": has_period,
            "total": len(period_rows),
            "implantados": status_count("implantado"),
            "em_andamento": status_count("em_andamento"),
            "descontinuados": status_count("descontinuado"),
            "cancelados": status_count("cancelado"),
            "period_savings": round(period_savings, 2),
            "period_implanted_count": len(implanted_period),
            "active_annual_savings": round(
                sum(self._as_float(row.get("annual_savings")) for row in active_rows), 2
            ),
            "realized_annual_savings": round(
                sum(self._as_float(row.get("realized_annual_savings")) for row in active_rows),
                2,
            ),
            "active_count": len(active_rows),
            "total_investment": round(
                sum(self._as_float(row.get("investment")) for row in period_rows), 2
            ),
            "expired_but_implanted": expired_but_implanted,
            "by_status": tally(period_rows, lambda row: row.get("status") or "—"),
            "by_branch": tally(period_rows, lambda row: row.get("branch_code") or "—"),
            "by_savings_type": tally(period_rows, lambda row: row.get("savings_type") or "—"),
            "by_category": tally(period_rows, lambda row: row.get("category") or "sem_categoria"),
            "top_accountables": tally(
                [row for row in period_rows if row.get("accountable")],
                lambda row: row.get("accountable"),
            )[:6],
            "implanted_by_month": implanted_by_month,
            "expiring_soon": expiring_soon,
            "recent": recent,
        }

    # ------------------------------------------------------------------ exportação (backup/migração)

    _EXPORT_FIELDS = (
        "branch_code",
        "title",
        "accountable",
        "sector",
        "investment",
        "savings_type",
        "seconds_per_occurrence",
        "occurrences_per_day",
        "hourly_cost",
        "quantity_saved_per_day",
        "unit_material_cost",
        "fixed_daily_savings",
        "realized_daily_savings",
        "status",
        "date_implemented",
        "date_discontinued",
        "notes",
        "process_description",
        "problem_description",
        "improvement_description",
        "expected_result",
        "category",
    )

    def export_records(self) -> list[dict[str, Any]]:
        """Todos os kaizens vivos no formato importável por ``create_record`` (com participantes)."""
        rows = self.fetch_all(
            f"""
            {_KAIZEN_SELECT}
             WHERE k.deleted_at IS NULL
             ORDER BY k.created_at
            """,
        )
        if not rows:
            return []

        ids = [str(row["id"]) for row in rows]
        participants = self.fetch_all(
            """
            SELECT kaizen_id, name, role, user_id
              FROM quality.kaizen_participants
             WHERE kaizen_id = ANY(%s)
             ORDER BY CASE role WHEN 'responsavel' THEN 0 WHEN 'participante' THEN 1 ELSE 2 END,
                      created_at
            """,
            (ids,),
        )
        by_kaizen: dict[str, list[dict[str, Any]]] = {}
        for item in participants:
            by_kaizen.setdefault(str(item["kaizen_id"]), []).append(
                {"name": item["name"], "role": item["role"], "user_id": item.get("user_id")}
            )

        exported: list[dict[str, Any]] = []
        for row in rows:
            fields = {key: self._json_safe(row.get(key)) for key in self._EXPORT_FIELDS}
            fields["participants"] = by_kaizen.get(str(row["id"]), [])
            exported.append(fields)
        return exported

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

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
        created_by_name: str | None = None,
        version_status: str = "implantado",
    ) -> str:
        snapshot = revision_service.build_snapshot(record)
        row = self.execute_returning_one(
            """
            INSERT INTO quality.kaizen_revisions (
                kaizen_id, revision_number, change_type, change_summary, change_reason,
                effective_from, effective_until, snapshot, daily_savings, annual_savings,
                created_by_user_id, created_by_name, version_status
            ) VALUES (%s, %s, %s, %s, %s, %s, NULL, %s::jsonb, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                kaizen_id,
                revision_number,
                change_type,
                change_summary,
                change_reason,
                effective_from,
                json.dumps(snapshot),
                record.get("daily_savings"),
                record.get("annual_savings"),
                created_by_user_id,
                created_by_name,
                version_status,
            ),
            auto_commit=False,
        )
        return str(row["id"]) if row else ""

    # ------------------------------------------------------------------ auditoria (history + governança)

    def _append_history(
        self,
        kaizen_id: str,
        *,
        event_type: str,
        old_value: str | None = None,
        new_value: str | None = None,
        comment: str | None = None,
        actor_user_id: str,
        actor_name: str | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO quality.kaizen_history (
                kaizen_id, event_type, old_value, new_value, comment,
                created_by_user_id, created_by_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (kaizen_id, event_type, old_value, new_value, comment, actor_user_id, actor_name),
            auto_commit=False,
        )

    def _append_audit_log(
        self,
        kaizen_id: str,
        *,
        event_type: str,
        payload: dict[str, Any] | None = None,
        actor_user_id: str,
        actor_name: str | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO quality.kaizen_audit_log (
                kaizen_id, event_type, payload, actor_user_id, actor_name
            ) VALUES (%s, %s, %s::jsonb, %s, %s)
            """,
            (kaizen_id, event_type, json.dumps(payload or {}), actor_user_id, actor_name),
            auto_commit=False,
        )

    def list_history(self, kaizen_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, kaizen_id, event_type, old_value, new_value, comment,
                   created_by_user_id, created_by_name, created_at
              FROM quality.kaizen_history
             WHERE kaizen_id = %s
             ORDER BY created_at DESC
             LIMIT 200
            """,
            (kaizen_id,),
        )

    def list_audit_log(self, kaizen_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, kaizen_id, event_type, payload, actor_user_id, actor_name, created_at
              FROM quality.kaizen_audit_log
             WHERE kaizen_id = %s
             ORDER BY created_at DESC
             LIMIT 200
            """,
            (kaizen_id,),
        )

    def savings_timeline(
        self,
        kaizen_id: str,
        *,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> dict[str, Any]:
        from datetime import date as _date

        revisions = self.list_revisions(kaizen_id)
        start = _date.fromisoformat(date_start) if date_start else None
        end = _date.fromisoformat(date_end) if date_end else None
        total = savings_timeline_service.period_savings(revisions, start, end)
        current = savings_timeline_service.current_active_savings(revisions)
        return {
            "kaizen_id": kaizen_id,
            "date_start": date_start,
            "date_end": date_end,
            "period_savings": total,
            "current": current,
            "improvements": revisions,
        }

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
        rows = self.fetch_all(
            """
            SELECT id, kaizen_id, revision_number, change_type, change_summary, change_reason,
                   effective_from, effective_until, snapshot, snapshot_schema_version,
                   daily_savings, annual_savings, version_status,
                   created_by_user_id, created_by_name, created_at
              FROM quality.kaizen_revisions
             WHERE kaizen_id = %s
             ORDER BY revision_number DESC
            """,
            (kaizen_id,),
        )
        for row in rows:
            row["savings_valid_until"] = kaizen_savings_validity.savings_valid_until(
                row.get("effective_from")
            )
        return rows

    def _get_active_version(self, kaizen_id: str) -> dict[str, Any] | None:
        """Versão implantada vigente; se não houver, o rascunho aberto mais recente."""
        return self.fetch_one(
            """
            SELECT id, kaizen_id, revision_number, version_status, effective_from
              FROM quality.kaizen_revisions
             WHERE kaizen_id = %s
             ORDER BY (version_status = 'implantado') DESC,
                      (effective_until IS NULL) DESC,
                      revision_number DESC
             LIMIT 1
            """,
            (kaizen_id,),
        )

    def _next_revision_number(self, kaizen_id: str) -> int:
        row = self.fetch_one(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 AS n FROM quality.kaizen_revisions WHERE kaizen_id = %s",
            (kaizen_id,),
        )
        return int(row["n"]) if row else 1

    def _update_version_snapshot(self, revision_id: str, record: dict[str, Any]) -> None:
        snapshot = revision_service.build_snapshot(record)
        self.execute(
            """
            UPDATE quality.kaizen_revisions
               SET snapshot = %s::jsonb,
                   daily_savings = %s,
                   annual_savings = %s
             WHERE id = %s
            """,
            (
                json.dumps(snapshot),
                record.get("daily_savings"),
                record.get("annual_savings"),
                revision_id,
            ),
            auto_commit=False,
        )

    def get_revision(self, kaizen_id: str, revision_number: int) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT id, kaizen_id, revision_number, change_type, change_summary, change_reason,
                   effective_from, effective_until, snapshot, snapshot_schema_version,
                   daily_savings, annual_savings, version_status,
                   created_by_user_id, created_by_name, created_at
              FROM quality.kaizen_revisions
             WHERE kaizen_id = %s
               AND revision_number = %s
            """,
            (kaizen_id, revision_number),
        )
        if row:
            row["savings_valid_until"] = kaizen_savings_validity.savings_valid_until(
                row.get("effective_from")
            )
        return row

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
        actor_name: str | None = None,
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
        initial_status = str(enriched.get("status", "em_andamento"))
        version_status = initial_status if initial_status in _VERSION_STATUSES else "em_andamento"
        self._create_revision(
            kaizen_id=kaizen_id,
            record=enriched,
            revision_number=1,
            change_type=change_type,
            change_summary="Versão inicial",
            change_reason=fields.get("change_reason"),
            effective_from=effective_from,
            created_by_user_id=created_by_user_id,
            created_by_name=actor_name,
            version_status=version_status,
        )
        self._append_history(
            kaizen_id,
            event_type="kaizen_created",
            new_value=str(enriched.get("title") or "").strip() or None,
            actor_user_id=created_by_user_id,
            actor_name=actor_name,
        )
        self._append_audit_log(
            kaizen_id,
            event_type="kaizen_created",
            payload={
                "title": str(enriched.get("title") or "").strip(),
                "status": enriched.get("status", "em_andamento"),
                "annual_savings": enriched.get("annual_savings"),
            },
            actor_user_id=created_by_user_id,
            actor_name=actor_name,
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
        actor_name: str | None = None,
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

        # Edição inline = CORREÇÃO da versão vigente (não cria versão nova).
        # A versão vigente é atualizada no lugar; a transição de status é refletida nela.
        self._apply_correction_to_active_version(
            record_id,
            current=current,
            enriched=enriched,
            changed_fields=changed_fields,
            effective_from_input=effective_from_input,
            actor_user_id=updated_by_user_id,
            actor_name=actor_name,
        )

        self.commit()
        return self.get_record(record_id)

    def _apply_correction_to_active_version(
        self,
        kaizen_id: str,
        *,
        current: dict[str, Any],
        enriched: dict[str, Any],
        changed_fields: list[str],
        effective_from_input: str | None,
        actor_user_id: str,
        actor_name: str | None,
    ) -> None:
        active = self._get_active_version(kaizen_id)
        if active is None:
            return
        revision_id = str(active["id"])
        self._update_version_snapshot(revision_id, enriched)

        old_status = str(current.get("status") or "")
        new_status = str(enriched.get("status") or "")
        status_changed = old_status != new_status

        if status_changed:
            if new_status == "implantado" and active.get("version_status") == "em_andamento":
                effective_from = revision_service.resolve_effective_from(
                    enriched, provided=effective_from_input
                )
                self._set_version_status(revision_id, "implantado", effective_from=effective_from)
            elif new_status in ("descontinuado", "cancelado"):
                effective_until = (
                    self._normalize_date(enriched.get("date_discontinued"))
                    or date.today().isoformat()
                )
                self._set_version_status(
                    revision_id, new_status, effective_until=effective_until
                )
            elif new_status == "em_andamento":
                self._set_version_status(revision_id, "em_andamento")

            self._append_history(
                kaizen_id,
                event_type="status_changed",
                old_value=old_status,
                new_value=new_status,
                comment=revision_service.build_change_summary(current, enriched, changed_fields),
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
            self._append_audit_log(
                kaizen_id,
                event_type="status_changed",
                payload={"from": old_status, "to": new_status},
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
        elif changed_fields:
            self._append_history(
                kaizen_id,
                event_type="kaizen_corrected",
                comment=revision_service.build_change_summary(current, enriched, changed_fields),
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
            self._append_audit_log(
                kaizen_id,
                event_type="kaizen_corrected",
                payload={"fields": changed_fields},
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )

    def _set_version_status(
        self,
        revision_id: str,
        version_status: str,
        *,
        effective_from: str | None = None,
        effective_until: str | None = None,
    ) -> None:
        sets = ["version_status = %s"]
        params: list[Any] = [version_status]
        if effective_from is not None:
            sets.append("effective_from = %s")
            params.append(effective_from)
        if effective_until is not None:
            sets.append("effective_until = %s")
            params.append(effective_until)
        params.append(revision_id)
        self.execute(
            f"UPDATE quality.kaizen_revisions SET {', '.join(sets)} WHERE id = %s",
            tuple(params),
            auto_commit=False,
        )

    @staticmethod
    def _normalize_date(value: Any) -> str | None:
        if value is None or value == "":
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()[:10]
        return str(value)[:10]

    # ------------------------------------------------------------------ versões (ciclo de vida)

    def create_version(
        self,
        kaizen_id: str,
        *,
        fields: dict[str, Any],
        created_by_user_id: str,
        actor_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Cria uma nova versão EM ANDAMENTO (rascunho). Não altera a versão vigente."""
        current = self.get_record(kaizen_id)
        if current is None:
            return None

        participants_input = fields.pop("participants", None)
        change_reason = fields.pop("change_reason", None)
        merged = {**current, **fields}
        merged.pop("id", None)
        enriched = enrich_savings_fields(merged)

        revision_number = self._next_revision_number(kaizen_id)
        effective_from = revision_service.resolve_effective_from(
            enriched, provided=fields.get("effective_from")
        )
        revision_id = self._create_revision(
            kaizen_id=kaizen_id,
            record=enriched,
            revision_number=revision_number,
            change_type="melhoria",
            change_summary=f"Nova versão v{revision_number} (rascunho)",
            change_reason=change_reason,
            effective_from=effective_from,
            created_by_user_id=created_by_user_id,
            created_by_name=actor_name,
            version_status="em_andamento",
        )
        if participants_input is not None:
            self._store_version_participants(revision_id, participants_input)

        self._append_history(
            kaizen_id,
            event_type="version_created",
            new_value=f"v{revision_number}",
            actor_user_id=created_by_user_id,
            actor_name=actor_name,
        )
        self._append_audit_log(
            kaizen_id,
            event_type="version_created",
            payload={"revision": revision_number},
            actor_user_id=created_by_user_id,
            actor_name=actor_name,
        )
        self.commit()
        return self.get_revision(kaizen_id, revision_number)

    def update_version(
        self,
        kaizen_id: str,
        revision_number: int,
        *,
        fields: dict[str, Any],
        updated_by_user_id: str,
        actor_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Edita uma versão que ainda está EM ANDAMENTO (rascunho)."""
        revision = self.get_revision(kaizen_id, revision_number)
        if revision is None:
            return None
        if revision.get("version_status") != "em_andamento":
            raise PluginsRepositoryError(
                "Só é possível editar uma versão em andamento (rascunho)."
            )

        base = dict(revision.get("snapshot") or {})
        fields.pop("participants", None)
        fields.pop("change_reason", None)
        merged = {**base, **fields}
        enriched = enrich_savings_fields(merged)
        self._update_version_snapshot(str(revision["id"]), enriched)
        self._append_history(
            kaizen_id,
            event_type="version_updated",
            new_value=f"v{revision_number}",
            actor_user_id=updated_by_user_id,
            actor_name=actor_name,
        )
        self.commit()
        return self.get_revision(kaizen_id, revision_number)

    def implement_version(
        self,
        kaizen_id: str,
        revision_number: int,
        *,
        effective_from: str | None = None,
        updated_by_user_id: str,
        actor_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Implanta uma versão em andamento: substitui a vigente e passa a contabilizar."""
        revision = self.get_revision(kaizen_id, revision_number)
        if revision is None:
            return None
        if revision.get("version_status") not in ("em_andamento", "substituido"):
            raise PluginsRepositoryError(
                "Só é possível implantar uma versão em andamento."
            )

        effective = self._normalize_date(effective_from) or date.today().isoformat()

        # Fecha a versão implantada vigente (se houver).
        self.execute(
            """
            UPDATE quality.kaizen_revisions
               SET version_status = 'substituido',
                   effective_until = %s
             WHERE kaizen_id = %s
               AND version_status = 'implantado'
            """,
            (effective, kaizen_id),
            auto_commit=False,
        )
        # Ativa a nova versão.
        self._set_version_status(
            str(revision["id"]), "implantado", effective_from=effective
        )
        self.execute(
            "UPDATE quality.kaizen_revisions SET effective_until = NULL WHERE id = %s",
            (str(revision["id"]),),
            auto_commit=False,
        )

        # Espelha a versão implantada no cabeçalho do kaizen.
        snapshot = dict(revision.get("snapshot") or {})
        self._apply_snapshot_to_head(
            kaizen_id,
            snapshot=snapshot,
            effective=effective,
            updated_by_user_id=updated_by_user_id,
        )

        self._append_history(
            kaizen_id,
            event_type="version_implemented",
            new_value=f"v{revision_number}",
            actor_user_id=updated_by_user_id,
            actor_name=actor_name,
        )
        self._append_audit_log(
            kaizen_id,
            event_type="version_implemented",
            payload={"revision": revision_number, "effective_from": effective},
            actor_user_id=updated_by_user_id,
            actor_name=actor_name,
        )
        self.commit()
        return self.get_record(kaizen_id)

    def _apply_snapshot_to_head(
        self,
        kaizen_id: str,
        *,
        snapshot: dict[str, Any],
        effective: str,
        updated_by_user_id: str,
    ) -> None:
        enriched = enrich_savings_fields({**snapshot})
        self.execute(
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
                   status = 'implantado',
                   date_implemented = %s,
                   notes = %s,
                   process_description = %s,
                   problem_description = %s,
                   improvement_description = %s,
                   expected_result = %s,
                   category = %s,
                   current_revision_number = current_revision_number + 1,
                   updated_by_user_id = %s,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
            """,
            (
                enriched.get("branch_code"),
                str(enriched.get("title") or "").strip(),
                enriched.get("accountable"),
                enriched.get("sector"),
                enriched.get("investment"),
                enriched.get("savings_type"),
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
                enriched.get("date_implemented") or effective,
                enriched.get("notes"),
                enriched.get("process_description"),
                enriched.get("problem_description"),
                enriched.get("improvement_description"),
                enriched.get("expected_result"),
                enriched.get("category"),
                updated_by_user_id,
                kaizen_id,
            ),
            auto_commit=False,
        )

    def delete_version(
        self,
        kaizen_id: str,
        revision_number: int,
        *,
        actor_user_id: str,
        actor_name: str | None = None,
    ) -> bool:
        """Exclui (hard delete) uma versão NÃO ativa. A versão implantada é protegida."""
        revision = self.get_revision(kaizen_id, revision_number)
        if revision is None:
            return False

        status = str(revision.get("version_status") or "implantado")
        if status == "implantado":
            raise PluginsRepositoryError(
                "Não é possível excluir a versão ativa (implantada). Implante outra versão antes."
            )

        revision_id = str(revision["id"])
        # Remove evidências desta versão para não reaparecerem como gerais (FK SET NULL).
        self.execute(
            """
            UPDATE quality.kaizen_evidences
               SET deleted_at = NOW()
             WHERE revision_id = %s
               AND deleted_at IS NULL
            """,
            (revision_id,),
            auto_commit=False,
        )
        self.execute(
            "DELETE FROM quality.kaizen_revisions WHERE id = %s",
            (revision_id,),
            auto_commit=False,
        )
        self._append_history(
            kaizen_id,
            event_type="version_deleted",
            old_value=f"v{revision_number}",
            actor_user_id=actor_user_id,
            actor_name=actor_name,
        )
        self._append_audit_log(
            kaizen_id,
            event_type="version_deleted",
            payload={"revision": revision_number, "version_status": status},
            actor_user_id=actor_user_id,
            actor_name=actor_name,
        )
        self.commit()
        return True

    def _store_version_participants(self, revision_id: str, participants_input: Any) -> None:
        """Placeholder: participantes por versão ficam no snapshot (accountable)."""
        # Participantes são derivados do snapshot da versão; sem tabela dedicada por versão.
        return None

    def delete_record(
        self,
        record_id: str,
        *,
        updated_by_user_id: str,
        actor_name: str | None = None,
    ) -> bool:
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
            auto_commit=False,
        )
        if row is None:
            self.rollback()
            return False
        self._append_history(
            record_id,
            event_type="kaizen_deleted",
            actor_user_id=updated_by_user_id,
            actor_name=actor_name,
        )
        self._append_audit_log(
            record_id,
            event_type="kaizen_deleted",
            actor_user_id=updated_by_user_id,
            actor_name=actor_name,
        )
        self.commit()
        return True
