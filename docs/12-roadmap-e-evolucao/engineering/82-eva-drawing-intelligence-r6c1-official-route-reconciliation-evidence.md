# 82 — EVA — Drawing Intelligence R6-C.1: Official PDF Route Reuse, Multiprovider Reconciliation & Real Benchmark Evidence

**Status:** IMPLEMENTED + DEPLOYED. **Data:** 2026-10-31. **SHA:** `ce66ea3c0e` (main).

## 1. Rota oficial (R6C1-01/02)

Confirmada: `GET /products/{code}/drawing` + `/drawing/pdf` em api-delpi exigem `require_any_permission(ENGINEERING_LMP_ACCESS)` — JWT delegado obrigatório (401 verificado em prod). Engineering API consome via `fetch_product_drawing`/`fetch_product_drawing_pdf` + `unwrap_delegated` — **contrato oficial reutilizado**; nenhuma rota paralela criada, nenhum acesso direto ao file server/banco.

## 2. Causa raiz do defeito de reconciliação (R6C1-03)

`reconcile_provider_fields` procurava texto em `run.get("_pages")`/`run.get("_text_blob")` — campos que o harness **não preenchia**. Resultado: campos corretamente extraídos eram classificados `not_found` (falso negativo sistêmico).

## 3. Fix — transient vs persistable (R6C1-03/04)

- `run_extraction_benchmark`: record ganha `_text_blob` transitório (evidência interna real do provider).
- `records_to_jsonl`: remove chaves `_` — **separação contratual**: resultado interno pode carregar texto; persistível só métricas/limitações (sem texto integral em artefatos).
- `reconcile_provider_fields`: estados `found|not_found|not_run|not_comparable` — `not_found` **só** quando o provider executou E procurou; `not_comparable` quando executou sem evidência textual; `valid_providers` denominador; `coincident`/`divergent`/`missing_everywhere` computados só sobre providers comparáveis (nenhum executado → nada de missing).

## 4. Execução real-PDF — estado honesto

`REAL_PDF_BENCHMARK = TEST_NOT_RUN` — rotas oficiais são JWT-gated e o executor não possui sessão OAuth delegada. Bridge `run_official_document_benchmark` pronto e testado (mesmo hash multi-provider via envelope realista); execução real requer sessão autorizada (consumidor MCP ou job operacional — `ARCHITECTURE_DECISION_REQUIRED`).

## 5. Testes / deploy / smoke

Suite **555 passed / 0 failed** no SHA `ce66ea3c0e`. Deploy: prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Sem deps prod novas; baseline pypdf default intacto. Rollback: SHA anterior + rebuild.

## 6. Matriz R6C1-01..30

PASS: 01–08, 14 parcial (semântica correta implementada/testada), 19–30. TEST_NOT_RUN: 09–13, 16–18 (run real-PDF — sessão delegada indisponível; OCR sem justificativa ainda). PENDING: 15 (coords reais avaliadas apenas sintético).

## 7. Residuais

1. Mecanismo oficial para benchmark autorizado (consumidor MCP existente ou job operacional governado) — decisão de owner.
2. ONDA14/ground-truth — EVAL_PENDING.
3. OCR — contracts prontos; instalação pendente de justificativa real.
4. Prod repo divergido — merge não destrutivo documentado.
