# 84 — EVA — Drawing Intelligence R6-D: Governed Benchmark Action, Authorized Real-PDF Execution & Provider Comparison Evidence

**Status:** IMPLEMENTED + DEPLOYED (ação governada disponível; E2E real pendente de sessão autorizada + flag). **Data:** 2026-10-31. **SHA:** `850a620b9e` (main).

## 1. Contrato (D02/D04/D05)

`analyze(product.drawing_benchmark)` — ação tipada dentro do MCP semântico vigente (nenhuma sétima tool). Parâmetros: `product_code` (obrigatório), `benchmark_profile` (default `approved_local_extractors`), `fields` (≤50 candidatos). Output `drawing_benchmark.v1`: `document` (code/filename/size/sha256/revision/source/authorized_via), `providers[]` (métricas/limitações — sem `_transient`), `field_coverage` (matriz found/not_found/not_run/not_comparable + denominador `valid_providers`), `same_document_verified`, `quality_gate: EVAL_PENDING`.

## 2. AuthZ / flag (D03/D08)

- `ENG_DRAWING_BENCHMARK_ENABLED` — env fail-closed → `feature_disabled` (403) sem opt-in do backend.
- Identidade delegada + permissão de desenho vigentes (`_require_engineering_human` + gateway Core-gated) — mesma autorização da análise oficial.
- Perfil desconhecido → `provider_profile_not_allowed` (400). Consumidor **não** escolhe provider/path/URL/módulo.
- Sem flags externas, sem SaaS, sem writes.

## 3. Execução real — estado honesto

- Bridge `run_official_document_benchmark` (mesma rota delegada, bytes uma vez, mesmo SHA) **pronto e testado** — happy path no teste cobre 3 providers com hash idêntico.
- **REAL PDF 90264302:** `TEST_NOT_RUN` no executor — requer sessão autorizada (`analyze` via MCP autenticado) + flag habilitada. Com a flag, um consumidor autorizado já pode executar — ação implementada e descobrível via `get_context`.
- Ativação da flag em prod: **não habilitada** (decisão de autorização do owner — FEATURE_GATED honesto).

## 4. Testes

4 novos (`test_drawing_benchmark_action.py`): flag-off fail-closed, profile rejeitado, happy path 3 providers mesmo SHA + coverage + `_transient` stripped + EVAL_PENDING, registry listing. **Suite: 559 passed / 0 failed** no SHA `850a620b9e`. Six-tool freeze preservado (L13).

## 5. Deploy / smoke

`origin/main=850a620b9e` → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Flag **off** por padrão (seguro). Rollback: SHA anterior + rebuild; desativação trivial via env.

## 6. Matriz D-01..32 (resumo)

PASS: 01–12 (contrato/authz/flag/gateway/bridge/hash), 18–26, 29–32. FEATURE_GATED: 13–17, 28 (execução real requer flag + sessão autorizada). PENDING: 18 (OCR recommendation depende dos gaps reais).

## 7. Residuais

1. E2E autenticado `analyze(product.drawing_benchmark)` — requer flag + sessão (owner enable).
2. Memory/resource instrumentation dos providers — não implementado.
3. OCR real — pendente de gaps observados no benchmark real.
4. Ground truth ONNDA14 — EVAL_PENDING.
5. Prod repo divergido — merge não destrutivo documentado.
