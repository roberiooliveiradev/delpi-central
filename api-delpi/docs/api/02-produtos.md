# 02 — Produtos

Prefixo: `/products`

**Permissão:** `api-delpi.access` em todas as rotas.

Formato de resposta: envelope `{ success, message, data }`.

> **Agentes (chat):** mapa de qual rota usar por intenção — [11-guia-agente-chat.md](./11-guia-agente-chat.md). Metadados OpenAPI (`summary`, `description`, `operationId`) em `app/interface/http/openapi_agent_metadata.py`.

> **Unidades de medida (MI, BOM, fiscal):** convenção produtiva e impacto nas rotas de estrutura, estoque e simulador — [playbook-conversao-unidades-protheus.md](../roadmaps/playbook-conversao-unidades-protheus.md).

> **Vigência da BOM (`SG1010`):** rotas que explodem estrutura consideram apenas linhas vigentes em `G1_INI` / `G1_FIM`. Default: **hoje**; rotas fabris com `reference_date` usam essa data. Módulo: `ProductBomValidityFilterService` — [bom-validity-filter-changelog-jun2026.md](./bom-validity-filter-changelog-jun2026.md).

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

Campos típicos (`view=full`): `code`, `description`, `type`, `unit`, `group_code`, `active`, `default_warehouse`, `customer_reference`, `last_purchase_price`, `standard_cost`, `current_revision`, `last_revision_date`, `ncm_ipi_position`.

**Referência do cliente:**

| Campo API | Origem Protheus | Significado |
|-----------|-----------------|-------------|
| `customer_reference` | `SB1.B1_REFEREN` | Código/REF. do cliente no cadastro — no desenho aparece como `REF:` / `COD. CLIENTE` |
| `customer_reference_old` | `SB1.B1_REFCANT` | Referência anterior (quando houver) |

O chat de análise de desenhos cruza a REF. lida no PDF com `customer_reference` (regra `customer_reference_cross_check`).

**Revisões (não confundir):**

| Campo API | Origem Protheus | Significado |
|-----------|-----------------|-------------|
| `current_revision` | `SB1.B1_REVATU` | Revisão **Delpi** do cadastro — existe **somente no TOTVS**, não impressa no PDF do desenho |
| `last_revision_date` | `SB1.B1_UREV` | Data da última revisão cadastral Delpi |

A **REV. no carimbo/título do PDF** é a revisão do **desenho do cliente**. O chat de análise **não** cruza REV. do PDF com `current_revision` (nem como crítico nem como pendente).

**Uso no chat:** perguntas de descrição, “o que é o produto X”, dados cadastrais — preferir esta rota antes do `/analyser` quando não precisar de todas as dimensões.

---

## GET /products/{code}/summary

Consolida cadastro + estoque (top locais) + preços em uma única chamada.

**Uso no chat:** visão geral rápida sem múltiplas requisições.

---

## GET /products/{code}/structure

Estrutura (BOM) do produto — somente componentes **vigentes na data de hoje** (`G1_INI` / `G1_FIM`).

| Query | Descrição |
|---|---|
| `max_depth` | Profundidade máxima da árvore. |
| `page`, `page_size` | Paginação de itens da estrutura. |

Quantidades retornadas (`accumulated_quantity`, `G1_QUANT`) estão na base **por 1 PA**. Para PA com `B1_UM = MI` (milheiro), isso equivale a **1 MI = 1000 peças** — a API não divide por 1000; ver [`playbook-conversao-unidades-protheus.md`](../roadmaps/playbook-conversao-unidades-protheus.md).

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

Exporta estrutura em Excel. `operationId`: `get_product_structure_excel`.  
`meta.entity`: `product_structure_excel` · `meta.shape`: `document_export`.

| Query | Descrição |
|---|---|
| `format` | `json` (default) retorna envelope com path de download; `xlsx` faz streaming do arquivo. |

**Resposta (`format=json`):** envelope padrão com `data`:

