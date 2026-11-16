# Backup & rollback (RQ-2)

## Backup

- `pg_dump -U plugins_user -d plugins_hub
  -t engineering.schema_migrations
  -t engineering.product_registration_record_flags
  -t engineering.product_registration_record_flag_events
  --format=plain --no-owner`
- Artifact (host): `~/c3t2-artifacts/v024-reconciliation/backup-2026-11-16.sql`
- sha256: `4d95368f19808f27fb4bf8bceb0108a2e68dcbee9d8cca26ef00f504a4ff5990f`
- Verified: 279 lines; contains V024 row with checksum `8f9c9753…`,
  the pre-change constraint definition, full schema_migrations table
  DDL+COPY (all 25 rows), both V024 tables DDL+data.
- Data-at-risk: none — both business tables empty; only metadata
  (constraint + 1 history row) touched.

## Rollback

- In-transaction: `--single-transaction` + `ON_ERROR_STOP=1` → any
  failure auto-rolls back (proven mechanism; all in-tx assertions
  would abort before commit).
- Post-commit reversal (pre-approved, technically safe):
  `ALTER TABLE … DROP CONSTRAINT …; ADD CONSTRAINT … CHECK
   (event_type IN ('created','updated','resolved','removed'))`
  + `UPDATE schema_migrations SET checksum='8f9c9753…' WHERE
   version='V024' AND checksum='817a70f4…'` — exact inverse CAS.
  Full data restore available via the pg_dump artifact.
- STOP conditions observed: none triggered — DB identity confirmed,
  checksums matched expectations, zero incompatible rows, backup
  readable, owner authorization present, no concurrent migrations.
