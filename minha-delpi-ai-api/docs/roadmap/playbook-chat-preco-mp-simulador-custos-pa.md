# Playbook — Integração no chat: preço de MP e simulador de impacto de custos PA

**Destinatário:** agente que manipula a API do chat (`minha-delpi-ai-api`).  
**Pré-requisito:** rotas já implementadas e validadas na **api-delpi** (commit `6374806d`).  
**Escopo deste playbook:** roteamento, parâmetros, apresentação e testes no **chat base** — **não** alterar lógica na api-delpi.

Documentação de referência cruzada:

- Playbook API preço MP: `api-delpi/docs/roadmaps/playbook-analise-preco-materia-prima.md`
- Playbook API simulador PA: `api-delpi/docs/roadmaps/playbook-simulador-impacto-custos-pa.md`
- Modelo fabril (jun/2026): `docs/changelog/2026-06-playbook-rotas-sessao-ativa-parametros.md`
- Arquitetura chat base: `docs/architecture/chat-intelligence-base.md`
- Vocabulário centralizado: `docs/architecture/vocabulary-centralization-jun2026.md`
- Regras workspace: `.cursor/rules/chat-intelligence-base.mdc`, `centralized-rules-first.mdc`, `assistant-content-json.mdc`

Knowledge RAG (agente):

- `docs/knowledge/domains/agents/minha-delpi-chat/sql-playbook-preco-materia-prima.txt`
- `docs/knowledge/domains/agents/minha-delpi-chat/sql-playbook-simulador-impacto-custos-pa.txt`

---

## 1. Objetivo

Conectar ao pipeline do chat as rotas de playbook recém-criadas na api-delpi, no **mesmo padrão** de `factory-status`, `production-status`, `shipping-status` e `structure/exclusivity`:

1. **Análise inteligente de preço de matéria-prima** — último fornecedor, última compra, ICMS, histórico de orçamento, variação de preço.
2. **Simulador de impacto de custos do PA** — ranking Pareto das MPs na BOM + simulação percentual de reajuste.

Resultado esperado: pergunta operacional → `execute_external_action` → resposta rápida (~0,1–0,4s) com apresentação rica, **sem** improvisação do LLM.

---

## 2. Rotas disponíveis na api-delpi

| Método | Path | operationId | shape | Quando preferir no chat |
|--------|------|-------------|-------|-------------------------|
| GET | `/products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` | `composite_analysis` | Análise **completa** de preço de MP |
| GET | `/products/{code}/last-purchase` | `get_product_last_purchase` | `playbook_report` | Só última NF + fornecedor + ICMS |
| GET | `/products/{code}/purchase-price-history` | `get_product_purchase_price_history` | `playbook_report` | Histórico + variação % |
| GET | `/products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` | `playbook_report` | SC1010 + SC7010 |
| GET | `/products/{code}/cost-impact-simulation` | `get_product_cost_impact_simulation` | `composite_analysis` | Pareto MPs no **PA** + simulação |

### Query params

**Preço MP** (`raw-material-price-intelligence`, históricos, last-purchase):

| Param | Obrigatório | Default API | Notas chat |
|-------|-------------|-------------|------------|
| `code` | sim (path) | — | MP esperada; API avisa se não for MP |
| `date_start`, `date_end` | não | últimos 12 meses | **Não** exigir `missing_date` por default |
| `branch` | não | todas | 2 chars |
| `history_limit` | não | 24 | máx. 200 |

**Simulador PA** (`cost-impact-simulation`):

| Param | Default | Notas |
|-------|---------|-------|
| `price_source` | `standard_cost` | ou `last_purchase` |
| `adjustment_percent` | 0 | ex.: 10 = +10% |
| `top_n` | todas | limitar ranking |
| `max_depth` | 50 | profundidade BOM |

**Restrição:** simulador só aceita **PA** (400 se MP).

### Produtos de teste homologados

- MP: `10080001` (TE Connectivity, NF, ICMS, orçamento)
- PA: `90261255` (BOM multinível, ranking de custo)

---

## 3. Regra-mãe do chat base

```text
Mensagem → vocabulário (JSON) → intent → seleção de rota → parâmetros → execute_external_action → presenter
```

**Proibido:**

