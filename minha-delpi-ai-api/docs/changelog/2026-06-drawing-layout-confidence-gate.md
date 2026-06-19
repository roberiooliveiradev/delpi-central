# Changelog — layout adaptativo + gate de confiança (jun/2026)

## Resumo

Duas camadas transversais na validação/extração de desenhos DELPI:

1. **Layout de página (XY-Cut)** — detecta regiões antes do OCR regional.
2. **Gate de confiança ≥ 95%** — divergências dependentes do PDF viram `pending` quando a leitura é incerta; críticos da API (roteiro, inspeção) permanecem.

## Commits

| Commit | Escopo |
|--------|--------|
| `5b502c86` | Gate confiança — `ChatDrawingExtractionConfidenceService`, `ChatDrawingValidationAssertionService`, `validationLayers` |
| `34fbc0ae` | Layout XY-Cut — `ChatDrawingPageLayoutAnalysisService`, integração `ChatDrawingRegionService` |

## Módulos novos

| Serviço | Responsabilidade |
|---------|------------------|
| `ChatDrawingPageLayoutAnalysisService` | XY-Cut + classificação stamp/title/bom/dimensions |
| `ChatDrawingExtractionConfidenceService` | Score composto (legibilidade, carimbo, BOM scope, OCR, conflitos) |
| `ChatDrawingValidationAssertionService` | Demotion assertiva antes de `_package` |

## JSON

| Bundle | Seção |
|--------|-------|
| `drawing_stamp.json` | `layoutAnalysis` |
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
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_assertion_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_drawing_validation_90264227.py -q
```
