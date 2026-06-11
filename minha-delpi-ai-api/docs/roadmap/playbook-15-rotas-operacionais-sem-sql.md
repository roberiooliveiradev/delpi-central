# Playbook 15 — Rotas api-delpi para produção, suprimentos e perdas (sem inferir SQL)

**Status:** implementado Fases 1–4 (jun/2026) — rotas REST P0–P3 na api-delpi + roteamento/presenter no chat base; SQL playbook mantido como fallback quando a action não estiver habilitada  
**Público:** api-delpi, minha-delpi-ai-api, gestão de agentes  
**Objetivo:** substituir execução ad hoc via `POST /data/sql` por **rotas REST declarativas**, com presenter e roteamento determinístico no chat base.

---

## 1. Problema

Hoje o agente técnico DELPI resolve perguntas operacionais montando T-SQL e chamando `POST /data/sql`. Isso funciona, mas:

| Risco | Impacto |
|-------|---------|
| LLM/agente **infere** JOIN, filtro de data ou fórmula de consumo | Resposta errada ou lenta |
| SQL grande (CTE recursiva, EXISTS) | `ResponseTooLargeError`, timeout |
| Regras duplicadas entre prompt RAG, playbook `.txt` e código | Drift e regressão |
| Sem `meta.operationId` / presenter | UI genérica ou markdown cru |
| Turno passa pelo loop SQL (`ChatSqlOperationalIntentService`) | Latência e tokens desnecessários |

**Regra-mãe (chat base):** regras validadas nos playbooks SQL viram **rotas + repositório + use case** na api-delpi; o chat **seleciona a action** — não reescreve a consulta.

---

## 2. Fontes de verdade (knowledge)

| Arquivo | Escopo | Rotas-alvo |
|---------|--------|------------|
| [`sql-playbook-producao-suprimentos-perdas.txt`](../knowledge/domains/agents/minha-delpi-chat/sql-playbook-producao-suprimentos-perdas.txt) | Consumo SD4010, compras SD1010, refugo SBC010, CT SH8010, apontamento SH6010 | `/production/consumption/*`, `/purchases/*`, `/production/losses/*` |
| [`sql-playbook-simulador-impacto-custos-pa.txt`](../knowledge/domains/agents/minha-delpi-chat/sql-playbook-simulador-impacto-custos-pa.txt) | Pareto MPs na BOM + simulação reajuste | **`GET /products/{code}/cost-impact-simulation`** ✅ |
| [`sql-playbook-preco-materia-prima.txt`](../knowledge/domains/agents/minha-delpi-chat/sql-playbook-preco-materia-prima.txt) | Preço MP, NF, ICMS, orçamento | **`GET /products/{code}/raw-material-price-intelligence`** ✅ (+ granulares) |
| [`sql-data-api-instructions.md`](../knowledge/domains/agents/minha-delpi-chat/sql-data-api-instructions.md) | 20 exemplos documentados (OPs, CT, consumo, refugo…) | `/production/orders/*`, `/production/work-centers/*`, … |

Playbooks api-delpi já entregues (referência de padrão):

- [`api-delpi/docs/roadmaps/playbook-analise-preco-materia-prima.md`](../../../api-delpi/docs/roadmaps/playbook-analise-preco-materia-prima.md)
- [`api-delpi/docs/roadmaps/playbook-simulador-impacto-custos-pa.md`](../../../api-delpi/docs/roadmaps/playbook-simulador-impacto-custos-pa.md)
- [`playbook-chat-preco-mp-simulador-custos-pa.md`](./playbook-chat-preco-mp-simulador-custos-pa.md) — integração chat (Fase 0)

---

## 3. Inventário — o que já existe

### 3.1 Rotas entregues (não reimplementar)

