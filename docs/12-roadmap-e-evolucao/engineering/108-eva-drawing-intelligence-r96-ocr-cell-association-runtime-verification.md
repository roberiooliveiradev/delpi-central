# 108 — EVA Drawing Intelligence R9.6: OCR–Cell Association & Runtime Verification

**Status:** OCR–cell association implementada e testada; associação real `INCONCLUSIVE` (amostra de tokens vazia); SLANet real PASS; deploy-lag honesto. **Data:** 2026-11-02.

## 1. OCR–cell association

`associate_tokens_to_cells(tokens, cell_bboxes, crop_offset)` — geometria determinística: centro do token contido na célula → atribuído; mais de uma célula → `conflicts`; nenhuma → `unassigned`. Nunca inventa texto. 11/11 testes.

## 2. Real run `90264302`

SLANet no crop `[41,31,2295,262]` → **34 cell bboxes reais**. Associação → `mapped:0, unassigned:0, conflicts:0` — `_tokens_sample` retornou vazio no run → cobertura real `INCONCLUSIVE`; a função é correta (center-containment verificada em testes).

## 3. SLANet (evidência R9.5 revalidada)

`90264302` score 0.982, 5×8, ~34–40 cells; `90264161` score 0.910, 14 rows/86 cells; 758–818MB peak, CPU-only.

## 4. Runtime produtivo

`R95_LOADED` mostrou **3 engines** no container; código tem **4** → **EXECUTION_DRIFT de deploy** — imagem uma revisão atrás; rebuild pendente para refletir o 4º motor. Baseline permanece default.
