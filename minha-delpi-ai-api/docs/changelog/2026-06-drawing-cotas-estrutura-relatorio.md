# Changelog — Cotas, estrutura e relatório DELPI

**Data:** 22/06/2026  
**Escopo:** referência de comprimento SG1010, gate OCR em `total_length`, seção de cotas no relatório, PI aninhado sob PA.  
**Arquitetura:** [`chat-drawing-skill-limitations.md`](../architecture/chat-drawing-skill-limitations.md) · Onda 12 · `drawing_validation.json`.

Princípio: regras no **pipeline da skill** (`ChatDrawing*` + JSON); MFE **render-only** (`drawingAnalysisExport.markdown`).

---

## Problema (ex.: `90260027`)

| Sintoma | Causa |
|---------|--------|
| `Comprimento total` crítico com PDF `1.0 mm` × API `653.0 MT` | OCR da região de cotas falhou; regex CA18 interpretou `00653` como mm; quantidade MT do cabo exposta sem conversão |
| Estrutura «sumida» na conversa | Outline no markdown (seção 3); checklist (seção 5) destacava só divergências |
| PI `50220010` ignorado | `collect_structure_intermediates` só lia 1º nível da SG1010 |

---

## Correção

| # | Entrega | Módulo canônico |
|---|---------|-----------------|
| 1 | `total_length` em `validationLayers.pdfDependentTemplateKeys` — crítico → pendente com confiança OCR &lt; 95% | `drawing_validation.json` + `ChatDrawingValidationAssertionService` |
| 2 | Referência SG1010 sempre em **mm**; descrição do PA (`660MM`) ancora chicote; PI recursivo; conversão MT via `per_piece_length_mm` | `ChatDrawingIntermediateSemanticsService`, `ChatDrawingTotalLengthReferenceService` |
| 3 | Seção **`### Cotas × estrutura (PDF × SG1010)`** no relatório markdown | `ChatDrawingValidationPresentationService.format_dimensions_comparison_section` |
| 4 | Padrão `patterns.productDescriptionLengthMm` no JSON | `drawing_validation.json` + `ChatDrawingPatternsService.compile_validation` |

---

## Relatório DELPI — ordem das seções

1. Status geral  
2. Dados PDF  
3. Dados API + **Estrutura (outline)** + Roteiro + Inspeções  
4. **Cotas × estrutura** (novo)  
5. Divergências  
6. Checklist completo  
7. Conclusão  

Export PDF/CSV/XLSX: tabelas em `drawingAnalysisExport.tables` (inalterado).

---

## Testes

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_drawing_validation_90260027.py \
  tests/unit/domain/services/test_chat_drawing_intermediate_semantics_service.py \
  tests/unit/domain/services/test_chat_drawing_validation_assertion_service.py \
  tests/unit/domain/services/test_chat_drawing_validation_orchestration_service.py -q
```

**Cenário manual:** anexar PDF chicote `90260027` → relatório com outline SG1010, tabela de cotas, `Comprimento total` pendente (não crítico) se OCR ruim, API `660 mm`.

---

## Commit

| Hash | Mensagem |
|------|----------|
| `ea98f90d` | Corrige cotas e visualização de estrutura na análise de desenho DELPI. |
