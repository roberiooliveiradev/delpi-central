"""Inspeção de integridade do runtime MES (Etapa 05).

Detecta e **loga** inconsistências — nunca auto-repara nem inventa história.
Executada no startup: migrations → integrity check → poller. A API continua
subindo mesmo com anomalias (diagnóstico > indisponibilidade).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

SEVERITY_OK = "OK"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"


def inspect_runtime_integrity(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Classifica inconsistências a partir de um relatório somente-leitura.

    ``report`` contém: ``runs`` (id/status/branch/work_center),
    ``open_states``, ``open_downtimes``, ``open_segments`` e ``state_runs``
    (mapa state_event_id → run_id).
    """
    issues: list[dict[str, Any]] = []
    runs = report.get("runs") or []
    open_states = report.get("open_states") or []
    open_downtimes = report.get("open_downtimes") or []
    open_segments = report.get("open_segments") or []
    state_runs: dict[str, str] = report.get("state_runs") or {}
    mes_observed_runs: set[str] = set(report.get("mes_observed_runs") or [])

    def issue(run: dict[str, Any], code: str, severity: str) -> None:
        issues.append(
            {
                "severity": severity,
                "issue_code": code,
                "run_id": str(run.get("id")),
                "branch": run.get("branch"),
                "work_center": run.get("work_center"),
            }
        )

    states_by_run: dict[str, list[dict[str, Any]]] = {}
    for st in open_states:
        states_by_run.setdefault(str(st.get("run_id")), []).append(st)
    dts_by_run: dict[str, list[dict[str, Any]]] = {}
    for dt in open_downtimes:
        dts_by_run.setdefault(str(dt.get("run_id")), []).append(dt)
    segments_by_run = {str(s.get("run_id")) for s in open_segments}

    for run in runs:
        rid = str(run["id"])
        status = run.get("status")
        states = states_by_run.get(rid, [])
        dts = dts_by_run.get(rid, [])
        observed = rid in mes_observed_runs

        if status == "running":
            if not observed:
                issue(run, "legacy_run_without_mes_events", SEVERITY_WARNING)
                continue
            if any(st["state"] == "stopped" for st in states):
                issue(run, "running_with_open_stopped", SEVERITY_CRITICAL)
            if not any(st["state"] == "producing" for st in states):
                issue(run, "running_without_open_producing", SEVERITY_CRITICAL)
            if dts:
                issue(run, "running_with_open_downtime", SEVERITY_CRITICAL)
            if rid not in segments_by_run:
                issue(run, "running_without_open_segment", SEVERITY_CRITICAL)
        elif status == "paused":
            if not observed:
                issue(run, "legacy_run_without_mes_events", SEVERITY_WARNING)
                continue
            if any(st["state"] == "producing" for st in states):
                issue(run, "paused_with_open_producing", SEVERITY_CRITICAL)
            if not any(st["state"] == "stopped" for st in states):
                issue(run, "paused_without_open_stopped", SEVERITY_CRITICAL)
            if not dts:
                issue(run, "paused_without_open_downtime", SEVERITY_CRITICAL)
            if rid in segments_by_run:
                issue(run, "paused_with_open_segment", SEVERITY_CRITICAL)
        elif status in {"completed", "aborted"}:
            if rid in segments_by_run:
                issue(run, "finished_with_open_segment", SEVERITY_CRITICAL)
            if states:
                issue(run, "finished_with_open_state", SEVERITY_CRITICAL)
            if dts:
                issue(run, "finished_with_open_downtime", SEVERITY_CRITICAL)

    # Cross-run: estado/parada abertos de um run em CT cujo run ativo é outro.
    active_by_ct = {
        (r["branch"], r["work_center"]): str(r["id"])
        for r in runs
        if r.get("status") in {"running", "paused"}
    }
    for st in open_states:
        active = active_by_ct.get((st.get("branch"), st.get("work_center")))
        if active and str(st.get("run_id")) != active:
            issues.append(
                {
                    "severity": SEVERITY_CRITICAL,
                    "issue_code": "open_state_of_other_run",
                    "run_id": str(st.get("run_id")),
                    "branch": st.get("branch"),
                    "work_center": st.get("work_center"),
                }
            )
    for dt in open_downtimes:
        active = active_by_ct.get((dt.get("branch"), dt.get("work_center")))
        if active and str(dt.get("run_id")) != active:
            issues.append(
                {
                    "severity": SEVERITY_CRITICAL,
                    "issue_code": "open_downtime_of_other_run",
                    "run_id": str(dt.get("run_id")),
                    "branch": dt.get("branch"),
                    "work_center": dt.get("work_center"),
                }
            )
        owner = state_runs.get(str(dt.get("state_event_id") or ""))
        if owner and str(dt.get("run_id")) != owner:
            issues.append(
                {
                    "severity": SEVERITY_CRITICAL,
                    "issue_code": "downtime_linked_to_other_run_state",
                    "run_id": str(dt.get("run_id")),
                    "branch": dt.get("branch"),
                    "work_center": dt.get("work_center"),
                }
            )
    return issues


class MesRuntimeIntegrityService:
    """Carrega o relatório do Postgres e loga anomalias — sem auto-repair."""

    def run(self) -> list[dict[str, Any]]:
        report = self._load_report()
        issues = inspect_runtime_integrity(report)
        for item in issues:
            log = logger.warning if item["severity"] == SEVERITY_WARNING else logger.error
            log(
                "mes_integrity_issue severity=%s issue=%s run_id=%s branch=%s "
                "work_center=%s",
                item["severity"],
                item["issue_code"],
                item["run_id"],
                item["branch"],
                item["work_center"],
            )
        if not issues:
            logger.info("mes_integrity_ok")
        return issues

    @staticmethod
    def _load_report() -> dict[str, Any]:
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        schema = PC_SCHEMA_NAME
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT id::text, status, branch, work_center "
                    f"FROM {schema}.production_runs"
                )
                runs = [dict(r) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT id::text, run_id::text, branch, work_center, state "
                    f"FROM {schema}.work_center_state_events WHERE ended_at IS NULL"
                )
                open_states = [dict(r) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT id::text, run_id::text, state_event_id::text, "
                    f"branch, work_center FROM {schema}.downtime_events "
                    f"WHERE ended_at IS NULL"
                )
                open_downtimes = [dict(r) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT id::text, run_id::text FROM "
                    f"{schema}.production_run_segments WHERE ended_at IS NULL"
                )
                open_segments = [dict(r) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT id::text, run_id::text FROM "
                    f"{schema}.work_center_state_events"
                )
                state_runs = {r["id"]: r["run_id"] for r in cur.fetchall()}
                cur.execute(
                    f"SELECT DISTINCT run_id::text FROM "
                    f"{schema}.work_center_state_events "
                    f"UNION SELECT DISTINCT run_id::text FROM "
                    f"{schema}.downtime_events WHERE run_id IS NOT NULL"
                )
                mes_observed = {r["run_id"] for r in cur.fetchall()}
        return {
            "runs": runs,
            "open_states": open_states,
            "open_downtimes": open_downtimes,
            "open_segments": open_segments,
            "state_runs": state_runs,
            "mes_observed_runs": mes_observed,
        }
