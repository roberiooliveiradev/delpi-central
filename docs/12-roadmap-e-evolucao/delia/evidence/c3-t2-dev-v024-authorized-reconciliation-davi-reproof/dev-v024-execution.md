# V024 reconciliation execution (RQ-4/RQ-5 audit)

## Operation

Single PostgreSQL transaction (`psql --single-transaction`,
`ON_ERROR_STOP=1`, lock_timeout 30s, statement_timeout 120s):

```text
1. SELECT pg_advisory_xact_lock(904221001)          -- canonical lock key
2. DO — revalidate in-tx: V024 checksum == 8f9c9753…, constraint == v1
   plain form (NOT flag.*), events table == 0 rows     → all held
3. ALTER TABLE engineering.product_registration_record_flag_events
     DROP CONSTRAINT …_event_type_check;
   ALTER TABLE … ADD CONSTRAINT …_event_type_check
     CHECK (event_type IN ('flag.created','flag.updated',
                          'flag.resolved','flag.removed'));
4. DO — CAS update (GET DIAGNOSTICS row_count, raise if <> 1):
   UPDATE engineering.schema_migrations
      SET checksum='817a70f4…'
    WHERE version='V024' AND name='prc_record_flags'
      AND checksum='8f9c9753…'                          → exactly 1 row
5. DO — post-conditions in-tx: checksum == 817a70f4…, constraint
   contains flag.created/flag.removed, exactly 1 V024 row → all held
6. COMMIT → RECONCILIATION_OK
```

No autocommit between operations; no data rows touched; `version`,
`name`, `executed_at` preserved; V025 and all other records untouched.

## Audit record

```yaml
CHANGE_TYPE: AUTHORIZED_DEV_MIGRATION_HISTORY_RECONCILIATION
OWNER: api-delpi/plugins_hub env owner + engineering/entry-audit content
EXECUTOR: devin-agent (DEV_ONLY, PO-authorized)
APPROVAL_REFERENCE: task authorization block — PO grant for
  controlled DEV reconciliation with backup/tx/audit/rollback
DATABASE_IDENTITY: plugins_hub @ delpi-postgres-plugins (DEV stack)
DATABASE_ENVIRONMENT: DEV
BACKUP_REFERENCE: ~/c3t2-artifacts/v024-reconciliation/backup-2026-11-16.sql
BACKUP_VERIFIED: YES
LOCK_STRATEGY: pg_advisory_xact_lock(904221001) — canonical runner key
ROWS_UPDATED: 1 (schema_migrations), 1 constraint replaced, 0 data rows
RESULT: COMMITTED — all in-tx pre/post assertions passed
```

This is an exceptional one-time reconciliation of a DEV database that
recorded a never-committed migration version — not a new practice.
Migrations applied remain immutable; legitimate schema changes still
require new incremental migrations.
