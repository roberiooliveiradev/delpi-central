# API DELPI — Guia de rotas para agentes operacionais

**Uso:** anexar este documento à inteligência do agente (base de conhecimento / RAG) ou colar trechos relevantes no `system_prompt` de agentes que usam o provider OpenAPI `api-delpi`.

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
| **Onde é usado / produto pai / where used** | `GET /products/{code}/parents` | `get_product_parents` |
| Fornecedores do item | `GET /products/{code}/suppliers` | (ver catálogo) |
| Histórico de compras | `GET /products/{code}/purchases` | `get_product_purchases` |
| Resumo de vendas do item | `GET /products/{code}/sales` | `get_product_sales_summary` |
| Carteira / pedidos em aberto do item | `GET /products/{code}/sales/open-orders` | `get_product_sales_open_orders` |

**Parâmetros comuns**

- `search`: `code`, `description`, `group_code`, `page`, `page_size`
- `stock`: `code` (path), `branch`, `location`, `page`, `page_size`
- `analyser`: `code` (path)

**Exemplos de frases → rota**

- “Qual a descrição do produto 10.080.055?” → `get_product_analyser`
- “Tem estoque do 10080047 na filial 01?” → `get_product_stock`
- “Busca parafuso M8 na descrição” → `search_products`
- “Qual a estrutura do 10080001?” → `get_product_structure`
- “Onde é usado o 10080001?” → `get_product_parents`
- “Produto pai do 10080001” → `get_product_parents`

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

- “Lista as LMPs da semana” → `list_lmps`
- “Dashboard de LMPs em aberto” → `list_lmps_dashboard`
- “Detalhe da LMP da OV 123456” → `get_lmp_by_sale_number` (não usar código de produto como OV)

**Atenção:** número de OV **não** é código de produto.

---

### Suprimentos — indicadores (`/supplies`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| **Valor total** de estoque (KPI) | `GET /supplies/stock-value` | `get_supplies_stock_value` |
| Giro de estoque (IDD) | `GET /supplies/inventory-turnover` | (ver catálogo) |
| CPV (custo produção vendido) | `GET /supplies/cpv` | `get_supplies_cpv` |
| OTD (entrega no prazo compras) | `GET /supplies/otd` | `get_supplies_otd` |
| Giro / IDD | `GET /supplies/inventory-turnover` | `get_supplies_inventory_turnover` |

**Exemplos**

- “Qual o valor total de estoque da empresa?” → `get_supplies_stock_value` (**não** `/products/{code}/stock`)
- “Estoque do produto X” → `get_product_stock` (**não** `stock-value`)

---

### Vendas — ordens (`/sales`)

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Listar ordens de venda no período | `GET /sales/` | `list_sale_orders` |

Não confundir com detalhe de LMP (`/engineering/lmps/{sale_number}`) nem vendas de um produto (`/products/{code}/sales`).

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

- “Roda esse SQL: SELECT TOP 10 …” → `execute_readonly_sql` com campo `sql`

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
| Estrutura/BOM | estrutura, componentes, composição, bill of materials, BOM |
| Onde é usado | onde é usado, produto pai, parent, where used, utilizado em, faz parte de |
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