| Método | Path | operationId | shape |
|--------|------|-------------|-------|
| GET | `/products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` | `composite_analysis` |
| GET | `/products/{code}/last-purchase` | `get_product_last_purchase` | `playbook_report` |
| GET | `/products/{code}/purchase-price-history` | `get_product_purchase_price_history` | `playbook_report` |
| GET | `/products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` | `playbook_report` |
| GET | `/products/{code}/cost-impact-simulation` | `get_product_cost_impact_simulation` | `composite_analysis` |
| GET | `/products/{code}/production-status` | `get_product_production_status` | `playbook_report` |
| GET | `/products/{code}/factory-status` | `get_product_factory_status` | `composite_analysis` |
| POST | `/data/sql` | `execute_sql_query` | — (fallback controlado) |

### 3.2 Lacunas (playbooks → rotas novas)

Mapeamento **SQL validado → rota proposta**:

| ID | Intenção do usuário | Modelo SQL (playbook) | Rota proposta | Prioridade |
|----|---------------------|----------------------|---------------|------------|
| **R01** | Itens mais consumidos (geral / filial) | A, B | `GET /production/consumption/top-items` | **P0** |
| **R02** | Consumo por CT planejado | C | `GET /production/consumption/top-items-by-work-center` | P1 |
| **R03** | Consumo validado por apontamento real | D | `GET /production/consumption/top-items-validated` | P1 |
| **R04** | Produtos mais comprados | E, sql-data §19 | `GET /purchases/top-products` | **P0** |
| **R05** | Última NF válida (produto) | F | *(coberto por `last-purchase`)* | ✅ |
| **R06** | Refugos/scrap no período (detalhe) | G, sql-data §20 | `GET /production/losses/records` | **P0** |
| **R07** | Refugos agrupados por MP | H | `GET /production/losses/top-materials` | **P0** |
| **R08** | Programados para produzir hoje | sql-data §1 | `GET /production/schedule/today` | **P0** |
| **R09** | OPs finalizadas hoje | sql-data §2 | `GET /production/orders/finished` | P1 |
| **R10** | OPs abertas / não finalizadas hoje | sql-data §3–4 | `GET /production/orders/open` | P1 |
| **R11** | OPs por CT — finalizadas vs abertas | sql-data §5 | `GET /production/work-centers/order-summary` | P1 |
| **R12** | Componentes sem empenho (travamento) | sql-data §6 | `GET /production/allocation-gaps` | P2 |
| **R13** | OP finalizada sem consumo | sql-data §7 | `GET /production/orders/finished-without-consumption` | P2 |
| **R14** | Tempo médio por CT (planejado) | sql-data §8 | `GET /production/work-centers/average-planned-time` | P2 |
| **R15** | Consumo real de item X por produto/grupo | sql-data §18 | `GET /production/consumption/by-item/{code}` | P2 |
| **R16** | Planejado × real (setup, hora-mil) | sql-data §17 | `GET /production/planned-vs-real-time` | P3 |
| **R17** | Catálogo MPs exclusivas (global) | playbook estrutura §8 | `GET /products/exclusive-raw-materials/catalog` | ✅ |
| **R18** | Estrutura PA + flags exclusividade | playbook estrutura §10 | `GET /products/{code}/structure/exclusivity` | ✅ |

Detalhe exclusividade: [`api-delpi/docs/roadmaps/playbook-catalogo-exclusividade-mp.md`](../../../api-delpi/docs/roadmaps/playbook-catalogo-exclusividade-mp.md).

---

## 4. Contrato comum (todas as rotas novas)

Seguir [Playbook 10 — contrato api-delpi](./playbook-10-contrato-respostas-api-delpi.md) e regra Cursor `api-delpi-response-contract.mdc`.

### 4.1 Query params padrão

| Param | Tipo | Obrigatório | Default | Notas |
|-------|------|-------------|---------|-------|
| `date_start` | `YYYYMMDD` ou `YYYY-MM-DD` | depende da rota | mês atual (início) | Intervalo **fechado-aberto** internamente |
| `date_end` | idem | não | exclusivo (1º dia mês seguinte) | |
| `reference_date` | idem | alternativa a intervalo | hoje | Rotas «hoje», «programados hoje» |
| `branch` | `01`, `02`, … | não | todas | 2 chars |
| `limit` | int | não | `10` | máx. 200 |
| `group_by` | enum | não | ver rota | `general`, `branch`, `work_center`, `product`, `material` |
| `loss_type` | enum | não | `both` | `refugo` (`R`), `scrap` (`S`), `both` |
| `work_center` | string | não | — | Filtro CT (`H8_CTRAB`) |
| `product_code` | string | não | — | Filtro adicional |
| `item_code` | string | não | — | Componente consumido (`D4_COD`) |
| `include_description` | bool | não | `true` | Join SB1010 |

