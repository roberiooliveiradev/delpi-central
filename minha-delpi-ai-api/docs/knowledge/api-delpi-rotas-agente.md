# API DELPI — Guia de rotas para agentes operacionais

**Uso:** anexar este documento à inteligência do agente (base de conhecimento / RAG) ou colar trechos relevantes no `system_prompt` de agentes que usam o provider OpenAPI `api-delpi`.

**Provider:** `api-delpi` · **Base:** `/apps/api-delpi` · **OpenAPI:** `/apps/api-delpi/openapi.json`

Após mudanças na API, **reimporte** o schema no agente e **reindexe** este documento se estiver na base de conhecimento.

---

## Regras gerais

1. Para dados operacionais (produto, estoque, LMP, SQL), use **`execute_external_action`** com a action correta — não invente valores.
2. O backend escolhe a action por `summary`, `description`, `path` e `operationId` do OpenAPI. Você deve alinhar a pergunta do usuário à rota certa.
3. Código de produto aceita máscara (`10.080.055` → enviar normalizado sem pontos na API).
4. Em follow-up ("estoque **desse** produto", "mesma OV"), use o código ou número mencionado antes na conversa.
5. **Não confunda** estoque de um item com indicador agregado de estoque da empresa.

---

## Mapa rápido: intenção → rota

### Produtos (`/products`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Achar produto sem código exato | `GET /products/search` | `search_products` |
| Dados cadastrais (descrição, tipo, unidade) | `GET /products/{code}` | `get_product_detail` |
| Resumo completo (cadastro + estoque + preços) | `GET /products/{code}/summary` | `get_product_summary` |
| Análise completa / ficha detalhada | `GET /products/{code}/analyser` | `get_product_analyser` |
| Saldo / estoque / disponível **de um código** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM / componentes | `GET /products/{code}/structure` | `get_product_structure` |
| **Onde é usado / produto pai / where used** | `GET /products/{code}/parents` | `get_product_parents` |
| Preço / tabela de preço / quanto custa | `GET /products/{code}/pricing` | `get_product_pricing` |
| Fornecedores do item | `GET /products/{code}/suppliers` | `get_product_suppliers` |
| Clientes do item | `GET /products/{code}/customers` | `get_product_customers` |
| Histórico de compras | `GET /products/{code}/purchases` | `get_product_purchases` |
| Resumo de vendas do item | `GET /products/{code}/sales` | `get_product_sales_summary` |
| Carteira / pedidos em aberto do item | `GET /products/{code}/sales/open-orders` | `get_product_sales_open_orders` |
| Faturamento do item | `GET /products/{code}/sales/billing` | `get_product_sales_billing` |
| Roteiro de fabricação | `GET /products/{code}/guide` | `get_product_guide` |
| Inspeção / qualidade | `GET /products/{code}/inspection` | `get_product_inspection` |
| Movimentações internas | `GET /products/{code}/internal-movements` | `get_product_internal_movements` |
| Notas de entrada | `GET /products/{code}/inbound-invoice-items` | `get_product_inbound_invoices` |
| Notas de saída | `GET /products/{code}/outbound-invoice-items` | `get_product_outbound_invoices` |

**Parâmetros comuns**

- `search`: `code`, `description`, `group_code`, `page`, `page_size`
- `stock`: `code` (path), `branch`, `location`, `page`, `page_size`
- `structure` / `parents`: `code` (path), `page_size` (até 200), `max_depth` (até 99)
- `analyser`: `code` (path)

**Exemplos de frases → rota**

- "Qual a descrição do produto 10.080.055?" → `get_product_detail`
- "O que é o produto 10080001?" → `get_product_detail`
- "Me fale sobre o 10080001" → `get_product_detail`
- "Detalhes do produto 90260147" → `get_product_detail`
- "Tem estoque do 10080047 na filial 01?" → `get_product_stock`
- "Busca parafuso M8 na descrição" → `search_products`
- "Qual a estrutura do 10080001?" → `get_product_structure`
- "Onde é usado o 10080001?" → `get_product_parents`
- "Pai do 10080001" → `get_product_parents`
- "Quais produtos usam o 10080001?" → `get_product_parents`
- "Quanto custa o 10080001?" → `get_product_pricing`
- "Notas de entrada do 10080001" → `get_product_inbound_invoices`
- "Notas de saída do 10080001" → `get_product_outbound_invoices`
- "Fornecedores do produto 10080001" → `get_product_suppliers`
- "Roteiro do 10080001" → `get_product_guide`
- "Movimentações internas do 10080001" → `get_product_internal_movements`

---

### Engenharia — LMP (`/engineering`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Listar / filtrar LMPs ou amostras | `GET /engineering/lmps` | `list_lmps` |
| Painel / dashboard / resumo de LMPs | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| Detalhe de uma LMP por OV | `GET /engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` |

**Parâmetros úteis**

- `list_lmps` / dashboard: `date_start`, `date_end`, `branch`, `listing_type` (`LMP`, `Amostra`, `Outro`), `page`, `page_size`
- dashboard: `status` (ex.: `Todos`)
- detalhe: `sale_number` = número da ordem de venda (OV)

**Exemplos**

- "Lista as LMPs da semana" → `list_lmps`
- "Dashboard de LMPs em aberto" → `list_lmps_dashboard`
- "Detalhe da LMP da OV 123456" → `get_lmp_by_sale_number` (não usar código de produto como OV)

**Atenção:** número de OV **não** é código de produto.

---

