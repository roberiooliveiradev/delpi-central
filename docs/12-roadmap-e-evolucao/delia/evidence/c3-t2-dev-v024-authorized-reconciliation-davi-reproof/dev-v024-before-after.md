# V024 before/after + post-commit validation (RQ-6)

| Field | BEFORE | AFTER |
|---|---|---|
| V024 checksum | `8f9c9753…` (v1) | `817a70f4…` (v2, = file bytes) |
| event_type CHECK | `('created','updated','resolved','removed')` | `('flag.created','flag.updated','flag.resolved','flag.removed')` |
| events rows | 0 | 0 (unchanged) |
| flags rows | 0 | 0 (unchanged) |
| V024 executed_at | 2026-11-14 15:54:55.266898-03 | unchanged |
| V025 checksum | `3df6a895…` | unchanged |
| total records | 25 | 25 |
| other mismatches | V024 only | none |

Post-commit independent queries (outside the tx): checksum =
`817a70f4…`, constraint def shows all four `flag.*` literals,
`pg_get_constraintdef` canonical form confirmed, record count 25.

## Startup gate outcome

`docker restart delpi-api-delpi` → **Up (healthy)** — no checksum
error in boot log; `plugins_migrations_startup` reports
"Nenhuma migration pendente" for all plugins; `/health` → 200
(operational, not just HTTP — MCP catalog verified downstream).
