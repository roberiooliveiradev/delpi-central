# API DELPI — Guia de rotas para agentes operacionais

**Uso:** anexar este documento à inteligência do agente (base de conhecimento / RAG) ou colar trechos relevantes no `system_prompt` de agentes que usam o provider OpenAPI `api-delpi`.

**Provider:** `api-delpi` · **Base no gateway:** `/apps/api-delpi` · **OpenAPI:** `/apps/api-delpi/openapi.json`

**Última revisão:** alinhada às rotas da `api-delpi` em maio/2026 (engenharia LMP em fases, comercial ampliado, qualidade PPM em `/summary`, financeiro em `/financial` e legado `/finacial`).

Após mudanças na API, **reimporte** o schema no agente e **reindexe** este documento se estiver na base de conhecimento.

---

## Regras gerais

1. Para dados operacionais (produto, estoque, LMP, KPIs, SQL), use **`execute_external_action`** com a action correta — não invente valores.
2. O backend escolhe a action por `summary`, `description`, `path` e `operationId` do OpenAPI. Priorize o **path** e o **summary** em português; alguns `operationId` são longos (gerados automaticamente pelo FastAPI).
3. Código de produto aceita máscara (`10.080.055` → enviar normalizado sem pontos na API).
4. Em follow-up ("estoque **desse** produto", "mesma OV"), use o código ou número mencionado antes na conversa.
5. **Não confunda** estoque de um item com indicador agregado de estoque da empresa.
6. Rotas de **dashboard** (LMP, comercial, RH, produção, qualidade) exigem permissões de dashboard ou `api-delpi.access` conforme a rota — o token do usuário precisa estar autorizado.

---

## Permissões (resumo)

| Domínio | Permissões típicas |
|---------|-------------------|
| Produtos, vendas, suprimentos, SQL, sistema | `api-delpi.access` |
| Financeiro | `api-delpi.access` |
| Engenharia (LMP, Transforma Mais) | `api-delpi.access` ou `dashboard-engineering.view` ou `dashboard-lmps.view` |
| Comercial (KPIs) | `api-delpi.access` ou `dashboard-commercial.view` |
| Produção (KPIs) | `api-delpi.access` ou `dashboard-production.view` |
| RH | `api-delpi.access` ou `dashboard-hr.view` |
| Qualidade (métricas TOTVS) | `api-delpi.quality.access` ou `dashboard-quality.view` |
| SQL | `api-delpi.data` ou `api-delpi.access.full` |
| Metadados sistema (tabelas/colunas) | `api-delpi.access.full` ou `api-delpi.system` |

---

## Mapa rápido: intenção → rota

### Produtos (`/products`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Achar produto sem código exato | `GET /products/search` | `search_products` |
| Dados cadastrais (descrição, tipo, unidade) | `GET /products/{code}` | `get_product_detail` |
| Resumo completo (cadastro + estoque + preços) | `GET /products/{code}/summary` | `get_product_summary` |
| Análise completa / ficha detalhada | `GET /products/{code}/analyser` | `get_product_analyser` |
| Saldo / estoque / disponível **de um código** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM / componentes | `GET /products/{code}/structure` | `get_product_structure` |
| Exportar estrutura em Excel | `GET /products/{code}/structure/excel` | (download; preferir JSON no chat) |
| **Onde é usado / produto pai / where used** | `GET /products/{code}/parents` | path contém `parents` |
| Preço / tabela de preço / quanto custa | `GET /products/{code}/pricing` | path contém `pricing` |
| Fornecedores do item | `GET /products/{code}/suppliers` | path contém `suppliers` |
| Clientes do item | `GET /products/{code}/customers` | path contém `customers` |
| Histórico de compras | `GET /products/{code}/purchases` | `get_product_purchases` |
| Resumo de vendas do item | `GET /products/{code}/sales` | `get_product_sales_summary` |
| Carteira / pedidos em aberto do item | `GET /products/{code}/sales/open-orders` | `get_product_sales_open_orders` |
| Faturamento do item | `GET /products/{code}/sales/billing` | path contém `sales/billing` |
| Roteiro de fabricação | `GET /products/{code}/guide` | path contém `guide` |
| Inspeção / qualidade do item | `GET /products/{code}/inspection` | path contém `inspection` |
| Movimentações internas | `GET /products/{code}/internal-movements` | path contém `internal-movements` |
| Notas de entrada | `GET /products/{code}/inbound-invoice-items` | path contém `inbound-invoice` |
| Notas de saída | `GET /products/{code}/outbound-invoice-items` | path contém `outbound-invoice` |

**Parâmetros comuns**

