# Confirmação focal de extração — desenhos DELPI

> **Status:** jul/2026 — Onda A + Onda B (âncora `/analyser` após código resolvido).  
> **Skill:** `drawing-analysis-delpi` · **Config:** `drawing_stamp.json` → `extractionQualityRetry.confirmation`

## Problema

O loop de qualidade (`ChatDrawingExtractionQualityRetryService`) escalava **genericamente** (DPI, layout, EasyOCR) quando o score composto ficava abaixo de **95%**, sem atacar o **componente fraco** (`stamp`, `bom_scope`, `dimensions`…).

Na validação, confiança baixa apenas **rebaixava** itens PDF-dependentes para `pending` — não havia re-leitura focal antes de desistir ou carregar EasyOCR.

## Solução — confirmação dirigida (Onda A)

Entre cada tentativa de extração que **não** atinge o limiar, o pipeline executa **re-OCR Tesseract focal** nas regiões mapeadas por diagnóstico, **antes** de escalar para o próximo perfil pesado.

```text
ChatDrawingPdfExtractionService.extract_from_storage_path
  → ChatDrawingExtractionQualityRetryService.extract_until_confident
       tentativa N (standard / region_ocr / high_dpi / …)
       → ChatDrawingExtractionConfidenceService.evaluate_for_extraction
       → [score < 95%]
            → ChatDrawingExtractionDiagnosticService.build_plan
            → ChatDrawingTesseractConfirmationService.try_improve
                 → ChatDrawingRegionService.ocr_selected_drawing_regions
                 → merge regionTexts + ChatDrawingPdfExtractionService.parse_from_text
            → re-score
       → [score ≥ 95%] stoppedReason=confirmation_reached
       → [senão] próxima tentativa genérica
  → validação (gate assertivo inalterado)
```

## Módulos

| Módulo | Camada | Papel |
|--------|--------|-------|
| `ChatDrawingExtractionDiagnosticService` | domain | `reasons` + componentes fracos → `ConfirmationPlan.regions` |
| `ChatDrawingTesseractConfirmationService` | domain | Executa até `maxPasses` de re-OCR focal e re-parse |
| `ChatDrawingRegionService.ocr_selected_drawing_regions` | domain | OCR Tesseract em `stamp` / `title` / `bom` / `dimensions` |
| `ChatDrawingExtractionQualityRetryService` | domain | Orquestra confirmação entre tentativas |
| `ChatDrawingValidationAssertionService` | domain | Gate pós-extração (sem mudança na Onda A) |

## Configuração (`drawing_stamp.json`)

```json
"confirmation": {
  "enabled": true,
  "maxPasses": 2,
  "dpiMultiplier": 1.5,
  "engines": ["tesseract"],
  "componentRegions": { "stamp": ["stamp", "title"], "bom_scope": ["bom"], … },
  "reasonRegions": { "product_code_missing": ["stamp"], … }
}
```

| Chave | Default | Efeito |
|-------|---------|--------|
| `enabled` | `true` | Master switch |
| `maxPasses` | `2` | Re-diagnóstico após melhora parcial |
| `dpiMultiplier` | `1.5` | Rasterização um pouco maior que a passagem base |
| `engines` | `["tesseract"]` | Sem EasyOCR na confirmação |
| `componentRegions` | ver JSON | Regiões por componente de score |
| `reasonRegions` | ver JSON | Regiões por `reason` do score |

## Metadata (`extractionQualityRetry`)

| Campo | Significado |
|-------|-------------|
| `stoppedReason: confirmation_reached` | Confirmação focal atingiu ≥ 95% |
| `confirmationAttempts[]` | Passes com `plan`, `scoreBefore`, `scoreAfter`, `improved` |
| `sourceMetadata.stages` | Inclui `tesseract_confirmation` após confirmação |

## Onda B — âncora `/analyser` (BOM)

Após `ChatDrawingProductCodeResolutionService` resolver o código no pré-turno, se `bom_scope` ou `bom_completeness` < 95%:

```text
ChatToolContextPreTurnService (pós resolução de código)
  → ChatDrawingAnalyserBomConfirmationOrchestrationService.try_anchor_after_code_resolution
       → ChatDrawingAnalyserFetchService.fetch_root (GET /products/{code}/analyser?view=full)
       → ChatDrawingAnalyserAnchorService.build_anchor
       → ChatDrawingBomAnchorConfirmationService.try_improve_with_anchor
            → OCR focal região bom (Tesseract, mesmo dpiMultiplier da Onda A)
            → merge + parse_from_text
            → inject códigos API presentes no haystack mas ausentes em componentCodes
```

| Módulo | Camada | Papel |
|--------|--------|-------|
| `ChatDrawingAnalyserFetchService` | domain | HTTP leve do payload analyser |
| `ChatDrawingAnalyserAnchorService` | domain | `expected_codes` + gate `should_anchor_bom` |
| `ChatDrawingBomAnchorConfirmationService` | domain | Re-OCR BOM + injeção por presença no haystack |
| `ChatDrawingAnalyserBomConfirmationOrchestrationService` | application | Orquestra após código resolvido no pré-turno |

Config: `drawing_stamp.json` → `extractionQualityRetry.analyserAnchor` (`enabled`, `minWeakBomComponentScore`, `view`).

Metadata extra: `bomAnchorConfirmation.addedCodes`, `extractionQualityRetry.analyserBomAnchor`.

## Backlog

- Textos de `extraction_confidence` no checklist distinguindo «confirmação tentada» vs «não tentada».

## Testes

```bash
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_extraction_confirmation_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_analyser_bom_anchor_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_extraction_quality_retry_service.py -q
```

## Referências

- [chat-drawing-page-layout-analysis.md](./chat-drawing-page-layout-analysis.md) § Gate de confiança
- [chat-pdf-document-extraction.md](./chat-pdf-document-extraction.md)
- Playbook OCR hierárquico § retentativas
