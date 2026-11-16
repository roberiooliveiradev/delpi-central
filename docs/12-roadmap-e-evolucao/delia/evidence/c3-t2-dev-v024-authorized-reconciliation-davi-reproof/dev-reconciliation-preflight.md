# DEV reconciliation preflight (RQ-1/RQ-3)

Executed: 2026-11-16 · executor: devin-agent under PO authorization
`DELIA-C3-T2-DEV-V024-AUTHORIZED-RECONCILIATION-AND-DAVI-REPROOF-01`.

## Environment identity (independent of container names)

```text
current_database() = plugins_hub
current_user       = plugins_user
version()          = PostgreSQL (engine check true)
```

This is the DEV instance serving the local docker-compose stack
(delpi-postgres-plugins → plugins_hub) — the same instance recorded as
the outlier in the previous diagnosis. No HML/PROD endpoints touched;
the operation never left this container.

## Reconfirmed values

```yaml
V024_GIT_CHECKSUM: 817a70f4b0a31a814edad0482a055541addfb6539c0188cdf9e0f0d22f1823ea
  (sha256sum of HEAD file — byte-exact v2, unchanged)
V024_DEV_CHECKSUM: 8f9c975396366117722a4f1a48c86217902a41fc54c3318eb95d607cad0cf73e
  (SELECT from engineering.schema_migrations — unchanged since diagnosis)
V024_DEV_CONSTRAINT (before): CHECK (event_type IN
  ('created','updated','resolved','removed')) — v1 plain
CANONICAL_CONSTRAINT: CHECK (event_type IN
  ('flag.created','flag.updated','flag.resolved','flag.removed')) — v2
V025: 3df6a895… — unchanged, consistent
EVENTS_TABLE_ROWS: 0 (SELECT count(*))
FLAGS_TABLE_ROWS: 0
DISTINCT event_type values: none (table empty → zero incompatible data)
OTHER_MIGRATION_MISMATCHES: NONE — sweep of all 25 engineering
  migration files vs records showed V024 as the only divergence
CONCURRENT_MIGRATION_EXECUTION: NO — pg_stat_activity showed only
  idle-in-transaction pool keepalives (SELECT 1), no migration queries
delpi-api-delpi: Up (unhealthy), restart-looping on checksum gate
```

## Lock strategy (from canonical runner)

`run_plugins_migrations.py` uses session advisory lock key
`904221001` (`pg_advisory_lock`) around all plugin migrations.
The reconciliation used `pg_advisory_xact_lock(904221001)` — same
keyspace, transaction-scoped, auto-released on COMMIT — so no runner
execution could interleave.
