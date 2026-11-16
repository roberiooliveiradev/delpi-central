# Migration history validation (post-COMMIT, RQ-6)

Independent queries outside the reconciliation transaction:

```text
V024 | prc_record_flags        | 817a70f4b0a31a814edad0482a055541addfb6539c0188cdf9e0f0d22f1823ea | 2026-11-14 15:54:55.266898-03
V025 | prc_record_flags_grants | 3df6a895407b51ff9f6246f66e506646270e7ec0083c87acf50a85c821c7a03d | 2026-11-14 15:54:55.378737-03
```

- Checksum now equals sha256 of the canonical file (byte-exact gate passes).
- `executed_at`, `version`, `name` preserved — no history rewrite of
  when/how it was applied; only the recorded checksum was reconciled
  to the content the file canonically holds (and prod applied).
- events/flags tables: 0 rows each — zero data touched.
- Total records: 25 — none added/removed.
- Other tables/constraints/indexes: untouched (only the one
  event_type CHECK replaced with same name + column).
- api-delpi startup runner now validates the whole history without
  divergence — the canonical gate itself is the independent validator.
