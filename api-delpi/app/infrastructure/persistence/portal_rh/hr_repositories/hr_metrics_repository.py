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
        sql = """
            WITH params AS (
                SELECT
                    CAST(%(branch_code)s AS varchar) AS branch_code,
                    TO_DATE(NULLIF(CAST(%(start_date)s AS text), ''), 'DD-MM-YYYY') AS start_date,
                    TO_DATE(NULLIF(CAST(%(end_date)s AS text), ''), 'DD-MM-YYYY') AS end_date
            ),
            active_collaborators AS (
                SELECT
                    c.collaborator_id,
                    COALESCE(c.daily_expected_hours, 0) AS daily_expected_hours
                FROM colaboradores_collaboratorprofile c
                LEFT JOIN users_userprofile up
                  ON up.collaborator_id = c.collaborator_id
                CROSS JOIN params p
                WHERE up.branch_code = p.branch_code
                  AND c.admission_date IS NOT NULL
                  AND (
                        p.start_date IS NULL
                        OR c.termination_date IS NULL
                        OR c.termination_date >= p.start_date
                  )
            ),
            workdays AS (
                SELECT
                    w.date,
                    w.branch_code
                FROM assiduidade_workcalendarday w
                CROSS JOIN params p
                WHERE w.branch_code = p.branch_code
                  AND w.is_workday = TRUE
                  AND (p.start_date IS NULL OR w.date >= p.start_date)
                  AND (p.end_date IS NULL OR w.date <= p.end_date)
            ),
            absences AS (
                SELECT
                    ad.collaborator_id,
                    SUM(COALESCE(ad.absence_hours, 0)) AS total_absence_hours
                FROM assiduidade_absenceday ad
                JOIN assiduidade_absenceevent ae
                  ON ae.id = ad.absence_event_id
                CROSS JOIN params p
                WHERE ad.counts_for_absenteeism = TRUE
                  AND COALESCE(ae.is_cancelled, FALSE) = FALSE
                  AND ae.branch_code_snapshot = p.branch_code
                  AND (p.start_date IS NULL OR ad.date >= p.start_date)
                  AND (p.end_date IS NULL OR ad.date <= p.end_date)
                GROUP BY ad.collaborator_id
            )
            SELECT
                p.branch_code,
                COALESCE(SUM(a.total_absence_hours), 0) AS total_absence_hours,
                COALESCE(
                    ((SELECT COUNT(*) FROM workdays) * SUM(ac.daily_expected_hours)),
                    0
                ) AS expected_hours
            FROM active_collaborators ac
            LEFT JOIN absences a
              ON a.collaborator_id = ac.collaborator_id
            CROSS JOIN params p
            GROUP BY p.branch_code
        """
        return self.fetch_one(
            sql,
            {
                "branch_code": branch_code,
                "start_date": start_date,
                "end_date": end_date,
            },
        ) or {
            "branch_code": branch_code,
            "total_absence_hours": 0,
            "expected_hours": 0,
        }

    def get_turnover_snapshot(
        self,
        *,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        sql = """
            WITH params AS (
                SELECT
                    CAST(%(branch_code)s AS varchar) AS branch_code,
                    TO_DATE(NULLIF(CAST(%(start_date)s AS text), ''), 'DD-MM-YYYY') AS start_date,
                    TO_DATE(NULLIF(CAST(%(end_date)s AS text), ''), 'DD-MM-YYYY') AS end_date
            ),
            base AS (
                SELECT
                    up.branch_code,
                    c.admission_date,
                    c.termination_date
                FROM colaboradores_collaboratorprofile c
                LEFT JOIN users_userprofile up
                  ON up.collaborator_id = c.collaborator_id
                CROSS JOIN params p
                WHERE up.branch_code = p.branch_code
            )
            SELECT
                p.branch_code,
                (
                    SELECT COUNT(*)
                    FROM base
                    WHERE admission_date IS NOT NULL
                      AND admission_date <= COALESCE(p.end_date, CURRENT_DATE)
                      AND (
                            termination_date IS NULL
                            OR termination_date > COALESCE(p.end_date, CURRENT_DATE)
                      )
                ) AS active_count,
                (
                    SELECT COUNT(*)
                    FROM base
                    WHERE admission_date IS NOT NULL
                      AND (p.start_date IS NULL OR admission_date >= p.start_date)
                      AND (p.end_date IS NULL OR admission_date <= p.end_date)
                ) AS admissions_count,
                (
                    SELECT COUNT(*)
                    FROM base
                    WHERE termination_date IS NOT NULL
                      AND (p.start_date IS NULL OR termination_date >= p.start_date)
                      AND (p.end_date IS NULL OR termination_date <= p.end_date)
                ) AS terminations_count
            FROM params p
        """
        return self.fetch_one(
            sql,
            {
                "branch_code": branch_code,
                "start_date": start_date,
                "end_date": end_date,
            },
        ) or {
            "branch_code": branch_code,
            "admissions_count": 0,
            "terminations_count": 0,
            "active_count": 0,
        }

    def get_training_hours_snapshot(
        self,
        *,
        branch_code: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        sql = """
            WITH params AS (
                SELECT
                    CAST(%(branch_code)s AS varchar) AS branch_code,
                    TO_DATE(NULLIF(CAST(%(start_date)s AS text), ''), 'DD-MM-YYYY') AS start_date,
                    TO_DATE(NULLIF(CAST(%(end_date)s AS text), ''), 'DD-MM-YYYY') AS end_date
            ),
            sessions AS (
                SELECT
                    s.id,
                    s.branch_code,
                    COALESCE(s.realized_workload_hours, 0) AS realized_workload_hours,
                    s.session_date
                FROM capacitacao_trainingsession s
                CROSS JOIN params p
                WHERE s.branch_code = p.branch_code
                  AND (p.start_date IS NULL OR s.session_date >= p.start_date)
                  AND (p.end_date IS NULL OR s.session_date <= p.end_date)
            ),
            participants AS (
                SELECT
                    tp.session_id,
                    COUNT(*) AS participants_count
                FROM capacitacao_trainingparticipant tp
                GROUP BY tp.session_id
            )
            SELECT
                p.branch_code,
                COALESCE(SUM(s.realized_workload_hours), 0) AS total_training_hours,
                COALESCE(SUM(p2.participants_count), 0) AS total_participations
            FROM params p
            LEFT JOIN sessions s
              ON s.branch_code = p.branch_code
            LEFT JOIN participants p2
              ON p2.session_id = s.id
            GROUP BY p.branch_code
        """
        return self.fetch_one(
            sql,
            {
                "branch_code": branch_code,
                "start_date": start_date,
                "end_date": end_date,
            },
        ) or {
            "branch_code": branch_code,
            "total_training_hours": 0,
            "total_participations": 0,
        }