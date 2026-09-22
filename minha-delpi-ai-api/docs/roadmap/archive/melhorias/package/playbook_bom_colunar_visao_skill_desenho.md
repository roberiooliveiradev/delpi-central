# Playbook — BOM colunar, refinamento de visão e assertividade 95% (desenhos DELPI)

> **Status (20/06/2026):** **Entregue no código** — Fases **15.8.0–15.8.6** implementadas; homologação live **`90263149` parcial** (QTD âncora `10090050` OK; `bom_extra` / códigos OCR fantasma ainda em evolução). Changelog: [`2026-06-drawing-bom-column-vision-refinement.md`](../../changelog/2026-06-drawing-bom-column-vision-refinement.md).  
> **Pré-requisitos:** Onda 13 (visão), Onda 14 (OCR regional), Onda 15.6 (quantidades BOM), Onda 15.7 (retry confiança ≥95%), assertividade jun/2026 (`ChatDrawingBomQuantityAssertivenessService`).  
> **Arquitetura:** [chat base](../../architecture/chat-intelligence-base.md) = visão **genérica** (regiões, tabelas, células); [skill `drawing-analysis-delpi`](./playbook_skill_analise_desenhos_delpi.md) = **BOM, SG1010, cotas DELPI, assertividade** — ver `.cursor/rules/chat-intelligence-base.mdc`, `centralized-rules-first.mdc`, `assistant-content-json.mdc`.

| Campo | Valor |
|-------|-------|
| Onda / fase | **15.8** — BOM colunar + loop skill → visão |
| Meta | **≥95% assertividade** de validação BOM (crítico certo + aprovado certo) na homologação `desenhos/` |
| Caso âncora | `90263149.pdf` — QTD OCR da descrição vs coluna QTD × milheiro SG1010 |
| Skills | `document-vision-delpi` (chat base, **sem** semântica DELPI) + `drawing-analysis-delpi` (BOM, validação) |

---

## 0. Fronteira chat comum × skill desenho (obrigatório)

O **chat comum** e a skill `document-vision-delpi` **não** conhecem vocabulário de desenho técnico DELPI. Quem sabe o que é BOM, QTD, SG1010, milheiro MI, intermediário 50xx ou decape é **somente** a skill `drawing-analysis-delpi` (e bundles `drawing_*.json`).

| Chat comum / visão genérica | Skill desenho |
|----------------------------|---------------|
| Região retangular + OCR (`region`, `bbox`, `text`) | Interpreta região como «lista de materiais DELPI» |
| Tabela genérica: `columns[]`, `rows[]`, `cells[][]` | Mapeia colunas → Pos/Código/QTD/UM/Descrição |
| Re-OCR de **célula** por `(tableId, rowIndex, colIndex)` | Decide **qual** coluna é QTD e se bate SG1010 |
| `documentVision.tables`, `textExcerpt`, `legible` | `bomRows`, `validationScopes`, `drawingAnalysis` |
| Perfil layout `drawing_delpi` = preset de **bboxes** (não semântica) | Regras normativas, checklist, crítico vs pending |
| Intent `attachment_document`, «extrair texto do PDF» | Intent «validar desenho», «conferir BOM com Protheus» |

```text
┌─────────────────────────────┐     ┌──────────────────────────────┐
│  Chat base                  │     │  Skill drawing-analysis-delpi │
│  document-vision-delpi      │     │  (só quando skill ativa)      │
│  ─────────────────────      │     │  ──────────────────────────  │
│  OCR, regiões, tabelas      │────▶│  bomRows, QTD×SG1010, 50xx   │
│  Port: refine_table_cell()  │◀────│  Orquestra refinamento       │
│  ZERO: BOM, QTD, SG1010     │     │  ZERO: Tesseract duplicado   │
└─────────────────────────────┘     └──────────────────────────────┘
```

**Proibido no chat comum** (prompt global, turn prep, `document-vision-delpi-skill.md`, serviços `ChatPdf*` genéricos):

