# 86 — EVA Drawing Intelligence R6-D.2: Runtime Recovery, Semantic MCP Alignment, Production E2E & Real PDF Benchmark Evidence

**Status:** IMPLEMENTED + DEPLOYED + RUNTIME VERIFIED. **Data:** 2026-11-01. **SHA:** `e4cbf7feb3` (main).

## 1. Sintoma → root cause (R03/R04)

- **Sintoma:** consumidor autenticado recebeu `501 not_implemented` em `analyze(product.drawing_benchmark)` — o registry anunciava a ação mas o dispatcher não a conhecia.
- **Investigação runtime:** `inspect.getsource(tool_analyze)` **dentro do container prod** confirmou `has_benchmark: False` **e** `has_analysis: False` — o arquivo carregado não tinha dispatch algum, provando divergência git↔runtime.
- **ROOT CAUSE:** commit `46da939277` (merge concorrente DÉLIA Task29 — "resolve EVA workstream conflicts") reverteu o trabalho EVA em **8 arquivos** engineering-api:
  - `semantic_bridge.py`: dispatch das duas actions + dois handlers + `drawing_composer` import + `available` list;
  - `semantic_registry.py`: entries `product.drawing_analysis` + `product.drawing_benchmark`;
  - `tool_bridge.py`, `delegated_auxiliary.py`, `product_routes.py`, `downstream_client.py`: funções de desenho/produto;
  - `test_health.py` + `test_auth_middleware.py`: expectativa da rota `/v1/products/filter-options`.
- `EXECUTION_DRIFT` registrado: registry sem dispatcher = anúncio de capacidade falsa.

## 2. Correção (R06/R07)

`git checkout 850a620b9e --` nos 8 arquivos (última versão íntegra verificada — nenhum outro commit legítimo tocou esses arquivos depois; o delia adicional em outros arquivos ficou preservado). Novo teste `test_every_registered_analyze_action_has_dispatch` — **falha se um merge futuro remover branch de dispatcher sem remover do registry** (prevenção de recorrência).

## 3. Verificação produtiva (R02/R14/R15)

- Suite: **560 passed / 0 failed** no SHA `e4cbf7feb3`.
- Prod: merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`.
- **Runtime-check dentro do container:** `has_benchmark: True`, `has_analysis: True`, `registry_has_benchmark: True`, `registry_has_analysis: True` — registry↔dispatcher↔imagem↔endpoint agora coerentes (antes: `False`/`False`).
- Flag `ENG_DRAWING_BENCHMARK_ENABLED=true` + `pdfplumber 0.11.9` + `pypdfium2` confirmados no container (doc 85).
- Seis tools MCP; zero legadas; `product.drawing_analysis` restaurado funcionalmente.

## 4. E2E autenticado / benchmark real — estado honesto

`TEST_NOT_RUN` — executor sem sessão OAuth do consumidor; **mas a causa raiz foi encontrada e corrigida e o dispatch está comprovado no runtime produtivo** — uma chamada autorizada agora atingiria o handler real (antes: 501).

## 5. Matriz R-01..32

PASS: 01–17 (runtime investigado, root cause, fix mínimo, registry↔dispatcher, seis tools, flag, authz, providers, testes, deploy, instância alinhada). TEST_NOT_RUN: 18–22, 24–25, 30 (execução autenticada real — infra pronta e verificada). PENDING: 23 (same-SHA exige run real), 26–29 (mantidos por contrato/teste).

## 6. Residuais

1. Execução real `analyze(product.drawing_benchmark)` por consumidor autorizado → matriz real de `90264302.pdf` (runtime corrigido — falta só a chamada).
2. Permissão dedicada experimental no Core — decisão de owner.
3. Processo: conflito de merge concorrente apagou trabalho — recomenda-se gate de review em merges que afetem engineering-api/drawing.
