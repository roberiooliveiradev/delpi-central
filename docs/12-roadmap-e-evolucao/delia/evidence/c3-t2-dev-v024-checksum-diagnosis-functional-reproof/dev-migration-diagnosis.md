# DEV migration diagnosis — V024 (master summary)

Task: `DELIA-C3-T2-DEV-V024-CHECKSUM-ROOT-CAUSE-AND-FUNCTIONAL-REPROOF-01`
Base HEAD: `1fbea4178d` → reanchored `66c98025e7` (= origin/main).

## Sequential diagnostic steps (task §3) — executed, read-only

1. `delpi-api-delpi` state: **Up (unhealthy)**, restart-looping.
2. Startup logs: `RuntimeError: Falha ao executar migrations de plugins
   no startup: Checksum divergente para V024__prc_record_flags.sql`
   → `Application startup failed. Exiting.`
3. `engineering.schema_migrations`: V024 checksum `8f9c9753…`,
   executed_at `2026-11-14 15:54:55` (with V025 same batch, intact).
4. sha256 of V024 file: HEAD `817a70f4…` (v2) ≠ DB `8f9c9753…` (v1).
5. Commits: `be614649b7` created the file as v2 (~3h AFTER the DEV
   apply) — v1 never entered history. Later: e94e3f9989 (v1 restore),
   3a95d6a3e7 (v2 restore for prod), e76018ee (temp v1, eval window),
   3ba6c292 (withdraw → tip v2, CI gate).
6. Exact applied-vs-current diff: only the `event_type` CHECK —
   v1 plain single-line vs v2 `flag.*` two-line; byte-exact v1
   reconstruction proven (`8f9c9753`).
7. Physical V024 tables: both exist; events CHECK = plain v1 values
   (pg_get_constraintdef) — consistent with recorded checksum.
8. DAVI MCP endpoint: down (api-delpi unhealthy → `mcp_unavailable`).
9. DÉLIA config: DAVI endpoint/audience unchanged — failure is owner
   side, not adapter.
10. Token exchange/initialize/tools/list for DAVI: cannot execute —
    service does not start (fails before HTTP). Separated failure
    class: **migration-integrity/startup boundary**, not AuthN/AuthZ.

## Failure-class separation

| Class | State |
|---|---|
| HTTP/MCP unavailable | symptom (DAVI down) |
| Backend API unavailable | root symptom (api-delpi startup fails) |
| Migration error | **FIRST DIVERGENT BOUNDARY** (checksum) |
| Authentication failure | not reached; 0 auth failures in probes |
| Authorization denial | not reached |
| DÉLIA adapter error | excluded — provider-neutral path identical for teo/vista which work |

## Environment provenance

The v1 bytes applied to DEV at 15:54 came from a **dirty working copy**
(never committed). This task forbids reproducing that state; the
previous-session temporary restores (e94e3f9989, e76018ee eval window)
are documented history, not replicable under current authorization.