- Mencionar BOM, lista de materiais, SG1010, QTD, decape, carimbo DELPI, família PA 9026.
- Parse de linha como «componente de desenho» — só entrega texto/tabela bruta.
- Validação ou severidade (crítico/pending) — skill exclusiva.
- Follow-up «Validar BOM» no pipeline genérico — só `ChatDrawingFollowUpService` com skill ativa.

**Dívida legada (não ampliar):** serviços `ChatDrawing*` e `ChatDocumentVisionBomService` vivem no pacote domain por histórico Onda 12–14; **novo código 15.8** introduz port genérico no chat base e move interpretação BOM para camada skill/application de desenho. Não criar `ChatDocumentVisionBomColumnService` no núcleo genérico.

---

## 1. Princípio operacional

```text
PDF já anexado
  → chat base: lê regiões/tabelas/células (vocabulário neutro)
  → skill desenho: interpreta tabela como BOM, compara × SG1010, pede refine_table_cell se QTD suspeita
  → usuário: NÃO participa do loop de leitura
```

| Responsabilidade | Camada | Módulo canônico |
|------------------|--------|-----------------|
| OCR regional, DPI, fusão, retry global | Chat base | `ChatPdfDocumentExtractionService`, `ChatPdfRegionOcrEngineService` |
| Estrutura tabular genérica (colunas/linhas/células) | Chat base | **`ChatPdfTableStructureService`** (novo) |
| Re-OCR de célula por coordenadas de tabela | Chat base | **`ChatPdfTableCellRefinementService`** (novo) + port `TableCellRefinementPort` |
| Preset bboxes layout desenho (sem parse BOM) | Chat base (perfil) | `drawing_delpi` em `ChatPdfDocumentExtractionService` — só geometria |
| Mapear tabela → `bomRows`; cabeçalho QTD | **Skill desenho** | **`ChatDrawingBomTableInterpretationService`** (novo) |
| Loop refinamento quando QTD suspeita | **Skill desenho** (application) | **`ChatDrawingBomVisionRefinementService`** (novo) |
| Rejeitar ruído OCR; crítico vs pending | Skill desenho | `ChatDrawingBomQuantityAssertivenessService` |
| Comparação PDF × SG1010 | Skill desenho | `ChatDrawingBomQuantityValidationService` |
| Relatório / checklist | Skill desenho | `ChatDrawingValidationOrchestrationService` |
| Vocabulário BOM/QTD/50xx, limiares | JSON skill | `drawing_stamp.json`, `drawing_validation.json` |
| Vocabulário OCR/tabela genérico | JSON visão | `document_vision.json` → `pdfExtraction.tableStructure` |
| Policy «não pedir print» | Skill policy | `drawing-analysis-delpi-skill.md` |

**Proibido** (`.cursor/rules/centralized-rules-first.mdc`):

- Pedir print, zoom, recorte ou confirmação manual ao usuário.
- Duplicar OCR na skill — skill **orquestra** port de visão, não Tesseract.
- Texto PT / regex / limiares fora dos bundles corretos (`document_vision.json` vs `drawing_*.json`).
- Crítico BOM antes da skill esgotar refinamento via port genérico.
- Ensinar o **chat comum** ou LLM base o que é BOM/QTD/SG1010 fora do turno com skill desenho ativa.

---

## 2. Situação atual vs alvo

### 2.1 Hoje

| Aspecto | Comportamento | Limite |
|---------|---------------|--------|
| OCR BOM | Região `bom` inteira → texto → `_parse_bom_line` | QTD = primeiro número plausível na **linha** (inclui descrição: `6,35`, `6 PINOS`, `00120`) |
| Retry extração | `ChatDrawingExtractionQualityRetryService` até confiança **95%** | Retry **global** (DPI/layout); não isola coluna QTD |
| Assertividade | `ChatDrawingBomQuantityAssertivenessService` + gate batch | Evita crítico falso → **pending**; comparação BOM preferencial por linhas colunar (`bomComparison`); gate exige `statusOk` |
| Skill policy | Usa `documentVision` / `visionRefinement` | Proíbe pedir print; chip «Reextrair BOM» documentado |
| Follow-up | `ChatDrawingFollowUpService` — chips fixos + **«Reextrair BOM do PDF»** condicional | Reanalisa com mesmo anexo quando há issue BOM + `visionRefinement` |

