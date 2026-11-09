# Pacote de revisão técnica — G1 (Engenharia)

## Identidade

| Campo | Valor |
|---|---|
| TASK_ID | `EVA-VAL01-G1-VISUAL-GROUND-TRUTH-AND-HOLDOUT` |
| PDF 90264135 SHA-256 | `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` |
| Páginas anotadas | 10, 12, 13 |
| ANNOTATION_STATUS | `DRAFT` |
| GT_APPROVAL_STATUS | `OWNER_BLOCKED` |
| SPLIT_APPROVAL_STATUS | `OWNER_BLOCKED` |
| THRESHOLD_APPROVAL_STATUS | `OWNER_BLOCKED` |
| ADJUDICATION_STATUS | `NOT_STARTED` |

## O que revisar

1. Overlays raster em `.local/eva-val01-g1-overlays/` (hashes em `overlays/overlay-registry.json`).
2. JSON `annotations/90264135_p{10,12,13}.json` — linhas, spans, papéis, relações.
3. Contrastes EVA (`eva_defect_contrast`) — confirmar que **não** entram no expected.
4. `dataset-split-manifest.json` + `holdout-protection-plan.md`.
5. `quality-metrics-proposal.md` — aceitar/ajustar thresholds.
6. Ambiguidades AMB-P10-01, AMB-P12-01, AMB-P13-01/02.

## Checklist de aceite owner

- [ ] Páginas 10/12/13: tabelas e drawing_area corretamente separadas
- [ ] A2≠A3 em p10; códigos 10080192 e 10090316 separados
- [ ] Grupo `50225702` = pai; AE/AH/AG = filhos
- [ ] `4 5` rejeitado como component_code
- [ ] Códigos em descrição marcados
- [ ] Split/holdout honestos (`TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE` ou novos PDFs)
- [ ] Thresholds críticos (0 fusão / 0 false promote) aceitos ou alterados

## Assinatura (a preencher)

```text
REVIEWER=
REVIEW_DATE=
REVIEW_EVIDENCE=
GT_APPROVAL_STATUS=          # APPROVED | REJECTED | OWNER_BLOCKED
SPLIT_APPROVAL_STATUS=
THRESHOLD_APPROVAL_STATUS=
```
