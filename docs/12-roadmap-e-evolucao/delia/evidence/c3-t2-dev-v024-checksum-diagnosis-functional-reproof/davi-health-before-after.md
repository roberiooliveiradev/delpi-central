# DAVI health — before/after (DEV)

## Current state (evaluated 2026-11-16, HEAD 66c98025e7)

- `delpi-api-delpi`: **Up (unhealthy)** — startup fails at migration gate:
  `Checksum divergente para V024__prc_record_flags.sql` (RuntimeError →
  Application startup failed; container restart-looping).
- DAVI MCP endpoint (`http://delpi-api-delpi:8000/mcp`): **unavailable**
  → DÉLIA reports `mcp_unavailable` for `mcp:davi` (fast fail), zero
  capabilities contributed.
- TÉO + VISTA: healthy, discovering normally (16→12 caps w/o davi group).

## History of states

| Window | api-delpi | DAVI |
|---|---|---|
| pre-2026-11-15 | DOWN (V024 divergence v1-record vs v2-file) | mcp_unavailable |
| 2026-11-15 (e94e3f9989 window, local v1) | healthy | discovered (16 caps, read OK) |
| 3a95d6a3e7 (file→v2 for prod) | DEV unhealthy again | mcp_unavailable |
| e76018ee eval window (local v1, withdrawn) | healthy — multiturn `http-mt-42e226d1432a` grounded on DAVI | OK during window |
| post-3ba6c292 (tip=v2 canonical) — **NOW** | unhealthy | mcp_unavailable |

## Postcondition status

`initialize`/`tools/list`/governed read for DAVI cannot be re-proven
in the current DEV state — blocked by the Caso-B decision required.
Prior-window evidence is historical and is NOT counted as proof of
this execution per task rules.
