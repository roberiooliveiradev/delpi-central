# Playbook — Validação normativa de desenhos DELPI (roadmap)

> **Status (19/06/2026):** Onda **15.0–15.7** entregue.  
> **Projeto:** Minha DELPI Chat IA  
> **Arquitetura:** inteligência transversal no [chat base](../../architecture/chat-intelligence-base.md); agente só habilita skill `drawing-analysis-delpi`.

| Campo | Valor |
|-------|-------|
| Skill | `drawing-analysis-delpi` |
| Action principal | `get_product_analyser` → `GET /products/{code}/analyser?view=full` |
| Orquestrador | `ChatDrawingValidationOrchestrationService` |
| Vocabulário checklist | `drawing_validation.json` |
| Playbooks relacionados | [Análise de desenhos](./playbook_skill_analise_desenhos_delpi.md) · [OCR hierárquico](./playbook_ocr_hierarquico_desenhos_delpi.md) · [Extração PDF](../../architecture/chat-pdf-document-extraction.md) · [Layout de página](../../architecture/chat-drawing-page-layout-analysis.md) |
| Changelog layout/confiança jun/2026 | [2026-06-drawing-layout-confidence-gate.md](../../changelog/2026-06-drawing-layout-confidence-gate.md) |
| Changelog BOM jun/2026 | [2026-06-drawing-bom-pa-families.md](../../changelog/2026-06-drawing-bom-pa-families.md) |
| Changelog validação jun/2026 | [2026-06-drawing-validation-roadmap.md](../../changelog/2026-06-drawing-validation-roadmap.md) |

**Normas de referência (RAG):** `drawing-validation-rules-delpi.md`, `validation_rules_delpi.md`, `drawing_analyser_instructions.md`.

---

## 1. Objetivo

Estender o **checklist automático** que confronta PDF × API DELPI × normas DELPI, reduzindo **falsos positivos** (reprovação indevida) e **falsos negativos** (cadastro ignorado), sem duplicar lógica no prompt do agente ou no MFE.

Pipeline canônico:

```text
PDF → ChatPdfDocumentExtractionService / document-vision-delpi
   → GET /products/{code}/analyser?view=full  (payload completo)
   → ChatDrawingAnalyserPayloadService.resolve_root_*
   → ChatDrawingValidationOrchestrationService.build_from_analyser_payload
        ├── ChatDrawingGuideStructureConsistencyService   (roteiro × estrutura)
        ├── ChatDrawingStructureValidationService         (BOM, 50xx, cotas)
        ├── ChatDrawingInspectionValidationService        (NOVO — Fase 15.3)
        ├── ChatDrawingMultipageCoverageService           (NOVO — Fase 15.4)
        └── …
   → drawing_validation.json (templates + severidade)
   → ChatDrawingValidationPresentationService (relatório + export)
```

**Regra:** PDF **não** é soberano quando contradiz Protheus — mas divergência só é **crítica** com evidência consistente nos dois lados (API + extração scoped).

---

## 2. Casos de referência (jun/2026)

### 2.1 Produto 90263622 — chicote multipágina

| Observação | Evidência | Classificação |
|------------|-----------|---------------|
| Relatório «Cadastro não encontrado» | API HTTP 200; 60 itens estrutura; 176 roteiro | **Falso negativo** (bug payload) |
| Preview `/analyser` ~194 KB > limite 100 KB | `json.loads(preview[:100k])` falha | Causa raiz Fase 15.0 |
| PDF legível, 18k chars, 17 componentes, 15 linhas BOM | `hasTitleBlock: false` | Extração parcial vs estrutura grande |
| Revisão vazia no PDF | Revisão API `20221103` | **Pendente**, não crítico |

**Lição:** validação não pode depender só de `metadata.responsePreview` truncado.

### 2.2 Produto 90262834 — montagem com PIs aninhados