**Datas Protheus:** repositório converte para `AAAAMMDD`; nunca confiar no LLM para formatar.

### 4.2 Fórmula canônica — consumo real (SD4010)

Única implementação — **domain service** api-delpi, não no chat:

```sql
CASE
  WHEN D4_QTDEORI > D4_QUANT THEN D4_QTDEORI - D4_QUANT
  ELSE 0
END
```

Referência: playbook produção §9 e sql-data §18.

### 4.3 Filtros canônicos — compras (SD1010)

```sql
AND SD1.D1_FORNECE NOT IN ('000019', '001149')
AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
```

Última NF: `ORDER BY D1_EMISSAO DESC, D1_DTDIGIT DESC, D1_DOC DESC` + `ROW_NUMBER()`.

### 4.4 Filtros canônicos — perdas (SBC010)

| loss_type | BC_TIPO |
|-----------|---------|
| `refugo` | `'R'` |
| `scrap` | `'S'` |
| `both` | `IN ('R','S')` |

Refugo MP: `SB1010.B1_TIPO = 'MP'`.

### 4.5 Resposta tipo `playbook_report`

```json
{
  "success": true,
  "message": "...",
  "data": {
    "items": [],
    "summary": {
      "total_records": 0,
      "branch": "01",
      "period": { "start": "20260301", "end": "20260401" }
    }
  },
  "meta": {
    "operationId": "get_production_consumption_top_items",
    "entity": "production_consumption_top_items",
    "shape": "playbook_report"
  }
}
```

Rotas agregadas complexas (ex.: schedule today + resumo por filial): considerar `composite_analysis` se ≥2 seções fixas.

---

## 5. Roadmap por fases

### Fase 0 — Concluída ✅

Preço MP + simulador PA + integração chat parcial.

| Entrega | Doc |
|---------|-----|
| 5 rotas produto (preço / simulador) | playbooks api-delpi preço + simulador |
| Chat intent + presenter | [`playbook-chat-preco-mp-simulador-custos-pa.md`](./playbook-chat-preco-mp-simulador-custos-pa.md) |

**Pendência chat Fase 0:** smoke E2E homologação manual (checklist §7 do playbook chat).

---

### Fase 1 — P0 (consumo, compras, perdas, programação do dia)

**Meta:** cobrir ~70% das perguntas do playbook produção/suprimentos/perdas sem SQL.

| Ordem | Rota | operationId | Esforço api-delpi |
|------:|------|-------------|-------------------|
| 1 | `GET /production/consumption/top-items` | `get_production_consumption_top_items` | M |
| 2 | `GET /purchases/top-products` | `get_purchases_top_products` | M |
| 3 | `GET /production/losses/top-materials` | `get_production_losses_top_materials` | M |
| 4 | `GET /production/losses/records` | `get_production_losses_records` | S |
| 5 | `GET /production/schedule/today` | `get_production_schedule_today` | M |

**Critério de aceite Fase 1:**

- [x] Perguntas smoke (§9) retornam `execute_external_action` sem `POST /data/sql`
- [x] `meta.operationId` registrado em `route_contract_registry.py`
- [x] OpenAPI reimportado no chat (`sync_api_delpi_openapi.py`)
- [x] Presenter com título/colunas de `presenter_content.json`
- [x] Casos PO01–PO14 em `production_operational_regression_cases.py` + smoke `scripts/smoke_playbook_production_operational.py`
- [ ] Latência p95 &lt; 2s (TOTVS dev) — validar em homologação

**Entrega chat (paralela):** [`playbook-15-chat-integracao-producao-suprimentos.md`](./playbook-15-chat-integracao-producao-suprimentos.md)