### 2.2 Alvo

| Aspecto | Comportamento |
|---------|---------------|
| Parse BOM | Cabeçalho `Pos \| Código \| QTD \| UM \| Descrição` → colunas com bbox |
| QTD | Lida preferencialmente da **coluna QTD** (`quantitySource: column`) |
| Refinamento | `reason=quantity_from_description` → crop célula QTD da linha → re-OCR → atualiza `bomRows` |
| Crítico | Só após refinamento esgotado **e** evidência `trusted=true` |
| Pending | Visão tentou perfis de refinamento e não obteve evidência forte |
| Assertividade | `false_critical_rate < 5%` na suite `desenhos/` (meta 95%) |

### 2.3 Caso âncora 90263149

| Código | QTD coluna (PDF) | ×1000 (MI) | SG1010 | OCR linha (ruído) |
|--------|------------------|------------|--------|-------------------|
| 10080010 | 1 | 1000 | 1000 ✓ | `6,35` da descrição |
| 10080044 | 2 | 2000 | 2000 ✓ | idem |
| 50212969 | 1 PI | 1 MI | 1 MI ✓ | — |

**Esperado pós-15.8 (unitário):** 0 críticos `bom_quantity_mismatch` em fixture OCR ruidoso (`test_chat_drawing_validation_90263149.py`).

**Homologação live `90263149` (20/06/2026):** `10090050.quantity=1`, `quantitySource=refined_column`; `visionRefinement.resolved` preservado entre passadas; `bom_extra` reduzido vs OCR bruto — **pendente** zerar críticos estruturais (códigos fantasma em linhas colunar trusted, QTD residual em `10500020`/`10500075`).

---

## 3. Fluxo alvo

```text
ChatPdfDocumentExtractionService (perfil drawing_delpi — só layout/regiões)
  → documentVision.tables[] + textExcerpt (contrato genérico, chat base)
  → ChatDrawingPdfExtractionService (skill — só com drawing-analysis ativa)
       → ChatDrawingBomTableInterpretationService → bomRows
       → ChatDrawingBomVisionRefinementService.refine_if_needed(...)
            → TableCellRefinementPort.refine_cell(tableId, row, colQtd)
            → merge bomRows; quantitySource=column
  → ChatDrawingValidationOrchestrationService.build(...)
```

**Turno único:** refinamento no mesmo turno, sem tool LLM extra. **Chat comum** não executa interpretação BOM — só enrichment de desenho com skill ativa.

---

## 4. Contrato de dados

### 4.0 Chat base — `documentVision.tables[]` (genérico)

Skill-agnostic; o chat comum **não** sabe que a tabela é BOM:

```json
{
  "tableId": "region_bom_p0",
  "sourceRegion": "bom",
  "columns": [{ "index": 2, "headerText": "QTD", "bbox": [0.18, 0.04, 0.22, 0.35] }],
  "rows": [{ "index": 0, "cells": [{ "col": 2, "text": "2" }] }]
}
```

### 4.1 Skill desenho — extensão `bomRows[]`

```json
{
  "code": "10080044",
  "quantity": "2",
  "description": "CABO …",
  "quantitySource": "column | line_heuristic | annotation | refined_column",
  "quantityTrusted": true,
  "quantityRefinement": {
    "attempted": true,
    "attemptId": "bom_qty_cell_2x",
    "reason": "quantity_from_description",
    "engines": ["tesseract"],
    "cellBbox": [0.12, 0.08, 0.18, 0.095]
  }
}
```

