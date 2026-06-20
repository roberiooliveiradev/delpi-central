# Changelog — BOM colunar, refinamento de visão e assertividade 95% (Fase 15.8)

**Data:** 20/06/2026  
**Escopo:** skill desenho orquestra visão do chat base; usuário não envia print/zoom.  
**Playbook:** [`playbook_bom_colunar_visao_skill_desenho.md`](../roadmap/melhorias/playbook_bom_colunar_visao_skill_desenho.md)

---

## Contexto

Regressão `90263149`: OCR lia QTD da **descrição** (`6,35`, `6 PINOS`, `00120` mm), gerando críticos BOM falsos. O fix jun/2026 (`ChatDrawingBomQuantityAssertivenessService`) evita crítico, mas **pending** não substitui leitura correta da coluna QTD.

## Diretriz

| Camada | Responsabilidade |
|--------|------------------|
| Chat base (`document-vision-delpi`) | OCR, regiões, `tables[]` genérico, `TableCellRefinementPort` — **sem** vocabulário BOM/QTD/SG1010 |
| Skill (`drawing-analysis-delpi`) | Interpreta tabela como BOM; compara × SG1010; orquestra refinamento; assertividade |
| Usuário | Anexa PDF uma vez — **não** participa do loop de leitura |

Fronteira detalhada: playbook § 0.

---

## Entregas

### 15.8.0–15.8.3 (commits anteriores)

Port genérico, interpretação colunar, OCR por célula, orquestração `ChatDrawingBomVisionRefinementService`, smoke E2E `scripts/smoke_drawing_90263149_chat_e2e.py`.

### 15.8.1b — Inferência de colunas (cabecalho OCR corrompido) ✅

| Artefato | Mudança |
|----------|---------|
| `ChatDrawingBomTableInterpretationService` | Resolução exato → fuzzy → inferência por perfil colunar + layout padrão |
| `drawing_stamp.json` → `bomColumnInference` | Layouts 4/5/6 colunas, edit distance, thresholds |
| `ChatDrawingPatternsService` | Loaders `bom_column_inference_rule`, `bom_column_default_layout` |
| `drawing_validation.json` | `criticalRequiresQuantitySource` inclui `column_inferred` |
| `ChatDrawingBomQuantityAssertivenessService` | Trust para `column_inferred` |
| Testes | Fixture cabeçalho corrompido + corpo legível — QTD colunar, não da descrição |

**Limitação mitigada (15.8.2):** refinamento OCR por célula no pipeline live preenche QTD quando a linha colunar existe mas a célula QTD veio vazia.

### 15.8.2b — Parse tabular/OCR regional do corpo BOM ✅

| Artefato | Mudança |
|----------|---------|
| `ChatPdfTableStructureService` | Re-ancoragem por linha-âncora (score largura/QTD), filtro de ruído OCR, linhas parciais 2 colunas, dedupe por qualidade |
| `document_vision.json` → `tableStructure.rowParsing` | Marcadores de cabeçalho, `rowAnchorMinDigits`, padrões de ruído |
| `ChatDocumentVisionContentService` | Loaders `table_structure_header_markers`, `table_structure_noise_row_patterns`, … |
| `ChatDrawingBomTableInterpretationService` | Resolução code/qty por linha; filtro `sourceRegion=bom`; `prefer_row`; metadata via `extract_from_metadata` |
| `ChatDrawingPdfBomExtractionService` / `ChatDrawingBomVisionRefinementService` | Merge colunar preferencial |

**Resultado `90263149` live:** `columnRowCount` 12+; refinamento OCR por célula preenche QTD pending (`10090050.quantity=1`, `refined_column`); smoke E2E sem crítico `bom_quantity_mismatch`.

### 15.8.2 — Refinamento OCR por célula no pipeline live ✅

| Artefato | Mudança |
|----------|---------|
| `ChatDrawingBomTableInterpretationService.locate_quantity_cell` | Localiza `(tableId, row, qtyCol)` com código desalinhado e layout padrão |
| `ChatDrawingBomVisionRefinementService._refine_quantities` | Roda na extração (sem analyser) e na validação; triggers `missing_quantity` |
| `drawing_validation.json` | Novos triggers `missing_quantity`, `untrusted_column_quantity` |
| Testes | `test_locate_quantity_cell_*`, `test_apply_refines_missing_quantity_via_cell_ocr_*` |

