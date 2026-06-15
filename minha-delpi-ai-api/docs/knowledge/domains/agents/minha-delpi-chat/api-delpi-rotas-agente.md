# API DELPI — Guia de rotas para agentes operacionais

> **⚠ Cópia legada (167 linhas).** Fonte canônica para RAG e ingestão: [`api-delpi-rotas-agente.md`](../../../../api-delpi-rotas-agente.md) (428 linhas, inclui Playbook 15 operacional, comercial, financeiro, RH, qualidade).  
> Não indexar esta cópia sem sincronizar com o canônico — risco de agente cego para rotas `/production/consumption/*`, `/purchases/top-products`, etc.

**Uso:** anexar o **documento canônico** à base de conhecimento / RAG ou colar trechos no `system_prompt` de agentes que usam o provider OpenAPI `api-delpi`.

**Provider:** `api-delpi` · **Base:** `/apps/api-delpi` · **OpenAPI:** `/apps/api-delpi/openapi.json`

Após mudanças na API, **reimporte** o schema no agente e **reindexe** este documento se estiver na base de conhecimento.

---

## Regras gerais

1. Para dados operacionais (produto, estoque, LMP, SQL), use **`execute_external_action`** com a action correta — não invente valores.
2. O backend escolhe a action por `summary`, `description`, `path` e `operationId` do OpenAPI. Você deve alinhar a pergunta do usuário à rota certa.
3. Código de produto aceita máscara (`10.080.055` → enviar normalizado sem pontos na API).
4. Em follow-up (“estoque **desse** produto”, “mesma OV”), use o código ou número mencionado antes na conversa.
5. **Não confunda** estoque de um item com indicador agregado de estoque da empresa.

---

## Mapa rápido: intenção → rota

### Produtos (`/products`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Achar produto sem código exato | `GET /products/search` | `search_products` |
| Descrição, ficha, visão geral do item | `GET /products/{code}/analyser` | `get_product_analyser` |
| Saldo / estoque / disponível **de um código** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM / componentes | `GET /products/{code}/structure` | `get_product_structure` |
| Estrutura + MPs exclusivas | `GET /products/{code}/structure/exclusivity` | `get_product_structure_exclusivity` |
| Catálogo MPs exclusivas (global) | `GET /products/exclusive-raw-materials/catalog` | `list_exclusive_raw_materials_catalog` |
| Situação produtiva (PA/PI/OP) | `GET /products/{code}/production-status` | `get_product_production_status` |
| Expedição / inspeção final PA | `GET /products/{code}/shipping-status` | `get_product_shipping_status` |
| Status fabril completo | `GET /products/{code}/factory-status` | `get_product_factory_status` |
| Análise de preço MP (compra, ICMS, orçamento) | `GET /products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` |
| Última NF / fornecedor / ICMS (MP) | `GET /products/{code}/last-purchase` | `get_product_last_purchase` |
| Histórico preço compra + variação | `GET /products/{code}/purchase-price-history` | `get_product_purchase_price_history` |
| Histórico orçamento SC/PC | `GET /products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` |
| Pareto MPs / simulação reajuste (PA) | `GET /products/{code}/cost-impact-simulation` | `get_product_cost_impact_simulation` |
| Preço de **venda** (tabela comercial) | `GET /products/{code}/pricing` | `get_product_pricing` |
| Fornecedores do item | `GET /products/{code}/suppliers` | (ver catálogo) |
| Histórico de compras | `GET /products/{code}/purchases` | `purchases` |
| Vendas / carteira / faturamento | `GET /products/{code}/sales*` | (ver catálogo) |

**Parâmetros comuns**

- `search`: `code`, `description`, `group_code`, `page`, `page_size`
- `stock`: `code` (path), `branch`, `location`, `page`, `page_size`
- `analyser`: `code` (path)

**Exemplos de frases → rota**

- “Qual a descrição do produto 10.080.055?” → `get_product_analyser`
- “Tem estoque do 10080047 na filial 01?” → `get_product_stock`
- “Busca parafuso M8 na descrição” → `search_products`

---

### Engenharia — LMP (`/engineering`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Listar / filtrar LMPs ou amostras | `GET /engineering/lmps` | `list_lmps` |
| Painel / dashboard / resumo de LMPs | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| KPIs do painel | `GET /engineering/lmps/dashboard/summary` | `get_lmps_dashboard_summary` |
| Itens paginados do painel | `GET /engineering/lmps/dashboard/items` | `list_lmps_dashboard_items` |
| Gráficos do painel | `GET /engineering/lmps/dashboard/charts` | `get_lmps_dashboard_charts` |
| Detalhe de uma LMP por OV | `GET /engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` |

**Parâmetros úteis**

- `list_lmps` / dashboard: `date_start`, `date_end`, `branch`, `listing_type` (`LMP`, `Amostra`, `Outro`), `page`, `page_size`
- dashboard: `status` (ex.: `Todos`)
- detalhe: `sale_number` = número da ordem de venda (OV); opcional `date_start`, `date_end`, `branch` (escopo do dashboard/MFE)

**Exemplos**

- “Lista as LMPs da semana” → `list_lmps`
- “Dashboard de LMPs em aberto” → `list_lmps_dashboard`
- “Detalhe da LMP da OV 123456” → `get_lmp_by_sale_number` (não usar código de produto como OV)

**Atenção:** número de OV **não** é código de produto.

---

