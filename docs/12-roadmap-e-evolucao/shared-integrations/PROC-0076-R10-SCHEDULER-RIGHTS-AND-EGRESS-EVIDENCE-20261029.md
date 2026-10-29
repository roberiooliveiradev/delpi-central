# PROC-0076.R10 — Scheduled Metals Refresh, Rights Gate & Egress Evidence (2026-10-29)

Execution: `PROC-0076.R10-PERSISTENT-METAL-HISTORY-AND-DAILY-REFRESH`
Deploy source SHA: `e963666854` — `delpi-external-data-api` rebuilt,
`delpi-external-data-scheduler` created.

## S0 — Root cause of "Sem dados no período" (AC-01 PASS)

Three independent operational facts, all proven in production:

1. `EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED=false` in the prod env —
   the feed was deliberately off.
2. **No scheduler existed**: no crontab, no systemd timer, no
   scheduler container. The last `metals-daily` run
   (`2026-10-27 04:48 -03`, 110 rows) was a manual `docker exec`.
3. `metal_quote_cache.expires_at` is `NOT NULL` (TTL 48h by design).
   Every row expired ≈ 29/10 → the read path correctly filters
   `expires_at > NOW()` → `data_status=no_data` → UI "Sem dados".

The read path is fail-closed and honest; nothing was deleted and no
upstream call is made per page refresh.

## S0 — Rights gate (EXECUTION_DRIFT, unchanged)

`external_data.market_data_sources` (prod, verified 29/10):

```
metalcharts | active=t | observation_retention=ttl_cache
allowed_use_scope = collect;derive;internal_display;
                    store_cache_only;no_redistribute
```

`store_permanent` remains **PENDING / not authorized** (see
`PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md`). The permanent
`metal_quote_observations` table exists and the binding resolver
already routes `permanent` sources to it — but **no MetalCharts row
was migrated or will be migrated** until institutional approval or a
license confirming archive rights. The persistent-history product
requirement stays OPEN against the rights gate (D-05/D-11).

## Budget economics — why "once daily" is plan-blocked (AC-09)

| Endpoint | Weight | Coverage |
|---|---|---|
| `/v1/prices` (spot) | 1 | all tracked symbols, one call |
| `/v1/history/{symbol}` | 2 | one symbol |

Daily per-symbol history refresh: 5 × 2 = **10 weight/day ≈ 300/month
> 200 upstream Free cap > 160 internal budget** — mathematically
impossible on the current plan. Adopted cadence:
`EXTERNAL_DATA_SCHEDULER_METALS_DAILY_INTERVAL_DAYS=3` ≈ **100/month**
with ~60 weight headroom for retries/incidents, inside the designed
`MetalChartsBudget` (160/month, 8/min, ledger-pre-charged).
`METALCHARTS_CACHE_TTL_HOURS=120` covers one failed cycle plus two
next-day retries before any gap — still an operational TTL cache,
not permanent retention (policy `ttl_cache` unchanged; change is a
runtime env, documented here, not silent).

Alternative for true daily freshness: `/v1/prices` spot (1/day ≈
30/month) feeding the latest bar — requires a new ingestion path and
spot-shape homologation; not implemented this round (egress blocked,
semantics differ from daily close).

## Egress — Sophos block, no bypass (AC-11)

Live diagnostics from `delpi-external-data-api`, 29/10:

- `fetch_spot`/`fetch_history` → `SSL: CERTIFICATE_VERIFY_FAILED`
  (unable to get local issuer certificate) — TLS interception.
- Diagnostic request with verification disabled → HTTP **403
  "Blocked site"** served by proxy `192.168.1.253` (Sophos).

The successful 27/10 run proves the provider/key work when egress is
open; the block is newer or intermittent. Resolution requires IT to
authorize `api.metalcharts.org` egress (category + CA trust) — **no
TLS bypass, proxy circumvention or firewall change was attempted**.

Runtime proof 29/10 12:52 -03 — same entrypoint the scheduler uses:

```
ingest_run_finished feed=metals-daily outcome=failed fetched=0
  safe_error_code=EXTERNAL_DATA_PROVIDER_UNAVAILABLE
```

Zero ledger weight consumed (recorded only after a successful fetch).
`feed_statuses()` now surfaces `last_outcome=failed`,
`last_error_code`, `last_successful_at=2026-10-27`, which the BFF
`_ingestion_meta` already propagates to the frontend as honest
"atualização indisponível" state.

## R10.S4 — Scheduler delivered

- `external-data-api/app/jobs/ingest_scheduler.py` — env-gated loop
  (`EXTERNAL_DATA_SCHEDULER_ENABLED`, master kill switch), one attempt
  per local day after `EXTERNAL_DATA_SCHEDULER_RUN_AT` (container TZ,
  provisional 20:30 pending provider publication-time evidence), due
  when the last success is older than the per-feed interval, restart
  state derived from `market_data_ingestion_runs` (no new table).
- Invokes `python -m app.jobs.ingest_market_data` — the tested CLI
  contract (feed flags, advisory lock, run ledger, exit codes) is
  reused verbatim.
- Compose service `delpi-external-data-scheduler` (same image, no
  ports, `depends_on external-data-api: healthy`), deployable via
  `up-prod-sequential.sh` (added to FASE_API).
- Deployed and running: `scheduler_start enabled=True
  feeds=metals-daily run_at=20:30 poll_s=300`.
- AC-18 runtime proof is PARTIAL: the loop runs and correctly sees
  "attempted today" (manual run suppressed today's slot); the first
  scheduled attempt fires next due day — expected `failed` until IT
  opens egress, which is itself the monitored signal.

## What was NOT done (drift-scoped out)

- No `metal_quote_cache` → `metal_quote_observations` copy (rights).
- No retention-policy change (`ttl_cache` preserved; TTL hours is a
  runtime env parameter, documented above).
- No spot-endpoint ingestion path (unhomologated + egress blocked).
- No BFF/frontend diff — existing `feed_ingestion`/freshness (grace
  4 business days) already expresses delayed/unavailable correctly.
- No frontend redesign; Comex S9 untouched.

## Open items

1. IT: authorize egress to `api.metalcharts.org` (Sophos) — then the
   first scheduled run populates cache and charts recover.
2. Institutional: decide permanent-retention path for metals —
   MetalCharts plan/license confirming archive rights, or an
   authorized alternative source for the persistent series.
3. Verify provider publication hour → adjust `RUN_AT` if needed.
4. Optional: spot-based daily latest-bar refresh if daily freshness
   becomes a product requirement (≈30 weight/month extra).