- Lógica de roteamento só no prompt do agente
- `if` duplicado em `SendChatMessageUseCase` / `StreamChatMessageUseCase`
- Strings PT em Python (usar `assistant/*.json`)
- Bypass do pipeline em simulate/preview sem histórico quando importa

**Obrigatório:** estender módulos canônicos listados na seção 5.

---

## 4. Desambiguação (crítico)

| Usuário pede | NÃO usar | Usar |
|--------------|----------|------|
| Preço de **compra**, NF, fornecedor, ICMS | `/pricing` (venda DA1010) | `raw-material-price-intelligence` ou `last-purchase` |
| Histórico de **orçamento** / cotação / SC / PC | `/purchases` (lista PC) | `purchase-budget-history` ou intelligence |
| **Variação** de preço entre compras | SQL ad hoc | `purchase-price-history` ou intelligence |
| Materiais que **impactam custo do PA** | `/structure` (BOM sem custo) | `cost-impact-simulation` |
| Análise completa de MP | várias rotas | **`raw-material-price-intelligence`** |
| Simular +10% nos materiais | — | `cost-impact-simulation?adjustment_percent=10` |
| Fornecedores cadastrados / lead time | — | `/suppliers` (já existe; não substituir intelligence) |

---

## 5. Mapa de arquivos — o que procurar e estender

### 5.1 OpenAPI e catálogo (passo 0)

| Arquivo | Ação |
|---------|------|
| `scripts/sync_api_delpi_openapi.py` | Rodar após deploy api-delpi |
| `api-delpi/docs/api/12-procedimento-reimport-openapi.md` | Procedimento |
| `docs/knowledge/api-delpi-rotas-agente.md` | Adicionar tabela das 5 rotas + frases exemplo |
| `docs/architecture/presentation-coverage-baseline.json` | Incluir operationIds |
| `api-delpi/app/content/openapi_baseline.json` | Verificar se sync atualiza |

Validar: cada action com `operationId` **idêntico** ao da api-delpi.

---

### 5.2 Vocabulário e intenção

| Arquivo | Padrão a espelhar | O que adicionar |
|---------|-------------------|-----------------|
| `app/content/pt-BR/assistant/product_query_intent.json` | `factoryStatus`, `productionStatus` | Seções: `rawMaterialPriceIntelligence`, `costImpactSimulation`; opcional: `lastPurchase`, `purchasePriceHistory`, `purchaseBudgetHistory` |
| `app/domain/services/chat_product_query_intent_service.py` | `_looks_like_factory_status_question` | `_looks_like_raw_material_price_question`, `_looks_like_cost_impact_question`, etc. |
| `app/application/services/external_actions/external_action_product_route_selection_service.py` | `_rank_product_actions` (~L186) | Flags + match path: `raw-material-price-intelligence`, `cost-impact-simulation`, `last-purchase`, … |
| `app/domain/services/chat_analysis_intent_service.py` | menções a factory | Avaliar se precisa hook para análise de preço |
| `app/content/pt-BR/assistant/external_action_responses.json` | `selectionReasons`, `actionSelection.productRouteRanking` | Reasons novos (**JSON**, não Python) |

**Termos sugeridos** (`product_query_intent.json`):

`rawMaterialPriceIntelligence`:

- análise de preço da matéria-prima, preço de compra, último fornecedor, última compra, icms compra, variação de preço, histórico de orçamento, cotação fornecedor, raw-material-price-intelligence

`costImpactSimulation`:

- impacto de custo, materiais que mais impactam, pareto matéria-prima, simular aumento, reajuste percentual, cost-impact-simulation, ranking custo mp

**Excludes:** termos de venda (`preço de venda`, `tabela comercial`) → não acionar intelligence; termos fabril puro → não confundir com cost-impact.

---

### 5.3 Parâmetros operacionais e sessão

| Arquivo | Padrão fabril | Comportamento destas rotas |
|---------|---------------|----------------------------|
| `ChatOperationalParameterService` | `missing_product_code` | Código obrigatório se ausente |
| `ChatOperationalDateParameterService` | data obrigatória em factory-status | **Preço MP:** data opcional (API default 12 meses); merge se usuário disser «últimos 6 meses» |
| `app/content/pt-BR/assistant/operational_parameters.json` | `missingDateByContext.factory_status` | Textos para código; data só se contexto pedir período |
| `ChatActiveQuerySessionService` | `routeSegment` factory-status | Segmentos: `raw-material-price-intelligence`, `cost-impact-simulation` |
| `ChatActivePendingService` | `resumeMessage` | Herdar intent ao enviar só código depois |

