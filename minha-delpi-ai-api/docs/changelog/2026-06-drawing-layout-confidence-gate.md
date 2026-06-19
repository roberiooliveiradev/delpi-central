# Changelog — layout adaptativo + gate de confiança (jun/2026)

## Resumo

Três camadas transversais na validação/extração de desenhos DELPI:

1. **Layout de página (XY-Cut)** — detecta regiões antes do OCR regional.
2. **Retentativas de extração** — repete OCR com perfis escalonados até confiança ≥ 95% ou estagnação.
3. **Gate de confiança ≥ 95%** — divergências dependentes do PDF viram `pending` quando a leitura é incerta; críticos da API (roteiro, inspeção) permanecem.

## Commits

| Commit | Escopo |
|--------|--------|
| `5b502c86` | Gate confiança — `ChatDrawingExtractionConfidenceService`, `ChatDrawingValidationAssertionService`, `validationLayers` |
| `34fbc0ae` | Layout XY-Cut — `ChatDrawingPageLayoutAnalysisService`, integração `ChatDrawingRegionService` |
| Onda 15.7.8 | Retentativas extração — `ChatDrawingExtractionQualityRetryService`, `evaluate_for_extraction` |

## Módulos novos

| Serviço | Responsabilidade |
|---------|------------------|
| `ChatDrawingPageLayoutAnalysisService` | XY-Cut + classificação stamp/title/bom/dimensions |
| `ChatDrawingExtractionQualityRetryService` | Repete extração com perfis DPI/layout até score ≥ 95% |
| `ChatDrawingExtractionConfidenceService` | Score composto; `evaluate_for_extraction` (pré-validação) e `evaluate` (com checklist) |
| `ChatDrawingValidationAssertionService` | Demotion assertiva antes de `_package` |

## JSON

| Bundle | Seção |
|--------|-------|
| `drawing_stamp.json` | `layoutAnalysis`, `extractionQualityRetry` |
| `drawing_validation.json` | `validationLayers`, template `extraction_confidence` |

## Regressão 90264227

Com OCR parcial e `hasTitleBlock: false`:

- Confiança ~50% → BOM/cotas **pendentes**
- Roteiro MP 90350413 + inspeção ausente → **críticos** mantidos

## Documentação

- [chat-drawing-page-layout-analysis.md](../architecture/chat-drawing-page-layout-analysis.md)
- [playbook_validacao_desenhos_delpi_roadmap.md](../roadmap/melhorias/playbook_validacao_desenhos_delpi_roadmap.md) § 15.7

## CI sugerido

```bash
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_page_layout_analysis_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_extraction_confidence_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_extraction_quality_retry_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_assertion_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90264227.py -q
```