- `search`: `code`, `description`, `group_code`, `page`, `page_size`, `sort`, `direction`
- `stock`: `code` (path), `branch`, `location`, `page`, `page_size`
- `structure` / `parents`: `code` (path), `page`, `page_size`, `max_depth` (até 99)
- `analyser`, `summary`, `pricing`: `code` (path)

**Exemplos de frases → rota**

- "Qual a descrição do produto 10.080.055?" → `GET /products/{code}`
- "Resumo do produto 10080001" → `GET /products/{code}/summary`
- "Tem estoque do 10080047 na filial 01?" → `GET /products/{code}/stock`
- "Busca parafuso M8 na descrição" → `GET /products/search`
- "Onde é usado o 10080001?" → `GET /products/{code}/parents`
- "Quanto custa o 10080001?" → `GET /products/{code}/pricing`

---

### Engenharia — LMP (`/engineering`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Listar / filtrar LMPs ou amostras | `GET /engineering/lmps` | `list_lmps` |
| Dashboard completo (legado / tabela) | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| **Só KPIs** do dashboard LMP | `GET /engineering/lmps/dashboard/summary` | path `dashboard/summary` |
| **Itens paginados** do dashboard | `GET /engineering/lmps/dashboard/items` | path `dashboard/items` |
| **Gráficos** do dashboard LMP | `GET /engineering/lmps/dashboard/charts` | path `dashboard/charts` |
| Detalhe de uma LMP por OV | `GET /engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` |
| Listar processos Transforma Mais | `GET /engineering/transforma-mais/processes` | path `transforma-mais/processes` |
| Resumo Transforma Mais | `GET /engineering/transforma-mais/processes/summary` | path `processes/summary` |

**Parâmetros úteis**

- Listagem / dashboard: `date_start`, `date_end`, `branch`, `listing_type` (`LMP`, `Amostra`, `Outro`), `status` (ex.: `Todos`), `page`, `page_size` (itens)
- Detalhe: `sale_number` = número da **ordem de venda (OV)** — não é código de produto
- Transforma Mais: `id`, `name_process`, `filial_id`, `sector_name`, `status`, `start_date`, `end_date`

**Exemplos**

- "Lista as LMPs da semana" → `GET /engineering/lmps`
- "KPIs do painel de LMP" → `GET /engineering/lmps/dashboard/summary`
- "Detalhe da LMP da OV 123456" → `GET /engineering/lmps/{sale_number}`
- "Processos do Transforma Mais" → `GET /engineering/transforma-mais/processes`

**Atenção:** número de OV **não** é código de produto. Para dashboard LMP no chat, prefira `list_lmps` ou detalhe por OV; rotas `/dashboard/*` são otimizadas para o MFE de engenharia.

---

### Suprimentos — indicadores (`/supplies`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| **Valor total** de estoque (KPI) | `GET /supplies/stock-value` | `get_supplies_stock_value` |
| Giro de estoque (IDD) | `GET /supplies/inventory-turnover` | `get_supplies_inventory_turnover` |
| CPV (custo produção vendido) | `GET /supplies/cpv` | `get_supplies_cpv` |
| OTD (entrega no prazo compras) | `GET /supplies/otd` | `get_supplies_otd` |

**Parâmetros importantes (`/supplies/stock-value`)**

- **Sem** `start_date`/`end_date`: saldo atual (SB2010).
- **Com** `start_date` e `end_date`: estimativa histórica (SB9010 + SD3010); retorna bloco `estimation` quando aplicável.
- `location` filtra no modo histórico.
- `top_limit` para ranking de locais.

**Parâmetros (`/supplies/inventory-turnover`)**

- `branch`, `location`, `start_date`, `end_date`, `strict_idd_period` (bool)
- Estoque do IDD usa a mesma lógica de valor de estoque (atual vs histórico).

**Exemplos**

- "Qual o valor total de estoque da empresa?" → `GET /supplies/stock-value` (**não** `/products/{code}/stock`)
- "Estoque do produto X" → `GET /products/{code}/stock` (**não** `stock-value`)
- "Giro de estoque em 2024" → `GET /supplies/inventory-turnover` com período
- "Qual o CPV?" → `GET /supplies/cpv`

Detalhes do cálculo histórico: `api-delpi/docs/api/supplies-estoque-historico.md`.

---

### Vendas — ordens (`/sales`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Listar ordens de venda no período | `GET /sales/` | `list_sale_orders` |

**Parâmetros:** `date_start`, `date_end`, `page`, `page_size`

Não confundir com detalhe de LMP (`/engineering/lmps/{sale_number}`) nem vendas de um produto (`/products/{code}/sales`).

