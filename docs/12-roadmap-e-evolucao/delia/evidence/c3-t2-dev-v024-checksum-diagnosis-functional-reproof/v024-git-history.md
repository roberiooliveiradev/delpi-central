# V024 git history — `api-delpi/migrations/plugins/engineering/V024__prc_record_flags.sql`

Evaluated at: 2026-11-16 · HEAD `66c98025e732`

## Timeline (all commits touching the file)

| Commit | Date (-03) | Effect on file | sha256 after |
|---|---|---|---|
| `be614649b7` | 2026-11-14 18:30 | **creates** file (`new file mode`) with two-line `flag.*` CHECK | `817a70f4…` |
| `e94e3f9989` | 2026-11-15 | restores single-line plain CHECK (byte-exact == DEV applied content) | `8f9c9753…` |
| `3a95d6a3e7` | 2026-11-15 18:21 | restores `flag.*` two-line — commit msg: prod plugins_hub records `817a70f4` (owner-attested direct read); DEV restore broke prod startup gate | `817a70f4…` |
| `e76018eea9` | 2026-11-16 08:33 | temporary v1 restore for live-eval DAVI unblock + C3/T2 impl | `8f9c9753…` |
| `3ba6c292f6` | 2026-11-16 08:39 | **withdraws** the V024 mutation from tip — CI `IMMUTABLE_MIGRATION_MUTATION` gate forbids editing versioned migrations | `817a70f4…` |

## Version inventory

```text
v1 (applied in DEV, NEVER committed):
  CHECK (event_type IN ('created','updated','resolved','removed'))  — single line
  sha256: 8f9c975396366117722a4f1a48c86217902a41fc54c3318eb95d607cad0cf73e
  Reconstructed byte-exact 2026-11-15 — file bytes → DB-recorded checksum (proof).

v2 (committed, canonical):
  CHECK (event_type IN ('flag.created','flag.updated',
                        'flag.resolved','flag.removed'))            — two lines
  sha256: 817a70f4b0a31a814edad0482a055541addfb6539c0188cdf9e0f0d22f1823ea
  = be614649b7 content = current HEAD content.
```

## Integrity / encoding

- `file`: Unicode text, UTF-8, no BOM; LF endings.
- Runner computes `sha256(path.read_bytes())` — raw bytes, no normalization
  (`api-delpi/scripts/run_plugins_migrations.py:132`).
- Therefore any byte difference (including the rewrap + literal change) diverges.

## The fork

```text
2026-11-14 15:54:55  DEV plugins_hub applies V024 from uncommitted working copy (v1)
                     → engineering.schema_migrations checksum = 8f9c9753…
2026-11-14 18:30     be614649b7 commits v2 (flag.*) — applied v1 was never committed
(prod, later)        prod applies committed v2 → prod schema_migrations = 817a70f4…
                     (owner-attested: commit msg 3a95d6a3e7, direct prod read)
HEAD                 file = v2 (817a70f4…) — canonical per owner + IMMUTABLE gate
```

Consequence: **no committed file version matches DEV's recorded checksum** —
DEV applied a version that never entered history.
