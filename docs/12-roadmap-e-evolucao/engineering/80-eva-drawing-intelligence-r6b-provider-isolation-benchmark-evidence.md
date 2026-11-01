# 80 — EVA — Drawing Intelligence R6-B: Provider Isolation, PDFium/OCR Benchmark, Spatial Extraction & Comparative Evaluation Evidence

**Status:** IMPLEMENTED + DEPLOYED (baseline pypdf preservado; experimentais fail-closed). **Data:** 2026-10-31. **SHA:** `a15a580d4c` (main).

## 1. Reparos arquiteturais (R6B-01/02)

- **DI fix:** `extraction_ports.py` agora é contracts-only (ports, modelos neutros, `ProviderCapability`, `ProviderResolutionError`, hook `set_default_extractor_factory`/`get_default_extractor`) — **zero imports de Infrastructure na Application**. Factories+catálogo migraram para `infrastructure/extraction/registry.py`; `composition/drawing_composer.py` registra `pypdf` como default produtivo; `semantic_bridge` carrega o composer (prod) e `tests/conftest.py` (testes).
- **Policy fix:** `resolve_extraction_provider(provider_id, allow_experimental=False)` — ID explícito **não autoriza** experimental; benchmark passa `allow_experimental=True`; env `EVA_DRAWING_EXTRACTION_PROVIDER` = autorização operador. Fail-closed.

## 2. Novos contratos (R6B-03)

`PdfRenderingPort` (`render_page→RenderedPage{png,width,height,dpi}`), `OcrExtractionPort` (`extract_text→OcrResult{tokens+box}`), `ImagePreprocessingPort` — todos com consumer real (pipeline P4/P5) ou contrato justificado.

## 3. Adapters e benchmark real (R6B-04..06/12)

- `pdfium_adapter.py` — pypdfium2 **opcional** (BSD-3): `extract` (textpage) + `render_page` (≤5 páginas, ≤300 DPI → PNG); `provider_unavailable` honesto se ausente.
- **Benchmark real executado** (container, fixture sintético `90264302`-like; PDF real está só no acervo produtivo — run em prod = pendente):

| Provider | Status | Chars | Duração | Posicional |
|---|---|---|---|---|
| pypdf_baseline | ok | 132 | 1ms | não |
| pdfplumber_experimental | ok | 132 | 3ms | **sim (words+coords)** |
| pdfium_experimental | ok | 100 | 3ms | não (texto menor) |

- Matriz preliminar: **pdfplumber = PROMISING** (mesma cobertura + coordenadas, MIT); **pdfium = INCONCLUSIVE** (render p/ OCR, mas texto reduzido); **pypdf = controle** (baseline estável). Nenhum vencedor declarado.

## 4. Deferidos honestamente (R6B-07..09)

- **OpenCV** (`ImagePreprocessingPort` pronto — adapter deferred: peso/avaliação pendente).
- **PaddleOCR** (`OcrExtractionPort` pronto — adapter deferred: modelos pesados + ambiente).
- **SaaS (Azure/Google/Gemini):** `OWNER_BLOCKED` — envio de desenhos de clientes exige autorização de dados/credenciais/custos. Nenhum SDK instalado.
- **PyMuPDF:** AGPL — bloqueado sem decisão de licenciamento.

## 5. Testes

Policy: experimental explicit-ID rejeitado sem flag, backend-flag resolve. Conftest registra default (DI). **Suite: 552 passed / 0 failed** no SHA `a15a580d4c`. R5.1 intacto.

## 6. Deploy / smoke

`origin/main=a15a580d4c` → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Sem deps prod novas (pdfplumber/pypdfium2 só em container de teste). Rollback: SHA anterior + rebuild.

## 7. Matriz R6B-01..34 (resumo)

PASS: 01–10, 14–18, 20, 23–30, 32–34. OWNER_BLOCKED: 19 parcial (OCR real — PaddleOCR não instalado), SaaS. TEST_NOT_RUN: 31 (smoke autenticado), benchmark em 90264302.pdf real (acervo prod, sem acesso local). FEATURE_GATED: experimentais por design.

## 8. R6-C readiness

Próximo: benchmark no `90264302.pdf` real (acervo autorizado) → avaliar se coordenadas pdfplumber melhoram evidência↔região; port ONDA14 + ground truth owner → decisão de promoção de provider com gates de Engenharia/segurança.
