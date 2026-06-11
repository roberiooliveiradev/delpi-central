# Playbook api-delpi — Produção operacional, compras ranking e perdas

**Parent:** [`minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md)  
**Status:** roadmap (jun/2026)  
**Público:** desenvolvimento api-delpi

---

## 1. Objetivo

Implementar rotas REST que encapsulam os SQL validados nos playbooks:

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

## 4. Rotas Fase 2 (P1) — resumo

| Path | operationId | SQL ref |
|------|-------------|---------|
| `GET /production/orders/open` | `get_production_orders_open` | sql-data §3–4 |
| `GET /production/orders/finished` | `get_production_orders_finished` | sql-data §2 |
| `GET /production/work-centers/order-summary` | `get_production_work_center_order_summary` | sql-data §5 |
| `GET /production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` | playbook **C** |
| `GET /production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` | playbook **D** |

---

## 5. Serviços de domínio compartilhados

Criar `app/domain/services/production/` (api-delpi):

| Serviço | Função |
|---------|--------|
| `ProtheusDateRangeService` | Converte `date_start`/`date_end`/`reference_date` → `AAAAMMDD`, intervalo fechado-aberto |
| `ConsumptionRealQuantityService` | Fórmula `D4_QTDEORI - D4_QUANT` |
| `PurchaseValidityFilterService` | Exclui transportadoras e fornecedores internos |
| `ProductionLossTypeFilterService` | Mapeia `loss_type` → `BC_TIPO` |

Evita duplicar SQL entre repositórios.

---

## 6. Registro HTTP

### 6.1 Router

```python
# app/interface/http/routes/production/production_operational_router.py
from app.interface.http.route_response_helpers import api_delpi_success

@router.get("/consumption/top-items")
def get_consumption_top_items(...):
    result = build_get_production_consumption_top_items_use_case().execute(dto)
    return api_delpi_success(
        result,
        operation_id="get_production_consumption_top_items",
        message="Itens mais consumidos consultados com sucesso.",
    )
```

Montar router em `app/main.py` com prefix `/production` (mesmo prefix dos KPIs — paths não colidem).

### 6.2 OpenAPI agent metadata

```python
# openapi_agent_metadata.py
PRODUCTION_CONSUMPTION_TOP_ITEMS = agent_route(
    summary="Itens mais consumidos no período",
    description="Ranking de consumo real (SD4010) por filial ou geral.",
    operation_id="get_production_consumption_top_items",
    tags=["production", "chat-critical"],
)
```

### 6.3 route_contract_registry.py

```python
"get_production_consumption_top_items": RouteContract(
    "production_consumption_top_items", "playbook_report"
),
```

---

## 7. Permissões RBAC

Sugestão (validar com Core API):

| Rota | Permissão |
|------|-----------|
| `/production/consumption/*`, `/production/losses/*`, `/production/schedule/*`, `/production/orders/*` | `api-delpi.production.access` ou `api-delpi.access` |
| `/purchases/top-products` | `api-delpi.purchases.access` ou `api-delpi.access` |

Importar de `api_delpi_permissions.py` — não strings literais no router.

---

## 8. Testes

### 8.1 Unitário (mock repository)

```python
def test_consumption_top_items_groups_by_branch(repository_mock):
    repository_mock.fetch_top_items.return_value = [{"item_code": "10080001", ...}]
    result = GetProductionConsumptionTopItemsUseCase(repository_mock).execute(dto)
    assert result["items"][0]["item_code"] == "10080001"
```

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

## 9. Documentação api-delpi

Após implementar Fase 1:

1. Criar `api-delpi/docs/api/13-producao-operacional.md`
2. Atualizar `10-referencia-rapida-endpoints.md`
3. Atualizar `11-guia-agente-chat.md`
4. Atualizar `fase-0-inventario-contrato-respostas.md` (matriz operationId)

---

## 10. Ordem de implementação recomendada (Fase 1)

1. `ProtheusDateRangeService` + testes
2. `production_consumption_repository` + R01
3. `purchases_ranking_repository` + R04
4. `production_losses_repository` + R06, R07
5. `production_schedule_repository` + R08
6. Registro contrato + OpenAPI + testes smoke
7. PR api-delpi → deploy → avisar equipe chat

---

## 11. Referências cruzadas

| Artefato | Caminho |
|----------|---------|
| allowed_tables | `api-delpi/app/config/allowed_tables.json` |
| Envelope | `api-delpi/app/core/responses.py` |
| Produto preço MP (modelo) | `product_raw_material_price_repository.py` |
| Playbook master | [`playbook-15-rotas-operacionais-sem-sql.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md) |
| Chat integration | [`playbook-15-chat-integracao-producao-suprimentos.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-chat-integracao-producao-suprimentos.md) |
