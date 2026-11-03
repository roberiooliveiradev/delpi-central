# 117 — EVA Drawing Intelligence M0: Evaluation Foundation — Scorecard & Ledger

**Status:** M0 partial — dataset+harness+baseline mensurados; GT técnico `OWNER_BLOCKED` (aprovação Engenharia); M1–M5 gates pendentes. **Data:** 2026-11-03.

## 1. Inventário (M0.1)

Pipeline real: `api-delpi PDF → run_pipeline_isolated (pdfium render + PaddleOCR det/rec, model_dir=/opt/ocr-models) → tokens (≤200 sample) → build_understanding (determinístico) → TableStructureEngine (SLANet, /root/.paddlex→/opt/ocr-models/paddlex) → associate_tokens_to_cells → table_structure_engines[]`. MCP `analyze(product.drawing_understanding)` — read-only, DRAFT.

## 2. Dataset Manifest v1 (M0.2)

| Desenho | SHA-256 | OCR tokens | SLANet cells | cells c/ texto | score |
|---|---|---|---|---|---|
| 90264302 | f33447b2…f0ef | 92 | 34 | 22 | ~0.9595 |
| 90264161 | 8d9fe28a…85195 | 126 | 44 | 29 | ~0.9385 |

Corpus target ~20 desenhos (doc 116); staged adicionais: 90263554, 90264135, 90264094, 10210267-2 — hash/acesso a verificar. **TO_INVENTORY** para 14 restantes.

## 3. GT formato v1 (M0.3)

`{document_id, revision, page, region{box_px,type}, cell{row,col,box,span}, token_id, field{item,qty,component_code,description,document_id,revision,customer}, raw_value, normalized_value, state{MATCH,CONFLICT,UNKNOWN,AMBIGUOUS,NOT_COMPARABLE}, annotator, reviewer}` — aprovação Engenharia pendente → `OWNER_BLOCKED`.

## 4. Harness + Baseline (M0.4/5)

Baselino R9.9 mensurada (R9.8 acceptance): ambos desenhos `executed=true`, células c/ texto real, `CANDIDATE_GENERATED`. Harness = subprocess isolado + association metrics (cell_token_map/conflicts/unassigned) + `_to_native` serialization. Split: 2 desenhos — holdout insuficiente para generalização (documentado).

## 5. Gaps / OWNER_BLOCKED

- GT revisão Engenharia: `OWNER_BLOCKED` — sem aprovação técnica M0 não é PASS completo.
- Holdout/treino split <20 desenhos; token→cell refs persistentes pendente (M1).
- Cotas/tolerâncias/símbolos: catálogo M3 não aprovado — fora de escopo.
- E2E autenticado: sem OAuth session — `TEST_NOT_RUN` (ChatGPT independente).