### 4.2 Metadata skill — `pdf_extract.bomVisionRefinement`

```json
{
  "triggered": true,
  "codesRefined": ["10080010", "10080044"],
  "stoppedReason": "all_resolved | max_attempts | no_column_layout",
  "attempts": [
    { "attemptId": "column_detect", "success": true },
    { "attemptId": "row_cell_ocr", "codes": ["10080044"], "success": true }
  ]
}
```

### 4.3 Checklist item (sem texto ao usuário pedindo print)

Campos opcionais para adminDebug / export — **não** viram pergunta ao usuário:

| Campo | Uso |
|-------|-----|
| `pdfScope` | Já existe — ex.: `BOM — região superior` |
| `visionRefinement` | `{ attempted, resolved, reason }` — metadado técnico |
| `recommendation` | Ação de **engenharia** (corrigir desenho/Protheus), não «envie print» |

---

## 5. Roadmap Fase 15.8 (entregas)

### 15.8.0 — Port e contrato genérico (chat base) ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.0.1 | `TableCellRefinementPort` | domain/port | ✅ |
| 15.8.0.2 | `ChatPdfTableStructureService` | domain (chat base) | ✅ |
| 15.8.0.3 | `ChatPdfTableCellRefinementService` | infrastructure/domain | ✅ |
| 15.8.0.4 | `document_vision.json` → `pdfExtraction.tableStructure` | JSON | ✅ |
| 15.8.0.5 | Testes sem vocabulário DELPI | tests | ✅ `test_chat_pdf_table_structure_service.py` |

### 15.8.1 — Interpretação tabular BOM (skill desenho) ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.1.1 | `ChatDrawingBomTableInterpretationService` | domain (skill) | ✅ |
| 15.8.1.2 | Vocabulário cabeçalho BOM em `drawing_stamp.json` | JSON skill | ✅ `bomColumnHeaders` |
| 15.8.1.3 | Integração em `ChatDrawingPdfBomExtractionService` | skill | ✅ |
| 15.8.1.4 | Testes | tests | ✅ |

### 15.8.1b — Inferência de colunas com cabeçalho OCR corrompido ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.1b.1 | Resolução em 3 passadas: exato → fuzzy (edit distance) → inferência por perfil colunar | domain (skill) | `resolve_column_indices` |
| 15.8.1b.2 | `drawing_stamp.json` → `bomColumnInference` | JSON skill | layouts 4/5/6 colunas, `fuzzyHeaderMaxEditDistance`, `minBodyRowsForInference` |
| 15.8.1b.3 | `quantitySource: column_inferred` + trust em assertiveness | domain (skill) | `criticalRequiresQuantitySource` inclui `column_inferred` |
| 15.8.1b.4 | Testes fixture cabeçalho corrompido + corpo legível | tests | `10090050` QTD=`1`, não `6.35` da descrição |

**Limitação mitigada (15.8.2b):** parse tabular re-ancora após ruído OCR e linhas parciais (`10090050 | descrição`); QTD ausente vira `pending`, não `6.35` da descrição.

Loader: `ChatDrawingPatternsService.bom_column_inference_rule` / `bom_column_default_layout`.

### 15.8.2 — Refinamento de célula (skill orquestra, chat base executa) ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.2.1 | `ChatDrawingBomTableInterpretationService.locate_quantity_cell` | domain (skill) | Código desalinhado + coluna QTD por layout |
| 15.8.2.2 | Chama `TableCellRefinementPort.refine_cell` no pipeline live | application (skill) | Com ou sem analyser; `storagePath` + bbox |
| 15.8.2.3 | Triggers `missing_quantity` / `untrusted_column_quantity` | JSON skill | `drawing_validation.json` → `refinementTriggers` |
| 15.8.2.4 | Regressão 90263149 live | tests + container | `10090050.quantity=1`, `quantitySource=refined_column` |

