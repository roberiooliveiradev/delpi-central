# 11 — Guia de rotas para agentes (Minha DELPI Chat)

Este documento orienta a **seleção automática de rotas** quando um agente do chat usa a api-delpi via **actions OpenAPI** importadas no `minha-delpi-ai-api`.

**Versão expandida para RAG (recomendada na base de conhecimento):**  
[`minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md)

**Última revisão:** maio/2026 (Onda 10 inteligência + rotas comercial/qualidade/RH/dashboard LMP).

---

## Como o agente escolhe a rota

1. Provider do agente aponta para `GET /apps/api-delpi/openapi.json` com `authMode: user_token`.
2. Cada operação vira **action** com `summary`, `description`, `path`, `operationId` e `tags`.
3. O pipeline filtra candidatos por palavras-chave, scoring por path/intent e ranking semântico (se habilitado).
4. Após mudar API ou este guia: **reimporte** o schema (`POST .../providers/{key}/import`) e **reindexe** o documento RAG.

| Campo OpenAPI | Uso |
|---|---|
| `summary` | Título curto em PT — filtro e embedding |
| `description` | Quando usar / quando **não** usar |
| `path` | Principal para heurísticas (produto vs KPI vs OV) |
| `operationId` | Identificador estável quando definido em `openapi_agent_metadata.py`; caso contrário pode ser auto-gerado pelo FastAPI |

Metadados centralizados: `app/interface/http/openapi_agent_metadata.py`.

---

## Produtos (`/products`)

| O usuário quer… | Rota preferida | `operationId` (ref.) |
|---|---|---|
| Busca sem código exato | `GET /products/search` | `search_products` |
| Dados cadastrais (leve) | `GET /products/{code}` | `get_product_detail` |
| Resumo produto + estoque + preços | `GET /products/{code}/summary` | `get_product_summary` |
| Ficha analítica completa | `GET /products/{code}/analyser` | `get_product_analyser` |
| Estoque/saldo **do item** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM | `GET /products/{code}/structure` | `get_product_structure` |
| Onde é usado / produto pai | `GET /products/{code}/parents` | path `parents` |
| Preço / tabela | `GET /products/{code}/pricing` | path `pricing` |
| Fornecedores / clientes | `.../suppliers`, `.../customers` | path |
| Compras / vendas / carteira / faturamento | `.../purchases`, `.../sales`, `.../open-orders`, `.../billing` | ver OpenAPI |
| Roteiro / inspeção / movimentações / NF | `guide`, `inspection`, `internal-movements`, `inbound|outbound-invoice-items` | path |

**Não confundir:** estoque do item → `/products/{code}/stock`; valor total da empresa → `/supplies/stock-value`.

Código com máscara (`10.080.055`) é válido. Follow-up (“estoque **desse** produto”) usa contexto da conversa.

---

## Engenharia — LMP (`/engineering`)

| O usuário quer… | Rota | Notas |
|---|---|---|
| Listar LMPs / amostras | `GET /engineering/lmps` | `list_lmps` |
| KPIs do painel | `GET /engineering/lmps/dashboard/summary` | Preferir no chat vs dashboard completo |
| Itens paginados do painel | `GET /engineering/lmps/dashboard/items` | MFE / tabelas grandes |
| Gráficos do painel | `GET /engineering/lmps/dashboard/charts` | MFE |
| Dashboard legado (tudo) | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| Detalhe por OV | `GET /engineering/lmps/{sale_number}` | OV ≠ código de produto |
| Transforma Mais | `GET /engineering/transforma-mais/processes` (+ `/summary`) | Melhoria contínua |

---

## Vendas, comercial, financeiro, produção, RH

| Domínio | Exemplos de rota |
|---|---|
| Ordens de venda (lista) | `GET /sales/` — não confundir com `/products/{code}/sales` |
| KPI comercial | `/commercial/closing-rate`, `/commercial/rol/series`, metas ROL, OTD, novos clientes/negócios |
| Financeiro | `GET /financial/rol`, `/financial/ebitda_pct`, `/financial/pmr`, `/financial/fixed_cost_pct` (também legado `/finacial/*`) |
| Produção | `/production/on_time_delivery_pct`, OEE, custos, `depreciation_pct` |
| RH | `/hr/branches`, `/hr/snapshot`, PDIs, avaliações |

---

## Suprimentos (`/supplies`)

| Rota | Uso |
|---|---|
| `/supplies/stock-value` | KPI valor total — sem datas: atual; com `start_date`+`end_date`: histórico estimado |
| `/supplies/inventory-turnover` | Giro (IDD) |
| `/supplies/cpv`, `/supplies/otd` | CPV e OTD compras |

Detalhes histórico: [supplies-estoque-historico.md](./supplies-estoque-historico.md).

---

## Qualidade (`/quality`)

Métricas TOTVS (não confundir com NC PostgreSQL — [07-qualidade-nc.md](./07-qualidade-nc.md)).

| Rota | Uso |
|---|---|
| `/quality/branches` | Filiais |
| `/quality/nonconformities` (+ `/series`) | NC Protheus |
| `/quality/ppm/internal|external/summary` | PPM resumo |
| `/quality/ppm/internal|external` | PPM detalhado (+ `/series`) |
| `/quality/audit-5s/summary`, `/quality/kaizens/summary` | 5S e kaizens |

Permissão: `api-delpi.quality.access` ou `dashboard-quality.view`.

---

## SQL e sistema

| Rota | Uso |
|---|---|
| `POST /data/sql` | SELECT somente leitura — `execute_readonly_sql` |
| `GET /system/tables/search` | Buscar tabelas por descrição |
| `GET /system/tables/{tableName}/schema` | Schema agregado |
| `GET /system/columns/search` | Busca global de colunas |

Permissão SQL: `api-delpi.data` ou `api-delpi.access.full`. Sistema: `api-delpi.system` ou `api-delpi.access.full`.

---

## Financeiro — prefixos

Em `main.py` o router financeiro está montado em **`/financial`** (preferido) e **`/finacial`** (legado, typo). Ex.: `GET /financial/rol` e `GET /finacial/rol`.

---

## Checklist após mudar a API

1. Deploy api-delpi → conferir `/apps/api-delpi/openapi.json`.
2. Reimportar provider no agente.
3. Reindexar `api-delpi-rotas-agente.md` na base de conhecimento.
4. Testar: estoque item, valor total estoque, OV LMP, listar OVs, PPM resumo, SELECT simples.

---

## Referências

- [02-produtos.md](./02-produtos.md)
- [04-sistema-e-dados.md](./04-sistema-e-dados.md)
- [06-modulos-departamentais.md](./06-modulos-departamentais.md)
- [10-referencia-rapida-endpoints.md](./10-referencia-rapida-endpoints.md)
- `minha-delpi-ai-api/docs/api/04-actions-openapi.md`
