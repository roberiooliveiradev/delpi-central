# Comentário para Issue #131 (Coordination)

`ISSUE_UPDATE_BLOCKED` neste executor (`gh` ausente/não autenticado). Publicar o texto abaixo em https://github.com/roberiooliveiradev/delpi-central/issues/131

---

## EVA VAL-01 G1 — fechamento técnico estrutural (DRAFT → owner)

**TASK_ID:** `EVA-VAL01-G1-STRUCTURAL-GT-COMPLETION-AND-OWNER-HANDOFF`

```text
G1_ANNOTATION_COMPLETENESS=PASS_DRAFT_STRUCTURAL
G1_GEOMETRY_VALIDATION=PASS
G1_OVERLAY_ACCESS=LOCAL_PATH_READY
G1_OWNER_APPROVAL=OWNER_BLOCKED
G1_SPLIT_APPROVAL=OWNER_BLOCKED
G1_THRESHOLD_APPROVAL=OWNER_BLOCKED
G1_TECHNICAL_PREPARATION=PASS
G1_EXIT_STATUS=PENDING_OWNER_APPROVAL
NEXT_GATE=G2_BLOCKED
TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE
SOURCE_HASH_STATUS=MATCH
PDF_SHA256=af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3
```

### Entregáveis

- Anotações geométricas completas no escopo selecionado: `docs/.../eva-val01-g1/annotations/90264135_p{10,12,13}.json`
- Overlays revisáveis (gitignored): `.local/eva-val01-g1-overlays/p{10,12,13}_cells_overlay.png` (+ zoom/DPI200)
- Hashes: `overlays/overlay-registry.json` + `overlays/annotation-content-hashes.json`
- Validador offline PASS: `scripts/validate_g1_annotations.py`
- Pacote owner: `owner-review-package.md`
- Ledger: Doc 119 §60.1; corpus log Doc 120

### Invariantes críticos (expected)

- p10: A2=`10080192` ≠ A3=`10090316`
- p12: parent `50225702` → AE/AH/AG (subset ≠ component_code)
- p13: drawing_area separado; `4 5` **não** é component_code expected

### Pedido à Engenharia

1. Revisar overlays + JSON (checklist em `owner-review-package.md`).
2. Assinar GT / split / thresholds ou rejeitar com evidência.
3. Coordination: disponibilizar PNGs locais por canal autorizado (não estão no Git público).

**G2 permanece bloqueado** até aceite formal do G1.