---

### Fase 2 — P1 (OPs, CT, consumo contextual) ✅

| Rota | operationId | Status |
|------|-------------|--------|
| `GET /production/orders/open` | `get_production_orders_open` | ✅ |
| `GET /production/orders/finished` | `get_production_orders_finished` | ✅ |
| `GET /production/work-centers/order-summary` | `get_production_work_center_order_summary` | ✅ |
| `GET /production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` | ✅ |
| `GET /production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` | ✅ |

---

### Fase 3 — P2 (qualidade produtiva, gaps) ✅

| Rota | operationId | Status |
|------|-------------|--------|
| `GET /production/allocation-gaps` | `get_production_allocation_gaps` | ✅ |
| `GET /production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` | ✅ |
| `GET /production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` | ✅ |
| `GET /production/consumption/by-item/{code}` | `get_production_consumption_by_item` | ✅ |

---

### Fase 4 — P3 (analítico avançado) ✅

| Rota | operationId | Status |
|------|-------------|--------|
| `GET /production/planned-vs-real-time` | `get_production_planned_vs_real_time` | ✅ |

Manter `POST /data/sql` apenas para **exploração ad hoc** (agente SQL avançado com skill), não para intents cobertos pelas fases 1–3.

---

## 6. Implementação api-delpi (instruções)

Guia detalhado por camada: [`api-delpi/docs/roadmaps/playbook-producao-consumo-compras-perdas-op.md`](../../../api-delpi/docs/roadmaps/playbook-producao-consumo-compras-perdas-op.md).

### 6.1 Checklist por rota

1. **DTO** — `app/application/dto/production/` ou `purchases/`
2. **Port** — `app/domain/ports/production/*_repository_port.py`
3. **Repository** — `app/infrastructure/persistence/totvs/production_repositories/`
   - SQL copiado dos modelos A–H / sql-data §N
   - Parametrizado (`:date_start`, `:branch`, …)
4. **Domain service** (se regra compartilhada) — ex.: `ConsumptionQuantityCalculator`
5. **Use case** — `app/application/use_cases/production/`
6. **Router** — `app/interface/http/routes/production/` (novo módulo operacional, distinto de KPI `/production/oee`)
7. **Composer** — `app/composition/production_operational_composer.py`
8. **Contrato** — `route_contract_registry.py` + `openapi_agent_metadata.py`
9. **Resposta** — `api_delpi_success(..., operation_id=...)`
10. **RBAC** — `@require_permission` via `api_delpi_permissions.py`
11. **Teste** — `api-delpi/tests/test_production_*_use_cases.py` (mock repo)
12. **Doc** — `api-delpi/docs/api/` (módulo produção operacional)

### 6.2 Estrutura de pastas sugerida (api-delpi)

```text
api-delpi/app/
  interface/http/routes/
    production/
      production_router.py          # KPIs existentes (OEE, OTD…)
      production_operational_router.py   # NOVO — R01–R16
    purchases/
      purchases_router.py           # NOVO — R04 top-products
  infrastructure/persistence/totvs/
    production_repositories/
      production_consumption_repository.py
      production_losses_repository.py
      production_orders_repository.py
      production_schedule_repository.py
    purchases_repositories/
      purchases_ranking_repository.py
```

### 6.3 Tabelas (whitelist)

Já autorizadas em `allowed_tables.json`: SC2010, SD4010, SH8010, SH6010, SB1010, SD1010, SA2010, SA5010, SBC010.

**Não** expandir whitelist sem revisão de segurança.

### 6.4 Desambiguação (não confundir)

| Usuário pede | Rota errada | Rota certa |
|--------------|-------------|------------|
| Produtos programados **hoje** | `/products/search` | `GET /production/schedule/today` |
| Mais **consumidos** | `/products/{code}/stock` | `GET /production/consumption/top-items` |
| Mais **comprados** (ranking) | `/products/{code}/purchases` (1 produto) | `GET /purchases/top-products` |
| Última compra **de um** item | ranking | `GET /products/{code}/last-purchase` |
| **Refugo** MP | `/quality/*` KPI | `GET /production/losses/*` |
| Preço / impacto custo PA | SQL SG1010 | rotas Fase 0 ✅ |