**Não** aplicar `missing_date` silencioso em intelligence — diferente de factory/production/shipping.

---

### 5.4 Apresentação rica

Espelhar cadeia do **factory-status**:

| Camada | Arquivo (referência fabril) | Ação |
|--------|----------------------------|------|
| Perfis | `app/content/pt-BR/assistant/presentation_profiles.json` | `entity` → profile; `pathContains` para novos paths; `stackPlan` |
| Profile map | `chat_api_delpi_response_profile_service.py` | Tuplas `("/factory-status", "product_factory_status")` → adicionar 5 rotas |
| Policy | `chat_presentation_route_policy_service.py` | `is_factory_status_route` → `is_raw_material_price_route`, `is_cost_impact_route` |
| Coverage | `chat_presentation_coverage_service.py` | Paths na lista playbook |
| Composto | `presenters/product_composite_analysis_presenter.py` | Factory hoje; estender ou criar presenter dedicado |
| Granular | `product_production_status_presenter.py`, `product_structure_exclusivity_presenter.py` | Modelo para last-purchase / price-history |
| Orquestrador | `external_action_result_presenter.py` | `_present_product_*`, `build_*_table_presentations` |
| Use case | `execute_external_action_use_case.py` (~L337) | `elif "/factory-status"` → branches novos |
| Texto | `presenters/text_presentation_presenter.py` | Dispatch por path |
| Conteúdo | `presenter_content.json` | Títulos, narrativas (ver `factoryStatus`) |
| Colunas | `column_labels.json` | `variation_percent`, `icms_rate`, `impact_on_material_cost_percent`, `price_status`, … |
| Schema | `chat_schema_driven_presentation_service.py` | Chaves de seção |
| Stack | `chat_presentation_stack_order_service.py`, `chat_presentation_section_availability_service.py` | Ordem seções intelligence / cost-impact |

**Payloads para desenhar UI:**

`raw-material-price-intelligence`:

```json
{
  "product": {},
  "last_purchase": {},
  "budget_history": { "items": [], "summary": {} },
  "price_history": { "items": [], "summary": {} },
  "price_variation": {},
  "price_status": "ESTAVEL | ALTA DE PRECO | QUEDA DE PRECO | SEM HISTORICO DE COMPRA",
  "indicators": {}
}
```

`cost-impact-simulation`:

```json
{
  "product": {},
  "materials": { "items": [{ "rank", "impact_on_material_cost_percent", "extended_cost" }] },
  "summary": {},
  "simulation": { "adjustment_percent", "projected_cost_delta" }
}
```

---

### 5.5 Testes e smoke

| Tipo | Arquivo |
|------|---------|
| Regressão intent/seleção | `tests/fixtures/chat_intelligence_regression_cases.py` |
| Parâmetros data | `tests/unit/domain/services/test_chat_operational_date_parameter_service.py` |
| Sessão ativa | `tests/unit/domain/services/test_chat_active_query_session_service.py` |
| Presenter | `tests/unit/domain/services/test_external_action_result_presenter_*.py` |
| Vocabulário | `tests/unit/domain/services/test_*_vocabulary_content.py` (se novos bundles) |
| Smoke E2E | `scripts/smoke_playbook_product_routes.py` |
| Fixtures | `tests/fixtures/api_delpi_responses/product_*_10080001.json`, `*_90261255.json` |

**Frases smoke:**

1. «Análise de preço da matéria-prima 10080001»
2. «Última compra e ICMS do 10080001»
3. «Histórico de orçamento de compra do 10080001»
4. «Quais materiais mais impactam o custo do PA 90261255?»
5. «Simule aumento de 10% nos materiais do produto 90261255»

Critério: `execute_external_action` + presenter; latência ~0,1–0,4s.

---

## 6. Ordem de implementação sugerida