### 15.8.2b — Parse tabular/OCR regional do corpo BOM ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.2b.1 | `ChatPdfTableStructureService` — re-ancoragem, ruído, linhas parciais | chat base | `document_vision.json` → `tableStructure.rowParsing` |
| 15.8.2b.2 | Dedupe prefere tabela mais rica (`structuredTables` × `regionTexts`) | chat base | `_table_quality` |
| 15.8.2b.3 | Interpretação por linha (código/QTD desalinhados) + filtro `sourceRegion=bom` | skill | `ChatDrawingBomTableInterpretationService` |
| 15.8.2b.4 | Merge colunar × linha (`prefer_row`) | skill | `10090050`: `quantity=null`, não `6.35` |
| 15.8.2b.5 | Testes snippet OCR real + dedupe | tests | `test_chat_pdf_table_structure_service.py` |

### 15.8.3 — Orquestração refinamento (skill application) ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.3.1 | `ChatDrawingBomVisionRefinementService.refine_if_needed` | application (**skill**) | ✅ extração + validação |
| 15.8.3.2 | `refinementTriggers` em `drawing_validation.json` | JSON skill | ✅ incl. `missing_quantity`, `untrusted_column_quantity` |
| 15.8.3.3 | Merge idempotente `bomRows` + `codesRefined` | application (skill) | ✅ acumula entre passadas |
| 15.8.3.4 | adminDebug `drawing:bom_qty_refine` | application (skill) | ✅ |
| 15.8.3.5 | Ponto único: `ChatDrawingPdfExtractionService` / enrichment desenho | guardrail | ✅ |
| 15.8.3.6 | Retry OCR em colunas adjacentes + plausibilidade QTD | application (skill) | ✅ `quantityColumnRetryOffsets`; `quantityMaxDigits` |

### 15.8.4 — Assertividade e validação ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.4.1 | Assertiveness consulta `quantitySource=column|refined_column` como trusted preferencial | domain | ✅ |
| 15.8.4.2 | `drawingAnalysis.visionRefinement` metadado | domain | ✅ `resolved`, `codesRefined`, `attemptCount` |
| 15.8.4.3 | Regressão `test_chat_drawing_validation_90263149.py` | tests | ✅ 0 críticos QTD em fixture; live parcial |
| 15.8.4.4 | Comparação BOM estruturada | domain | ✅ `ChatDrawingBomComparisonService` + `bomComparison` JSON |
| 15.8.4.5 | Regressão assertiveness existente verde | tests | ✅ `test_chat_drawing_bom_quantity_assertiveness_service.py` |

### 15.8.5 — Policy e follow-up (sem pedir anexo extra) ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.5.1 | Atualizar `drawing-analysis-delpi-skill.md` | policy | ✅ |
| 15.8.5.2 | `ChatDrawingFollowUpService` — chip «Reextrair BOM do PDF» | application | ✅ condicional; priorizado nos 6 chips |
| 15.8.5.3 | Queries em `personality_playbook.json` → `drawingFollowUpQueries` | JSON | ✅ `{{productCode}}` |
| 15.8.5.4 | `ChatDrawingFollowUpTurnService._wants_bom_reextract` | application | ✅ não intercepta — reanálise com mesmo PDF |

### 15.8.6 — Métricas assertividade 95% ✅

| ID | Entrega | Camada | DoD |
|----|---------|--------|-----|
| 15.8.6.1 | `ChatDrawingValidationAssertivenessMetricsService` | application | ✅ `falseCriticalRate`, `statusOk`, `pendingRate` |
| 15.8.6.2 | `scripts/validate_drawing_samples.py --assertiveness-gate` | scripts | ✅ falha se `falseCriticalRate > 0.05` **ou** `statusOk` falso |
| 15.8.6.3 | Baseline `desenhos/` commitada em fixture JSON (sem PDFs) | tests | ✅ `drawing_assertiveness_baseline.json` |
| 15.8.6.4 | Homologação batch documentada | doc | ✅ § 7 abaixo |

---

## 6. Configuração JSON (novas chaves)

