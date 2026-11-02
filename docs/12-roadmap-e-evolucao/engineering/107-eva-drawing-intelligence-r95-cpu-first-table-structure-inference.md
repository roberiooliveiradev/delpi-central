# 107 — EVA Drawing Intelligence R9.5: CPU-First Table-Structure Real Inference — FUNCTIONAL_DELIVERY_PASS

**Status:** **FUNCTIONAL_DELIVERY_PASS** — primeiro motor moderno executando inferência real em desenhos DELPI, dentro do orçamento CPU-only; baseline preservada; E2E MCP `TEST_NOT_RUN`. **Data:** 2026-11-02.

## 1. Motor e modelo

- **Engine:** `table_structure_slanet` — PaddleOCR `TableStructureRecognition`.
- **Modelo:** **SLANet** (7.67MB, `~/.paddlex/official_models/SLANet`, cached, read-only). Licença Apache-2.0 (PaddleX).
- **Modo:** CPU-only, processo isolado, concorrência 1.

## 2. Inferência real — `90264302` (SHA f33447b2)

- Crop da região de tabela R8.2.3 `[41,31,2295,262]` → SLANet.
- **Resultado:** `structure_score 0.982` — **5 linhas × 8 colunas** (com colspan), **40 bounding boxes de células**.
- **Baseline:** 4 linhas / 24 células — o modelo reconstrói estrutura mais fiel à tabela real (5 linhas, 8 colunas vs o agrupamento heurístico de 4 linhas).
- **Tempo:** init 35.8s (1ª vez, download+load) / inferência 0.6–1.0s | **peak RSS 758–818MB** — **dentro do orçamento ~2–3GiB**.

## 3. Regressão — `90264161` (SHA 8d9fe28a)

- Crop banda superior `[25,7,2282,520]` → SLANet.
- **Resultado:** `structure_score 0.910` — **14 linhas**, **86 cell bboxes**.
- 775MB peak, 0.7s — real, sem OOM.

## 4. Adapter + contrato

`TableStructureEngine` → `PerceptionEnginePort` → `drawing_perception_candidate.v1` (tables com `structure_score`+`row_count`+`structure_html`, cells com `bounding_box_px`). Erro tipado isolado (MODEL_NOT_PROVISIONED/UNAVAILABLE). `engine_capabilities()` = **4 motores**.

## 5. Decisão

`table_structure_slanet` é o primeiro motor moderno funcional CPU-first: estrutura superior à heurística R8.2.3 (score 0.98, células reais) dentro do orçamento. **Shadow-readiness:** candidato — OCR-cell association + deploy governado pendem de gate. **Baseline permanece padrão.**

## 6. Residuais

- `structure` devolve boxes sem texto — associação OCR↔célula = próxima etapa.
- Colspan no HTML precisa de parsing p/ células nominais.
- E2E MCP/GT/production replacement: `TEST_NOT_RUN`/pendente.
