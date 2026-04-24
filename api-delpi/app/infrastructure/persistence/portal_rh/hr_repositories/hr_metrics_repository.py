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

    def get_internal_satisfaction_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        result = self._get_indicator_average_or_latest_value(
            start_date=start_date,
            end_date=end_date,
            indicator_codes=["SAT_INT"],
            fallback_to_latest_before_end=True,
        )

        return {
            "indicator_code": "SAT_INT",
            "value": result.get("value"),
            "measurement_date": result.get("measurement_date"),
            "effective_date": result.get("effective_date"),
            "used_fallback": result.get("used_fallback", False),
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

    def _get_indicator_average_or_latest_value(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        indicator_codes: list[str],
        fallback_to_latest_before_end: bool = False,
    ) -> dict:
        exact_sql = """
            WITH params AS (
                SELECT
                    TO_DATE(NULLIF(CAST(%(start_date)s AS text), ''), 'DD-MM-YYYY') AS start_date,
                    TO_DATE(NULLIF(CAST(%(end_date)s AS text), ''), 'DD-MM-YYYY') AS end_date
            ),
            filtered AS (
                SELECT
                    ma.actual_value,
                    make_date(ma.year, ma.month, 1) AS measurement_date
                FROM indicators_monthlyactual ma
                INNER JOIN indicators_indicator i
                    ON i.id = ma.indicator_id
                CROSS JOIN params p
                WHERE i.active = TRUE
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
            SELECT
                AVG(actual_value) AS value,
                MAX(measurement_date) AS measurement_date
            FROM filtered
        """

        row = self.fetch_one(
            exact_sql,
            {
                "start_date": start_date,
                "end_date": end_date,
                "indicator_codes": indicator_codes,
            },
        )

        exact_value = self._safe_round((row or {}).get("value"))
        if exact_value is not None:
            return {
                "value": exact_value,
                "measurement_date": (row or {}).get("measurement_date"),
                "effective_date": end_date or start_date,
                "used_fallback": False,
            }

        if not fallback_to_latest_before_end:
            return {
                "value": None,
                "measurement_date": None,
                "effective_date": end_date or start_date,
                "used_fallback": False,
            }

        fallback_sql = """
            WITH params AS (
                SELECT
                    COALESCE(
                        TO_DATE(NULLIF(CAST(%(end_date)s AS text), ''), 'DD-MM-YYYY'),
                        TO_DATE(NULLIF(CAST(%(start_date)s AS text), ''), 'DD-MM-YYYY'),
                        CURRENT_DATE
                    ) AS reference_date
            )
            SELECT
                ma.actual_value AS value,
                make_date(ma.year, ma.month, 1) AS measurement_date
            FROM indicators_monthlyactual ma
            INNER JOIN indicators_indicator i
                ON i.id = ma.indicator_id
            CROSS JOIN params p
            WHERE i.active = TRUE
              AND i.code = ANY(%(indicator_codes)s)
              AND make_date(ma.year, ma.month, 1) <= date_trunc('month', p.reference_date)::date
            ORDER BY ma.year DESC, ma.month DESC
            LIMIT 1
        """

        fallback_row = self.fetch_one(
            fallback_sql,
            {
                "start_date": start_date,
                "end_date": end_date,
                "indicator_codes": indicator_codes,
            },
        )

        return {
            "value": self._safe_round((fallback_row or {}).get("value")),
            "measurement_date": (fallback_row or {}).get("measurement_date"),
            "effective_date": end_date or start_date,
            "used_fallback": True,
        }

    def _safe_round(self, value) -> float | None:
        if value is None:
            return None

        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return None