---

### Comercial — indicadores (`/commercial`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Taxa de conversão de vendas | `GET /commercial/closing-rate` | `get_sales_conversion_rate` |
| ROL — série temporal | `GET /commercial/rol/series` | `get_commercial_rol_series` |
| OTD de pedidos de venda | `GET /commercial/sales-order-otd` | `get_sales_order_otd` |
| Média de novos clientes | `GET /commercial/new-clients-average` | `get_new_clients_average` |
| % ROL de clientes novos | `GET /commercial/new-clients-rol-pct` | `get_new_clients_rol_pct` |
| % ROL de novos negócios | `GET /commercial/new-business-rol-pct` | `get_new_business_rol_pct` |
| Meta % ROL matriz | `GET /commercial/head_office_rol_target_pct` | path `head_office_rol` |
| Meta % ROL filial | `GET /commercial/branch_rol_target_pct` | path `branch_rol_target` |

**Parâmetros comuns:** `branch` (2 chars quando aplicável), `start_date`, `end_date`; `rol/series` exige `granularity` (`day`, `week`, `month`, `year`).

---

### Financeiro (`/financial` e legado `/finacial`)

O router está montado **duas vezes** no serviço: prefira rotas com prefixo **`/financial`**. Existe legado **`/finacial`** (typo em `main.py`) — evite documentar ao usuário; no OpenAPI podem aparecer ambos.

| O usuário quer | Rota preferida | operationId (referência) |
|----------------|----------------|--------------------------|
| ROL | `GET /financial/rol` | `get_rol` |
| EBITDA % | `GET /financial/ebitda_pct` | `get_ebitda_pct` |
| Custo fixo % | `GET /financial/fixed_cost_pct` | `get_fixed_cost_pct` |
| PMR (prazo médio recebimento) | `GET /financial/pmr` | `get_pmr` |

**Parâmetros:** `branch`, `start_date`, `end_date` (conforme endpoint).

---

### Produção (`/production`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| OTD produção | `GET /production/on_time_delivery_pct` | `get_on_time_delivery_pct` |
| OEE (eficiência equipamentos) | `GET /production/overall_equipment_effectiveness_pct` | `get_overall_equipment_effectiveness_pct` |
| Custo direto mão de obra | `GET /production/direct_labor_cost_pct` | `get_direct_labor_cost_pct` |
| Custo de produção | `GET /production/production_cost_pct` | `get_production_cost_pct` |
| Depreciação % ROL | `GET /production/depreciation_pct` | `get_depreciation_pct` |

---

### RH (`/hr`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Listar filiais (Portal RH) | `GET /hr/branches` | path `hr/branches` |
| Snapshot RH (headcount, turnover, PDI, avaliações) | `GET /hr/snapshot` | `get_hr_snapshot` |
| PDIs ativos (detalhe) | `GET /hr/active-pdi-count` | path `active-pdi-count` |
| Avaliações de desempenho | `GET /hr/performance-reviews-completion` | path `performance-reviews` |

**Parâmetros:** `branch`, `start_date`, `end_date` (datas normalizadas Portal RH).

---

### Qualidade — métricas TOTVS (`/quality`)

Consultas analíticas no Protheus; **não** confundir com módulo NC em PostgreSQL.

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Filiais disponíveis | `GET /quality/branches` | path `quality/branches` |
| Listar não conformidades | `GET /quality/nonconformities` | path `nonconformities` |
| Série temporal de NC | `GET /quality/nonconformities/series` | path `nonconformities/series` |
| PPM interno — resumo | `GET /quality/ppm/internal/summary` | path `ppm/internal/summary` |
| PPM externo — resumo | `GET /quality/ppm/external/summary` | path `ppm/external/summary` |
| PPM interno — detalhado | `GET /quality/ppm/internal` | path `ppm/internal` |
| PPM externo — detalhado | `GET /quality/ppm/external` | path `ppm/external` |
| Série PPM interno | `GET /quality/ppm/internal/series` | path `ppm/internal/series` |
| Série PPM externo | `GET /quality/ppm/external/series` | path `ppm/external/series` |
| Auditoria 5S — resumo | `GET /quality/audit-5s/summary` | path `audit-5s/summary` |
| Kaizens — resumo | `GET /quality/kaizens/summary` | path `kaizens/summary` |

**Parâmetros (`/quality/nonconformities`)**

- `type`: `internal`, `external` ou `all`
- `branch`, `date_start`, `date_end`, `status`, `item_code`, `description`, `page`, `page_size`

**Rotas antigas (não usar)**

- `GET /quality/ppm/internal` como único resumo — preferir `/summary` e `/series`
- `GET /quality/nonconformities` sem sufixo era genérico; manter `type` explícito

