## EVA VAL-01 G4 — execution report (candidate code, no deploy)

**TASK_ID:** `EVA-VAL01-G4-MINIMAL-TABLE-INTEGRATION-FIX`

### Result

`G4_IMPLEMENTATION=PASS_WITH_RESIDUAL`

| AC | Status |
|---|---|
| G4-AC01 minimal correct layer | PASS — Understanding/regioner only |
| G4-AC02 A2/A3 split | PASS — real G2 `line_texts` cell + fixtures |
| G4-AC03 footer not component | PASS — crop trim + type gate |
| G4-AC04 subset≠component | PASS — rowspan fixtures |
| G4-AC05 parent only with evidence | PASS — missing parent → no invent |
| G4-AC06 multiline/rowspan negatives | PASS |
| G4-AC07 DEC-040–043 | PASS (64 with related suite) |
| G4-AC08 provenance/limitations | PASS — no Totus invent |
| G4-AC09 no parallel parser/hardcode | PASS |
| G4-AC10 SHA-tracked | PASS (commit this comment references) |
| G4-AC11 Doc119/120 + issue | PASS (docs + this draft) |

### Residual / blocked

- P12 u_crop giant `rowspan=11`: hierarchy still depends on crop tightness (G3 finding); fixture/parent path PASS.
- Corpus 13 live: `TEST_NOT_RUN`.
- G5/G6/G7 **NOT_AUTHORIZED**. No production deploy.
- GT remains DRAFT / `OWNER_BLOCKED`. **No generalization claim.**

### Models

- Baseline SLANet retained (`inference.pdiparams` SHA `9d33d47b…7a60`).
- Residual RT-DETR from G3 probe removed from local host cache; G4 triggered no downloads.

### Next

G5 entry only after Coordination ack. Candidate code ready for review; deploy gate separate.
