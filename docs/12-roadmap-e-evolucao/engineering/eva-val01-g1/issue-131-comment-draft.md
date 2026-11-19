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

---

## VAL-04 — `graphic_primitives.dots` implementado (release bloqueado)

Canal aditivo de terminadores geométricos implementado em
`opencv_adapter` (`saturation_opening` + fallback `distance_transform`)
e consumido pelo B2 em `understanding` (`terminator_dots_px` +
`termination:{DOT_TERMINATED|DOT_OVERSHOOT,dot_px,overshoot_px}`).

Desenho real 90480120: p1=81 dots, p2=67; A4/A8/AA/A1 `DOT_TERMINATED`
com endpoints físicos inalterados; A5 leque AMBIGUOUS com os 3 dots
expostos; A9/E compartilham o dot (2002,1086) recuperado via
distance_transform — ambiguidade preservada. Irmãos
90261723/90261731/90264311 sem regressão; 90264311-A2 `DOT_OVERSHOOT`
61 px confirmado visualmente. B1/tabela/B3 estáveis;
`automatic_approval=false`.

Testes: +13 (adapter+B2), 111 pass nos arquivos afetados em container;
suíte 1713 pass com 6 falhas ambientais pré-existentes (worker sem
cv2/paddle no venv — reproduzidas com diff stasheado).

Verificação independente: `INCONCLUSIVE` (cursor usage limit até
02/12/2026). **Código NÃO publicado** — permanece em working tree
governado até motor verificador disponível ou exceção da Coordination.
Doc 119 §94.42.19 + pacote `eva-val01-g1/val04-dots-review-package.md`.

---

## VAL-04R — Consolidação: terminação por ramo + auditoria dos 148 dots

- `branch_terminations[]` por raiz em ocorrências AMBIGUOUS: A5 =
  `[DOT_OVERSHOOT, DOT_TERMINATED, DOT_TERMINATED, OPEN]` (overshoot
  ~61 px do ramo do meio anotado por raiz, sem escolher destino).
- Auditoria: 19/148 associados (LIKELY_TERMINATOR), 78 em caixas OCR
  (glifos), 51 fora de texto (setas de cota/features). Nenhum filtro
  seguro remove candidatos sem perder terminadores — nada removido.
- Suíte no ambiente correto (container): **1721 pass / 0 fail**.
- Irmãos e B1/tabela/B3 sem regressão; `automatic_approval=false`.
- Verificador independente: `INCONCLUSIVE` r1 (cursor usage limit até
  02/12/2026). **Código permanece não-publicado** — pacote auditável
  (patch + fingerprint `cc1bd570…`) disponível à Coordination.
