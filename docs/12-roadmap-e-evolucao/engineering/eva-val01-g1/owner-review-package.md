# Pacote de revisão técnica — G1 (Engenharia)

## Identidade

| Campo | Valor |
|---|---|
| TASK_ID | `EVA-VAL01-G1-STRUCTURAL-GT-COMPLETION-AND-OWNER-HANDOFF` |
| PDF 90264135 SHA-256 | `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` |
| `SOURCE_HASH_STATUS` | `MATCH` |
| Páginas anotadas | 10, 12, 13 |
| Render DPI | 200 |
| Schema | `eva_val01_g1_page_annotation.v1` |
| ANNOTATION_STATUS | `DRAFT` |
| GT_APPROVAL_STATUS | `OWNER_BLOCKED` |
| SPLIT_APPROVAL_STATUS | `OWNER_BLOCKED` |
| THRESHOLD_APPROVAL_STATUS | `OWNER_BLOCKED` |
| ADJUDICATION_STATUS | `NOT_STARTED` |
| G1_TECHNICAL_PREPARATION | `PASS` (candidato; depende de aceite humano) |
| G1_EXIT_STATUS | `PENDING_OWNER_APPROVAL` |
| TRUE_UNSEEN_HOLDOUT | `NOT_AVAILABLE` |

## Onde está cada artefato

| Artefato | Caminho |
|---|---|
| Fonte / render verification | `g1-source-and-render-verification.md` |
| Anotações geométricas | `annotations/90264135_p{10,12,13}.json` |
| Hashes das anotações | `overlays/annotation-content-hashes.json` |
| Relatório validador remoto | `overlays/g1_validation_report.json` |
| Validador offline | `scripts/validate_g1_annotations.py` |
| Overlay hashes | `overlays/overlay-registry.json` |
| Raster revisável (local) | `.local/eva-val01-g1-overlays/` |
| Split | `dataset-split-manifest.json` |
| Holdout | `holdout-protection-plan.md` |
| Famílias | `layout-family-matrix.md` |
| Thresholds (proposta) | `quality-metrics-proposal.md` |

## Overlays para revisão visual

Arquivos principais (hashes completos em `overlay-registry.json`):

| Arquivo | Função | SHA-256 (prefixo) |
|---|---|---|
| `90264135_p{10,12,13}_dpi200.png` | render oficial | ver registry |
| `p{10,12,13}_cells_overlay.png` | grade + células + IDs | `e9c5a7c4…` / `eb61979f…` / `4ee45099…` |
| `p{10,12,13}_cells_zoom.png` | zoom da região tabular | ver registry |

```text
OVERLAY_REVIEW_ACCESS=LOCAL_PATH_READY
OVERLAY_STORAGE=.local/eva-val01-g1-overlays/
OVERLAY_CHANNEL=authorized_local_or_fileserver_share_by_owner
NOTE=PNGs proprietários não versionados no Git público; Coordination disponibiliza ao revisor por canal autorizado.
```

Não foi enviado overlay a serviço externo. Não declarar recebimento pelo revisor até confirmação humana.

## Resumo geométrico das regiões anotadas

| Página | table_id | coverage | rows×cols | cells | spans (rs\|cs>1) | Notas |
|---|---|---|---|---|---|---|
| 10 | `90264135:p10:t_main` | `COMPLETE_SELECTED_REGION` | 15×6 | 64 | 2 | header + set A1–AD/AG; cabo abaixo excluído |
| 12 | `90264135:p12:t_subsets` | `COMPLETE_SELECTED_REGION` | 16×7 | 82 | 15 | blocos 50225701–40; 50225741 omitido |
| 13 | `90264135:p13:t_main` | `COMPLETE_SELECTED_REGION` | 19×6 | 86 | 2 | + `drawing_area` bbox separado; A1–AS |

Cobertura **não** declara tabela integral da página quando há linhas fora do bbox selecionado. Campos `unannotated_row_ranges` / `coverage_limitations` estão nos JSON.

## Checklist executável do owner

### A. Ground truth (páginas 10 / 12 / 13)

- [ ] Abrir PNG DPI 200 + `*_cells_overlay.png` lado a lado com o PDF
- [ ] Confirmar `table_bounding_box_px` e limites de coluna/linha
- [ ] p10: A1 presente na grade; A2=`10080192`; A3=`10090316`; A2≠A3
- [ ] p10: textos longos de Descrição e códigos citados na descrição
- [ ] p12: `50225702` é **subset_code** com rowspan; filhos AE/AH/AG distintos
- [ ] p12: conferir também 50225701 / 03 / 04 / 40 (e adjudicar AMB-P12-01 / 50225741)
- [ ] p13: `drawing_area` ≠ `component_table`
- [ ] p13: A3 código `10090316` ≠ menção `10090317` na descrição
- [ ] Rejeitar `component_code='4 5'` e fusão `10080192 10090316` como expected (só em `eva_defect_contrast`)
- [ ] Adjudicar AMB-P10-01 / AMB-P12-01 / AMB-P13-01 / AMB-P13-02
- [ ] Aprovar ou rejeitar cada célula/span/relação material

### B. Split

- [ ] Aprovar `development` vs `validation_exposed` em `dataset-split-manifest.json`
- [ ] Confirmar que nenhum PDF exposto é rotulado `true_unseen`
- [ ] Autorizar (ou negar) obtenção de novos PDFs para holdout cego

### C. Thresholds

- [ ] Revisar `quality-metrics-proposal.md`
- [ ] Aceitar/ajustar limites de fusão de códigos, false promote, spans, abstenção

### D. Evidências / assinatura

```text
REVIEWER=
REVIEW_DATE=
DOCUMENT_ID=90264135
DOCUMENT_REVISION_REVIEWED=
REVIEW_EVIDENCE=
GT_APPROVAL_STATUS=          # APPROVED | REJECTED | OWNER_BLOCKED
SPLIT_APPROVAL_STATUS=
THRESHOLD_APPROVAL_STATUS=
ADJUDICATION_NOTES=
```

## Ambiguidades

| ID | Status | Ação owner |
|---|---|---|
| AMB-P10-01 | `RESOLVED_IN_DRAFT` (A1 geometrizado) | Confirmar caixa |
| AMB-P12-01 | `PARTIAL` | Descrições 04/40 e presença 50225741 |
| AMB-P13-01 | `AMBIGUOUS` | Origem EVA `4 5` — não inventar; G2 first-loss |
| AMB-P13-02 | `PARTIAL` | Parent de AQ/AR/AS |

## Validação automática (não substitui owner)

```bash
python3 docs/12-roadmap-e-evolucao/engineering/eva-val01-g1/scripts/validate_g1_annotations.py
```

Esperado: `SUMMARY PASS`. Relatório da rodada de construção: `overlays/g1_validation_report.json`.

## Decisão recomendada à Coordination

1. Disponibilizar overlays locais ao revisor de Engenharia por canal autorizado.
2. Coletar assinatura A–D acima.
3. Somente após `GT_APPROVAL_STATUS=APPROVED` (e thresholds necessários) autorizar G2.
4. Manter `TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE` até PDFs inéditos autorizados.
