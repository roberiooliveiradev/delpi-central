# 02 — Produtos

Prefixo: `/products`

**Permissão:** `api-delpi.access` em todas as rotas.

Formato de resposta: envelope `{ success, message, data }`.

> **Agentes (chat):** mapa de qual rota usar por intenção — [11-guia-agente-chat.md](./11-guia-agente-chat.md). Metadados OpenAPI (`summary`, `description`, `operationId`) em `app/interface/http/openapi_agent_metadata.py`.

## GET /products/search

Busca paginada de produtos no Protheus.

| Query | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `code` | string | não | Código do produto. |
| `group_code` | string | não | Grupo de produtos. |
| `description` | string | não | Descrição parcial. |
| `page` | int | não | Página (default `1`, mín. `1`). |
| `page_size` | int | não | Tamanho (default `50`, máx. `500`). |
| `sort` | string | não | Campo de ordenação. |
| `direction` | string | não | Direção (`asc`/`desc`). |

**Exemplo:**

```http
GET /apps/api-delpi/products/search?description=parafuso&page=1&page_size=20
```

---

## GET /products/{code}

Dados cadastrais do produto (leve, sem o payload completo do analyser).

| Query | Default | Descrição |
|---|---|---|
| `view` | `full` | `summary` retorna ~15 campos (`code`, `description`, `type`, `unit`, `group_code`, `active`, `blocked`, `default_warehouse`, preços, NCM, revisão, `make_or_buy`). |
| `legacy` | `false` | Reservado para evoluções de cadastro; playbook usa em rotas fabris. |

Campos típicos (`view=full`): `code`, `description`, `type`, `unit`, `group_code`, `active`, `default_warehouse`, `last_purchase_price`, `standard_cost`, `last_revision_date`, `ncm_ipi_position`.

**Uso no chat:** perguntas de descrição, “o que é o produto X”, dados cadastrais — preferir esta rota antes do `/analyser` quando não precisar de todas as dimensões.

---

## GET /products/{code}/summary

Consolida cadastro + estoque (top locais) + preços em uma única chamada.

**Uso no chat:** visão geral rápida sem múltiplas requisições.

---

## GET /products/{code}/structure

Estrutura (BOM) do produto.

| Query | Descrição |
|---|---|
| `max_depth` | Profundidade máxima da árvore. |
| `page`, `page_size` | Paginação de itens da estrutura. |

---

## GET /products/{code}/structure/exclusivity

Estrutura vigente multinível com **exclusividade de matérias-primas** (playbook `playbook-estrutura-produto-exclusividade-mp.md`).

| Query | Descrição |
|---|---|
| `max_depth` | Profundidade máxima da árvore (default `50`, máx. `100`). |

Retorna `product`, `items` (componentes com `exclusive_raw_material`, `accumulated_quantity`, `path`) e `summary` (`total_intermediates`, `total_raw_materials`, `total_exclusive_raw_materials`).

| Query | Default | Descrição |
|---|---|---|
| `legacy` | `false` | `false`: `exclusive_raw_material` é `bool` + `exclusive_raw_material_label`; `true`: string `SIM`/`NAO` legada. |

**Uso no chat:** MPs exclusivas, estrutura com quantidade acumulada por PA, BOM com flag de exclusividade.

---

## GET /products/{code}/production-status

Situação produtiva do PA e intermediários com OPs (`SC2010`) e apontamentos (`SH6010`) até uma data de referência (playbook `playbook-situacao-de-producao-pa.md`).

| Query | Descrição |
|---|---|
| `reference_date` | Data de avaliação (`YYYY-MM-DD` ou `DD/MM/YYYY`; default: hoje). |
| `max_depth` | Profundidade da BOM (default `50`). |
| `branch` | Filial (`01`, `02`). |
| `legacy` | `false` | `false`: `production_started` bool + label; resposta inclui `reference_date_iso`. |

Retorna `items` por produto da rota (PA + PIs) com OP, apontamentos, `production_started`, `equivalent_in_pa` e `summary`.

**Uso no chat:** “já começou a produzir?”, OPs do produto, quanto foi apontado.

---

## GET /products/{code}/shipping-status

Quantidade do PA finalizada para expedição e perdas no **CT de inspeção final** (playbook `playbook-pa-inspecao-expedicao.md`).