```json
{
  "message": "Arquivo Excel gerado com sucesso!",
  "filename": "Estrutura_90261823.xlsx",
  "downloadPath": "/products/90261823/structure/excel?format=xlsx",
  "download_url": "/products/90261823/structure/excel?format=xlsx"
}
```

O chat usa `downloadPath` (relativo) e o MFE baixa com Bearer + blob.  
`downloadUrl` absoluto só aparece com `X-Forwarded-Host` / `X-Forwarded-Proto` públicos.

---

## GET /products/{code}/parents

Produtos “pai” que utilizam o item na estrutura (somente vínculos **vigentes hoje** em `SG1010`).

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

Dados de inspeção / qualidade do item. O escopo de produtos na árvore respeita vigência da BOM (hoje).

| Query | Descrição |
|---|---|
| `page`, `page_size` | Paginação. |
| `max_depth` | Profundidade (máx. `15`). |

---

## GET /products/{code}/guide

Roteiro de produção. A árvore de códigos para roteiro (`SG2010`) usa apenas componentes vigentes na BOM (hoje).

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

Visão consolidada (“analisador”) com múltiplas dimensões do produto em uma única chamada. Os blocos `structure`, `guide` e `inspection` aplicam vigência da BOM (hoje).

**Uso no chat:** tela de detalhe do plugin Dashboard DELPI; skill `drawing-analysis-delpi` em turnos de validação PDF × Protheus (`view=full` obrigatório).

---

## GET /products/{code}/drawing

Metadados do PDF técnico na biblioteca corporativa (FILESERVER).

| Campo em `data` | Descrição |
|-----------------|-----------|
| `filename` | Nome do arquivo resolvido |
| `revision` | Revisão extraída de `_R{NN}` no nome, se houver |
| `size_bytes` | Tamanho em bytes |
| `modified_at` | ISO-8601 UTC |

**operationId:** `get_product_drawing` · **shape:** `scalar` · **entity:** `product_drawing`

**Uso no chat:** verificar existência do desenho antes do download; a skill usa principalmente `/drawing/pdf`.

Doc completa: [14-desenhos-pdf.md](./14-desenhos-pdf.md).

---

## GET /products/{code}/drawing/pdf

Download inline do PDF (`application/pdf`). Resposta **binária** — fora do envelope JSON.

**operationId:** `get_product_drawing_pdf` · **shape:** `document_export`

**Uso no chat:** `ChatDrawingLibraryService` baixa o arquivo quando o usuário informa o código sem anexar PDF.

---

## GET /products/{code}/cost-impact-simulation

Simulador de impacto de custos do **PA** — ranking Pareto das MPs na BOM vigente e simulação percentual de reajuste (playbook [`playbook-simulador-impacto-custos-pa.md`](../roadmaps/playbook-simulador-impacto-custos-pa.md)).

| Query | Default | Descrição |
|---|---|---|
| `price_source` | `standard_cost` | `standard_cost` → `B1_CUSTD`; `last_purchase` → `B1_UPRC` |
| `adjustment_percent` | `0` | Reajuste simulado em todas as MPs (ex.: `10` = +10%) |
| `top_n` | todas | Limita ranking às N MPs de maior impacto |
| `max_depth` | `50` | Profundidade máxima da BOM |

**Restrição:** disponível apenas para produto tipo **PA** (MP retorna erro).

**Unidade:** `quantity_per_pa` e custos de materiais referem-se a **1 PA**; para PA em **MI**, 1 PA = 1 milheiro. Campo `pa_reference` documenta a base. Ver [`playbook-conversao-unidades-protheus.md`](../roadmaps/playbook-conversao-unidades-protheus.md).

**operationId:** `get_product_cost_impact_simulation` · **shape:** `composite_analysis`

**Exemplo:**

```http
GET /apps/api-delpi/products/90261255/cost-impact-simulation?adjustment_percent=10&price_source=standard_cost
```

**Uso no chat:** «quais materiais mais impactam o custo do PA …?», «simule aumento de 10% nos materiais».
