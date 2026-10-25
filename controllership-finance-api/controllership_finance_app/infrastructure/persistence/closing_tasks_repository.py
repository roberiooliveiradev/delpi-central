"""TaskProjection self-only (doc 27 / RQ-TASK-01..07).

Composição on-read a partir dos owners P4/P5 — nunca TaskEntity
paralela, nunca estado de negócio copiado, nunca SLA inventado.
Regra geral:

```text
owner context exists
AND owner state requires a human action
AND responsibility is explicitly attributable to current user
AND actor can access resource
→ TaskProjection
```

`PENDING != MY_TASK`, `BLOCKER != MY_TASK`, `MENTION != MY_TASK`.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CompetenceNotOpened,
    PersistenceUnavailable,
)
from controllership_finance_app.infrastructure.persistence.closing_catalog_repository import (
    ClosingCatalogRepository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME

OPEN_PENDENCY_STATES = ("OPEN", "IN_ANALYSIS", "WAITING_EXTERNAL")
MFE_BASE = "/apps/controllership-finance"


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


def _context(period: str) -> dict[str, Any]:
    return {
        "contextType": "competence",
        "contextId": period,
        "contextLabel": f"Competência {period}",
        "competence": period,
    }


class ClosingTasksRepository:
    """Projeções self-only do usuário autenticado."""

    def _conn(self) -> psycopg.Connection:
        if not plugins_db_configured():
            raise PersistenceUnavailable(
                "Persistência do workflow não configurada."
            )
        try:
            return plugins_db_connect()
        except psycopg.Error as exc:
            raise PersistenceUnavailable(
                "Persistência do workflow indisponível."
            ) from exc

    def list_my_tasks(
        self,
        *,
        subject: str,
        user_groups: Any = (),
        period: str | None = None,
    ) -> dict[str, Any]:
        """Worklist self-only do `subject` — producers P4 + P5.

        `user_groups` alimenta o binding REVIEW_ELIGIBILITY quando
        configurado (fail-closed: binding existe e não casa → tarefa
        não é projetada para este usuário).
        """
        tasks: list[dict[str, Any]] = []
        catalog = ClosingCatalogRepository()
        groups = set(user_groups or ())
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            params: list[Any] = [subject]
            period_sql = ""
            if period:
                period_sql = " AND mc.period = %s"
                params.append(period)

            # -- P4: pendências abertas sob responsabilidade do usuário ------
            cur.execute(
                f"""
                SELECT p.pendency_id, p.title, p.state, p.kind,
                       p.created_at, mc.period
                  FROM {_q('closing_pendency')} p
                  JOIN {_q('monthly_competence')} mc
                    ON mc.competence_id = p.competence_id
                 WHERE p.responsible_subject = %s
                   AND p.state = ANY(%s)
                   {period_sql}
                 ORDER BY p.created_at
                """,
                (subject, list(OPEN_PENDENCY_STATES), *params[1:]),
            )
            for row in cur.fetchall():
                per = row["period"]
                tasks.append(
                    {
                        "id": f"p4:{row['pendency_id']}",
                        "sourceType": "PENDENCY",
                        "sourceId": str(row["pendency_id"]),
                        "actionKind": "PENDENCY_ACTION_REQUIRED",
                        "title": row["title"],
                        "ownerPage": "pendencies",
                        "ownerState": row["state"],
                        "statusLabel": row["state"],
                        "assigneeUserId": subject,
                        "context": _context(per),
                        "pendingSince": row["created_at"],
                        "sourceStatus": row["state"],
                        "deepLink": (
                            f"{MFE_BASE}/closing/pendencies"
                            f"?period={per}"
                        ),
                    }
                )

            # -- P5: áreas obrigatórias pendentes de aceite -------------------
            # assignment ativo do usuário + versão vigente SUBMITTED +
            # required_area sem decisão ACCEPTED nesta versão.
            cur.execute(
                f"""
                SELECT v.package_version_id, v.package_id, v.version_no,
                       p.recipient_area, mc.period, a.area,
                       a.assignment_id
                  FROM {_q('closing_review_assignment')} a
                  JOIN {_q('closing_package')} p
                    ON p.package_id = a.package_id
                  JOIN {_q('monthly_competence')} mc
                    ON mc.competence_id = p.competence_id
                  JOIN LATERAL (
                      SELECT package_version_id, package_id, version_no,
                             required_areas
                        FROM {_q('closing_package_version')}
                       WHERE package_id = p.package_id
                       ORDER BY version_no DESC
                       LIMIT 1
                  ) v ON true
                 WHERE a.subject = %s::uuid
                   AND a.role = 'REVIEWER'
                   AND a.active
                   AND v.package_version_id IS NOT NULL
                   AND NOT EXISTS (
                       SELECT 1
                         FROM {_q('closing_terminal_rejection')} r
                        WHERE r.competence_id = p.competence_id
                          AND r.state = 'ACTIVE'
                   )
                   {period_sql}
                """,
                params,
            )
            assignments = cur.fetchall()
            for a in assignments:
                per = a["period"]
                # versão vigente precisa estar SUBMITTED
                cur.execute(
                    f"""
                    SELECT status, required_areas
                      FROM {_q('closing_package_version')}
                     WHERE package_version_id = %s
                    """,
                    (a["package_version_id"],),
                )
                ver = cur.fetchone()
                if ver is None or ver["status"] != "SUBMITTED":
                    continue
                required = ver["required_areas"] or []
                if a["area"] not in required:
                    continue
                # área já aceita nesta versão → sem tarefa
                cur.execute(
                    f"""
                    SELECT outcome
                      FROM {_q('closing_review_decision')}
                     WHERE package_version_id = %s AND area = %s
                     ORDER BY created_at DESC, decision_id DESC
                     LIMIT 1
                    """,
                    (a["package_version_id"], a["area"]),
                )
                last = cur.fetchone()
                if last and last["outcome"] == "ACCEPTED":
                    continue
                # binding de elegibilidade configurado → fail-closed
                binding = catalog.eligibility_groups_for(a["area"])
                if binding and not (groups & binding):
                    continue
                tasks.append(
                    {
                        "id": (
                            f"p5:{a['package_version_id']}:{a['area']}"
                        ),
                        "sourceType": "PACKAGE",
                        "sourceId": str(a["package_version_id"]),
                        "actionKind": "PACKAGE_REVIEW_REQUIRED",
                        "title": (
                            f"Revisar pacote {a['recipient_area']} "
                            f"(área {a['area']})"
                        ),
                        "ownerPage": "packages",
                        "ownerState": "SUBMITTED",
                        "statusLabel": "PENDING_AREA_ACCEPTANCE",
                        "assigneeUserId": subject,
                        "context": _context(per),
                        "sourceStatus": "SUBMITTED",
                        "deepLink": (
                            f"{MFE_BASE}/closing/packages/{per}"
                        ),
                    }
                )

            # -- P5: clarifications abertas em versões que o usuário
            # submeteu — resposta pertence a quem submeteu o pacote.
            cur.execute(
                f"""
                SELECT c.clarification_id, c.opened_at, v.package_version_id,
                       v.submitted_by, p.recipient_area, mc.period
                  FROM {_q('closing_clarification')} c
                  JOIN {_q('closing_package_version')} v
                    ON v.package_version_id = c.package_version_id
                  JOIN {_q('closing_package')} p
                    ON p.package_id = v.package_id
                  JOIN {_q('monthly_competence')} mc
                    ON mc.competence_id = p.competence_id
                 WHERE c.state = 'OPEN'
                   AND v.submitted_by = %s::uuid
                   AND NOT EXISTS (
                       SELECT 1
                         FROM {_q('closing_terminal_rejection')} r
                        WHERE r.competence_id = p.competence_id
                          AND r.state = 'ACTIVE'
                   )
                   {period_sql}
                """,
                params,
            )
            for row in cur.fetchall():
                per = row["period"]
                tasks.append(
                    {
                        "id": f"p5c:{row['clarification_id']}",
                        "sourceType": "PACKAGE",
                        "sourceId": str(row["clarification_id"]),
                        "actionKind": "PACKAGE_CLARIFICATION_REQUIRED",
                        "title": (
                            f"Responder esclarecimento do pacote "
                            f"{row['recipient_area']}"
                        ),
                        "ownerPage": "packages",
                        "ownerState": "CLARIFICATION_OPEN",
                        "statusLabel": "CLARIFICATION_OPEN",
                        "assigneeUserId": subject,
                        "context": _context(per),
                        "pendingSince": row["opened_at"],
                        "sourceStatus": "OPEN",
                        "deepLink": (
                            f"{MFE_BASE}/closing/packages/{per}"
                        ),
                    }
                )

        return {
            "items": tasks,
            "total": len(tasks),
            "source": "controllership-finance-api",
            "selfOnly": True,
        }
