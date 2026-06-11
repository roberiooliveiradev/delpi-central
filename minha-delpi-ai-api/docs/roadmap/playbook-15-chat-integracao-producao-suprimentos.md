# Playbook 15 — Integração chat: produção, suprimentos e perdas (sem SQL)

**Parent:** [`playbook-15-rotas-operacionais-sem-sql.md`](./playbook-15-rotas-operacionais-sem-sql.md)  
**Pré-requisito:** rotas Fases 1–4 entregues na api-delpi + OpenAPI reimportado  
**Status:** implementado (jun/2026) — Fases P0–P3 + knowledge/regressão PO01–PO14

Modelo: [`playbook-chat-preco-mp-simulador-custos-pa.md`](./playbook-chat-preco-mp-simulador-custos-pa.md).

---

## 1. Objetivo

Conectar ao pipeline base as rotas operacionais para que perguntas como «itens mais consumidos mês passado» ou «refugos de março» disparem `execute_external_action` — **não** `POST /data/sql`.

---

## 2. Mapa intent → rota (Fases 1–4 — completo)

| Frase exemplo | operationId | Parâmetros mínimos |
|---------------|-------------|-------------------|
| «itens mais consumidos», «maior consumo» | `get_production_consumption_top_items` | período (default: mês atual) |
| «produtos mais comprados» | `get_purchases_top_products` | período |
| «refugos matéria-prima», «scrap no período» | `get_production_losses_top_materials` | período; `loss_type` inferido |
| «listar refugos detalhado» | `get_production_losses_records` | período |
| «produzidos hoje», «programados hoje» | `get_production_schedule_today` | `reference_date` (default hoje) |
| «OPs em aberto» | `get_production_orders_open` | `reference_date`, `branch` |
| «OPs finalizadas» | `get_production_orders_finished` | `reference_date`, `branch` |
| «resumo OPs por CT» | `get_production_work_center_order_summary` | `reference_date`, `limit` |
| «consumo por centro de trabalho» | `get_production_consumption_top_items_by_work_center` | período |
| «consumo validado por apontamento» | `get_production_consumption_top_items_validated` | período |
| «componentes sem empenho» | `get_production_allocation_gaps` | `reference_date`, `branch` |
| «OPs finalizadas sem consumo» | `get_production_orders_finished_without_consumption` | `reference_date` |
| «tempo médio planejado por CT» | `get_production_work_center_average_planned_time` | `reference_date` |
| «consumo real do item X» | `get_production_consumption_by_item` | `code` (path), período |
| «planejado × real por OP» | `get_production_planned_vs_real_time` | `reference_date`, `branch` |

---

## 3. Desambiguação (crítico)

| Usuário pede | NÃO usar | Usar |
|--------------|----------|------|
| Itens mais **consumidos** | `/products/search`, SQL SC2010 | `get_production_consumption_top_items` |
| Produtos mais **comprados** (ranking) | `/products/{code}/purchases` | `get_purchases_top_products` |
| Última compra **de um** produto | ranking | `get_product_last_purchase` (Fase 0) |
| **Refugo** / perda MP | KPI `/quality/*` | `get_production_losses_*` |
| Programação **hoje** | `ChatSqlProductionQueryService` + `/data/sql` | `get_production_schedule_today` |
| Preço MP / impacto PA | SQL SG1010 | Fase 0 ✅ |

---

## 4. Arquivos a estender

### 4.1 Vocabulário JSON

| Arquivo | Seções novas |
|---------|--------------|
| `app/content/pt-BR/assistant/production_operational_intent.json` | **Novo bundle** — termos consumo, compras ranking, refugo, programação |
| `app/content/pt-BR/assistant/product_query_intent.json` | Excludes — não confundir consumo com estoque |
| `app/content/pt-BR/assistant/api_route_domains.json` | Domínios `production_consumption`, `production_losses`, `purchases_ranking`, `production_schedule` |
| `app/content/pt-BR/assistant/external_action_responses.json` | `selectionReasons.*` |
| `app/content/pt-BR/assistant/presenter_content.json` | Títulos por path fragment |
| `app/content/pt-BR/assistant/column_labels.json` | `real_consumption_qty`, `total_loss_qty`, `invoice_count`, … |
| `app/content/pt-BR/labels/api_paths.json` | Rótulos PT das novas rotas |

