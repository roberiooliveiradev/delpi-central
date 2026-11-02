# 108 — EVA Drawing Intelligence R9.6: OCR–Cell Association & Runtime Verification

**Status:** OCR–cell association implementada e testada (função pura); associação real  — tokens de amostra vieram vazios no run; SLANet real PASS; deploy-lag honesto. **Data:** 2026-11-02.

## 1. OCR–cell association (RQ-01/02/05)

 — geometria determinística: centro do token contido na célula → atribuído; >1 célula → ; nenhuma → . Nunca inventa texto. 11/11 testes.

## 2. Real run 

SLANet no crop  → **34 cell bboxes reais**.  →  —  retornou vazio (amostra de tokens não populada neste run) → cobertura real ; a função é correta (center-containment verificada em testes).

## 3. SLANet (evidência R9.5 revalidada)

 score 0.982, 5×8, ~34–40 cells;  score 0.910, 14 rows/86 cells; 758–818MB peak, CPU-only.

## 4. Runtime produtivo (GATE A)

 mostrou **3 engines** no container; código atual tem **4** (baseline+pps+docling+slanet) → **EXECUTION_DRIFT de deploy** — imagem uma revisão atrás; novo rebuild pendente p/ refletir o 4º motor. Baseline permanece default.
