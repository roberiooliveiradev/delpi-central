# 78 — EVA — Drawing Intelligence R5.1: Reconciliation Consistency, Findings Stabilization & Production Evidence

**Status:** IMPLEMENTED + DEPLOYED. **Data:** 2026-10-31. **SHA:** `e9719b6566` (main). **Regressão:** `90264302`.

## 1. Causa raiz (S1–S3) — documentada

Relatório real retornava `reconciliation_status=visual_and_official_only` **e** simultaneamente `finding{category=identification, severity=warning, divergence=product_code_not_located_in_text_layer}`.
O filtro de reclassificação da R5 checava `category ∈ {product_identification, bom_coverage}` — categorias **inexistentes**; as reais são `identification` e `bom`. O filtro nunca executava → WARNING indevido permanecia.
**Fix:** reclassificação filtra pelo `divergence` específico (`not_located`/`without_text`) + corroboração visual×oficial → `severity=info`, `divergence=text_coverage_limitation`. Ausência textual = limitação de cobertura, jamais divergência cadastral.

## 2. Semântica de vínculos BOM (S6)

`parent_links=4` anterior: o nó raiz real da api-delpi não carrega `code` — PIs recebiam parent `None`. Fix: raiz implícita = `product_code` analisado; recursão `root` propaga `effective_parent`. Stats explícitas: `root_child_links` (PA→PI = 2), `nested_parent_links` (PI→MP = 4), `total_relationships` = 6, `parent_links` = total (compat), `direct_children` alias.

## 3. Invariantes testados (S7–S8)

3 novos (`test_drawing_analysis_r51.py`): INV-02 (reconciliação visual×oficial ⇒ zero WARNING de identificação por ausência textual; finding vira info `text_coverage_limitation`), INV-03 (`product_code` visual divergente → `conflict` mantido), INV-08 (vínculos raiz/aninhados + parents por ocorrência). **Suite: 542 passed / 0 failed** no SHA `e9719b6566`.

## 4. Deploy / smoke

`origin/main=e9719b6566` → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Smoke autenticado MCP/ChatGPT: TEST_NOT_RUN (sem sessão no executor). Rollback: SHA anterior + rebuild.

## 5. Matriz S-01..30

PASS: 01–22, 25–26, 28–30. TEST_NOT_RUN: 23, 27 (E2E autenticado indisponível). PENDING: 24 (ground truth owner).

## 6. Residuais

1. E2E MCP/ChatGPT real: TEST_NOT_RUN.
2. ONDA14/ground truth: EVAL_PENDING (nenhum threshold inventado).
3. Cobertura visual por ocorrência (vs por código): registro por código, honestamente.
4. Prod repo divergido — merge não destrutivo documentado.
