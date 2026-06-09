# 11 — Guia de rotas para agentes (Minha DELPI Chat)

Este documento orienta a **seleção automática de rotas** quando um agente do chat usa a api-delpi via **actions OpenAPI** importadas no `minha-delpi-ai-api`.

**Versão expandida para RAG (recomendada na base de conhecimento):**  
[`minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md)

**Última revisão:** jun/2026 (playbooks fabril: estrutura/exclusividade, produção, expedição, status fabril).

**Roadmap — padronizar JSON para IA:** [`playbook-10-contrato-respostas-api-delpi.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md) (índice api-delpi: [`docs/roadmaps/playbook-contrato-respostas-ia.md`](../roadmaps/playbook-contrato-respostas-ia.md)).

**Após alterar rotas ou `operationId`:** [12-procedimento-reimport-openapi.md](./12-procedimento-reimport-openapi.md).

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
| Ficha analítica (multi-dimensão) | `GET /products/{code}/analyser` | `get_product_analyser` |
| Estoque/saldo **do item** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM | `GET /products/{code}/structure` | `get_product_structure` |
| Estrutura + MPs exclusivas | `GET /products/{code}/structure/exclusivity` | `get_product_structure_exclusivity` |
| Situação produtiva (PA/PI/OP/apontamentos) | `GET /products/{code}/production-status` | `get_product_production_status` |
| Expedição / inspeção final do PA | `GET /products/{code}/shipping-status` | `get_product_shipping_status` |
| Status fabril completo do produto | `GET /products/{code}/factory-status` | `get_product_factory_status` |
| Onde é usado / produto pai | `GET /products/{code}/parents` | `get_product_parents` |
| Preço / tabela | `GET /products/{code}/pricing` | `get_product_pricing` |
| Fornecedores / clientes | `.../suppliers`, `.../customers` | `get_product_suppliers`, `get_product_customers` |
| Compras / vendas / carteira / faturamento | `.../purchases`, `.../sales`, `.../open-orders`, `.../billing` | `get_product_purchases`, `get_product_sales_summary`, `get_product_sales_open_orders`, `get_product_sales_billing` |
| Roteiro / inspeção / movimentações / NF | `guide`, `inspection`, `internal-movements`, `inbound|outbound-invoice-items` | `get_product_guide`, `get_product_inspection`, `get_product_internal_movements` (NF: path) |

**Não confundir:** estoque do item → `/products/{code}/stock`; valor total da empresa → `/supplies/stock-value`. Inspeção de qualidade (QP6/QP7/QP8) → `/products/{code}/inspection`; expedição após inspeção final (CT SHB010 + apontamento SH6010) → `/products/{code}/shipping-status`.

### Quando usar granular vs analyser vs factory-status

| Intenção do usuário | Rota preferida | Evitar |
|---|---|---|
| Saldo / estoque do código | `/stock` | `/analyser` full |
| BOM / estrutura / componentes | `/structure` ou `/structure/exclusivity` | `/analyser` full |
| Roteiro / operações / CTs | `/guide` | `/analyser` full |
| Inspeção de qualidade (QP) | `/inspection` | `/shipping-status` |
| Cadastro + amostra estoque/preços | `/summary` | `/analyser` full |
| Visão fabril integrada (OP, MPs, expedição) | `/factory-status` | várias rotas separadas |
| Ficha multi-dimensão explícita | `/analyser?view=full` | — |
| Visão leve multi-dimensão (chat) | `/analyser?view=summary` | `view=full` sem necessidade |

Respostas `composite_analysis` incluem `meta.sections[]` com `{ key, label, itemCount, truncated }` para o chat sinalizar cobertura parcial.

**Playbooks fabril** (SQL validado em `api-delpi/docs/roadmaps/`):

| Intenção | Rota | Parâmetros úteis |
|---|---|---|
| BOM com exclusividade de MP | `/structure/exclusivity` | `max_depth` |
| Produção iniciada / OP / apontamento | `/production-status` | `reference_date`, `branch`, `max_depth` |
| PA liberado para expedição | `/shipping-status` | `date_start`, `date_end`, `reference_date`, `branch` |
| Visão integrada na fábrica | `/factory-status` | `reference_date`, `date_start`, `date_end`, `branch`, `max_depth` |

Preferir `/factory-status` quando o usuário pedir status completo do produto na fábrica.

Código com máscara (`10.080.055`) é válido. Follow-up (“estoque **desse** produto”) usa contexto da conversa.

---

## Engenharia — LMP (`/engineering`)

| O usuário quer… | Rota | Notas |
|---|---|---|
| Listar LMPs / amostras | `GET /engineering/lmps` | `list_lmps` |
| KPIs do painel | `GET /engineering/lmps/dashboard/summary` | `get_lmps_dashboard_summary` |
| Itens paginados do painel | `GET /engineering/lmps/dashboard/items` | `list_lmps_dashboard_items` |
| Gráficos do painel | `GET /engineering/lmps/dashboard/charts` | `get_lmps_dashboard_charts` |
| Dashboard legado (tudo) | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| Detalhe por OV | `GET /engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` |
| Transforma Mais (lista) | `GET /engineering/transforma-mais/processes` | `list_transforma_mais_processes` |
| Transforma Mais (resumo) | `GET /engineering/transforma-mais/processes/summary` | `get_transforma_mais_summary` |

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
| `/supplies/negotiation-savings/summary` | Economia em negociações de compras (planilha `idd_suprimentos`, por filial) |

**Parâmetros (`/supplies/negotiation-savings/summary`)**

- `start_date`, `end_date` — período (obrigatório para IDD mensal; aceita `YYYY-MM-DD` ou `DD/MM/YYYY`)
- `branch` — `01` ou `02` (opcional; sem filial retorna `branches` com totais por unidade)
- Fonte: Google Sheets (`SUPPLIES_IDD_SHEET_ID` + `SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID`); indicador SI `supplies_negotiation_savings`

**Exemplos**

- "Quanto foi a economia em negociações de compras em maio?" → `/supplies/negotiation-savings/summary` com período
- "Economia de negociação da filial 01" → mesma rota com `branch=01`

Detalhes histórico: [supplies-estoque-historico.md](./supplies-estoque-historico.md).

---

## Qualidade (`/quality`)

Métricas TOTVS e Google Sheets (PPM, NC Protheus, kaizen, 5S resumo).

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
