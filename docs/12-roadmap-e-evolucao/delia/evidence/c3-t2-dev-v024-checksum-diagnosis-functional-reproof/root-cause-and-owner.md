# Root cause and owner — V024 checksum divergence (DEV)

## RQ-3 result

```yaml
ROOT_CAUSE: V024 was applied to DEV plugins_hub from an uncommitted
  working copy (v1, plain event_type values) at 2026-11-14 15:54,
  ~3h before the file was committed as v2 (flag.* literals) in
  be614649b7. Prod later applied the committed v2. The applied
  histories of DEV and prod forked at V024.
FIRST_DIVERGENT_COMMIT: be614649b7 (commits content that diverges
  from what DEV already recorded; the divergent act itself was the
  uncommitted DEV apply at 15:54 — no commit exists for v1)
APPLIED_DATABASE_VERSION (DEV): v1 / 8f9c9753… / plain CHECK
APPLIED_DATABASE_VERSION (PROD): v2 / 817a70f4… (owner-attested)
CURRENT_GIT_VERSION: v2 / 817a70f4… (canonical; CI IMMUTABLE gate)
ACTUAL_SCHEMA_VERSION (DEV): v1 — pg_get_constraintdef proves
  plain literals physically installed
MIGRATION_RUNNER_BEHAVIOR: sha256(file bytes) compared to
  schema_migrations.checksum; RuntimeError aborts startup;
  retries only for transient DB errors; gate=RUN_PLUGINS_MIGRATIONS_ON_STARTUP
OWNER: engineering/entry-audit (migration content) +
  api-delpi/env owner (DEV schema_migrations reconciliation)
CORRECTION_REQUIRED: owner reconciliation of DEV DB — see
  dev-correction-decision.md. Forbidden to this task.
```

## Hypothesis ledger

| Hypothesis | Verdict | Evidence |
|---|---|---|
| File edited post-apply | CONFIRMED (partial) — committed version ≠ applied version | git log + checksums |
| DEV applied different version | **PROVEN — first divergent boundary** | DB checksum `8f9c9753` vs all committed contents; byte-exact v1 reconstruction |
| Deploy != HEAD | REJECTED — container /app is bind-mounted to HEAD tree | sha256 of file in HEAD = 817a70f4 = container reads same |
| Stale file in container volume | REJECTED | `/app` bind mount; file on host == container |
| Encoding/line-ending | REJECTED | UTF-8, LF, no BOM; sha256 over raw bytes; v1 reconstructed exactly |
| Runner checksum bug | REJECTED | `sha256(read_bytes())` is correct and honest; gate working as designed |
| Recorded checksum vs schema drift | REJECTED | physical CHECK == v1 == recorded checksum — consistent |
| Legitimate change w/o incremental migration | CONFIRMED as the *mechanism*: v1→v2 edit happened pre-commit, bypassing review | be614649b7 diff |

## Earlier-diagnosis correction (self-audit)

The 2026-11-15 remediation restored the file to v1 — correct for DEV
(proven byte-exact against `8f9c9753`) but it broke **prod**, where
v2 was already recorded. Commit `3a95d6a3e7` documents the owner's
direct prod read (`817a70f4`). Both restorations were "the right file"
— the fork means a single file cannot satisfy both environments.
The canonical resolution is environment reconciliation, not file choice.
