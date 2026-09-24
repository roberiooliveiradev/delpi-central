# Carteira semanal — previsto × realizado

Convenção Delpi para **receita prevista** (carteira de pedidos) versus **receita realizada** (faturamento), no estilo do relatório operacional «Carteira Semanal / Novos Negócios».

Nome de domínio: **weekly billing portfolio**.  
Família HTTP: **`/commercial/billing-portfolio/*`** — ver [commercial-billing-portfolio.md](../commercial-billing-portfolio.md).

## Conceito

```text
previsto  = valor de pedido cuja entrega prometida cai no período
realizado = valor faturado cuja emissão de NF cai no mesmo período
```

Não é meta comercial digitada. Não é projeção estatística. Não é programação PCP/OP.

| Papel | Tabelas | Data-base | Valor |
|-------|---------|-----------|--------|
| **Previsto (forecast)** | SC5 + SC6 (+ SA1) | `C6_ENTREG` | `qtd × C6_PRCVEN` (bruto de pedido) |
| **Realizado (realized)** | SD2 (− SD1) / SF2 | `D2_EMISSAO` | gross NF **ou** ROL líquido |

**Invariante:** não misturar as âncoras de data. Previsto usa entrega prometida; realizado usa emissão fiscal. A mesma família de data (`C6_ENTREG`) alimenta o OTD — ver [comercial-sales-order-otd.md](../comercial-sales-order-otd.md).

## Vocabulário

| Termo | Significado Delpi |
|-------|-------------------|
| `forecast` / previsto | Soma das linhas SC6 com `C6_ENTREG` no período |
| `realized` / realizado | Faturamento no período (`D2_EMISSAO`) |
| `variance` | `realized − forecast` (mesmos filtros) |
| `quantity_basis=planned` | `C6_QTDVEN × C6_PRCVEN` (default HTTP) |
| `quantity_basis=open` | `(C6_QTDVEN − C6_QTDENT) × C6_PRCVEN` (saldo em aberto) |
| `nature=order_gross` | Valor bruto de pedido / NF (default HTTP; Excel operacional) |
| `nature=rol` | Receita operacional líquida canônica — ver `CommercialRolReturnSql` |
| `customer_segment=new_business` | Clientes ≠ WEG (`000001`) |
| `customer_segment=weg` | Cliente WEG |
| Filial `01` / `02` | Matriz (Jaraguá) / Filial (ES) — [filiais.md](./filiais.md) |

## Família HTTP (viva)

```text
GET /commercial/billing-portfolio/summary
GET /commercial/billing-portfolio/series
GET /commercial/billing-portfolio/by-customer
GET /commercial/billing-portfolio/by-branch
```

| operationId | Shape |
|-------------|-------|
| `get_billing_portfolio_summary` | scalar |
| `get_billing_portfolio_series` | scalar |
| `get_billing_portfolio_by_customer` | paged_list |
| `get_billing_portfolio_by_branch` | paged_list |

Contrato sempre inclui `forecast_value`, `realized_value`, `variance_value`, `nature`, `quantity_basis`, âncoras de data e `as_of=live`.  
Uma família cobre comparativo e «só previsão» (consumidor ignora `realized_*` se quiser).  
**Não** há rota composta nem `include=portfolio` em `/rol/*`.

Permissão: `KPI_COMMERCIAL_ACCESS`. Semana via `build_period_buckets` (seg→dom).

## Fórmula de previsto

```text
forecast(period, branch?, segment?, quantity_basis?) =
  Σ line_value(SC6)
  where
    C6_ENTREG ∈ period
    C6_QTDVEN > 0
    linha não deletada
    sem bloqueio (C6_BLOQUEI / C6_BLQ vazios)
    filtros opcionais de filial / segmento / carteira
```

## O que fazer

- Tratar previsto e realizado como **duas métricas** com datas declaradas no contrato/`data`.
- Reusar `CommercialCustomerSegmentService` para WEG / novos negócios.
- Reusar ROL canônico (`CommercialRolReturnSql` / `FinancialRepository.get_rol`) para realizado líquido (`nature=rol`); `gross_revenue` do mesmo payload para `nature=order_gross`.
- Declarar `nature` e `quantity_basis` no contrato antes de comparar números.
- Owner da regra TOTVS: **api-delpi** (commercial). BFF/MFE só consome.

## O que NÃO fazer

- Derivar previsto a partir do realizado («semana passada faturada = previsto»).
- Comparar `C6_PRCVEN` bruto com ROL sem declarar `nature`.
- Usar data de OP / alocação estoque / PCP como previsão comercial.
- Hardcodar clientes do Excel (Buhler, Wanke, …) — o Excel é um caso da classe.
- Assumir que «previsto da semana passada» no SC6 live é auditável: sem snapshot `as_of`, o ERP já pode ter entregue/alterado linhas.
- Inventar tabela FCT / meta digitada sem decisão de produto (FCT Postgres foi dropada).
- Colocar a regra no commercial-api ou no MFE.
- Reativar composta ROL / `include=portfolio`.
- Alterar contratos de `/commercial/rol/*` para embutir forecast.

## Estado no código

| Artefato | Estado |
|----------|--------|
| Entity HTTP (`BillingPortfolio*`) + `WeeklyPortfolioCustomerForecast` | Vivo — `weekly_portfolio.py` |
| `WeeklyPortfolioSnapshot` | Shape de relatório Excel — **não** body HTTP |
| `CommercialWeeklyPortfolioRepository` | Forecast agregados + lista por cliente |
| Família `/commercial/billing-portfolio/*` | **Viva** (summary / series / by-customer / by-branch) |
| Realizado ROL isolado | Intacta — `/commercial/rol/*` |

Detalhe SQL, homologação e composição: [playbook-carteira-semanal-previsto-realizado.md](./playbooks/playbook-carteira-semanal-previsto-realizado.md).  
Contrato de rota: [commercial-billing-portfolio.md](../commercial-billing-portfolio.md).

## Relacionados

- Doc de rota: [commercial-billing-portfolio.md](../commercial-billing-portfolio.md)
- ROL / rotas comerciais: [commercial-analysis-routes.md](../commercial-analysis-routes.md)
- OTD (`C6_ENTREG`): [comercial-sales-order-otd.md](../comercial-sales-order-otd.md)
- Postergação de carteira (outro conceito): [pedido-venda-postergacao.md](./pedido-venda-postergacao.md)
- Mercado CFOP no ROL: [rol-mercado-cfop.md](./rol-mercado-cfop.md)
- Cliente / nome reduzido: [cadastro-cliente.md](./cadastro-cliente.md)