---

## 7. Integração chat (resumo)

Detalhes: [`playbook-15-chat-integracao-producao-suprimentos.md`](./playbook-15-chat-integracao-producao-suprimentos.md).

Módulos canônicos (não duplicar em use case):

| Camada | Arquivo |
|--------|---------|
| Vocabulário | `product_query_intent.json`, novo `production_operational_intent.json` |
| Intent | `ChatProductionOperationalIntentService` (novo) |
| Seleção | `ExternalActionRouteSelectionService`, `ExternalActionProductRouteSelectionService` |
| Parâmetros | `ChatOperationalDateParameterService`, `ChatOperationalParameterService` |
| Domínio rota | `api_route_domains.json` → domínio `production_operational`, `purchases_ranking` |
| Presenter | `external_action_result_presenter.py` + sub-presenters |
| Conteúdo | `presenter_content.json`, `column_labels.json`, `external_action_responses.json` |
| Labels | `labels/api_paths.json` |
| RAG agente | `api-delpi-rotas-agente.md` |

**Desligar SQL operacional** para intents cobertos:

- `ChatSqlOperationalIntentService` — não acionar quando intent mapeia para R01–R08
- `ChatSqlProductionQueryService` — programação «hoje» migra para R08

---

## 8. Atualização dos playbooks knowledge (pós-rota)

Quando cada fase fechar, editar os `.txt` / `.md` do agente:

```text
Preferir rota dedicada quando disponível:
GET /production/consumption/top-items

Se a rota ainda não existir, montar SQL via POST /data/sql.
```

Ordem:

1. Deploy api-delpi
2. `sync_api_delpi_openapi.py`
3. Atualizar playbooks knowledge + `api-delpi-rotas-agente.md`
4. Reindexar RAG do agente `minha-delpi-chat`
5. `export_agent_knowledge_bundle.py`

---

## 9. Testes e homologação

### 9.1 api-delpi (unitário)

```bash
cd api-delpi && pytest tests/test_production_consumption_use_cases.py -q
```

### 9.2 chat (regressão)

```bash
cd minha-delpi-ai-api && pytest \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/application/services/test_external_action_selection_service.py -q
```

### 9.3 Smoke E2E (Fases 1–4)

Script: `scripts/smoke_playbook_production_operational.py` (API R01–R16 + chat S1–S14).

| # | Pergunta | Rota / operationId |
|---|----------|-------------------|
| S1 | «Itens mais consumidos mês passado filial 01 top 10» | R01 `get_production_consumption_top_items` |
| S2 | «Produtos mais comprados março 2026» | R04 `get_purchases_top_products` |
| S3 | «Refugos de matéria-prima março filial 02 top 10» | R07 `get_production_losses_top_materials` |
| S4 | «Quais produtos serão produzidos hoje?» | R08 `get_production_schedule_today` |
| S5 | «Liste as OPs em aberto de hoje filial 01» | R09/R10 `get_production_orders_open` |
| S6 | «Quais OPs finalizadas hoje?» | R09 `get_production_orders_finished` |
| S7 | «Resumo de OPs por centro de trabalho hoje» | R11 `get_production_work_center_order_summary` |
| S8 | «Itens com maior consumo por CT mês passado top 10» | R02 `get_production_consumption_top_items_by_work_center` |
| S9 | «Consumo validado por apontamento no mês top 10» | R03 `get_production_consumption_top_items_validated` |
| S10 | «Liste componentes sem empenho hoje filial 01» | R12 `get_production_allocation_gaps` |
| S11 | «Quais OPs finalizadas sem consumo hoje?» | R13 `get_production_orders_finished_without_consumption` |
| S12 | «Tempo médio planejado por CT hoje» | R14 `get_production_work_center_average_planned_time` |
| S13 | «Consumo real do item 01010001» | R15 `get_production_consumption_by_item` |
| S14 | «Compare tempo planejado e tempo real das OPs hoje filial 01» | R16 `get_production_planned_vs_real_time` |

