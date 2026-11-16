# V024 — DEV database state (sanitized, read-only capture)

DB: `delpi-postgres-plugins` container → `plugins_hub` DB → schema `engineering`.
All queries SELECT-only; no DDL/DML executed. Captured 2026-11-16.

## Migration records

```text
version | checksum                                                         | executed_at
V024    | 8f9c975396366117722a4f1a48c86217902a41fc54c3318eb95d607cad0cf73e | 2026-11-14 15:54:55.266898-03
V025    | 3df6a895407b51ff9f6246f66e506646270e7ec0083c87acf50a85c821c7a03d | 2026-11-14 15:54:55.378737-03
```

- V024 recorded checksum `8f9c9753…` = the never-committed v1 bytes.
- V025 checksum matches the committed file — V025 untouched.

## Physical CHECK on the events table

```text
product_registration_record_flag_events_event_type_check:
CHECK (((event_type)::text = ANY ((ARRAY[
  'created','updated','resolved','removed'
]::character varying[])::text[])))
```

Physical constraint = **v1 plain values** — consistent with the recorded checksum.

## Tables (exist, structure complete)

- `engineering.product_registration_record_flags` — 29 cols (id, record_id,
  title, status, target_*, revision/version bookkeeping, audit subjects, close_*);
  pkey + `uq_prc_record_flags_open_target` + 2 ix; CHECKs: status, subject,
  close coherence, title/description length, revision numbers; FKs to records.
- `engineering.product_registration_record_flag_events` — 9 cols;
  pkey + 2 ix; CHECKs: event_type (v1 above), revision_number >= 1.

## Code ↔ constraint compatibility (CONFIRMED_NO_CODIGO)

`engineering-api` record-flag path writes `flag.{created,updated,resolved,removed}`
(service.py:3606/3674/3736 → `_insert_record_flag_event` → this table).
Any record-flag write in DEV violates the v1 CHECK — feature path is broken
in DEV independently of the API startup issue. `flag.reopened`/`flag.deleted`
go to `product_registration_events` (attendance path, different table).
