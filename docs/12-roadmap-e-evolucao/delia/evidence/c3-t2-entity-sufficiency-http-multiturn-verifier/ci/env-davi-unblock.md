# DEV env unblock (DAVI) — local only

`delpi-api-delpi` was unhealthy due to checksum divergence on
`V024__prc_record_flags.sql` (DB applied `8f9c97…` vs git tip `817a70…`
from `3a95d6a3e7`).

For the live HTTP E2E, the applied content was restored **locally** long
enough to boot DAVI, capture `http-mt-42e226d1432a`, then withdrawn from
the published git tip because `IMMUTABLE_MIGRATION_MUTATION` forbids
editing versioned migrations in CI.

Owner handoff (engineering/entry-audit / env): reconcile DEV
`schema_migrations` vs git without rewriting V024 in history — prefer
environment alignment or an incremental migration if DDL must change.

`PRODUCTION_DEPLOY=NOT_AUTHORIZED`. No DB checksum mutation performed.