| Observação | Evidência | Classificação |
|------------|-----------|---------------|
| Roteiro «50212870/71 fora da estrutura» | PIs existem sob `50230969/70` em `components[]` | **Falso positivo** |
| Nível BOM 2 vs esperado 1 | SG2010 usa `bom_level` real; regra fixa PA=0/resto=1 | **Falso positivo** |
| Inspeção QP6/QP7/QP8 ausente | API entrega `measurable_tests` / `textual_tests` | **Bug de contrato** |
| Decape 30 mm vs 6/11/5/6 | 30 mm de ensaio termoretração, não decape cabo | **Provável falso positivo** |

**Lição:** índice de estrutura deve ser **recursivo**; inspeção deve seguir contrato api-delpi; notas dimensionais precisam **classificação semântica**.

---

## 3. Mapa canônico de módulos

| Responsabilidade | Módulo | Não duplicar em |
|------------------|--------|-----------------|
| Desembrulho payload `/analyser` | `ChatDrawingAnalyserPayloadService` | use case, presenter |
| Preview truncado → `authorizedResult` | `ChatToolContextExternalActionFormatter` | — |
| Payload completo no turno | `ChatToolContextAuxiliaryService._build_drawing_analysis_enrichment` + `external_action_data` | Send/Stream inline |
| Orquestração checklist | `ChatDrawingValidationOrchestrationService` | prompt agente |
| BOM PDF × SG1010 | `ChatDrawingBomComparisonService` + `ChatDrawingStructureValidationService` | componente MFE |
| Roteiro × estrutura | `ChatDrawingGuideStructureConsistencyService` | — |
| **Índice recursivo estrutura (NOVO)** | `ChatDrawingStructureIndexService` | presenter, use case |
| **Inspeção QP (NOVO)** | `ChatDrawingInspectionValidationService` | `if QP6` na orquestração |
| **Cobertura multipágina (NOVO)** | `ChatDrawingMultipageCoverageService` | heurística no relatório |
| **Layout de página (NOVO)** | `ChatDrawingPageLayoutAnalysisService` | bboxes fixos só no fallback |
| **Confiança da leitura (NOVO)** | `ChatDrawingExtractionConfidenceService` | `legibilityScore` isolado |
| **Gate assertivo PDF (NOVO)** | `ChatDrawingValidationAssertionService` | demotion no use case |
| Cotas / decape | `ChatDrawingDimensionsExtractionService` | regex no MFE |
| Textos PT checklist | `drawing_validation.json` | strings em Python |
| Relatório / export | `ChatDrawingValidationPresentationService` | markdown ad hoc |
| Flatten estrutura (apresentação) | `product_analyser_presenter._flatten_analyser_structure_rows` | **migrar lógica para domain** |

---

## 4. Roadmap por fases (Onda 15 — validação normativa)

### Visão geral

```text
Fase 15.0 — Payload analyser completo na validação           [concluída jun/2026]
Fase 15.1 — Índice recursivo da estrutura (SG1010)          [entregue]
Fase 15.2 — Roteiro × estrutura com profundidade real        [entregue — via StructureIndex]
Fase 15.3 — Inspeção alinhada ao contrato api-delpi           [entregue]
Fase 15.4 — Cobertura multipágina (PDF parcial × API grande)  [entregue]
Fase 15.5 — Classificação de notas dimensionais             [entregue]
Fase 15.6 — Quantidades BOM, balões, registro declarativo     [entregue]
Fase 15.7 — Layout adaptativo (XY-Cut) + gate confiança ≥95%  [entregue]
```

---

### Fase 15.0 — Payload analyser na validação ✅

| ID | Entrega | DoD |
|----|---------|-----|
| 15.0.1 | `ChatDrawingAnalyserPayloadService.resolve_root_from_data` | Unwrap + normalize via presenter |
| 15.0.2 | `external_action_data` no enrichment de desenho | Turno usa payload da execução da tool |
| 15.0.3 | `authorizedResult` em metadata quando preview truncado (`/analyser`) | Só quando preview termina em `\n…` |
| 15.0.4 | Testes unitários payload + enrichment + formatter | `pytest` verde nos 3 arquivos de teste |

**Meta:** produtos com analyser > 100 KB (ex.: 90263622) não geram `product_not_found`.

---

### Fase 15.1 — Índice recursivo da estrutura

