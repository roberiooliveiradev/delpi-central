from __future__ import annotations

from app.infrastructure.persistence.portal_rh.portal_rh_base_repository import (
    PortalRhBaseRepository,
)


class HrMetricsRepository(PortalRhBaseRepository):
    def list_active_branches(self) -> list[str]:
        sql = """
            SELECT DISTINCT branch_code
            FROM users_userprofile
            WHERE branch_code IS NOT NULL
              AND branch_code <> ''
            ORDER BY branch_code
        """
        rows = self.fetch_all(sql)
        return [str(row["branch_code"]).strip() for row in rows if row.get("branch_code")]

    def get_absenteeism_snapshot(
        self,
        *,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        value = self._get_indicator_average_value(
            branch_code=branch_code,
            start_date=start_date,
            end_date=end_date,
            indicator_codes=["ABS_MOD", "ABS_MOI"],
        )

        return {
            "branch_code": branch_code,
            "total_absence_hours": float(value),
            "expected_hours": 100.0,
        }

    def get_turnover_snapshot(
        self,
        *,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        value = self._get_indicator_average_value(
            branch_code=branch_code,
            start_date=start_date,
            end_date=end_date,
            indicator_codes=["TUR_MOD", "TUR_MOI"],
        )

        return {
            "branch_code": branch_code,
            "admissions_count": 0.0,
            "terminations_count": float(value),
            "active_count": 100.0,
        }

    def get_training_hours_snapshot(
        self,
        *,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        value = self._get_indicator_average_value(
            branch_code=branch_code,
            start_date=start_date,
            end_date=end_date,
            indicator_codes=["TRN_MOD", "TRN_MOI"],
        )

        return {
            "branch_code": branch_code,
            "total_training_hours": float(value),
            "total_participations": 1.0,
        }

    def _get_indicator_average_value(
        self,
        *,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
        indicator_codes: list[str],
    ) -> float:
        sql = """
            WITH params AS (
                SELECT
                    CAST(%(branch_code)s AS varchar) AS branch_code,
                    TO_DATE(NULLIF(CAST(%(start_date)s AS text), ''), 'DD-MM-YYYY') AS start_date,
                    TO_DATE(NULLIF(CAST(%(end_date)s AS text), ''), 'DD-MM-YYYY') AS end_date
            ),
            filtered AS (
                SELECT
                    ma.actual_value
                FROM indicators_monthlyactual ma
                INNER JOIN indicators_indicator i
                    ON i.id = ma.indicator_id
                CROSS JOIN params p
                WHERE ma.branch_code = p.branch_code
                  AND i.active = TRUE
                  AND i.code = ANY(%(indicator_codes)s)
                  AND (
                        p.start_date IS NULL
                        OR make_date(ma.year, ma.month, 1) >= date_trunc('month', p.start_date)::date
                  )
                  AND (
                        p.end_date IS NULL
                        OR make_date(ma.year, ma.month, 1) <= date_trunc('month', p.end_date)::date
                  )
            )
            SELECT COALESCE(AVG(actual_value), 0) AS value
            FROM filtered
        """

        row = self.fetch_one(
            sql,
            {
                "branch_code": branch_code,
                "start_date": start_date,
                "end_date": end_date,
                "indicator_codes": indicator_codes,
            },
        )

        try:
            return round(float((row or {}).get("value") or 0.0), 2)
        except (TypeError, ValueError):
            return 0.0