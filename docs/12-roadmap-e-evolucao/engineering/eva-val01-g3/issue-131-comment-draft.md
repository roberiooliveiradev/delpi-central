# Comentário para Issue #131 (Coordination)

`ISSUE_UPDATE_BLOCKED` se `gh` indisponível. Publicar em https://github.com/roberiooliveiradev/delpi-central/issues/131

---

## EVA VAL-01 G3 — Benchmark framework-first (sem código produtivo)

**TASK_ID:** `EVA-VAL01-G3-NATIVE-TABLE-FRAMEWORK-BENCHMARK`

```text
PDF_SHA256=af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3
GT_STATUS=DRAFT_G1
FRAMEWORKS_OPERATIONAL=SLANet_only
PPStructureV3=UNAVAILABLE
TableRecognitionPipelineV2=UNAVAILABLE
TableCellsDetection=UNAVAILABLE (download probe cleaned; cache restored to G0)

P10: SLANet still fuses 10080192|10090316 (line_texts present) — crop does not fix
P12: tight crop removes giant rowspan; AE/AH/AG+codes preserved; parent link still integration gap
P13: tight crop eliminates false component_code "4 5"

FRAMEWORK_SUFFICIENCY_DECISION=CURRENT_SLANET_SUFFICIENT_WHEN_CROP_CORRECT; residuals=integration
G4_ENTRY_RECOMMENDATION=regioner_crop + understanding_line_texts/roles (no new framework)
G3_EXIT_STATUS=PASS
PRODUCTION_CODE_CHANGED=false
```

Artefatos: `docs/.../eva-val01-g3/`. Ledger: Doc 119 §62.
