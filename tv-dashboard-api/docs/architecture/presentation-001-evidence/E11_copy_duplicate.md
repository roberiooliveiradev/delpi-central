# E11 — Copy / duplicate

**Status:** IMPLEMENTED

- Op `duplicate_blocks`: novos IDs, offset frame, strip enrich stamps.
- Editor: `duplicateSelected` → `commitDuplicateBlocks` quando sem policy de data-source; senão clone local + `upsert_block` ack dos pasted.
