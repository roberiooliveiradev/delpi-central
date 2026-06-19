# Changelog — Validação de desenhos: Onda 15 (fases 15.1–15.6)

**Data:** 19/06/2026  
**Escopo:** falsos positivos/negativos em 90262834 e 90263622; regras declarativas em JSON.  
**Playbook:** [`playbook_validacao_desenhos_delpi_roadmap.md`](../roadmap/melhorias/playbook_validacao_desenhos_delpi_roadmap.md)

Princípio: Python **só carrega lógica**; vocabulário, limiares e templates em `drawing_validation.json`, `drawing_validation_rules.json` e `drawing_stamp.json`.

---

## Fases entregues

| Fase | Serviço | Efeito |
|------|---------|--------|
| **15.1–15.2** | `ChatDrawingStructureIndexService` | Flatten recursivo SG1010; nível BOM real |
| **15.3** | `ChatDrawingInspectionValidationService` | `measurable_tests` / `textual_tests` |
| **15.4** | `ChatDrawingMultipageCoverageService` | Cobertura BOM multipágina |
| **15.5** | `dimensionNoteTypes` | Termoretração ≠ decape |
| **15.6** | BOM qty, guide component, balões, registry | Extensões + `--validate-report` |

**15.6:** `ChatDrawingBomQuantityValidationService`, `ChatDrawingGuideComponentConsistencyService`, `ChatDrawingBalloonValidationService`, `ChatDrawingValidationRuleRegistryService`, `drawing_validation_rules.json`, `scripts/validate_drawing_samples.py`, `validate_drawing_library.py --validate-report`.

---

## Homologação (live)

Script: `PYTHONPATH=. python scripts/validate_drawing_samples.py` (90262834, 90263622).

---

## Testes

Suite Onda 15: `tests/unit/domain/services/test_chat_drawing_validation_*.py`, `test_chat_drawing_validation_rules_phase_15_6.py`.
