# EVA VAL-01 — G1 Ground Truth Visual (artefatos)

**TASK:** `EVA-VAL01-G1-VISUAL-GROUND-TRUTH-AND-HOLDOUT`  
**Ledger:** Doc 119 §60  
**Corpus:** Doc 120  
**Status:** `ANNOTATION_STATUS=DRAFT` · `GT_APPROVAL_STATUS=OWNER_BLOCKED`

## Conteúdo

| Artefato | Arquivo |
|---|---|
| Guia de anotação | `annotation-guide.md` |
| Manifesto de split | `dataset-split-manifest.json` |
| Matriz de famílias | `layout-family-matrix.md` |
| Plano de holdout | `holdout-protection-plan.md` |
| Métricas/thresholds (proposta) | `quality-metrics-proposal.md` |
| Pacote de revisão owner | `owner-review-package.md` |
| Anotações 90264135 p10/12/13 | `annotations/*.json` |
| Registro de overlays (hashes) | `overlays/overlay-registry.json` |

## Overlays raster

PNGs de revisão humana ficam em `.local/eva-val01-g1-overlays/` (**gitignored**). Não versionar PDF oficial nem raster proprietário. Conferir identidade via `overlay-registry.json` + `PDF_SHA256`.

## Formato GT

Alinhado ao Doc 117 §3 (`GT formato v1`), estendido com `roles`, `relations`, `ambiguities` e `eva_defect_contrast` (histórico EVA ≠ expected).
