# 13 — Produção operacional e compras (Playbook 15)

**Status:** implementado (jun/2026)  
**Parent:** [`playbook-producao-consumo-compras-perdas-op.md`](../roadmaps/playbook-producao-consumo-compras-perdas-op.md)  
**Integração chat:** [`playbook-15-rotas-operacionais-sem-sql.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md)

Rotas REST que encapsulam SQL validado de produção, consumo, perdas, OPs e ranking de compras — **preferir estas rotas** em vez de `POST /data/sql` quando o agente tiver a action habilitada.

**Permissão:** `api-delpi.access` (`API_DELPI_ACCESS`) em todos os endpoints abaixo.

**Envelope:** `{ success, message, data, meta }` com `meta.operationId` e `meta.shape = playbook_report`.

---

## Parâmetros comuns

| Parâmetro | Uso |
|-----------|-----|
| `date_start`, `date_end` | Intervalo em `D4_DATA` / período de compras (formato `YYYY-MM-DD` ou `AAAAMMDD`) |
| `reference_date` | Data única para OPs, programação e análises do dia |
| `branch` | Filial Protheus (`01`, `02`, …) — opcional |
| `limit` | TOP N (default varia por rota; máx. 200 onde aplicável) |
| `code` | Código do item (path em `by-item/{code}`) |

---

## Consumo (`/production/consumption`)

| Método | Path | operationId | Quando usar |
|--------|------|-------------|-------------|
| GET | `/production/consumption/top-items` | `get_production_consumption_top_items` | Ranking geral de consumo real no período |
| GET | `/production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` | Consumo agrupado por centro de trabalho |
| GET | `/production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` | Consumo com apontamento SH6010 confirmado |
| GET | `/production/consumption/by-item/{code}` | `get_production_consumption_by_item` | Consumo real de um item por produto pai |

**Query extras:** `group_by` (`general` \| `branch`) em `top-items`; `work_center`, `product_group` onde aplicável.

**Não confundir:** consumo de produção ≠ estoque (`/products/{code}/stock`) ≠ compras de um item (`/products/{code}/purchases`).

---

## Perdas / refugo (`/production/losses`)

| Método | Path | operationId | Quando usar |
|--------|------|-------------|-------------|
| GET | `/production/losses/top-materials` | `get_production_losses_top_materials` | Ranking agregado de MP com mais refugo/scrap |
| GET | `/production/losses/records` | `get_production_losses_records` | Detalhe linha a linha (OP, motivo, quantidade) |

**Query extras:** `loss_type` = `refugo` \| `scrap` \| `both`.

---

## Ordens de produção e programação

| Método | Path | operationId | Quando usar |
|--------|------|-------------|-------------|
| GET | `/production/schedule/today` | `get_production_schedule_today` | Produtos programados para a data (PCP) |
| GET | `/production/orders/open` | `get_production_orders_open` | OPs em aberto na data |
| GET | `/production/orders/finished` | `get_production_orders_finished` | OPs finalizadas na data |
| GET | `/production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` | OPs finalizadas sem baixa de MP |
| GET | `/production/work-centers/order-summary` | `get_production_work_center_order_summary` | Contagem de OPs por CT |
| GET | `/production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` | Tempo médio planejado por CT |
| GET | `/production/allocation-gaps` | `get_production_allocation_gaps` | Componentes sem empenho (travamento) |
| GET | `/production/planned-vs-real-time` | `get_production_planned_vs_real_time` | Planejado × real por OP (OK/ATENÇÃO/ESTOURO) |

---

## Compras — ranking global (`/purchases`)

| Método | Path | operationId | Quando usar |
|--------|------|-------------|-------------|
| GET | `/purchases/top-products` | `get_purchases_top_products` | Produtos mais comprados no período (ranking global) |

**Não confundir:** `/purchases/top-products` (ranking) ≠ `/products/{code}/purchases` (histórico de um item) ≠ `/products/{code}/last-purchase` (última compra).

---

## Implementação (referência)

| Camada | Caminho |
|--------|---------|
| Router produção | `app/interface/http/routes/production/production_operational_router.py` |
| Router compras | `app/interface/http/routes/purchases/purchases_router.py` |
| Metadata OpenAPI | `app/interface/http/openapi_agent_metadata.py` (`PRODUCTION_*`, `PURCHASES_TOP_PRODUCTS`) |
| Contrato | `app/interface/http/route_contract_registry.py` |
| Domain services | `app/domain/services/production/` |
| Testes | `tests/test_production_operational_use_cases.py`, `test_production_operational_domain_services.py` |

Montagem em `app/main.py` com prefix `/production` (KPIs e operacional coexistem sem colisão de paths).

---

## Chat (minha-delpi-ai-api)

| Camada | Serviço / artefato |
|--------|-------------------|
| Intent | `ChatProductionOperationalIntentService` + `production_operational_intent.json` |
| Seleção | `external_action_production_operational_route_selection_service.py` |
| Presenter | `ExternalActionPlaybookReportPresenter` + `presenter_content.json` |
| Readiness | `ChatProductionOperationalActionReadinessService` (Playbook 16) |
| Regressão | `production_operational_regression_cases.py`, `chat_intelligence_regression_cases.py` |
| Smoke | `scripts/smoke_playbook_production_operational.py` |

Após deploy: reimportar OpenAPI (`POST .../providers/api-delpi/import?async=true`) e reindexar [`api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md).

---

## Frases exemplo (agente)

| Intenção | Exemplos |
|----------|----------|
| Consumo | «itens mais consumidos mês passado», «top consumo MP filial 01» |
| Compras ranking | «produtos mais comprados em março», «ranking de compras» |
| Perdas | «refugos de MP no trimestre», «materiais com mais scrap» |
| Programação | «programados para produzir hoje», «OPs do dia filial 01» |
| OPs | «OPs em aberto hoje», «OPs finalizadas ontem» |
| Travamento | «componentes sem empenho», «travamento de produção» |

Guia expandido para RAG: [`minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md) (seção Playbook 15).
