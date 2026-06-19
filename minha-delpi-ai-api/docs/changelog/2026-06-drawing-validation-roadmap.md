# Changelog — Validação de desenhos: Onda 15 (fases 15.1–15.5)

**Data:** 19/06/2026  
**Escopo:** falsos positivos/negativos em 90262834 e 90263622; regras declarativas em JSON.  
**Playbook:** [`playbook_validacao_desenhos_delpi_roadmap.md`](../roadmap/melhorias/playbook_validacao_desenhos_delpi_roadmap.md)

Princípio: Python **só carrega lógica**; vocabulário, limiares e templates em `drawing_validation.json` / `drawing_stamp.json` via `ChatDrawingPatternsService`.

---

## Fases entregues

| Fase | Serviço | Efeito |
|------|---------|--------|
| **15.1** | `ChatDrawingStructureIndexService` | Flatten recursivo SG1010 (PI aninhados) |
| **15.2** | Guide × structure | Nível BOM pela profundidade real |
| **15.3** | `ChatDrawingInspectionValidationService` | `measurable_tests` / `textual_tests` (api-delpi) |
| **15.4** | `ChatDrawingMultipageCoverageService` | Warning/pending quando BOM parcial em PDF multipágina |
| **15.5** | `dimensionNoteTypes` + dimensions extraction | Termoretração não vira decape; template `dimension_note_ambiguous` |

Regras JSON: `validationRules.structureIndex`, `intermediateColorOcrMarkers`, `inspectionContract`, `multipageCoverage`, `dimensionNoteValidation`; `drawing_stamp.json` → `dimensionNoteTypes`.

---

## Testes (47 passed)

- `test_chat_drawing_structure_index_service.py`
- `test_chat_drawing_validation_90262834.py`
- `test_chat_drawing_validation_90263622.py`
- `test_chat_drawing_inspection_validation_service.py`
- `test_chat_drawing_dimensions_extraction_service.py`
- Regressão guide/BOM/orchestration

---

## Próximo (15.6)

- `ChatDrawingBomQuantityValidationService`
- `ChatDrawingValidationRuleRegistryService` + `drawing_validation_rules.json`
- Batch `validate_drawing_library.py --validate-report`
