# Carteira semanal — previsto × realizado

Convenção Delpi para **receita prevista** (carteira de pedidos) versus **receita realizada** (faturamento), no estilo do relatório operacional «Carteira Semanal / Novos Negócios».

Nome de domínio: **weekly billing portfolio**.

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
| `quantity_basis=planned` | `C6_QTDVEN × C6_PRCVEN` |
| `quantity_basis=open` | `(C6_QTDVEN − C6_QTDENT) × C6_PRCVEN` (saldo em aberto) |
| `nature=order_gross` | Valor bruto de pedido (padrão do Excel operacional) |
| `nature=rol` | Receita operacional líquida canônica — ver `CommercialRolReturnSql` |
| `customer_segment=new_business` | Clientes ≠ WEG (`000001`) |
| `customer_segment=weg` | Cliente WEG |
| Filial `01` / `02` | Matriz (Jaraguá) / Filial (ES) — [filiais.md](./filiais.md) |

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

- Tratar previsto e realizado como **duas métricas** com datas declaradas no contrato/`meta`.
- Reusar `CommercialCustomerSegmentService` para WEG / novos negócios.
- Reusar ROL canônico (`CommercialRolReturnSql` / `FinancialRepository.get_rol`) para realizado líquido.
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

## Estado no código (set/2026)

| Artefato | Estado |
|----------|--------|
| Entity `WeeklyPortfolioSnapshot` | Existe — shape do relatório |
| `CommercialWeeklyPortfolioRepository.list_delivery_week_forecast_by_customer` | SQL de forecast pronto |
| Use case / rota HTTP | **Ainda não expostos** (bloco `portfolio` fora das compostas ROL) |
| Realizado ROL / billing-series | Vivo (`/commercial/rol/*`, carteira billing-series) |

Detalhe SQL, homologação e composição: [playbook-carteira-semanal-previsto-realizado.md](./playbooks/playbook-carteira-semanal-previsto-realizado.md).

## Relacionados

- ROL / rotas comerciais: [commercial-analysis-routes.md](../commercial-analysis-routes.md)
- OTD (`C6_ENTREG`): [comercial-sales-order-otd.md](../comercial-sales-order-otd.md)
- Postergação de carteira (outro conceito): [pedido-venda-postergacao.md](./pedido-venda-postergacao.md)
- Mercado CFOP no ROL: [rol-mercado-cfop.md](./rol-mercado-cfop.md)
- Cliente / nome reduzido: [cadastro-cliente.md](./cadastro-cliente.md)