| ID | Entrega | DoD |
|----|---------|-----|
| 15.1.1 | `ChatDrawingStructureIndexService.flatten_items(structure)` | Lista `{code, type, depth, parent_code, path}` |
| 15.1.2 | `collect_all_codes(root, product_code)` | Inclui `components[]` aninhados |
| 15.1.3 | `expected_bom_level(code, path)` | PA=0; PI filho direto=1; aninhado=2+ |
| 15.1.4 | Migrar lógica de `_flatten_analyser_structure_rows` para domain | Presenter delega ao serviço |
| 15.1.5 | Fixture `test_chat_drawing_validation_90262834.py` | 50212870/71 **não** são «extra no roteiro» |

---

### Fase 15.2 — Roteiro × estrutura (profundidade)

| ID | Entrega | DoD |
|----|---------|-----|
| 15.2.1 | `ChatDrawingGuideStructureConsistencyService` usa `StructureIndexService` | `collect_expected_guide_codes` recursivo |
| 15.2.2 | `_collect_level_mismatches` usa `expected_bom_level` | Nível 2 aceito para PI aninhado |
| 15.2.3 | `ChatDrawingBomComparisonService.collect_structure_bom_codes` recursivo | MPs sob PI incluídos quando aplicável |
| 15.2.4 | Regressão 90263622 (60 itens) | BOM missing não lista PI só por estar aninhado |

---

### Fase 15.3 — Inspeção (contrato api-delpi)

| ID | Entrega | DoD |
|----|---------|-----|
| 15.3.1 | `ChatDrawingInspectionValidationService` | Domain puro |
| 15.3.2 | `has_inspection_plan`: `items[]` ou `measurable_tests` / `textual_tests` | Substitui `row.QP6` na orquestração |
| 15.3.3 | Templates `inspection_plan_ok`, `inspection_plan_missing` em `drawing_validation.json` | Gate: teste de chave |
| 15.3.4 | Severidade configurável por família PA (9026 vs 7026) | JSON, não `if` no serviço |
| 15.3.5 | Fixture payload QP real (90262834) | Não crítico quando ensaios existem |

---

### Fase 15.4 — Cobertura multipágina

| ID | Entrega | DoD |
|----|---------|-----|
| 15.4.1 | `ChatDrawingMultipageCoverageService` | Razão `pdf_codes / api_codes` |
| 15.4.2 | Limiares em `drawing_validation.json` → `validationRules.multipageCoverage` | warning < 0,7; pending < 0,4 |
| 15.4.3 | Templates `multipage_low_coverage`, `multipage_bom_partial` | Texto só em JSON |
| 15.4.4 | Fase adminDebug `validation:multipage_coverage` | `ChatDrawingMetricsService` |
| 15.4.5 | Fixture 90263622 | Item warning quando 15 BOM vs 60 API |

---

### Fase 15.5 — Notas dimensionais

| ID | Entrega | DoD |
|----|---------|-----|
| 15.5.1 | Tipos de nota em `drawing_stamp.json`: `decape_cable`, `shrink_wrap`, `machine_side` | Vocabulário centralizado |
| 15.5.2 | `ChatDrawingDimensionsExtractionService` classifica contexto antes de preencher decape | 30 mm termoretração não vira decape |
| 15.5.3 | Template `dimension_note_ambiguous` (warning) | Regressão 90262834 |
| 15.5.4 | Doc § validação dimensional atualizada | [chat-pdf-document-extraction.md](../../architecture/chat-pdf-document-extraction.md) |

---

### Fase 15.6 — Extensões e governança

| ID | Entrega | DoD |
|----|---------|-----|
| 15.6.1 | `ChatDrawingBomQuantityValidationService` | ±10% vs `validationRules.quantityToleranceRatio` |
| 15.6.2 | `ChatDrawingGuideComponentConsistencyService` | `component_code` SG2010 × estrutura do PI |
| 15.6.3 | `ChatDrawingBalloonValidationService` (fase 1: presença) | Anotações × BOM scoped |
| 15.6.4 | `drawing_validation_rules.json` + `ChatDrawingValidationRuleRegistryService` | Regras on/off por família |
| 15.6.5 | Batch `validate_drawing_library.py` + flag `--validate-report` | CI opcional |

---