### 4.2 Serviços domain/application

| Serviço | Ação |
|---------|------|
| `ChatProductionOperationalIntentService` | **Novo** — classifica consumo/compras ranking/perdas/schedule |
| `ExternalActionRouteSelectionService` | Registrar paths antes do fallback semântico |
| `ExternalActionProductRouteSelectionService` | N/A para rotas **sem** `{code}` no path |
| `ChatOperationalDateParameterService` | Merge período; **schedule today** usa `reference_date` |
| `ChatSqlOperationalIntentService` | **Excluir** intents cobertos (schedule today → R08) |
| `ChatSqlProductionQueryService` | Deprecar após R08 em produção |
| `OperationalApiParameterBuilderService` | Strategies `date_branch`, `limit`, `loss_type` |

### 4.3 Apresentação

| Arquivo | Ação |
|---------|------|
| `chat_api_delpi_response_profile_service.py` | Perfis `production_consumption_top_items`, … |
| `presentation_profiles.json` | `pathContains`: `/consumption/`, `/losses/`, `/purchases/top` |
| `external_action_result_presenter.py` | Branch por path; tabela default `playbook_report` |
| `execute_external_action_use_case.py` | `enrich_metadata` |

Rotas **sem** `{code}`: presenter genérico `playbook_report` (como KPIs departamentais).

### 4.4 RAG e knowledge

| Arquivo | Ação |
|---------|------|
| `docs/knowledge/api-delpi-rotas-agente.md` | Tabela Fase 1 + frases |
| Playbooks `.txt` | Bloco «Preferir rota dedicada» |
| `capabilities.json` | `pathRules`, `commonExamples` |

---

## 5. Parâmetros e sessão ativa

| Rota | Código produto | Data |
|------|----------------|------|
| consumption top | não | obrigatória se usuário citar período; default mês atual |
| purchases top | não | idem |
| losses | não | idem + `loss_type` default `both` |
| schedule today | não | `reference_date` default hoje |

`ChatActiveQuerySessionService`: segmentos `production/consumption`, `production/losses`, `purchases/top-products`, `production/schedule`.

Follow-up «filial 02», «top 20», «mês passado» → recomponer via `compose_selection_message`.

---

## 6. Ordem de implementação chat

1. Sync OpenAPI + `api_paths.json`
2. `production_operational_intent.json` + intent service
3. `ExternalActionRouteSelectionService` (rotas **sem** produto no path — novo delegate ou estender `ExternalActionOperationalRouteSelectionService`)
4. Desligar SQL fast path para intents cobertos
5. Presenter mínimo (tabela + summary)
6. Regressão + smoke
7. Atualizar playbooks knowledge

---

## 7. Testes

### Fixtures (`tests/fixtures/production_operational_regression_cases.py`)

Casos PO01–PO02/PO04 em `chat_intelligence_regression_cases.py`; PO03–PO14 no fixture dedicado — wired em `test_action_selection_regression`.

### Smoke

Estender ou criar `scripts/smoke_playbook_production_operational.py` — frases S1–S4 do playbook master §9.3.

---

## 8. Checklist de aceite

- [x] PO01–PO14 passam seleção sem `/data/sql` (regressão `test_action_selection_regression`)
- [x] «Produzidos hoje» usa `get_production_schedule_today` (não SQL template SC2010)
- [x] «Estoque do produto X» **não** aciona consumption top (decoys nos fixtures)
- [x] Textos só em JSON
- [x] Send/stream paridade (mesmo pipeline base)
- [x] `meta.operationId` no presenter
- [x] Smoke E2E S1–S14 — script `smoke_playbook_production_operational.py` (0 falhas de rota; validar qualidade de resposta em homologação)

---

## 9. Comandos

```bash
# Reimport OpenAPI
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/sync_api_delpi_openapi.py

# Regressão
cd minha-delpi-ai-api && pytest tests/unit/domain/services/test_chat_intelligence_regression.py -q
```

---

## 10. Referências

- Master: [`playbook-15-rotas-operacionais-sem-sql.md`](./playbook-15-rotas-operacionais-sem-sql.md)
- api-delpi: [`playbook-producao-consumo-compras-perdas-op.md`](../../../api-delpi/docs/roadmaps/playbook-producao-consumo-compras-perdas-op.md)
- Arquitetura: [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
