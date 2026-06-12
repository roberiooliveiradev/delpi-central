# Playbook api-delpi — Produção operacional, compras ranking e perdas

**Parent:** [`minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md)  
**Status:** implementado Fases 1–4 (jun/2026) — 15 rotas REST + integração chat base  
**Público:** desenvolvimento api-delpi  
**Doc API:** [`13-producao-operacional.md`](../api/13-producao-operacional.md)

---

## Resumo executivo (estado do código)

| Bloco | Rotas | api-delpi | chat base | Notas |
|-------|------:|-----------|-----------|-------|
| Fase 1 P0 | R01–R04, R06–R08 | ✅ | ✅ | Consumo, compras ranking, perdas, programação |
| Fase 2 P1 | R09–R11, R02b, R03 | ✅ | ✅ | OPs abertas/finalizadas, CT, consumo por CT/validado |
| Fase 3 P2 | R12–R15 | ✅ | ✅ | Gaps empenho, OP sem consumo, tempo médio CT, consumo por item |
| Fase 4 P3 | R16 | ✅ | ✅ | Planejado × real por OP |
| R05 (produto) | `/products/{code}/last-purchase` | ✅ | ✅ | Rota de produto, não operacional |

**Pendências operacionais (não bloqueiam release):** latência p95 em TOTVS dev; smoke meta em `test_route_meta_smoke.py` para rotas operacionais; regenerar `openapi_baseline.json` e catálogo `_generated`.

---

## 1. Objetivo

Rotas REST que encapsulam os SQL validados nos playbooks:

- [`sql-playbook-producao-suprimentos-perdas.txt`](../../../minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/sql-playbook-producao-suprimentos-perdas.txt)
- [`sql-data-api-instructions.md`](../../../minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/sql-data-api-instructions.md) (exemplos §1–8, §17–20)

**Não** substituir `POST /data/sql` globalmente — apenas cobrir intents recorrentes.

---

## 2. Padrão de implementação (espelhar preço MP)

Referência concluída: [`playbook-analise-preco-materia-prima.md`](./playbook-analise-preco-materia-prima.md).

```text
Router (fino)
  → build_*_use_case() [composition]
    → UseCase.execute(dto)
      → Repository (TOTVS SQL parametrizado)
      → Domain service (fórmulas compartilhadas)
    → api_delpi_success(data, operation_id=...)
```

---

## 3. Rotas Fase 1 (P0) — especificação

### 3.1 `GET /production/consumption/top-items`

| Campo | Valor |
|-------|-------|
| operationId | `get_production_consumption_top_items` |
| entity | `production_consumption_top_items` |
| shape | `playbook_report` |
| SQL base | playbook modelos **A** (por filial) e **B** (geral) |

**Query params:**

| Param | Default | Descrição |
|-------|---------|-----------|
| `date_start`, `date_end` | mês atual | Intervalo fechado-aberto em `D4_DATA` |
| `branch` | todas | `D4_FILIAL` |
| `limit` | 10 | TOP N |
| `group_by` | `general` | `general` \| `branch` |

**Colunas resposta (`items[]`):**

| Campo API | Origem |
|-----------|--------|
| `item_code` | `D4_COD` |
| `description` | `SB1.B1_DESC` |
| `branch` | `D4_FILIAL` (se group_by=branch) |
| `real_consumption_qty` | fórmula consumo real §4.2 parent playbook |
| `unit` | `SB1.B1_UM` |

---

### 3.2 `GET /purchases/top-products`

| Campo | Valor |
|-------|-------|
| operationId | `get_purchases_top_products` |
| entity | `purchases_top_products` |
| shape | `playbook_report` |
| SQL base | playbook modelo **E**, sql-data §19 |

**Query params:** `date_start`, `date_end`, `branch`, `limit` (default 10)

**Colunas:**

| Campo | Origem |
|-------|--------|
| `product_code` | `D1_COD` |
| `description` | `SB1.B1_DESC` |
| `branch` | `D1_FILIAL` |
| `invoice_count` | `COUNT(DISTINCT D1_DOC)` |
| `total_quantity` | `SUM(D1_QUANT)` |
| `total_value` | `SUM(D1_TOTAL)` |
| `last_purchase_date` | `MAX(D1_EMISSAO)` |

**Ordenação:** `total_quantity DESC`, depois `total_value DESC`.

---

### 3.3 `GET /production/losses/top-materials`

| Campo | Valor |
|-------|-------|
| operationId | `get_production_losses_top_materials` |
| entity | `production_losses_top_materials` |
| shape | `playbook_report` |
| SQL base | playbook modelo **H**, sql-data §20 (agregado) |

**Query params:** `date_start`, `date_end`, `branch`, `limit`, `loss_type` (`refugo`|`scrap`|`both`)

**Colunas:** `material_code`, `description`, `branch`, `loss_type`, `total_loss_qty`, `occurrence_count`

Filtro MP: `SB1.B1_TIPO = 'MP'`.

---

### 3.4 `GET /production/losses/records`

| Campo | Valor |
|-------|-------|
| operationId | `get_production_losses_records` |
| entity | `production_losses_records` |
| shape | `playbook_report` |
| SQL base | playbook modelo **G** (detalhe linha a linha) |

**Colunas:** `branch`, `loss_date`, `production_order`, `operation`, `material_code`, `description`, `loss_type`, `loss_qty`, `reason`, `resource`, …

---

### 3.5 `GET /production/schedule/today`

| Campo | Valor |
|-------|-------|
| operationId | `get_production_schedule_today` |
| entity | `production_schedule_today` |
| shape | `playbook_report` |
| SQL base | sql-data §1 (SC2010 + SH8010 + SB1010) |

**Query params:**

| Param | Default |
|-------|---------|
| `reference_date` | hoje |
| `branch` | todas |
| `limit` | 50 |

**Regras de negócio (sql-data §1):**

- OP ativa: `SC2010.D_E_L_E_T_ = ''`
- Prioridade livre: `C2_PRIOR` conforme ambiente (validar com PCP)
- Operação programada para `reference_date` via `SH8010.H8_DTINI`
- Produto acabado válido via join `SB1010`

**Colunas:** `branch`, `production_order`, `product_code`, `description`, `planned_qty`, `produced_qty`, `priority`, `work_center`, …

> **Nota chat:** esta rota **substitui** o fast path `ChatSqlProductionQueryService` («produzidos hoje») quando entregue.

---

## 4. Rotas Fase 2 (P1) — resumo ✅

| Path | operationId | SQL ref |
|------|-------------|---------|
| `GET /production/orders/open` | `get_production_orders_open` | sql-data §3–4 |
| `GET /production/orders/finished` | `get_production_orders_finished` | sql-data §2 |
| `GET /production/work-centers/order-summary` | `get_production_work_center_order_summary` | sql-data §5 |
| `GET /production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` | playbook **C** |
| `GET /production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` | playbook **D** |

---

## 4.1 Rotas Fase 3 (P2) — resumo ✅

| Path | operationId | Uso |
|------|-------------|-----|
| `GET /production/allocation-gaps` | `get_production_allocation_gaps` | Componentes sem empenho (travamento) |
| `GET /production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` | OP finalizada sem baixa de MP |
| `GET /production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` | Tempo médio planejado por CT |
| `GET /production/consumption/by-item/{code}` | `get_production_consumption_by_item` | Consumo real de item por produto |

---

## 4.2 Rotas Fase 4 (P3) — resumo ✅

| Path | operationId | Uso |
|------|-------------|-----|
| `GET /production/planned-vs-real-time` | `get_production_planned_vs_real_time` | Planejado × real por OP (classificação OK/ATENÇÃO/ESTOURO) |

---

## 5. Serviços de domínio compartilhados ✅

Implementados em `app/domain/services/production/` (api-delpi):

| Serviço | Função |
|---------|--------|
| `ProtheusDateRangeService` | Converte `date_start`/`date_end`/`reference_date` → `AAAAMMDD`, intervalo fechado-aberto |
| `ConsumptionRealQuantityService` | Fórmula `D4_QTDEORI - D4_QUANT` |
| `PurchaseValidityFilterService` | Exclui transportadoras e fornecedores internos |
| `ProductionLossTypeFilterService` | Mapeia `loss_type` → `BC_TIPO` |

Evita duplicar SQL entre repositórios.

---

## 6. Registro HTTP ✅

### 6.1 Routers

- `app/interface/http/routes/production/production_operational_router.py` — 14 endpoints sob `/production`
- `app/interface/http/routes/purchases/purchases_router.py` — `GET /purchases/top-products`
- Montados em `app/main.py` (prefix `/production` compartilhado com KPIs — paths não colidem)

### 6.2 OpenAPI agent metadata ✅

Constantes `PRODUCTION_*` e `PURCHASES_TOP_PRODUCTS` em `openapi_agent_metadata.py` via `agent_route()` (`summary`, `description`, `operation_id`).  
**Nota:** `agent_route()` não expõe `tags` FastAPI — routers usam `tags=["Produção operacional"]` / `["Compras operacionais"]`.

### 6.3 route_contract_registry.py ✅

Todos os 15 `operationId` registrados com `shape: playbook_report`.

---

## 7. Permissões RBAC

**Implementação atual (jun/2026):** todos os endpoints operacionais usam `API_DELPI_ACCESS` (`api-delpi.access`) via `@require_permission` em `api_delpi_permissions.py`.

Permissões granulares (`api-delpi.production.access`, `api-delpi.purchases.access`) permanecem **backlog** — depende de perfis formais no Core API.

---

## 8. Testes ✅

### 8.1 Unitário (mock repository)

Arquivos: `tests/test_production_operational_use_cases.py`, `tests/test_production_operational_domain_services.py`.

### 8.2 Integração TOTVS (manual)

```bash
curl -s "$BASE/apps/api-delpi/production/consumption/top-items?date_start=2026-03-01&date_end=2026-04-01&branch=01&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.meta.operationId, .data.summary'
```

### 8.3 Contrato meta

Assertar em todo teste de rota chat-critical:

```python
assert body["meta"]["operationId"] == "get_production_consumption_top_items"
assert body["meta"]["shape"] == "playbook_report"
```

---

## 9. Documentação api-delpi ✅

1. ✅ [`13-producao-operacional.md`](../api/13-producao-operacional.md)
2. ✅ [`10-referencia-rapida-endpoints.md`](../api/10-referencia-rapida-endpoints.md) — rotas operacionais + `/purchases`
3. ✅ [`11-guia-agente-chat.md`](../api/11-guia-agente-chat.md) — seção Playbook 15
4. ✅ [`fase-0-inventario-contrato-respostas.md`](./fase-0-inventario-contrato-respostas.md) — matriz operationId operacional

**Pendente:** smoke meta em `test_route_meta_smoke.py`; regenerar `openapi_baseline.json` e catálogo `_generated` após deploy.

---

## 10. Ordem de implementação (concluída)

Fases 1–4 entregues conforme §Resumo executivo. Pós-deploy: `sync_api_delpi_openapi.py` + reindex RAG + homologação `smoke_playbook_production_operational.py`.

---

## 11. Referências cruzadas

| Artefato | Caminho |
|----------|---------|
| allowed_tables | `api-delpi/app/config/allowed_tables.json` |
| Envelope | `api-delpi/app/core/responses.py` |
| Produto preço MP (modelo) | `product_raw_material_price_repository.py` |
| Playbook master | [`playbook-15-rotas-operacionais-sem-sql.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md) |
| Chat integration | [`playbook-15-chat-integracao-producao-suprimentos.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-chat-integracao-producao-suprimentos.md) |