### Fase 15.7 — Layout adaptativo + confiança da leitura ✅

| ID | Entrega | DoD |
|----|---------|-----|
| 15.7.1 | `ChatDrawingPageLayoutAnalysisService` (XY-Cut + classificação) | `drawing_stamp.json` → `layoutAnalysis` |
| 15.7.2 | Integração em `ChatDrawingRegionService` | `regions._layoutAnalysis` + OCR adaptativo |
| 15.7.3 | `ChatDrawingExtractionConfidenceService` | Score composto; limiar 95% |
| 15.7.4 | `ChatDrawingValidationAssertionService` | Demotion PDF-dependent; API crítica mantida |
| 15.7.5 | Templates `extraction_confidence` + `validationLayers` | Só JSON PT |
| 15.7.6 | Regressão `90264227` | BOM/cotas pending; roteiro/inspeção críticos |
| 15.7.7 | Doc [chat-drawing-page-layout-analysis.md](../../architecture/chat-drawing-page-layout-analysis.md) | Arquitetura + anti-padrões |

---

## 5. Matriz problema → fase → teste

| Problema | Fase | Fixture / teste |
|----------|------|-----------------|
| Cadastro «não encontrado» com API OK | 15.0 ✅ | `test_chat_drawing_analyser_payload_service.py` |
| PI aninhado «extra no roteiro» | 15.1–15.2 | `test_chat_drawing_validation_90262834.py` |
| Nível BOM incorreto | 15.2 | idem |
| Inspeção ausente com dados QP | 15.3 | payload `measurable_tests` |
| PDF multipágina, BOM parcial | 15.4 | `test_chat_drawing_validation_90263622.py` |
| 30 mm termoretração vs decape | 15.5 | `test_chat_drawing_dimensions_extraction_service.py` |
| OCR ruim reprova BOM/cotas | 15.7 | `test_chat_drawing_validation_90264227.py` |
| Layout BOM deslocado | 15.7 | `test_chat_drawing_page_layout_analysis_service.py` |

---

## 6. Gates CI (por PR)

```bash
cd minha-delpi-ai-api

# Onda 15 — mínimo ao alterar validação de desenho
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_analyser_payload_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_drawing_analysis_enrichment.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_orchestration_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_guide_structure_consistency_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_bom_comparison_service.py -q

# Após Fase 15.1+
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90262834.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90263622.py -q

# Após Fase 15.7
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_page_layout_analysis_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_extraction_confidence_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_assertion_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90264227.py -q

# Homologação batch (opcional)
.venv/bin/python scripts/validate_drawing_samples.py
```

---

## 7. O que NÃO fazer

- Aumentar **somente** `CHAT_TOOL_RESPONSE_PREVIEW_MAX_CHARS` sem `authorizedResult` / `external_action_data`.
- Marcar inspeção **crítica** com `row.QP6` quando o contrato api-delpi usa listas aninhadas.
- Reprovar multipágina por BOM incompleta **sem** item `multipage_low_coverage`.
- Duplicar flatten de estrutura no MFE ou no use case Send/Stream.
- Textos PT novos fora de `drawing_validation.json` / `drawing_stamp.json` — ver `assistant-content-json.mdc`.

---

## 8. Ordem de implementação recomendada

1. **15.1** — `ChatDrawingStructureIndexService` (desbloqueia 90262834 e melhora 90263622).
2. **15.3** — inspeção (quick win, contrato claro).
3. **15.4** — cobertura multipágina (transparência 90263622).
4. **15.5** — notas dimensionais (90262834).
5. **15.6** — quantidades, balões, registry declarativo.

---

## 9. Referências cruzadas

| Documento | Conteúdo |
|-----------|----------|
| [inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) | MVP skill + validação |
| [inteligencia-chat-onda-14-ocr-hierarquico-desenhos.md](../inteligencia-chat-onda-14-ocr-hierarquico-desenhos.md) | Extração que alimenta validação |
| [chat-pdf-document-extraction.md](../../architecture/chat-pdf-document-extraction.md) | BOM, cotas, famílias PA |
| [assistant-content-catalog.md](../../architecture/assistant-content-catalog.md) | `drawing_validation.json` |
