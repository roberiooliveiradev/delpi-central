# E7 — Tipografia / estilo / cores

**Status:** IMPLEMENTED (via upsert deep-merge)

- Ribbon style patches → `updateSelected` / `updateBlock` → local preview + `upsert_block` ack.
- Nested merge: `style`, paints via `BLOCK_DEEP_MERGE_KEYS`.
- Conditional color-by-value / display format: já backend (`DisplayFormatService` / enrich) — sem mudança de ownership.
- Theme: `applySlideTheme` local + upsert blocks afetados via update paths.

Paint publicado continua preferindo modelo canônico; `?? DEFAULT` residual documentado em E13.
