# DEV correction decision — Caso B, DECISION_REQUIRED

## Classification

**Caso B** — Git and the DEV database hold genuinely divergent applied
histories (DEV recorded a never-committed v1; tip canonically holds v2
that prod applied). No environment-only correction exists.

## Options ruled out (all forbidden by task §3)

| Option | Verdict |
|---|---|
| Edit V024 to v1 (as done 2026-11-15 / 2026-11-16 window) | FORBIDDEN — `MIGRATION_EDIT`, temp working-tree restore banned; CI `IMMUTABLE_MIGRATION_MUTATION` FAIL proven; also breaks prod gate |
| UPDATE `schema_migrations` checksum | FORBIDDEN — checksum-table mutation |
| ALTER CONSTRAINT to `flag.*` | `DATABASE_SCHEMA_MUTATION: NOT_AUTHORIZED` |
| Disable checksum validation (`RUN_PLUGINS_MIGRATIONS_ON_STARTUP=false`) | FORBIDDEN |
| Substitute migration inside container / mount override | FORBIDDEN |
| Recreate DB / baseline / repair / fake | FORBIDDEN |
| New incremental migration (V026) | Cannot fix a recorded-checksum mismatch (file-vs-record check precedes pending migrations); also requires owner decision first |

## Gate evaluation (task §7)

```yaml
ROOT_CAUSE: PROVEN
OWNER: CONFIRMED (engineering/entry-audit + api-delpi env owner)
CORRECTION: ENVIRONMENT_ONLY → IMPOSSIBLE — no compliant path exists
MIGRATION_FILE_CHANGE: NO (honored — zero file edits in this task)
DB_SCHEMA_CHANGE: NO
CHECKSUM_RECORD_CHANGE: NO
DATA_LOSS_RISK: NONE_PROVEN (no operation executed)
AUTHORIZED_DEV_SCOPE: YES — but no allowed operation achieves the fix
→ STOP → DECISION_REQUIRED
```

## Proposal to owner (handoff — not executed)

DEV `plugins_hub` is the sole outlier (file+prod+code all on `flag.*` v2).
Canonical reconciliation, in order of preference:

1. **Owner-executed DEV repair** (recommended): on DEV only —
   `ALTER TABLE engineering.product_registration_record_flag_events
    DROP CONSTRAINT …event_type_check, ADD CONSTRAINT …
    CHECK (event_type IN ('flag.created','flag.updated','flag.resolved','flag.removed'))`
   then `UPDATE engineering.schema_migrations SET checksum='817a70f4…'
    WHERE version='V024'`. Flyway-repair-equivalent; aligns record+physical
   schema to the committed/applied-elsewhere content; zero data loss
   (table is empty of flag.* events — v1 constraint never admitted them).
2. Alternative: rebuild DEV `plugins_hub` engineering schema from
   committed migrations (dev-only data loss accepted by owner).
3. If owner instead wants plain `created` vocabulary: a NEW migration
   (V026) `ALTER CONSTRAINT` — but prod already records v2, so code
   would ALSO have to change; v2 alignment is strictly simpler.

DEV api-delpi health cannot be restored inside this task's
authorization — every path mutates either the versioned file or the
DB. **DÉLIA receives no code change and no DAVI-specific fallback.**
