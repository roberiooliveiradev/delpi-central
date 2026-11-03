# 110 — EVA Drawing Intelligence R9.8: SLANet MCP Integration, Real E2E — Wired

**Status:** SLANet agora executado pelo use case `product.drawing_understanding` via bridge; células com texto real em ambos os desenhos; baseline preservada; E2E MCP autenticado `TEST_NOT_RUN` (sem OAuth). **Data:** 2026-11-02.

## 1. Causa raiz (gap R9.7→R9.8)

SLANet estava **registrado** no registry mas o `product.drawing_understanding` nunca o invocava — só consumia `build_understanding` sobre tokens. O motor não tinha consumer semântico. Corrigido no ponto canônico.

## 2. Integração (mínima, aditiva)

- `document_benchmark_service` expõe `_pdf_bytes` internamente (nunca na resposta).
- `semantic_bridge._analyze_drawing_understanding`: após `build_understanding`, chama `TableStructureEngine().run(_pdf_bytes, crop_box=component_table.box)` → `understanding["table_structure_engines"]` com `provider_id`, `model_version`, `executed`, `structure_score`, `row_count`, `cells` (com texto), `cell_count`, `cells_with_text`, `duration_ms`, `state:CANDIDATE_GENERATED`.
- Erro tipado isolado — falha SLANet não quebra a baseline.

## 3. E2E real (caminho do bridge)

**`90264302`**: 34 cells, **22 com texto** (`QTD`, `CHICOTE DE LIGACÄO`), score ~0.96.
**`90264161`**: 44 cells, **29 com texto** (`Código 90264161`, `Descrição CABO DE LIGACAO 15.5M-3X2.5`, `Item QTD Componente A1 1 10210771`, `COD: 5101.5561`) — conteúdo real do produto.

## 4. Semântica

`table_structure_engines[]` distingue baseline (`pdfium_render_paddleocr`) de SLANet (`table_structure_slanet`) — consumer identifica o motor. Nada marca baseline como SLANet. Candidate-only.

## 5. Residuais

- Prod container precisa de rebuild p/ refletir a integração (deploy-lag).
- E2E MCP autenticado: `TEST_NOT_RUN` (sem sessão OAuth).
- `component_table.box` nem sempre presente → engine faz fallback de crop (funcionou em ambos).