### Produção — indicadores (`/production`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| OTD produção (%) | `GET /production/on_time_delivery_pct` | `get_on_time_delivery_pct` |
| OTD produção — ordens no/atraso | `GET /production/otd` | `get_production_otd` |
| Série OTD produção | `GET /production/otd/series` | `get_production_otd_series` |
| OEE produção (%) | `GET /production/overall_equipment_effectiveness_pct` | `get_overall_equipment_effectiveness_pct` |
| OEE produção — apontamentos | `GET /production/oee` | `get_production_oee` |
| Detalhe apontamento OEE | `GET /production/oee/appointments/{appointment_id}` | `get_production_oee_appointment_by_id` |
| Série OEE produção | `GET /production/oee/series` | `get_production_oee_series` |

**`GET /production/otd`:** `branch`, `start_date`, `end_date`, `status` (`on_time` / `late`), `page`, `page_size`, `sort_by`, `sort_dir`. Resposta: `summary` + `orders` (SC2010).

**`GET /production/oee`:** `branch`, `start_date`, `end_date`, `status` (`valid` / `outlier`), `product_type` (`PA` / `PI`), `work_center`, `production_order`, `page`, `page_size`, `sort_by`, `sort_dir`. Resposta: `summary` + `appointments` (SH6010, `H6_ZEFICI`, `appointment_id`). Não confundir com `/production/eficiencia-fabril/*` (métrica MOD/view).

**`GET /production/oee/appointments/{appointment_id}`:** `appointment_id` (path), `branch` opcional. Resposta composta: `appointment`, `time_analysis` (previsto/real/eficiência, `findings`), `routing_operations` (SG2), `structure` (BOM em árvore). Usada pelo OEE e pela eficiência fabril.

**`GET /production/eficiencia-fabril/dashboard`:** `date_start`, `date_end`, `branch`, `op`, `employee`, `work_center`, `page`, `page_size`. Resposta: `summary` + `charts` + `items` com `appointment_id`.

**`GET /production/eficiencia-fabril/appointments`:** carga bulk do período (`list_eficiencia_fabril_appointments`).

---

### Suprimentos — indicadores (`/supplies`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| **Valor total** de estoque (KPI) | `GET /supplies/stock-value` | `get_supplies_stock_value` |
| Giro de estoque (IDD) | `GET /supplies/inventory-turnover` | `get_supplies_inventory_turnover` |
| CPV / OTD compras | `GET /supplies/cpv`, `GET /supplies/otd` | `get_supplies_cpv`, `get_supplies_otd` |
| Economia em negociações (IDD / planilha) | `GET /supplies/negotiation-savings/summary` | `get_supplies_negotiation_savings_summary` |

**Parâmetros (`/supplies/negotiation-savings/summary`)**

- `start_date`, `end_date` — período mensal (planilha `economia_negociacoes_compra`)
- `branch` — opcional (`01` / `02`); sem filial retorna `branches` com totais por unidade
- Sem linhas no período: `total_savings` vem `null` (não zero)

**Exemplos**

- “Qual o valor total de estoque da empresa?” → `get_supplies_stock_value` (**não** `/products/{code}/stock`)
- “Estoque do produto X” → `get_product_stock` (**não** `stock-value`)
- “Economia em negociações de compras em maio?” → `get_supplies_negotiation_savings_summary` com período
- “Economia de negociação da filial 01” → mesma action com `branch=01`

---

### Dados — SQL (`/data`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Executar SELECT / consulta analítica | `POST /data/sql` | `execute_readonly_sql` |

**Corpo da requisição**

- JSON: `{ "sql": "SELECT ..." }`
- ou `text/plain` com a query

Somente leitura (SELECT, CTE). Permissão: `api-delpi.data` ou `api-delpi.access.full`.

**Exemplos**

- “Roda esse SQL: SELECT TOP 10 ...” → `execute_readonly_sql` com campo `sql`

---

## Erros e respostas

| HTTP | Significado para o usuário |
|------|----------------------------|
| 200–299 | Sucesso — use `humanizedSummary` ou resposta direta do pipeline |
| 401 / 403 | Sem permissão para esta rota |
| 404 | Produto, OV ou recurso não encontrado |
| 422 | Parâmetro faltando ou inválido (código, datas, página) |

Não pergunte se o usuário “tem permissão”; a API já valida com o token dele.

---

## Vocabulário (sinônimos)

Inclua estes termos ao interpretar a pergunta:

| Domínio | Termos |
|---------|--------|
| Produto | produto, item, código, referência, ref, SKU, material, MP, insumo |
| Estoque item | estoque, saldo, disponível, quantidade, posição, armazém |
| LMP | LMP, lista de materiais de projeto, amostra, ordem de venda, OV |
| SQL | SQL, consulta, SELECT, query, dados |
| KPI estoque | valor total de estoque, valor em estoque, indicador suprimentos |

---

## Checklist do administrador

1. Provider `api-delpi` com `authMode: user_token` e `openApiUrl` apontando para o gateway.
2. Agente com `allowRead` e actions de leitura/SQL habilitadas.
3. Reimport OpenAPI após deploy da api-delpi.
4. Anexar **este documento** à base de conhecimento do agente (tags sugeridas: `api-delpi`, `operacional`, `rotas`) **ou** referenciar no `system_prompt`.
5. Testar: estoque de código, OV de LMP, valor total de estoque, SELECT simples.

---

## Referências técnicas

- OpenAPI enriquecido: `api-delpi/app/interface/http/openapi_agent_metadata.py`
- Documentação humana: `api-delpi/docs/api/11-guia-agente-chat.md`
- Actions no chat: `minha-delpi-ai-api/docs/api/04-actions-openapi.md`