1. [x] Sync OpenAPI + `api-delpi-rotas-agente.md` + `presentation-coverage-baseline.json` *(OpenAPI sync requer FastAPI no container)*
2. [x] `product_query_intent.json` + `ChatProductQueryIntentService`
3. [x] `ExternalActionProductRouteSelectionService` + desambiguação vs `/pricing`, `/purchases`, `/structure`
4. [x] Parâmetros: código produto; data opcional; `activeQuery` / segmentos
5. [x] `presentation_profiles.json` + presenter mínimo (tabelas)
6. [x] `presenter_content.json` + `column_labels.json`
7. [x] Testes regressão + smoke *(smoke E2E requer gateway; script estendido com 10080001/90261255)*
8. [ ] (Fase 2) Narrativa humanizada / insights — opcional

---

## 7. Checklist de aceite

- [x] Pergunta «análise de preço MP {code}» chama `get_product_raw_material_price_intelligence` sem LLM synthesis
- [x] «Último fornecedor {code}» → `get_product_last_purchase` ou intelligence (preferência: intelligence quando ICMS/fornecedor composto)
- [x] «Materiais que impactam custo PA {code}» → `get_product_cost_impact_simulation`
- [x] «Preço de venda» **não** aciona rotas de compra
- [x] `/purchases` **não** substitui histórico de orçamento quando usuário pede SC/PC/cotação
- [x] Simulador com PA inválido: erro amigável (400 API)
- [x] Continuação de sessão: segundo código herda mesmo subIntent
- [x] Textos UI vêm de JSON; `meta.operationId` bate com OpenAPI
- [x] Smoke script inclui cenários MP/PA 10080001 e 90261255 *(execução E2E manual/homologação)*

---

## 8. O que NÃO fazer

- Usar `/pricing` para preço de compra de MP
- Duplicar cálculo de `variation_percent` no chat (já vem da API)
- Exigir data em intelligence quando API defaulta 12 meses
- Chamar cost-impact para MP (API retorna 400)
- Hardcodar `reason`, activity SSE ou labels de tabela em Python
- Patch local em componente MFE fora de `assistantProseRendering.ts` / pipeline base

---

## 9. Referência rápida — pipeline fabril (modelo)

Ver `docs/changelog/2026-06-playbook-rotas-sessao-ativa-parametros.md`:

| Playbook | Rota | Presenter |
|----------|------|-----------|
| Status fabril | `/factory-status` | `product_composite_analysis` |
| Situação produtiva | `/production-status` | `product_production_status` |
| Expedição | `/shipping-status` | `product_shipping_status` |
| Exclusividade MP | `/structure/exclusivity` | `product_structure_exclusivity` |

**Novos (este playbook):**

| Playbook | Rota composta | Presenter sugerido |
|----------|---------------|-------------------|
| Preço MP | `/raw-material-price-intelligence` | `product_raw_material_price_intelligence` (novo ou estender composite) |
| Impacto custo PA | `/cost-impact-simulation` | `product_cost_impact_simulation` (novo ou estender composite) |

---

## 10. Comandos úteis

```bash
# Sync OpenAPI (container chat)
cd minha-delpi-ai-api && PYTHONPATH=/app python scripts/sync_api_delpi_openapi.py

# Unitários chat (ajustar paths após implementar)
cd minha-delpi-ai-api && .venv/bin/pytest \
  tests/fixtures/chat_intelligence_regression_cases.py \
  tests/unit/domain/services/test_chat_active_query_session_service.py -q

# Smoke E2E (estender script)
docker exec -e PYTHONPATH=/app -e SMOKE_BASE_URL=http://delpi-gateway \
  delpi-minha-delpi-ai-api python scripts/smoke_playbook_product_routes.py

# Validar rota api-delpi direto
curl -s "http://localhost/apps/api-delpi/products/10080001/raw-material-price-intelligence?history_limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 11. Resumo executivo

As rotas de playbook já existem na api-delpi. O trabalho no chat é **conectar o pipeline base** (intent → seleção → parâmetros → action → presenter) copiando o padrão de `factory-status`, com atenção especial à **desambiguação** compra vs venda e à **opcionalidade de data** nas rotas de preço MP. Vocabulário e textos ficam em JSON; testes de regressão e smoke são obrigatórios antes de merge.