### 6.1 `document_vision.json` (chat base — genérico)

```json
{
  "pdfExtraction": {
    "tableStructure": {
      "enabled": true,
      "maxRows": 40,
      "minColumns": 3,
      "rowParsing": {
        "headerScanMaxLines": 24,
        "rowAnchorMinDigits": 8,
        "minPartialRowColumns": 2,
        "noiseRowPatterns": ["^[DO\\s|lo/@\"'.]+$"]
      },
      "cellRefinement": {
        "maxAttempts": 3,
        "dpiMultiplier": 2.0,
        "cellPadding": 0.005
      }
    }
  }
}
```

Loader: `ChatDocumentVisionContentService`.

### 6.2 `drawing_stamp.json` (skill desenho)

```json
{
  "bomColumnHeaders": {
    "position": ["POS", "POS.", "ITEM"],
    "code": ["CÓDIGO", "CODIGO", "COD", "CÓD"],
    "quantity": ["QTD", "QTD.", "QTDE", "QUANT"],
    "unit": ["UM", "UN", "UNID"],
    "description": ["DESCRIÇÃO", "DESCRICAO", "DESC", "DES"]
  },
  "bomRowRefinement": {
    "enabled": true,
    "maxAttempts": 3,
    "dpiMultiplier": 2.0,
    "cellHorizontalPadding": 0.005,
    "engines": ["tesseract"],
    "quantityColumnRetryOffsets": [0, -1, 1, -2, 2]
  },
  "bomComparison": {
    "preferStructuredRowsMinCount": 2,
    "structuredQuantitySources": ["column", "column_inferred", "refined_column"]
  },
  "bomColumnInference": {
    "enabled": true,
    "fuzzyHeaderMaxEditDistance": 3,
    "minBodyRowsForInference": 2,
    "minColumnMatchScore": 0.45,
    "quantityMaxDigits": 4,
    "defaultLayouts": {
      "4": ["position", "code", "quantity", "description"],
      "5": ["position", "code", "quantity", "unit", "description"],
      "6": ["position", "code", "quantity", "unit", "description", "notes"]
    }
  }
}
```

Loader: `ChatDrawingPatternsService` (`bom_column_inference_rule`, `bom_row_refinement_rule`, `bom_comparison_rule`, `bom_structured_quantity_sources`).

### 6.3 `personality_playbook.json` (follow-up skill)

```json
{
  "drawingFollowUpChips": ["…", "Reextrair BOM do PDF", "Reanalisar desenho"],
  "drawingFollowUpQueries": {
    "Reextrair BOM do PDF": "reextraia a tabela de materiais do desenho {{productCode}} com o PDF anexado"
  }
}
```

Loader: `ChatDrawingFollowUpService` via `ContentService.personality_playbook()`.

### 6.4 `drawing_validation.json` → `bomQuantitySemantics`

```json
{
  "refinementTriggers": [
    "missing_quantity",
    "untrusted_column_quantity",
    "quantity_from_description",
    "decimal_piece_quantity",
    "intermediate_length_as_quantity",
    "quantity_api_crosscheck"
  ],
  "refinementExhaustedPending": true,
  "criticalRequiresQuantitySource": ["column", "column_inferred", "refined_column", "annotation"]
}
```

### 6.5 `stream.json` (opcional)

Estágios SSE genéricos: `vision:table_structure`, `vision:table_cell_refine` (textos em JSON). Estágios skill: `drawing:bom_qty_refine` — só com skill ativa.

---

## 7. Gates CI e homologação