---

### Dados — SQL (`/data`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Executar SELECT / consulta analítica | `POST /data/sql` | `execute_readonly_sql` |

**Corpo:** JSON `{ "sql": "SELECT ..." }` ou `text/plain` com a query. Somente leitura (SELECT, CTE). Permissão: `api-delpi.data` ou `api-delpi.access.full`.

---

### Sistema — metadados Protheus (`/system`)

| O usuário quer | Rota | Notas |
|----------------|------|--------|
| Buscar tabelas por descrição | `GET /system/tables/search` | `description` (mín. 2 chars), `page`, `limit` |
| Metadados de uma tabela | `GET /system/tables/{tableName}` | SX2 |
| Colunas da tabela (paginado) | `GET /system/tables/{tableName}/columns` | `page`, `limit` |
| Buscar colunas dentro da tabela | `GET /system/tables/{tableName}/columns/search` | query `q` (mín. 2 chars) |
| Índices da tabela | `GET /system/tables/{tableName}/indexes` | SIX |
| Relacionamentos | `GET /system/tables/{tableName}/relations` | SX9 |
| Schema agregado completo | `GET /system/tables/{tableName}/schema` | SX2+SX3+SIX+SX9 |
| Busca global de colunas | `GET /system/columns/search` | `description`, `page`, `limit` |

Permissão: `api-delpi.access.full` ou `api-delpi.system`.

---

## Erros e respostas

| HTTP | Significado para o usuário |
|------|----------------------------|
| 200-299 | Sucesso — use `humanizedSummary` ou resposta direta do pipeline |
| 401 / 403 | Sem permissão para esta rota |
| 404 | Produto, OV ou recurso não encontrado |
| 422 | Parâmetro faltando ou inválido (código, datas, página) |
| 503 | Dependência indisponível (ex.: Portal RH em rotas `/hr`) |

Não pergunte se o usuário "tem permissão"; a API já valida com o token dele.

---

## Vocabulário (sinônimos)

| Domínio | Termos |
|---------|--------|
| Produto | produto, item, código, referência, ref, SKU, material, MP, insumo |
| Estoque item | estoque, saldo, disponível, quantidade, posição, armazém |
| Estrutura/BOM | estrutura, componentes, composição, bill of materials, BOM |
| Onde é usado | onde é usado, produto pai, parent, where used, utilizado em, pai do |
| Preço | preço, pricing, tabela de preço, quanto custa, custo |
| Notas | nota de entrada, nota de saída, NF-e, invoice, inbound, outbound |
| LMP | LMP, lista de materiais de projeto, amostra, ordem de venda, OV |
| OV | ordens de venda, pedidos de venda, OV, sale_number |
| Transforma Mais | transforma mais, processo de melhoria, engenharia |
| SQL | SQL, consulta, SELECT, query, dados, Protheus |
| KPI estoque | valor total de estoque, valor em estoque, indicador suprimentos, stock-value |
| KPI comercial | closing rate, conversão, ROL, OTD pedido, novos clientes, novos negócios |
| KPI financeiro | EBITDA, PMR, custo fixo, ROL |
| KPI produção | OTD produção, OEE, custo de produção, mão de obra, depreciação |
| Qualidade | não conformidade, NC, PPM, kaizen, 5S, auditoria |

---

## Checklist do administrador

1. Provider `api-delpi` com `authMode: user_token` e `openApiUrl` apontando para o gateway.
2. Agente com `allowRead` e actions de leitura/SQL habilitadas.
3. **Reimport OpenAPI** após deploy da api-delpi (`POST .../providers/{key}/reload-schema` ou import).
4. Anexar **este documento** à base de conhecimento do agente (tags: `api-delpi`, `operacional`, `rotas`) **ou** referenciar no `system_prompt`.
5. Testar: estoque de código, OV de LMP, valor total de estoque com e sem período, PPM interno resumo, SELECT simples.

---

## Referências técnicas

- Metadados OpenAPI (rotas com `summary`/`description` PT): `api-delpi/app/interface/http/openapi_agent_metadata.py`
- Documentação humana por módulo: `api-delpi/docs/api/06-modulos-departamentais.md`, `api-delpi/docs/api/02-produtos.md`, `api-delpi/docs/api/04-sistema-e-dados.md`
- Guia resumido: `api-delpi/docs/api/11-guia-agente-chat.md`
- Estoque histórico suprimentos: `api-delpi/docs/api/supplies-estoque-historico.md`
- Actions no chat: `minha-delpi-ai-api/docs/api/04-actions-openapi.md`