### Suprimentos — indicadores (`/supplies`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| **Valor total** de estoque (KPI) | `GET /supplies/stock-value` | `get_supplies_stock_value` |
| Giro de estoque (IDD) | `GET /supplies/inventory-turnover` | `get_supplies_inventory_turnover` |
| CPV (custo produção vendido) | `GET /supplies/cpv` | `get_supplies_cpv` |
| OTD (entrega no prazo compras) | `GET /supplies/otd` | `get_supplies_otd` |

**Exemplos**

- "Qual o valor total de estoque da empresa?" → `get_supplies_stock_value` (**não** `/products/{code}/stock`)
- "Estoque do produto X" → `get_product_stock` (**não** `stock-value`)
- "Qual o CPV?" → `get_supplies_cpv`
- "Giro de estoque" → `get_supplies_inventory_turnover`

---

### Vendas — ordens (`/sales`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Listar ordens de venda no período | `GET /sales/` | `list_sale_orders` |

**Exemplos**

- "Listar ordens de venda" → `list_sale_orders`
- "Pedidos de venda abertos" → `list_sale_orders`

Não confundir com detalhe de LMP (`/engineering/lmps/{sale_number}`) nem vendas de um produto (`/products/{code}/sales`).

---

### Comercial — indicadores (`/commercial`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Taxa de conversão de vendas | `GET /commercial/closing-rate` | `get_sales_conversion_rate` |
| Receita operacional líquida (ROL) série | `GET /commercial/rol/series` | `get_commercial_rol_series` |
| OTD de pedidos de venda | `GET /commercial/sales-order-otd` | `get_sales_order_otd` |
| Novos clientes | `GET /commercial/new-clients-average` | `get_new_clients_average` |

---

### Financeiro (`/financial`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| EBITDA % | `GET /financial/ebitda_pct` | `get_ebitda_pct` |
| Custo fixo % | `GET /financial/fixed_cost_pct` | `get_fixed_cost_pct` |
| PMR (prazo médio recebimento) | `GET /financial/pmr` | `get_pmr` |
| ROL | `GET /financial/rol` | `get_rol` |

---

### Produção (`/production`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| OTD produção | `GET /production/on_time_delivery_pct` | `get_on_time_delivery_pct` |
| OEE (eficiência equipamentos) | `GET /production/overall_equipment_effectiveness_pct` | `get_oee_pct` |
| Custo direto mão de obra | `GET /production/direct_labor_cost_pct` | `get_direct_labor_cost_pct` |
| Custo de produção | `GET /production/production_cost_pct` | `get_production_cost_pct` |

---

### RH (`/hr`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Snapshot RH (headcount, turnover) | `GET /hr/snapshot` | `get_hr_snapshot` |
| PDIs ativos | `GET /hr/active-pdi-count` | `get_hr_active_pdi_count` |
| Avaliações desempenho | `GET /hr/performance-reviews-completion` | `get_hr_performance_reviews_completion` |

---

### Qualidade (`/quality`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Não conformidades | `GET /quality/nonconformities` | `list_nonconformities` |
| PPM interno | `GET /quality/ppm/internal` | `list_internal_ppm` |
| PPM externo | `GET /quality/ppm/external` | `list_external_ppm` |
| Auditoria 5S | `GET /quality/audit-5s/summary` | `get_audit_5s_summary` |
| Kaizens | `GET /quality/kaizens/summary` | `get_kaizen_summary` |

---

### Dados — SQL (`/data`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Executar SELECT / consulta analítica | `POST /data/sql` | `execute_readonly_sql` |

**Corpo da requisição**

- JSON: `{ "sql": "SELECT ..." }`
- ou `text/plain` com a query

Somente leitura (SELECT, CTE). Permissão: `api-delpi.data` ou `api-delpi.access.full`.

---

### Sistema — metadados (`/system`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Buscar tabelas por descrição | `GET /system/tables/search` | `search_tables` |
| Buscar colunas por descrição | `GET /system/columns/search` | `search_columns` |
| Schema completo de tabela | `GET /system/tables/{tableName}/schema` | `get_table_schema` |

---

## Erros e respostas

| HTTP | Significado para o usuário |
|------|----------------------------|
| 200-299 | Sucesso — use `humanizedSummary` ou resposta direta do pipeline |
| 401 / 403 | Sem permissão para esta rota |
| 404 | Produto, OV ou recurso não encontrado |
| 422 | Parâmetro faltando ou inválido (código, datas, página) |

Não pergunte se o usuário "tem permissão"; a API já valida com o token dele.

---

## Vocabulário (sinônimos)

Inclua estes termos ao interpretar a pergunta:

| Domínio | Termos |
|---------|--------|
| Produto | produto, item, código, referência, ref, SKU, material, MP, insumo |
| Estoque item | estoque, saldo, disponível, quantidade, posição, armazém |
| Estrutura/BOM | estrutura, componentes, composição, bill of materials, BOM |
| Onde é usado | onde é usado, produto pai, parent, where used, utilizado em, faz parte de, pai do |
| Preço | preço, pricing, tabela de preço, quanto custa, custo |
| Notas | nota de entrada, nota de saída, NF-e, invoice, inbound, outbound |
| LMP | LMP, lista de materiais de projeto, amostra, ordem de venda, OV |
| OV | ordens de venda, pedidos de venda, OV |
| SQL | SQL, consulta, SELECT, query, dados |
| KPI estoque | valor total de estoque, valor em estoque, indicador suprimentos |
| KPI comercial | closing rate, ROL, OTD, novos clientes |
| KPI financeiro | EBITDA, PMR, custo fixo, ROL |
| KPI produção | OTD produção, OEE, custo de produção, mão de obra |

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
