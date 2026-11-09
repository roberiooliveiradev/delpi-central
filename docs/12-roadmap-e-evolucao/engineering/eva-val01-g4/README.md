# EVA VAL-01 G4 — Minimal table integration fix

**TASK_ID:** `EVA-VAL01-G4-MINIMAL-TABLE-INTEGRATION-FIX`  
**Gate:** G4 (authorized §62.1 / Issue #131)  
**Deploy:** **not** executed

## Scope

Minimal diff in existing Understanding / regioner path:

1. **G4-A** — Exclude administrative sheet-index strips from table crop; refuse page-index cells as `component_code`.
2. **G4-B** — Recover fused SLANet code/item bands via `line_texts` + geometric separation.
3. **G4-C** — Preserve subset rowspan parent links; do not invent parent; no component dedupe.

No parallel parser, no new engine, no Totus fill-in, no G1 bbox runtime dependency, no product hardcodes.

## Evidence

- Unit: `engineering-api/tests/test_eva_val01_g4_table_integration.py`
- Regressions: DEC-040–043 + slanet + table_perception (64 passed with G4 suite)
- Real-cell replay: `.local/eva-val01-g4/replay_report.json` (from G2 page dumps)
- Docs: Doc 119 §62.2, Doc 120 Log G4

## Residual

- P12 Understanding crop still yields SLANet `rowspan=11` giant cell (G3); hierarchy PASS on structured rowspan fixtures and on G3 `g1_draft_crop`. Parent recovery on giant u_crop cell is **RESIDUAL**, not claimed PASS.
- Corpus Doc 120 live AuthZ battery: `TEST_NOT_RUN`.
- GT G1 remains `OWNER_BLOCKED` / DRAFT — no homologated accuracy claim.
