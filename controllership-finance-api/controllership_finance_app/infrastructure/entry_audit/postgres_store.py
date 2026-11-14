"""Persistência da V023. O status da ocorrência não é apagado na reexecução."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from psycopg.rows import dict_row
from psycopg.types.json import Json

from controllership_finance_app.application.entry_audit.vocabulary import FIELD_LABELS
from controllership_finance_app.infrastructure.persistence.plugins_db import plugins_db_connect

SCHEMA = "controllership_finance"


class PostgresEntryAuditStore:
    def find_open(self, date_from: date, date_to: date, document_types: list[str], branches: list[str]) -> dict | None:
        return self._one(
            f"""
            SELECT * FROM {SCHEMA}.entry_audit_analysis
             WHERE status IN ('queued', 'running')
               AND date_from = %s AND date_to = %s
               AND document_types = %s AND branches = %s
            """,
            (date_from, date_to, document_types, branches),
        )

    def insert_analysis(self, record: dict) -> dict:
        try:
            return self._one(
                f"""
                INSERT INTO {SCHEMA}.entry_audit_analysis (
                    date_from, date_to, document_types, branches, config_snapshot,
                    status, requested_by_user_id, requested_by_name, requested_via
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    record["date_from"],
                    record["date_to"],
                    record["document_types"],
                    record["branches"],
                    Json(record["config_snapshot"]),
                    record["status"],
                    record["requested_by_user_id"],
                    record["requested_by_name"],
                    record["requested_via"],
                ),
            )
        except Exception as exc:
            if exc.__class__.__name__ != "UniqueViolation":
                raise
            found = self.find_open(record["date_from"], record["date_to"], record["document_types"], record["branches"])
            if found is None:
                raise
            return found

    def insert_runs(self, analysis_id: str, branches: list[str]) -> list[dict]:
        created = []
        for branch in branches:
            created.append(self._one(
                f"""
                INSERT INTO {SCHEMA}.entry_audit_run (analysis_id, branch_code, status)
                VALUES (%s, %s, 'queued')
                RETURNING *
                """,
                (analysis_id, branch),
            ))
        return created

    def get_analysis(self, analysis_id: str) -> dict | None:
        return self._one(f"SELECT * FROM {SCHEMA}.entry_audit_analysis WHERE id = %s", (analysis_id,))

    def list_analyses(self, *, date_from, date_to, branch, status, page, page_size) -> tuple[list[dict], int]:
        clauses = ["TRUE"]
        params: list = []
        if date_from:
            clauses.append("date_to >= %s")
            params.append(date_from)
        if date_to:
            clauses.append("date_from <= %s")
            params.append(date_to)
        if branch:
            clauses.append("%s = ANY(branches)")
            params.append(branch)
        if status:
            clauses.append("status = %s")
            params.append(status)
        where = " AND ".join(clauses)
        total = self._one(f"SELECT COUNT(*) AS total FROM {SCHEMA}.entry_audit_analysis WHERE {where}", tuple(params))
        rows = self._all(
            f"""
            SELECT * FROM {SCHEMA}.entry_audit_analysis
             WHERE {where}
             ORDER BY created_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple(params + [page_size, (page - 1) * page_size]),
        )
        return rows, int((total or {}).get("total") or 0)

    def runs_of(self, analysis_id: str) -> list[dict]:
        return self._all(
            f"SELECT * FROM {SCHEMA}.entry_audit_run WHERE analysis_id = %s ORDER BY branch_code",
            (analysis_id,),
        )

    def requeue_running(self) -> int:
        rows = self._all(
            f"""
            UPDATE {SCHEMA}.entry_audit_run
               SET status = 'queued', stage = '', started_at = NULL
             WHERE status = 'running'
            RETURNING analysis_id
            """,
            (),
        )
        for row in rows:
            self._refresh(row["analysis_id"])
        return len(rows)

    def claim_next_queued(self) -> dict | None:
        claimed = self._one(
            f"""
            WITH next_run AS (
                SELECT id FROM {SCHEMA}.entry_audit_run
                 WHERE status = 'queued'
                 ORDER BY id
                 FOR UPDATE SKIP LOCKED
                 LIMIT 1
            )
            UPDATE {SCHEMA}.entry_audit_run AS run
               SET status = 'running', stage = 'reading', started_at = now()
              FROM next_run
             WHERE run.id = next_run.id
            RETURNING run.*
            """,
            (),
        )
        if claimed:
            self._refresh(claimed["analysis_id"])
        return claimed

    def mark_run(self, run_id: str, **fields) -> None:
        allowed = {
            "status", "stage", "documents_read", "xml_downloaded", "counts",
            "engine_version", "sources_hash", "error_message",
        }
        assignments = []
        params = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            assignments.append(f"{key} = %s")
            params.append(Json(value) if key == "counts" else value)
        if fields.get("status") in {"done", "failed"}:
            assignments.append("finished_at = now()")
        if not assignments:
            return
        params.append(run_id)
        updated = self._one(
            f"UPDATE {SCHEMA}.entry_audit_run SET {', '.join(assignments)} WHERE id = %s RETURNING analysis_id",
            tuple(params),
        )
        if updated:
            self._refresh(updated["analysis_id"])

    def clear_output(self, run_id: str) -> None:
        for table in (
            "entry_audit_document",
            "entry_audit_occurrence",
            "entry_audit_unmatched",
            "entry_audit_cte",
            "entry_audit_tes_used",
        ):
            self._execute(f"DELETE FROM {SCHEMA}.{table} WHERE run_id = %s", (run_id,))

    def replace_output(self, run_id: str, *, documents, occurrences, unmatched, ctes, tes_used) -> None:
        self.clear_output(run_id)
        for row in documents:
            comparison = dict(row.get("comparison") or {})
            comparison["document_type"] = row.get("document_type") or ""
            self._execute(
                f"""
                INSERT INTO {SCHEMA}.entry_audit_document (
                    run_id, access_key, branch_code, document_number, series,
                    supplier_code, supplier_store, supplier_name, issue_date, received_date,
                    situation, divergence_count, comparison
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id, row.get("access_key") or "", row.get("branch") or "", row.get("document_number") or "",
                    row.get("series") or "", row.get("supplier_code") or "", row.get("supplier_store") or "",
                    row.get("supplier_name") or "", _day(row.get("issue_date")), _day(row.get("received_date")),
                    row.get("situation") or "", int(row.get("divergence_count") or 0), Json(comparison),
                ),
            )
        for row in occurrences:
            self._execute(
                f"""
                INSERT INTO {SCHEMA}.entry_audit_occurrence (
                    run_id, analysis_id, stable_key, rule_id, severity, theme, title,
                    document_number, series, supplier_name, item, field, protheus_value,
                    xml_value, difference, tes, why, action, access_key
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id, row["analysis_id"], row["stable_key"], row["rule_id"], row["severity"],
                    row.get("theme") or "", row.get("title") or "", row.get("document_number") or "",
                    row.get("series") or "", row.get("supplier_name") or "", row.get("item") or "",
                    row.get("field") or "", row.get("protheus_value") or "", row.get("xml_value") or "",
                    row.get("difference") or "", row.get("tes") or "", row.get("why") or "",
                    row.get("action") or "", row.get("access_key") or "",
                ),
            )
        for row in unmatched:
            self._execute(
                f"""
                INSERT INTO {SCHEMA}.entry_audit_unmatched (
                    run_id, analysis_id, stable_key, side, rule_id, severity, reason, situation,
                    lnf_request_id, lnf_status, access_key, document_number, series, party_name,
                    issue_date, amount
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id, row["analysis_id"], row["stable_key"], row["side"], row["rule_id"],
                    row.get("severity") or "", row.get("reason") or "", row.get("situation") or "",
                    row.get("lnf_request_id") or "", row.get("lnf_status") or "", row.get("access_key") or "",
                    row.get("document_number") or "", row.get("series") or "", row.get("party_name") or "",
                    _day(row.get("issue_date")), None,
                ),
            )
        for row in ctes:
            comparison = dict(row.get("comparison") or {})
            comparison["document_type"] = "cte"
            comparison["document_number"] = row.get("document_number") or ""
            self._execute(
                f"INSERT INTO {SCHEMA}.entry_audit_cte (run_id, access_key, comparison) VALUES (%s, %s, %s)",
                (run_id, row.get("access_key") or "", Json(comparison)),
            )
        for row in tes_used:
            sf4 = dict(row.get("sf4") or {})
            sf4["document_type"] = row.get("document_type") or "nfe"
            self._execute(
                f"""
                INSERT INTO {SCHEMA}.entry_audit_tes_used (run_id, tes_code, sf4)
                VALUES (%s, %s, %s)
                ON CONFLICT (run_id, tes_code) DO UPDATE SET sf4 = EXCLUDED.sf4
                """,
                (run_id, row.get("tes_code") or "", Json(sf4)),
            )

    def get_run(self, run_id: str) -> dict | None:
        return self._one(f"SELECT * FROM {SCHEMA}.entry_audit_run WHERE id = %s", (run_id,))

    def runs_for_branches(self, analysis_id: str, branches: list[str]) -> list[dict]:
        return self._all(
            f"SELECT * FROM {SCHEMA}.entry_audit_run WHERE analysis_id = %s AND branch_code = ANY(%s)",
            (analysis_id, branches),
        )

    def queue_run(self, run_id: str) -> None:
        updated = self._one(
            f"""
            UPDATE {SCHEMA}.entry_audit_run
               SET status = 'queued', stage = '', error_message = '', started_at = NULL, finished_at = NULL
             WHERE id = %s
            RETURNING analysis_id
            """,
            (run_id,),
        )
        if updated:
            self._refresh(updated["analysis_id"])

    def status_of(self, stable_key: str) -> dict | None:
        return self._one(f"SELECT * FROM {SCHEMA}.entry_audit_status WHERE stable_key = %s", (stable_key,))

    def upsert_status(self, stable_key: str, *, kind: str, status: str, user_id: str, user_name: str) -> dict:
        return self._one(
            f"""
            INSERT INTO {SCHEMA}.entry_audit_status (
                stable_key, kind, status, resolved_by_user_id, resolved_by_name, resolved_at, reopened_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                CASE WHEN %s = 'resolved' THEN now() ELSE NULL END,
                CASE WHEN %s = 'pending' THEN now() ELSE NULL END
            )
            ON CONFLICT (stable_key) DO UPDATE SET
                kind = EXCLUDED.kind,
                status = EXCLUDED.status,
                resolved_by_user_id = CASE WHEN EXCLUDED.status = 'resolved' THEN EXCLUDED.resolved_by_user_id ELSE {SCHEMA}.entry_audit_status.resolved_by_user_id END,
                resolved_by_name = CASE WHEN EXCLUDED.status = 'resolved' THEN EXCLUDED.resolved_by_name ELSE {SCHEMA}.entry_audit_status.resolved_by_name END,
                resolved_at = CASE WHEN EXCLUDED.status = 'resolved' THEN now() ELSE {SCHEMA}.entry_audit_status.resolved_at END,
                reopened_at = CASE WHEN EXCLUDED.status = 'pending' THEN now() ELSE {SCHEMA}.entry_audit_status.reopened_at END,
                updated_at = now()
            RETURNING *
            """,
            (stable_key, kind, status, user_id, user_name, status, status),
        )

    def rows(self, kind: str, analysis_id: str) -> list[dict]:
        if kind == "documents":
            found = self._all(
                f"""
                SELECT d.*, d.branch_code AS branch, r.analysis_id
                  FROM {SCHEMA}.entry_audit_document d
                  JOIN {SCHEMA}.entry_audit_run r ON r.id = d.run_id
                 WHERE r.analysis_id = %s
                """,
                (analysis_id,),
            )
            for row in found:
                row["document_type"] = (row.get("comparison") or {}).get("document_type") or "nfe"
                row["received_date"] = _iso(row.get("received_date"))
                row["issue_date"] = _iso(row.get("issue_date"))
            return found
        if kind == "occurrences":
            found = self._all(
                f"""
                SELECT o.*, r.branch_code AS branch, d.received_date
                  FROM {SCHEMA}.entry_audit_occurrence o
                  JOIN {SCHEMA}.entry_audit_run r ON r.id = o.run_id
                  LEFT JOIN {SCHEMA}.entry_audit_document d
                    ON d.run_id = o.run_id AND d.document_number = o.document_number
                 WHERE o.analysis_id = %s
                """,
                (analysis_id,),
            )
            for row in found:
                row["field_label"] = FIELD_LABELS.get(row.get("field") or "", row.get("field") or "")
                row["document_type"] = "cte" if str(row.get("rule_id") or "").startswith("cte.") else "nfe"
                row["received_date"] = _iso(row.get("received_date"))
            return found
        if kind == "unmatched":
            found = self._all(
                f"""
                SELECT u.*, r.branch_code AS branch
                  FROM {SCHEMA}.entry_audit_unmatched u
                  JOIN {SCHEMA}.entry_audit_run r ON r.id = u.run_id
                 WHERE u.analysis_id = %s
                """,
                (analysis_id,),
            )
            for row in found:
                row["title"] = row.get("reason") or ""
                row["supplier_name"] = row.get("party_name") or ""
                row["theme"] = "unmatched"
                row["field"] = "key"
                row["document_type"] = "cte" if str(row.get("access_key") or "")[20:22] == "57" else "nfe"
                row["issue_date"] = _iso(row.get("issue_date"))
            return found
        if kind == "ctes":
            found = self._all(
                f"""
                SELECT c.*, r.branch_code AS branch, r.analysis_id
                  FROM {SCHEMA}.entry_audit_cte c
                  JOIN {SCHEMA}.entry_audit_run r ON r.id = c.run_id
                 WHERE r.analysis_id = %s
                """,
                (analysis_id,),
            )
            for row in found:
                comparison = row.get("comparison") or {}
                row["document_type"] = "cte"
                row["document_number"] = comparison.get("document_number") or ""
            return found
        found = self._all(
            f"""
            SELECT t.*, r.branch_code AS branch, r.analysis_id
              FROM {SCHEMA}.entry_audit_tes_used t
              JOIN {SCHEMA}.entry_audit_run r ON r.id = t.run_id
             WHERE r.analysis_id = %s
            """,
            (analysis_id,),
        )
        for row in found:
            row["document_type"] = (row.get("sf4") or {}).get("document_type") or "nfe"
        return found

    def _refresh(self, analysis_id: str) -> None:
        runs = self.runs_of(str(analysis_id))
        statuses = {run["status"] for run in runs}
        if "running" in statuses:
            status, finished = "running", None
        elif "queued" in statuses:
            status, finished = "queued", None
        elif statuses == {"failed"}:
            status, finished = "failed", "now"
        elif "done" in statuses:
            status, finished = "done", "now"
        else:
            return
        if finished == "now":
            self._execute(
                f"UPDATE {SCHEMA}.entry_audit_analysis SET status = %s, finished_at = now(), updated_at = now() WHERE id = %s",
                (status, str(analysis_id)),
            )
        else:
            self._execute(
                f"UPDATE {SCHEMA}.entry_audit_analysis SET status = %s, finished_at = NULL, updated_at = now() WHERE id = %s",
                (status, str(analysis_id)),
            )

    def _one(self, sql: str, params: tuple) -> dict | None:
        rows = self._all(sql, params)
        return rows[0] if rows else None

    def _all(self, sql: str, params: tuple) -> list[dict]:
        with plugins_db_connect() as connection:
            connection.row_factory = dict_row
            rows = connection.execute(sql, params).fetchall()
        return [_public(row) for row in rows]

    def _execute(self, sql: str, params: tuple) -> None:
        with plugins_db_connect() as connection:
            connection.execute(sql, params)


def _public(row: dict) -> dict:
    public = {}
    for key, value in dict(row).items():
        if isinstance(value, UUID):
            public[key] = str(value)
        elif isinstance(value, datetime):
            public[key] = value
        else:
            public[key] = value
    if "branch_code" in public and "branch" not in public:
        public["branch"] = public["branch_code"]
    return public


def _day(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-":
        return date.fromisoformat(text[:10])
    return None


def _iso(value) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value or "")