```bash
cd minha-delpi-ai-api

# Unit — Fase 15.8 mínimo (chat base genérico)
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_pdf_table_structure_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_pdf_table_cell_refinement_service.py -q

# Unit — skill desenho
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_bom_table_interpretation_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_drawing_bom_vision_refinement_service.py -q
# Unit — skill desenho (15.8.4–15.8.6)
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_bom_comparison_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_drawing_validation_assertiveness_metrics_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_drawing_follow_up_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_drawing_follow_up_turn_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90263149.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_bom_quantity_assertiveness_service.py -q

# Regressão Onda 15 existente
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_extraction_quality_retry_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90262834.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90263622.py -q

# Homologação local (PDFs em desenhos/, gitignored)
DRAWING_VALIDATE_CODES=90263149,90262834,90263622,90264227 \
  .venv/bin/python scripts/validate_drawing_samples.py --assertiveness-gate

# Diagnóstico live (container) — extração + validação offline
docker exec -e PYTHONPATH=/app delpi-minha-delpi-ai-api python /app/scripts/_diag_90263149.py

# E2E chat real (container) — gate assertividade QTD (0 críticos bom_quantity_mismatch)
docker exec -e SMOKE_BASE_URL=http://delpi-gateway -e PYTHONPATH=/app \
  delpi-minha-delpi-ai-api python /app/scripts/smoke_drawing_90263149_chat_e2e.py

# Smoke desenho
.venv/bin/python scripts/smoke_drawing_analyser.py
```

**Live OCR** (sem Tesseract local): rodar no container `delpi-minha-delpi-ai-api` — ver `.cursor/rules/test-and-commit.mdc`.

---

## 8. Matriz problema → entrega → teste

| Problema | Entrega | Teste |
|----------|---------|-------|
| QTD da descrição vira crítico BOM | 15.8.1–15.8.4 | `test_chat_drawing_validation_90263149.py` |
| `componentCodes` OCR gera `bom_extra` falso | 15.8.4.4 | `test_structured_bom_rows_ignore_noisy_component_codes` |
| Retry global não corrige coluna | 15.8.2–15.8.3 | `test_chat_drawing_bom_vision_refinement_service.py` |
| Skill pede print ao usuário | 15.8.5 | `drawing-analysis-delpi-skill.md` + `test_chat_drawing_follow_up_turn_service.py` |
| Assertividade < 95% na biblioteca | 15.8.6 | `validate_drawing_samples.py --assertiveness-gate` |
| Layout BOM sem cabeçalho | 15.8.1 fallback | `_parse_bom_line` + pending, não crítico |
| Duplicação OCR skill/visão | guardrail § 1 | Code review — skill só orquestra |

---

## 9. Integração com serviços existentes

| Serviço | Camada | Papel na 15.8 |
|---------|--------|---------------|
| `ChatDrawingExtractionQualityRetryService` | skill (extração) | Retry global PDF; complementar ao refinamento de célula |
| `ChatDrawingBomQuantityAssertivenessService` | skill | Pós-refinamento; crítico vs pending |
| `ChatDocumentVisionBomService` | skill (legado) | Fallback line heuristic; **não** estender com semântica colunar no chat base |
| `ChatPdfRegionOcrEngineService` | chat base | Motor OCR das células |
| `ChatDocumentVisionService` | chat base | Emite `tables[]`; merge neutro |
| `ChatDrawingPdfExtractionService` | skill | Fachada que liga visão genérica + interpretação DELPI |
| `ChatDrawingBomComparisonService` | skill | Comparação PDF × SG1010; modo estruturado (`bomComparison`) |
| `ChatDrawingBomVisionRefinementService` | application (skill) | Loop refinamento; merge `codesRefined` idempotente |
| `ChatDrawingValidationAssertivenessMetricsService` | application | Gate batch 95% (`falseCriticalRate` + `statusOk`) |
| `ChatDrawingFollowUpService` | application | Chip «Reextrair BOM do PDF» condicional |

---

## 10. O que NÃO fazer

- Colocar parse BOM, SG1010 ou «QTD» em `ChatPdfDocumentExtractionService`, `ChatDocumentVisionTurnService` ou turn prep genérico.
- Expor `bomRows` no metadata de anexo genérico (`attachment_document` sem skill desenho).
- Estágios SSE ou activity strings com «BOM» no fluxo de visão genérica.
- Implementar OCR colunar **nomeado** `BomColumn` no pacote chat base — usar `TableStructure` / `TableCell`.
- Ensinar o LLM do chat comum sobre desenhos DELPI via prompt global — só policies da skill quando ativa.

