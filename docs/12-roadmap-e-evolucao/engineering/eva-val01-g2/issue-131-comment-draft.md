# Comentário para Issue #131 (Coordination)

`ISSUE_UPDATE_BLOCKED` se `gh` indisponível. Publicar em https://github.com/roberiooliveiradev/delpi-central/issues/131

---

## EVA VAL-01 G2 — First-loss + inventário Totus (sem código produtivo)

**TASK_ID:** `EVA-VAL01-G2-FIRST-LOSS-AND-TOTUS-STRUCTURE-CONTRACT-INVENTORY`

```text
PDF_SHA256=af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3
SOURCE_HASH_STATUS=MATCH
G2_FIRST_LOSS_TRACE=PASS
PRODUCTION_CODE_CHANGED=false
G3_EXECUTED=false
G4_EXECUTED=false
DEPLOY_EXECUTED=false
```

### First loss (PROVEN)

| Caso | Primeira fronteira | Nota |
|---|---|---|
| p10 A2/A3 fusão | **SLANet** cell merge (`10080192 10090316` + `line_texts` presentes); Understanding mantém campo fundido | OCR tokens estavam separados |
| p12 50225702→AE/AH/AG | **SLANet** rowspan=11 monolítico; Understanding tipa subset como `component_code` sem parent link | OCR OK |
| p13 `4 5` | Tokens OCR de **rodapé** (índices 4 e 5); SLANet→célula; Understanding→`component_code` | não é código Totus |

### Totus

Inventário `GET /products/{code}/structure` (SG1010+SB1010) em `eva-val01-g2/totus-structure-contract-inventory.md`.  
`CONTRACT_GAP`: `occurrence_id`, binding revisão PDF. Live sample 90264135: `TEST_NOT_RUN` (AUTH).

### Decisão

`SLANet_ALONE_INSUFFICIENT…`; `G3_ENTRY_DECISION=RECOMMENDED_AFTER_COORDINATION_ACK`.  
Menor ajuste candidato documentado — **não implementado**.

Artefatos: `docs/.../engineering/eva-val01-g2/`. Ledger: Doc 119 §61.
