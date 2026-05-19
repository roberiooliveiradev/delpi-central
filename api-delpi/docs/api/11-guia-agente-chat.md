# 11 — Guia de rotas para agentes (Minha DELPI Chat)

Este documento orienta a **seleção automática de rotas** quando um agente do chat usa a api-delpi via **actions OpenAPI** importadas no `minha-delpi-ai-api`.

## Como o agente escolhe a rota

1. O provider do agente aponta para `GET /apps/api-delpi/openapi.json`.
2. Cada operação vira uma **action** com `summary`, `description`, `path`, `operationId` e `tags`.
3. O chat filtra candidatos por palavras-chave e ranqueia por path + metadados (+ embeddings, se habilitado).
4. Após alterar este guia ou o OpenAPI, **reimporte** o schema no agente (`POST .../providers/{key}/import`).

Campos OpenAPI mais importantes para acertar a rota:

| Campo | Uso |
|---|---|
| `summary` | Título curto em PT — entra no filtro SQL e no embedding |
| `description` | Quando usar / quando **não** usar (evita confusão estoque item vs valor total) |
| `operationId` | Identificador estável (`get_product_stock`, `list_lmps`, …) |
| `tags` | Primeira tag vira namespace da action (`api_delpi.engenharia.list_lmps`) |
| Parâmetros `code`, `sale_number` | Mapeados automaticamente a partir da mensagem |

## Mapa de intenção → rota preferida

### Produtos (`/products`)

| O usuário quer… | Método e rota | `operationId` |
|---|---|---|
| Achar produto sem código exato | `GET /products/search` | `search_products` |
| Descrição / ficha resumida / visão geral do item | `GET /products/{code}/analyser` | `get_product_analyser` |
| Saldo, estoque, disponível **de um código** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM / componentes | `GET /products/{code}/structure` | `get_product_structure` |
| Histórico de compras | `GET /products/{code}/purchases` | `purchases` (legado EN) |
| Vendas / carteira / faturamento | `GET /products/{code}/sales*` | ver OpenAPI |

**Código do produto:** aceitar máscara (`10.080.055` → normalizado para a API). Em follow-up (“estoque **desse** produto”), o chat pode recuperar o código do histórico da conversa.

**Não confundir:**

| Pergunta | Rota correta | Rota errada comum |
|---|---|---|
| Estoque do item 10080047 | `/products/{code}/stock` | `/supplies/stock-value` |
| Valor total de estoque da empresa | `/supplies/stock-value` | `/products/{code}/stock` |

### Engenharia — LMP (`/engineering`)

| O usuário quer… | Método e rota | `operationId` |
|---|---|---|
| Listar / filtrar várias LMPs ou amostras | `GET /engineering/lmps` | `list_lmps` |
| Painel / dashboard / resumo gerencial | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| Uma LMP pela ordem de venda (OV) | `GET /engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` |

Parâmetros úteis na listagem: `listing_type` (`LMP`, `Amostra`, `Outro`), `date_start`, `date_end`, `branch`, `page`, `page_size`.

### Dados — SQL (`/data`)

| O usuário quer… | Método e rota | `operationId` |
|---|---|---|
| Rodar SELECT / consulta analítica | `POST /data/sql` | `execute_readonly_sql` |

Corpo: JSON `{ "sql": "SELECT ..." }` ou `text/plain` com a query. Somente leitura; validador bloqueia DML.

Permissão: `api-delpi.data` ou `api-delpi.access.full`.

### Suprimentos — indicadores (`/supplies`)

| O usuário quer… | Método e rota | `operationId` |
|---|---|---|
| Valor total de estoque (KPI) | `GET /supplies/stock-value` | `get_supplies_stock_value` |
| Giro de estoque (IDD) | `GET /supplies/inventory-turnover` | (ver OpenAPI) |
| CPV / OTD compras | `/supplies/cpv`, `/supplies/otd` | (ver OpenAPI) |

## Vocabulário recomendado nos metadados OpenAPI

Incluir no `summary` ou `description` (PT):

- **Produto:** produto, item, código, referência, SKU, descrição, estoque, saldo, disponível, estrutura, BOM.
- **LMP:** LMP, lista de materiais de projeto, amostra, ordem de venda, OV.
- **SQL:** SQL, consulta, SELECT, dados, query.
- **Suprimentos (KPI):** valor total de estoque, indicador, suprimentos (evitar só “estoque” sem contexto).

Implementação centralizada em `app/interface/http/openapi_agent_metadata.py`.

## Checklist após mudar a API

1. Subir api-delpi e conferir `/apps/api-delpi/openapi.json`.
2. Reimportar provider no agente do chat.
3. (Opcional) Reindexar embeddings das actions no admin do chat.
4. Testar frases reais: estoque do 10.080.055, listar LMPs da semana, OV 123456, SELECT TOP 10…

## Documento para anexar ao agente (RAG)

Versão expandida para ingestão na base de conhecimento do chat:

`minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`

## Referências

- [02-produtos.md](./02-produtos.md) — detalhes humanos das rotas de produto
- [04-sistema-e-dados.md](./04-sistema-e-dados.md) — SQL e metadados Protheus
- [06-modulos-departamentais.md](./06-modulos-departamentais.md) — LMP e suprimentos
- `minha-delpi-ai-api/docs/api/04-actions-openapi.md` — import e permissões do agente
