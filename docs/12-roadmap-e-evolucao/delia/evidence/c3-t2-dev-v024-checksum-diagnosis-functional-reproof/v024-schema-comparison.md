# V024 — applied vs committed vs code (three-way comparison)

| Dimension | v1 (DEV applied) | v2 (committed/HEAD, prod) |
|---|---|---|
| `event_type` literals | `created`,`updated`,`resolved`,`removed` | `flag.created`,`flag.updated`,`flag.resolved`,`flag.removed` |
| CHECK layout | single line | two lines |
| sha256 | `8f9c9753…` | `817a70f4…` |
| In git history | **never committed** | `be614649b7` → HEAD |
| In DEV DB record | yes (executed_at 15:54) | no |
| In prod DB record | no (owner-attested) | yes (owner-attested, `3a95d6a3e7`) |
| Code writes | none — all record-flag writes are `flag.*` | exact match for this table |
| All other DDL | identical | identical |

Only the `event_type` CHECK differs between versions (1 logical line;
the byte-exact proof: substituting just that CHECK in v2 reproduces
the v1 checksum — no other divergence exists between the contents).

## Variant attribution

- v1 (plain values): working-copy content applied to DEV at 15:54,
  before commit. Never existed in history.
- v2 (`flag.*`): the committed contract; prod applied it; the
  engineering-api code was written against it.
- Therefore: **DEV is the outlier**, not the file, not the code.
