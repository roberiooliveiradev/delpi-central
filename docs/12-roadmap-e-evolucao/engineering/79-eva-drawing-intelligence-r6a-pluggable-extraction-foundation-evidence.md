# 79 — EVA — Drawing Intelligence R6-A: Pluggable PDF/Visual Extraction Foundation, Provider Contracts, Benchmark Harness & Deployment Evidence

**Status:** IMPLEMENTED + DEPLOYED (baseline `pypdf` preservado; experimentais desabilitados). **Data:** 2026-10-31. **SHA:** `1fa7513d7c` (main).

## 1. Inventário de acoplamentos (R6A-01) — matriz executada

| Componente | Responsabilidade | Coupling | Decisão |
|---|---|---|---|
| `pdf_text_extractor.py` | bytes→`PdfTextExtraction` | pypdf na application | **KEEP** (baseline; port o envolve) |
| `drawing_analysis_service` | orquestração | chamava `extract_pdf_text` direto | **ADAPT** → `extractor` param + resolver |
| `delegated_auxiliary` | fatos oficiais | envelope HTTP | KEEP |
| `drawing_comparator`/models | comparação/domínio | zero SDK | KEEP |
| `semantic_bridge` | MCP dispatch | sem provider | KEEP (seleção backend-only) |

## 2. Ports & adapters (R6A-03/05)

- `PdfExtractionPort` (application): `extract(bytes)->PdfTextExtraction` + `capability_descriptor()` — mesmo contrato do baseline; `PdfTextExtraction.metadata` = canal aditivo de proveniência espacial.
- `ProviderCapability`: id, versão, status (baseline/experimental/unavailable), capabilities (text_layer/coordinates/tables/ocr/scanned), formats, runs_local, requires_credentials, license, limits.
- Catálogo allowlist explícito — `pypdf_baseline` (default) + `pdfplumber_experimental` (opt-in via `EVA_DRAWING_EXTRACTION_PROVIDER`); resolução por backend, sem import dinâmico nem nome de provider via request MCP. Erros tipados: `unknown_provider`, `provider_not_enabled`.

## 3. Adapters (R6A-06/07)

- **pypdf_baseline** — delega ao extrator existente (15MB/30p/60k, assinatura, hash, honesto); BSD. Pipeline R5.1 **inalterado** (default).
- **pdfplumber_experimental** — MIT, dependência **opcional** (não está no requirements prod): instalado → texto + `metadata.positional_words` por página com coordenadas; ausente → `provider_unavailable` honesto, nunca fabricado.
- Diferidos (contrato/documentados, não implementados): pypdfium2, OpenCV, PaddleOCR, Azure/Google Document AI, Gemini — exigem avaliação de peso/licença/credenciais/dados. **PyMuPDF: AGPL — bloqueado sem decisão de licenciamento.** ChatGPT visual preservado via contrato de observações (sem SDK no backend).

## 4. Benchmark harness (R6A-11/14)

`run_extraction_benchmark(pdf_bytes, providers, corpus_id, environment)` → run records JSONL (`run_id`, provider/versão/status, document_hash, input_bytes, pages, text_chars, duration_ms, limitations, has_positional_data, error) — mesmos bytes, comparável, reprodutível. `precision`/`recall` = `metric_not_available` sem ground truth aprovado.

## 5. Testes (R6A-15)

10 novos (`test_extraction_providers.py`): baseline, swap por fake contratual (sem tocar domínio), unknown provider rejeitado, experimental opt-in, descriptor contract, unavailable honesto (T20 sem fabricação), benchmark 2 providers mesmo hash, PDF inválido rejeitado, domínio sem imports de provider, default inalterado + R5.1 intacto. **Suite: 552 passed / 0 failed** no SHA `1fa7513d7c`. Rework: 1 (async test).

## 6. Deploy / smoke

`origin/main=1fa7513d7c` → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Sem novas deps prod, sem SaaS, sem 7ª tool. Rollback: SHA anterior + rebuild.

## 7. Matriz R6A-01..35

PASS: 01–17, 21–30, 33–35 parcial (matriz de avaliação definida 18; corpus 90264302 preparado 19; ONDA14 inventariado 20). TEST_NOT_RUN: 32 (smoke autenticado). PENDING: 18 parcial (corpus amplo), 20 (port de cases autorizados). FEATURE_GATED: adapters experimentais por design.

## 8. R6-B readiness

Comparáveis hoje: `pypdf_baseline` vs `pdfplumber_experimental` (texto+coordenadas). R6-B executa benchmark em `90264302.pdf` real + corpus autorizado e avalia se coordenadas melhoram associação evidência↔região. Providers SaaS continuam OWNER_BLOCKED (dados de clientes → política/credenciais). Próximos: corpus ONDA14 + ground-truth owner + eval comparativo real.
