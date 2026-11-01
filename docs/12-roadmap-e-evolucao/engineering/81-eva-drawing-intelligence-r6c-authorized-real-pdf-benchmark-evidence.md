# 81 — EVA — Drawing Intelligence R6-C: Authorized Real-PDF Benchmark, Spatial Evidence & Provider Evaluation

**Status:** IMPLEMENTED + DEPLOYED (bridge autorizado pronto; run real-PDF pendente de sessão delegada). **Data:** 2026-10-31. **SHA:** `b000fd6b74` (main).

## 1. Bridge autorizado (R6C-01..05)

`run_official_document_benchmark(code, source, ctx, providers)` usa **o mesmo gateway delegado** e identidade da análise oficial (`fetch_product_drawing` + `fetch_product_drawing_pdf` via `unwrap_delegated`) — read-only, sem acesso paralelo ao acervo, sem JWT fabricado, sem path direto ao file server. Bytes obtidos **uma vez**; todos os providers processam o mesmo `sha256` (`same_document_verified` nos registros). Document identity no resultado: filename, size_bytes, document_hash, drawing_library_revision, source, authorized_via — **nenhum token**.

## 2. Reconciliação multiprovider (R6C-12/16)

`reconcile_provider_fields(runs, fields)` — matriz campo×provider (`found`/`not_found`/`not_run`) + `coverage_summary` (coincident/divergent/missing_everywhere). Cobertura textual honesta — não acurácia, não ground truth, não fato.

## 3. Execução real

- **P1–P3 sintético:** executado na R6-B — pypdf 132ch/1ms, pdfplumber 132ch/3ms + coordenadas, pdfium 100ch/3ms (container, mesmos bytes).
- **PDF real 90264302:** `TEST_NOT_RUN` — executor não possui sessão delegada OAuth para obter bytes do acervo; bridge pronto, requer execução com identidade autorizada (MCP E2E ou benchmark autorizado).
- **OCR:** avaliação condicional — sem execução real (PaddleOCR pesado, sem justificativa comprovada ainda) → `TEST_NOT_RUN` honesto. Ports `OcrExtractionPort`/`ImagePreprocessingPort` prontos.

## 4. Matriz de decisão (estado atual)

| Provider | Status | Evidência |
|---|---|---|
| pypdf_baseline | controle produção | estabilidade, 132ch, sem coords |
| pdfplumber_experimental | **PROMISING** | mesma cobertura + positional_words (MIT) |
| pdfium_experimental | INCONCLUSIVE | texto reduzido (100ch), render disponível p/ OCR |
| PaddleOCR | OWNER_BLOCKED | peso/modelos + sem justificativa comprovada |
| SaaS (Azure/Google/Gemini) | OWNER_BLOCKED | política de dados de clientes |

## 5. Testes / deploy / smoke

3 novos (`test_drawing_benchmark_r6c.py`): mesmo hash multi-provider, `drawing_pdf_unavailable` tipado, matriz de cobertura. **Suite: 555 passed / 0 failed** no SHA `b000fd6b74`. Deploy: merge prod → `--build engineering-api` → `delpi-engineering-api Up (healthy)`; zero deps prod novas. Rollback: SHA anterior + rebuild.

## 6. Matriz R6C-01..32 (resumo)

PASS: 01–05, 10–13 parcial, 16–17, 21–27, 29–32. TEST_NOT_RUN: 06–09 (run real-PDF — sem sessão delegada), 15, 28. PENDING/EVAL: 18–20 (ground truth owner).

## 7. Residuais

1. Run real-PDF com identidade delegada — bridge pronto, sessão autorizada pendente.
2. OCR real — pendente de justificativa + ambiente; ports prontos.
3. Ground truth/labels — EVAL_PENDING (owner Engenharia).
4. Recursos (memória) — não instrumentados ainda.
5. Prod repo divergido — merge não destrutivo documentado.
