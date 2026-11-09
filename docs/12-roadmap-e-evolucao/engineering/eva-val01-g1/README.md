# EVA VAL-01 — G1 Ground Truth Visual (artefatos)

**TASK:** `EVA-VAL01-G1-STRUCTURAL-GT-COMPLETION-AND-OWNER-HANDOFF`  
**Ledger:** Doc 119 §60  
**Corpus:** Doc 120  
**Status:** `ANNOTATION_STATUS=DRAFT` · `GT_APPROVAL_STATUS=OWNER_BLOCKED` · `G1_TECHNICAL_PREPARATION=PASS` · `G1_EXIT_STATUS=PENDING_OWNER_APPROVAL`

## Conteúdo

| Artefato | Arquivo |
|---|---|
| Verificação fonte/render | `g1-source-and-render-verification.md` |
| Guia de anotação | `annotation-guide.md` |
| Manifesto de split | `dataset-split-manifest.json` |
| Matriz de famílias | `layout-family-matrix.md` |
| Plano de holdout | `holdout-protection-plan.md` |
| Métricas/thresholds (proposta) | `quality-metrics-proposal.md` |
| Pacote de revisão owner | `owner-review-package.md` |
| Anotações 90264135 p10/12/13 | `annotations/*.json` |
| Registro de overlays (hashes) | `overlays/overlay-registry.json` |
| Hashes das anotações | `overlays/annotation-content-hashes.json` |
| Relatório validação remota | `overlays/g1_validation_report.json` |
| Validador offline | `scripts/validate_g1_annotations.py` |

## Overlays raster

PNGs de revisão humana ficam em `.local/eva-val01-g1-overlays/` (**gitignored**). Não versionar PDF oficial nem raster proprietário. Conferir identidade via `overlay-registry.json` + `PDF_SHA256`. Inclui `*_cells_overlay.png` com grade, células, spans e IDs legíveis.

## Formato GT

Schema `eva_val01_g1_page_annotation.v1` (Doc 117 §3 estendido): `row_boundaries` / `column_boundaries`, `cells[]` com geometria, `roles`, `relations`/`parent_groups`/`component_occurrences`, `ambiguities`, `annotation_coverage`, e `eva_defect_contrast` (histórico EVA ≠ expected).

## Validação

```bash
python3 docs/12-roadmap-e-evolucao/engineering/eva-val01-g1/scripts/validate_g1_annotations.py
```