---

## 11. Ordem de implementação (concluída 20/06/2026)

1. **15.8.0** — port + tabela genérica no chat base ✅
2. **15.8.1 / 15.8.1b** — interpretação BOM + inferência colunas ✅
3. **15.8.2 / 15.8.2b** — refinamento célula + parse tabular corpo ✅
4. **15.8.3** — loop skill + retry colunas adjacentes ✅
5. **15.8.4–15.8.6** — assertividade, policy, gate 95% ✅

### Próximo (pós-15.8 — homologação live)

| Item | Objetivo |
|------|----------|
| Filtro código BOM × SG1010 fuzzy | Reduzir `bom_extra` quando OCR troca dígitos (`10080106` vs `10080010`) |
| Validação código antes de `quantityTrusted` | Não confiar linha colunar cujo código não existe no analyser nem é 50xx |
| Bbox real por célula | Substituir grade uniforme em `apply_cell_bboxes` |
| Gate live `--assertiveness-gate` | Zerar críticos em `90263149` na suite completa |

---

## 12. Referências cruzadas

| Documento | Conteúdo |
|-----------|----------|
| [playbook_validacao_desenhos_delpi_roadmap.md](./playbook_validacao_desenhos_delpi_roadmap.md) | Onda 15 — fases 15.0–15.8 ✅ (homologação live parcial) |
| [2026-06-drawing-bom-column-vision-refinement.md](../../changelog/2026-06-drawing-bom-column-vision-refinement.md) | Changelog Fase 15.8 |
| [playbook_ocr_hierarquico_desenhos_delpi.md](./playbook_ocr_hierarquico_desenhos_delpi.md) | § 14.5 BOM por região |
| [playbook_skill_visao_documentos_ocr_delpi.md](./playbook_skill_visao_documentos_ocr_delpi.md) | Skill `document-vision-delpi` |
| [playbook_skill_analise_desenhos_delpi.md](./playbook_skill_analise_desenhos_delpi.md) | Skill `drawing-analysis-delpi` |
| [chat-pdf-document-extraction.md](../../architecture/chat-pdf-document-extraction.md) | Pipeline PDF + BOM |
| [chat-drawing-page-layout-analysis.md](../../architecture/chat-drawing-page-layout-analysis.md) | XY-Cut + bboxes |
| [chat-intelligence-base.md](../../architecture/chat-intelligence-base.md) | Mapa de serviços |
| [assistant-content-catalog.md](../../architecture/assistant-content-catalog.md) | Bundles JSON |
| `.cursor/rules/presentation-operational-decoupling.mdc` | Avisos fora do presenter — metadado vs markdown |

---

## 13. Critérios de aceite (Fase 15.8)

- [x] Chat base expõe `tables[]` **sem** campos `bomRows` / `quantity` semânticos.
- [x] Nenhum serviço `ChatPdf*` referencia SG1010, BOM ou milheiro MI.
- [ ] `90263149` live: 0 erros críticos BOM após pipeline skill completo (unitário OK; live parcial).
- [x] `bomRows` de itens comparados trazem `quantitySource` ∈ `{column, column_inferred, refined_column}` quando layout tabular detectado.
- [x] Nenhum template `recommendation` ou policy pede print/zoom/recorte ao usuário.
- [x] Refinamento roda no mesmo turno, sem nova tool LLM obrigatória.
- [ ] `false_critical_rate ≤ 5%` **e** `statusOk` na lista de homologação configurada (gate implementado; batch depende de PDFs locais).
- [x] Zero string PT / regex / limiar novo fora de `drawing_stamp.json` / `drawing_validation.json` / `personality_playbook.json` (exceto loaders).
- [x] Regressões Onda 15.7 e assertiveness jun/2026 permanecem verdes.