**Resultado live:** 9/11 códigos refinados via Tesseract; `10090050` QTD=`1` (não `6.35` da descrição).

### 15.8.4 — Assertividade e validação ✅

| Artefato | Mudança |
|----------|---------|
| `ChatDrawingBomComparisonService` | Com sinal BOM colunar (`columnRowCount` ou `bomRows` com `quantitySource` estruturado), ignora `componentCodes` OCR ruidoso — reduz `bom_extra` falso |
| `drawing_stamp.json` → `bomComparison` | `preferStructuredRowsMinCount`, `structuredQuantitySources` |
| `ChatDrawingBomVisionRefinementService` | Merge idempotente de `codesRefined`/`attempts` entre extração e validação |
| `ChatDrawingValidationOrchestrationService` | `visionRefinement.resolved` preserva códigos refinados na 2ª passada |
| Testes | `test_structured_bom_rows_ignore_noisy_component_codes`, metadata `codesRefined` |

### 15.8.5 — Policy e follow-up ✅

| Artefato | Mudança |
|----------|---------|
| `personality_playbook.json` | Chip «Reextrair BOM do PDF» + query com `{{productCode}}` |
| `ChatDrawingFollowUpService` | Chip condicional quando há issue BOM + `visionRefinement.attempted` |
| `ChatDrawingFollowUpTurnService` | `_wants_bom_reextract` — não intercepta (reanálise com mesmo PDF) |
| `drawing-analysis-delpi-skill.md` | Proíbe pedir print; documenta chip de reextração |

### 15.8.6 — Gate assertividade 95% ✅

| Artefato | Mudança |
|----------|---------|
| `ChatDrawingValidationAssertivenessMetricsService` | `passesGate` exige `falseCriticalRate ≤ limiar` **e** `statusOk` por amostra |
| `scripts/validate_drawing_samples.py` | `--assertiveness-gate` já reporta `statusOk` por código |
| `drawing_assertiveness_baseline.json` | Baseline âncora (90263149, 90262834, 90263622, 90264227) |

### 15.8.3 (acabamento) — Retry colunas adjacentes ✅

| Artefato | Mudança |
|----------|---------|
| `drawing_stamp.json` → `bomRowRefinement.quantityColumnRetryOffsets` | `[0, -1, 1, -2, 2]` |
| `ChatDrawingBomVisionRefinementService._refine_quantity_cell` | Retry OCR em colunas vizinhas quando QTD primária falha |

---

## Gates

```bash
cd minha-delpi-ai-api

.venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_drawing_bom_table_interpretation_service.py \
  tests/unit/domain/services/test_chat_drawing_bom_quantity_assertiveness_service.py \
  tests/unit/domain/services/test_chat_drawing_validation_90263149.py \
  tests/unit/domain/services/test_chat_drawing_bom_comparison_service.py \
  tests/unit/application/services/test_chat_drawing_bom_vision_refinement_service.py \
  tests/unit/application/services/test_chat_drawing_validation_assertiveness_metrics_service.py \
  tests/unit/application/services/test_chat_drawing_follow_up_service.py -q

# Gate assertividade (requer PDFs locais / container)
DRAWING_VALIDATE_CODES=90263149,90262834,90263622,90264227 \
  .venv/bin/python scripts/validate_drawing_samples.py --assertiveness-gate

# E2E chat (container) — gate QTD: 0 críticos bom_quantity_mismatch
docker exec -e SMOKE_BASE_URL=http://delpi-gateway -e PYTHONPATH=/app \
  delpi-minha-delpi-ai-api python /app/scripts/smoke_drawing_90263149_chat_e2e.py
```

---

## Relacionado

- Assertividade QTD jun/2026: `ChatDrawingBomQuantityAssertivenessService`
- Onda 15.7 retry confiança: `ChatDrawingExtractionQualityRetryService`
