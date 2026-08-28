# OTD de pedidos de venda — `/commercial/sales-order-otd`

**Última atualização:** 2026-08-13  
**Operação OpenAPI:** `get_sales_order_otd` (+ `…/panel`, `…/series`, `…/lines/{…}`)  
**Repositório:** `app/infrastructure/persistence/totvs/commercial_repositories/sales_order_otd_repository.py`  
**SQL:** `sales_order_otd_sql.py`

## Objetivo

Calcular o percentual de linhas de pedido de venda (SC6) atendidas no prazo em relação à data prometida (`C6_ENTREG`), considerando **linhas faturadas e não faturadas**.

## Endpoint

```http
GET /commercial/sales-order-otd?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&branch=02&customer_segment=weg
GET /commercial/sales-order-otd/panel?...&status=late&page=1&page_size=20&sort_by=promised_date&sort_dir=desc&search=WEG
GET /commercial/sales-order-otd/series?granularity=month&start_date=...&end_date=...
GET /commercial/sales-order-otd/lines/{branch}/{order_number}/{line_item}
```

| Parâmetro | Descrição |
|-----------|-----------|
| `start_date` / `end_date` | Filtra linhas pela **data prometida** (`C6_ENTREG`). |
| `branch` | Filial TOTVS (`01`, `02`, …). |
| `customer_segment` | `weg` (cliente `000001`) ou `new_business` (demais clientes). |
| `status` (panel) | `on_time` \| `late` (opcional). |
| `search` (panel) | Busca em pedido, cliente (código/nome), produto (código/descrição). |
| `page` / `page_size` | Paginação server-side (default page_size 20, máx. 1000). |
| `sort_by` / `sort_dir` | Ordenação server-side (ver OpenAPI / DTO panel). |

## Fonte TOTVS

| Tabela | Papel |
|--------|-------|
| `SC6010` (C6) | Itens do pedido de venda |
| `SC5010` (C5) | Cabeçalho do pedido (cliente, segmento) |
| `SA1010` (A1) | Cliente — `A1_NOME`, `A1_NREDUZ` (nome reduzido) |
| `SB1010` (B1) | Produto — fallback de UM (`B1_UM`) e descrição |

Leitura analítica com `WITH (NOLOCK)`.

## Unidade de medida (`unit`)

| Superfície | Comportamento |
|------------|---------------|
| Painel / detalhe / insights de linha | Sempre expõe `unit` por linha |
| Fonte | `COALESCE(NULLIF(RTRIM(C6_UM), ''), RTRIM(B1_UM), '')` — UM da **linha** do pedido; cadastro só como fallback |
| Agregações (série, por cliente, etc.) | `unit` só se todas as linhas do bucket tiverem a mesma UM; senão `unit: null` e `mixed_units: true` |
| Conversão MI→peça / `B1_CONV` | **Não** — qty permanece na UM nativa (ver `padroes-totvs/unidades-medida.md`) |

## Linhas elegíveis (denominador)

Entram linhas que atendem **todos** os critérios:

| Regra | Campo |
|-------|-------|
| Registro ativo | `C6.D_E_L_E_T_ = ''` e `C5.D_E_L_E_T_ = ''` |
| Quantidade vendida | `C6_QTDVEN > 0` |
| Data prometida preenchida | `C6_ENTREG` não nula/vazia |
| Sem bloqueio | `C6_BLOQUEI` e `C6_BLQ` vazios |
| Período | `C6_ENTREG` entre `start_date` e `end_date` |
| Filial / segmento | Quando informados na query |

**Não exige** faturamento (`C6_DATFAT`) nem entrega total (`C6_QTDENT >= C6_QTDVEN`).

## Classificação no prazo vs. atrasado

| Situação | Regra |
|----------|-------|
| **Faturada** (`C6_DATFAT` preenchida) | **No prazo** se `C6_DATFAT <= C6_ENTREG`; **atrasada** se `C6_DATFAT > C6_ENTREG`. |
| **Não faturada** | **No prazo** se a data de referência `<= C6_ENTREG`; **atrasada** se a data de referência `> C6_ENTREG`. |

**Data de referência** para linhas não faturadas: `end_date` da requisição; se omitida, `GETDATE()` (data corrente no SQL Server).

## Resposta (`data`)

| Campo | Descrição |
|-------|-----------|
| `total_lines` | Total de linhas elegíveis |
| `on_time_lines` | Linhas no prazo |
| `late_lines` | Linhas atrasadas |
| `sales_order_otd_pct` | `on_time_lines / total_lines × 100` (2 casas decimais) |

Painel (`/panel`) — `summary` + `insights` + `lines` paginado:

| Bloco | Campos |
|-------|--------|
| `summary` | KPI (`total_lines`, `on_time_lines`, `late_lines`, `sales_order_otd_pct`, `late_percentage`) + `avg_late_days`, `p50_late_days`, `p90_late_days` (só late) |
| `insights.recurringCustomers` | Top 10 clientes com ≥2 linhas late (`customer_code`, `customer_store`, `customer_name`, `customer_short_name`, `late_count`, `total_late_days`) |
| `insights.worstDelays` | Top 10 linhas late por `days_diff` DESC |
| `insights.upcomingPromises` | Top 10 linhas abertas por `promised_date` ASC |
| `lines` | Página de itens (incl. `days_diff`, promessa, fatura, qtds) |

Painel — campos de linha relevantes:

| Campo | Fonte |
|-------|--------|
| `customer_code` | `C5.C5_CLIENTE` |
| `customer_store` | `C5.C5_LOJACLI` (loja do cliente) |
| `customer_name` | Preferência `SA1.A1_NREDUZ`; se vazio, `SA1.A1_NOME` |
| `customer_short_name` | `SA1.A1_NREDUZ` (nome reduzido do **cliente**) |
| `unit` | `C6.C6_UM` com fallback `B1.B1_UM` (sem conversão) |
| `days_diff` | Dias entre promessa e fatura (ou data de referência se aberta) |

Metas do Indicadores Estratégicos: `source_key` = `commercial_sales_order_otd`.

## Consumidores

- Portal Comercial (`plugins/commercial` → commercial-api BFF `/analytics/sales-order-otd*`)
- Dashboard Comercial (`plugins/dashboard-commercial`) — KPI na home + painel `/apps/dashboard-commercial/otd`
- Strategic Indicators API (`commercial-sales-order-otd`)
- Chat / agente (`get_sales_order_otd`)
- TV Dashboard — overlay `get_sales_order_otd_panel` (coluna Unidade)

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-08-28 | Painel/detalhe/insights: campo `unit` (`C6_UM` / fallback `B1_UM`); agregações com `mixed_units` quando UM não homogênea. |
| 2026-08-13 | Panel: `customer_store` (loja) nas linhas e reincidência agrupada por código+loja. |
| 2026-08-13 | Panel: `search`, stats de atraso, insights (recorrência + top 10 atrasos/promessas); BFF commercial-api encaminha page/sort/status/search. |
| 2026-07-09 | Passa a incluir linhas **não faturadas**; atraso de abertas medido por `end_date` vs. `C6_ENTREG`. |
| Anterior | Considerava apenas linhas faturadas e totalmente entregues. |
