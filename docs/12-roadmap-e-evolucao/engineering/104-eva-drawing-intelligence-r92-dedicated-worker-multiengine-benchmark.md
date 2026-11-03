# 104 — EVA Drawing Intelligence R9.2: Dedicated Worker Provisioning & Multi-Engine Benchmark Execution

**Status:** Docling adapter implementado e registrado; execução real bloqueada por incompatibilidade de modelo; PP-StructureV3 RESOURCE_BLOCKED; baseline preservada; deploy verificado; E2E MCP `TEST_NOT_RUN`. **Data:** 2026-11-02. Refs: docs 100–103.

## 1. Infraestrutura (INVENTORY)

Dev host: 9.7GiB total, ~4.6GiB livre, 8 cores, 6GB swap — insuficiente para PPS-v3 (modelos multi-GB na init) e marginal para Docling. `INFRASTRUCTURE_CAPACITY_REPORT`: worker dedicado requer ≥12GB RAM isolada (PPS-v3) ou ≥8GB (Docling) — fora do envelope atual → `ARCHITECTURE_DECISION_REQUIRED` para provisioning dedicado real (VM/worker), não improvisado.

## 2. Execuções reais (mesmo corpus, mesmo contrato)

| Motor | 90264302 | Resultado |
|---|---|---|
| eva_baseline_r823 | EXECUTADO | 2 regions, 4-row table, 24 cells, 2 dims, ~60s, ~3GB |
| pp_structure_v3 | RESOURCE_BLOCKED | modelos multi-GB na init → SIGTERM (flags não evitam carga) |
| docling | **UNAVAILABLE** | `docling 2.145 + torch 2.15+cpu` instalados; `docling-layout-heron` snapshot falha carregar image processor sob transformers 5.22 — `UNAVAILABLE` tipado, 37,9s, erro isolado |

## 3. Entregas

- `DoclingEngine` adapter (contract v1 completo) + registry → `engine_capabilities()` agora devolve 3 motores no runtime real (`R9_LOADED` incluía baseline+pps; docling adicionado).
- Erro tipado isolado por motor — falha Docling não afeta baseline/PPS-v3.
- BOM gate R9.1 preservado (90264161 → NOT_COMPARABLE).

## 4. Decisão

Baseline permanece motor produtivo (único executável offline dentro dos recursos). PPS-v3/Docling: candidatos válidos mas requerem worker dedicado ≥12GB isolado — `OWNER_BLOCKED`/`ARCHITECTURE_DECISION_REQUIRED` para provisioning real (VM/container separado via processo canônico de infra). Nenhuma substituição automática; fusão não avaliada (motores não executaram).
