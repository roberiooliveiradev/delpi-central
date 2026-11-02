# 111 — EVA Drawing Intelligence R9.8: Production MCP Runtime Reconciliation

**Status:** root cause do `FINAL_CHAT_ACCEPTANCE_FAIL` identificado e corrigido — imagem prod estava **stale** (container recriado sem rebuild real da imagem); código R9.8 agora no container; SLANet executa em prod; E2E MCP autenticado `TEST_NOT_RUN` (sem OAuth). **Data:** 2026-11-02.

## 1. Causa raiz (verificada, não hipótese)

- Repo prod `HEAD 0eaf0be88` contém `7e7a637dd` (grep=2, `HAS_R98_COMMIT`).
- Container `delpi-engineering-api` usa código **baked na imagem** (compose `infra/docker-compose.yml`, sem `/app` mount — só `ocr-models`).
- `docker exec grep table_structure_engines` = **0** → o `docker compose up -d --build` anterior recriou o container mas **não rebuildou a imagem** com o código novo (cache/stale).
- Correção: `up-prod-sequential.sh --build engineering-api` → novo container com `table_structure_engines`=2, `_pdf_bytes`=1, `R98B` 4 engines.

## 2. Provisionamento do modelo

`TableStructureRecognition` importa em prod (`TSR_OK`) mas `NO_PADDLEX_CACHE` — SLANet não estava provisionado. Copiado `~/.paddlex/official_models/SLANet` (7.7MB) dev→prod→container. **Inferência real em prod: sintético score 0.9999, 25 cells, 5 rows, 1.3s.**

## 3. Estado MCP (após fix)

`analyze(product.drawing_understanding)` agora produz `understanding.table_structure_engines[]` com `provider_id`, `executed`, `structure_score`, `cell_count`, `cells_with_text`, `cells` (com texto), `state:CANDIDATE_GENERATED` — campo que antes estava **ausente** na resposta.

## 4. Residuais honestos

- Modelo SLANet copiado via `docker cp` (ephemeral no recreate); persistência requer bake na imagem ou volume/env `PADDLEX_MODEL_HOME` — **residual documentado**.
- `/opt/ocr-models` é read-only mount — SLANet não persistiu lá.
- E2E MCP autenticado: `TEST_NOT_RUN` (sem OAuth); ChatGPT valida via `analyze` real.
- Inferência SLANet ~800MB spike no container — episódico, dentro do orçamento.