Doc manual: [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) (seção **Playbook 15**).

---

## 10. Estimativa e dependências

| Fase | Rotas | api-delpi | chat | RAG |
|------|------:|-----------|------|-----|
| 1 P0 | 5 | 2–3 sprints | 1 sprint | 0,5 sprint |
| 2 P1 | 5 | 2 sprints | 1 sprint | 0,5 sprint |
| 3 P2 | 4 | 2 sprints | 0,5 sprint | 0,5 sprint |
| 4 P3 | 1 | 1 sprint | 0,5 sprint | — |

**Dependências:** VPN/TOTVS dev, `allowed_tables.json`, reimport OpenAPI, permissões RBAC (`api-delpi.access` + escopo produção/compras).

---

## 11. Referências

| Doc | Conteúdo |
|-----|----------|
| [playbook-producao-consumo-compras-perdas-op.md](../../../api-delpi/docs/roadmaps/playbook-producao-consumo-compras-perdas-op.md) | Implementação api-delpi (SQL, camadas, exemplos) |
| [playbook-15-chat-integracao-producao-suprimentos.md](./playbook-15-chat-integracao-producao-suprimentos.md) | Integração chat base |
| [playbook-16-openapi-import-async-e-readiness-operacional.md](./playbook-16-openapi-import-async-e-readiness-operacional.md) | Import async, progresso UI, readiness pós-deploy |
| [playbook-10-contrato-respostas-api-delpi.md](./playbook-10-contrato-respostas-api-delpi.md) | meta.shape / operationId |
| [playbook-11-clean-architecture-chat-api.md](./playbook-11-clean-architecture-chat-api.md) | Camadas chat |
| [chat-intelligence-base.md](../architecture/chat-intelligence-base.md) | Pipeline |
| [api-delpi-chat-intelligence-audit.md](./api-delpi-chat-intelligence-audit.md) | Auditoria rotas |

---

## 12. Resumo executivo

**Status jun/2026:** as **15 rotas operacionais** do Playbook 15 (R01–R04, R06–R16) estão entregues na **api-delpi** e integradas no **chat base** (intent, seleção, presenter, regressão PO01–PO14, smoke S1–S14). Rotas de produto da Fase 0 (preço MP, simulador, exclusividade) permanecem como estavam.

| Bloco | Rotas | api-delpi | chat | RAG |
|-------|------:|-----------|------|-----|
| Fase 0 (produto) | 5+ | ✅ | ✅ | ✅ |
| Fase 1 P0 | 5 | ✅ | ✅ | ✅ |
| Fase 2 P1 | 5 | ✅ | ✅ | ✅ |
| Fase 3 P2 | 4 | ✅ | ✅ | ✅ |
| Fase 4 P3 | 1 | ✅ | ✅ | ✅ |

**Pendência operacional:** latência p95 em TOTVS dev; qualidade de resposta direct answer em alguns cenários (S9/S14) — evoluir no pipeline base, não no MFE.

`POST /data/sql` permanece **fallback** para exploração ad hoc quando a action REST não estiver habilitada no agente.

---

## 13. Próximas implementações (Playbook 16)

**Roadmap:** [`playbook-16-openapi-import-async-e-readiness-operacional.md`](./playbook-16-openapi-import-async-e-readiness-operacional.md)

| Tema | Problema | Entrega alvo |
|------|----------|--------------|
| Import async | «Atualizar rotas» bloqueia ~minutos (embedding síncrono × N actions) | Job `202` + progresso `done/total` |
| Readiness | Rota na api-delpi mas chat cai no LLM | 3 camadas: API → catálogo → agente enabled |
| UX operador | «Atualizando…» sem percentual | Barra por fase; reload após cadastro das rotas |
| Pipeline | Intent REST reconhecida, action ausente | Direct answer (JSON), não inferência silenciosa |

**Nota:** rotas Playbook 15 (ex.: `get_production_schedule_today`) usam `path_token` — **não** dependem de embedding para seleção. Habilitar a action no agente após reimport da fase 2 já desbloqueia S4.
