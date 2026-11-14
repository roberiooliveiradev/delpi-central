"""Repositório em memória. Os testes da T5 usam este store; o Postgres é o de runtime."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from uuid import uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryEntryAuditStore:
    def __init__(self) -> None:
        self.analyses: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.documents: list[dict] = []
        self.occurrences: list[dict] = []
        self.unmatched: list[dict] = []
        self.ctes: list[dict] = []
        self.tes_used: list[dict] = []
        self.statuses: dict[str, dict] = {}

    def find_open(self, date_from: date, date_to: date, document_types: list[str], branches: list[str]) -> dict | None:
        for analysis in self.analyses.values():
            if analysis["status"] not in {"queued", "running"}:
                continue
            if (
                analysis["date_from"] == date_from
                and analysis["date_to"] == date_to
                and analysis["document_types"] == document_types
                and analysis["branches"] == branches
            ):
                return deepcopy(analysis)
        return None

    def insert_analysis(self, record: dict) -> dict:
        analysis_id = str(uuid4())
        stored = {
            **record,
            "id": analysis_id,
            "created_at": _now(),
            "updated_at": _now(),
            "finished_at": None,
        }
        self.analyses[analysis_id] = stored
        return deepcopy(stored)

    def insert_runs(self, analysis_id: str, branches: list[str]) -> list[dict]:
        created = []
        for branch in branches:
            run = {
                "id": str(uuid4()),
                "analysis_id": analysis_id,
                "branch_code": branch,
                "status": "queued",
                "stage": "",
                "documents_read": 0,
                "xml_downloaded": 0,
                "counts": {},
                "engine_version": "",
                "sources_hash": "",
                "error_message": "",
                "started_at": None,
                "finished_at": None,
            }
            self.runs[run["id"]] = run
            created.append(deepcopy(run))
        return created

    def get_analysis(self, analysis_id: str) -> dict | None:
        found = self.analyses.get(analysis_id)
        return deepcopy(found) if found else None

    def list_analyses(self, *, date_from, date_to, branch, status, page, page_size) -> tuple[list[dict], int]:
        rows = list(self.analyses.values())
        if date_from:
            rows = [row for row in rows if row["date_to"] >= date_from]
        if date_to:
            rows = [row for row in rows if row["date_from"] <= date_to]
        if branch:
            rows = [row for row in rows if branch in row["branches"]]
        if status:
            rows = [row for row in rows if row["status"] == status]
        rows.sort(key=lambda row: row["created_at"], reverse=True)
        start = (page - 1) * page_size
        return [deepcopy(row) for row in rows[start : start + page_size]], len(rows)

    def runs_of(self, analysis_id: str) -> list[dict]:
        rows = [row for row in self.runs.values() if row["analysis_id"] == analysis_id]
        return [deepcopy(row) for row in sorted(rows, key=lambda row: row["branch_code"])]

    def requeue_running(self) -> int:
        changed = 0
        for run in self.runs.values():
            if run["status"] == "running":
                run["status"] = "queued"
                run["stage"] = ""
                run["started_at"] = None
                changed += 1
                self._refresh(run["analysis_id"])
        return changed

    def claim_next_queued(self) -> dict | None:
        queued = [run for run in self.runs.values() if run["status"] == "queued"]
        if not queued:
            return None
        queued.sort(key=lambda row: row["id"])
        run = queued[0]
        run["status"] = "running"
        run["stage"] = "reading"
        run["started_at"] = _now()
        self._refresh(run["analysis_id"])
        return deepcopy(run)

    def mark_run(self, run_id: str, **fields) -> None:
        run = self.runs[run_id]
        run.update(fields)
        if fields.get("status") in {"done", "failed"}:
            run["finished_at"] = _now()
        self._refresh(run["analysis_id"])

    def clear_output(self, run_id: str) -> None:
        self.documents = [row for row in self.documents if row["run_id"] != run_id]
        self.occurrences = [row for row in self.occurrences if row["run_id"] != run_id]
        self.unmatched = [row for row in self.unmatched if row["run_id"] != run_id]
        self.ctes = [row for row in self.ctes if row["run_id"] != run_id]
        self.tes_used = [row for row in self.tes_used if row["run_id"] != run_id]

    def replace_output(self, run_id: str, *, documents, occurrences, unmatched, ctes, tes_used) -> None:
        self.clear_output(run_id)
        self.documents.extend(documents)
        self.occurrences.extend(occurrences)
        self.unmatched.extend(unmatched)
        self.ctes.extend(ctes)
        self.tes_used.extend(tes_used)

    def get_run(self, run_id: str) -> dict | None:
        found = self.runs.get(run_id)
        return deepcopy(found) if found else None

    def runs_for_branches(self, analysis_id: str, branches: list[str]) -> list[dict]:
        return [
            deepcopy(run)
            for run in self.runs.values()
            if run["analysis_id"] == analysis_id and run["branch_code"] in branches
        ]

    def note_requester(self, analysis_id: str, *, user_id: str, user_name: str, via: str) -> None:
        analysis = self.analyses[analysis_id]
        analysis["requested_by_user_id"] = user_id
        analysis["requested_by_name"] = user_name
        analysis["requested_via"] = via
        analysis["updated_at"] = _now()

    def queue_run(self, run_id: str) -> None:
        run = self.runs[run_id]
        run["status"] = "queued"
        run["stage"] = ""
        run["error_message"] = ""
        run["started_at"] = None
        run["finished_at"] = None
        self._refresh(run["analysis_id"])

    def has_stable_key(self, stable_key: str) -> bool:
        return any(row["stable_key"] == stable_key for row in (*self.occurrences, *self.unmatched))

    def status_of(self, stable_key: str) -> dict | None:
        found = self.statuses.get(stable_key)
        return deepcopy(found) if found else None

    def upsert_status(self, stable_key: str, *, kind: str, status: str, user_id: str, user_name: str) -> dict:
        current = self.statuses.get(stable_key, {"stable_key": stable_key, "kind": kind, "status": "pending"})
        now = _now()
        current["kind"] = kind
        current["status"] = status
        current["updated_at"] = now
        if status == "resolved":
            current["resolved_by_user_id"] = user_id
            current["resolved_by_name"] = user_name
            current["resolved_at"] = now
        if status == "pending":
            current["reopened_at"] = now
        self.statuses[stable_key] = current
        return deepcopy(current)

    def rows(self, kind: str, analysis_id: str) -> list[dict]:
        table = {
            "documents": self.documents,
            "occurrences": self.occurrences,
            "unmatched": self.unmatched,
            "ctes": self.ctes,
            "tes": self.tes_used,
        }[kind]
        return [deepcopy(row) for row in table if row["analysis_id"] == analysis_id]

    def _refresh(self, analysis_id: str) -> None:
        runs = [run for run in self.runs.values() if run["analysis_id"] == analysis_id]
        analysis = self.analyses[analysis_id]
        statuses = {run["status"] for run in runs}
        if "running" in statuses:
            analysis["status"] = "running"
            analysis["finished_at"] = None
        elif "queued" in statuses:
            analysis["status"] = "queued"
            analysis["finished_at"] = None
        elif statuses == {"failed"}:
            analysis["status"] = "failed"
            analysis["finished_at"] = _now()
        elif "partial" in statuses:
            analysis["status"] = "partial"
            analysis["finished_at"] = _now()
        elif "done" in statuses:
            analysis["status"] = "done"
            analysis["finished_at"] = _now()
        analysis["updated_at"] = _now()