| Query | Descrição |
|---|---|
| `reference_date` | Atalho para dia único (equivale a `date_start` quando `date_end` omitido). |
| `date_start`, `date_end` | Período inclusivo no início e exclusivo no fim (`H6_DTAPONT >= start` e `< end+1`). |
| `branch` | Filial (`01`, `02`). |
| `legacy` | `false` | `false`: inclui `date_start_iso` / `date_end_exclusive_iso`. |

Retorna apontamentos agregados por OP/recurso/CT com `shipped_quantity`, `inspection_loss_quantity` e totais em `summary`.

**Não confundir** com `/inspection` (definição de ensaios QP6/QP7/QP8).

---

## GET /products/{code}/factory-status

Visão fabril consolidada (playbook `playbook-visaostatus-produto.md`): estrutura + exclusividade, estoque de MPs, produção, expedição e classificação `factory_status`.

| Query | Descrição |
|---|---|
| `reference_date` | Data para estrutura/produção (default: hoje). |
| `date_start`, `date_end` | Período de expedição (default: dia de `reference_date`). |
| `max_depth` | Profundidade da BOM (default `50`). |
| `branch` | Filial opcional. |
| `legacy` | `false` | `false`: booleanos normalizados + datas ISO; `true`: formato Protheus legado. |

Retorna blocos `structure`, `raw_material_stock`, `production`, `shipping`, `indicators` e `factory_status` (ex.: `PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO`).

**Uso no chat:** status completo do produto na fábrica — preferir esta rota em perguntas amplas.

---

## GET /products/{code}/structure/excel

Exporta estrutura em Excel.

| Query | Descrição |
|---|---|
| `format` | `json` (default) retorna URL de download; `xlsx` faz streaming do arquivo. |

**Resposta (`format=json`):**

```json
{
  "message": "Arquivo Excel gerado com sucesso!",
  "download_url": "https://..."
}
```

---

## GET /products/{code}/parents

Produtos “pai” que utilizam o item na estrutura.

Parâmetros: `max_depth`, `page`, `page_size`.

---

## GET /products/{code}/suppliers

Fornecedores do item.

| Query | Default |
|---|---|
| `page` | `1` |
| `page_size` | `50` (máx. `500`) |

---

## GET /products/{code}/customers

Clientes vinculados ao item.

---

## GET /products/{code}/inspection

Dados de inspeção / qualidade do item.

| Query | Descrição |
|---|---|
| `page`, `page_size` | Paginação. |
| `max_depth` | Profundidade (máx. `15`). |

---

## GET /products/{code}/guide

Roteiro de produção.

| Query | Descrição |
|---|---|
| `branch` | Filial. |
| `page`, `page_size`, `max_depth` | Paginação e profundidade. |

---

## GET /products/{code}/internal-movements

Movimentações internas de estoque.

| Query | Descrição |
|---|---|
| `date_start`, `date_end` | Período. |
| `branch`, `location` | Filial e armazém. |
| `tm`, `op` | Transformação / ordem de produção. |

---

## GET /products/{code}/stock

Posição de estoque.

| Query | Default | Descrição |
|---|---|---|
| `branch` | — | Filial. |
| `warehouse` | — | Armazém/local (preferido). |
| `location` | — | Alias legado de `warehouse` (aceito). |
| `legacy` | `false` | `false`: cada item inclui `location` espelhando `warehouse`. |

---

## GET /products/{code}/inbound-invoice-items

Itens de NF-e de **entrada** com o produto.

| Query | Descrição |
|---|---|
| `issue_date_start`, `issue_date_end` | Emissão. |
| `supplier`, `branch` | Fornecedor e filial. |

---

## GET /products/{code}/outbound-invoice-items

Itens de NF-e de **saída**.

| Query | Descrição |
|---|---|
| `issue_date_start`, `issue_date_end` | Emissão. |
| `customer`, `branch` | Cliente e filial. |

---

## GET /products/{code}/purchases

Histórico de compras do produto.

---

## GET /products/{code}/sales

Resumo de vendas do produto.

---

## GET /products/{code}/sales/open-orders

Carteira de pedidos em aberto.

---

## GET /products/{code}/sales/billing

Resumo de faturamento.

---

## GET /products/{code}/pricing

Preços comerciais (tabelas de preço).

---

## GET /products/{code}/analyser

Visão consolidada (“analisador”) com múltiplas dimensões do produto em uma única chamada.

**Uso típico:** tela de detalhe do plugin Dashboard DELPI.
