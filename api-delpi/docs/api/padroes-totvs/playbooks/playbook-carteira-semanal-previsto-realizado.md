# Playbook — carteira semanal previsto × realizado

Seção curta: [../carteira-semanal-previsto-realizado.md](../carteira-semanal-previsto-realizado.md).

## Objetivo

Documentar a implementação de referência e a homologação do conceito **weekly billing portfolio**, alinhado ao relatório operacional «Carteira Semanal / Novos Negócios» (Matriz/Filial, previsto × realizado, previsão por cliente).

## Owner e boundaries

| Camada | Responsabilidade |
|--------|------------------|
| api-delpi domain/infra TOTVS | Fórmula, SQL, contrato futuro |
| commercial-api | No máximo BFF — **não** reimplementar SC6/SD2 |
| MFE / Excel | Consumo / visualização — **não** autoridade do cálculo |

## Código de referência

| Artefato | Caminho |
|----------|---------|
| Snapshot (shape) | `app/domain/entities/commercial/weekly_portfolio.py` |
| Port | `app/domain/ports/commercial/commercial_weekly_portfolio_repository_port.py` |
| Forecast SQL | `app/infrastructure/persistence/totvs/commercial_repositories/commercial_weekly_portfolio_repository.py` |
| Segmento WEG/NB | `app/domain/services/commercial_customer_segment_service.py` |
| Realizado ROL | `app/domain/services/commercial/commercial_rol_return_sql.py` + `FinancialRepository.get_rol` |
| OTD (irmã `C6_ENTREG`) | `sales_order_otd_sql.py` / [comercial-sales-order-otd.md](../../comercial-sales-order-otd.md) |

## SQL de referência — previsto por cliente

Espelha `list_delivery_week_forecast_by_customer` (`open_only=false` → planned; `true` → open):

```sql
SELECT
    RTRIM(C5.C5_CLIENTE) AS customer_code,
    ISNULL(
        NULLIF(RTRIM(A1.A1_NREDUZ), ''),
        ISNULL(RTRIM(A1.A1_NOME), RTRIM(C5.C5_CLIENTE))
    ) AS customer_name,
    RTRIM(C6.C6_FILIAL) AS branch,
    SUM(CONVERT(FLOAT, {qty_expr} * ISNULL(C6.C6_PRCVEN, 0))) AS forecast_value
FROM SC6010 C6 WITH (NOLOCK)
INNER JOIN SC5010 C5 WITH (NOLOCK)
    ON  C5.C5_FILIAL = C6.C6_FILIAL
    AND C5.C5_NUM = C6.C6_NUM
    AND C5.D_E_L_E_T_ = ''
LEFT JOIN SA1010 A1 WITH (NOLOCK)
    ON  A1.D_E_L_E_T_ = ''
    AND A1.A1_COD = C5.C5_CLIENTE
    AND A1.A1_LOJA = C5.C5_LOJACLI
WHERE C6.D_E_L_E_T_ = ''
  AND C6.C6_QTDVEN > 0
  AND C6.C6_ENTREG IS NOT NULL
  AND RTRIM(CAST(C6.C6_ENTREG AS VARCHAR(20))) <> ''
  AND (C6.C6_BLOQUEI IS NULL OR RTRIM(C6.C6_BLOQUEI) = '')
  AND (C6.C6_BLQ IS NULL OR RTRIM(C6.C6_BLQ) = '')
  -- AND C6.C6_FILIAL = @branch
  -- AND RTRIM(C5.C5_CLIENTE) <> '000001'   -- new_business
  AND C6.C6_ENTREG >= @start_yyyymmdd
  AND C6.C6_ENTREG <= @end_yyyymmdd
GROUP BY C5.C5_CLIENTE, A1.A1_NREDUZ, A1.A1_NOME, C6.C6_FILIAL
HAVING SUM(CONVERT(FLOAT, {qty_expr} * ISNULL(C6.C6_PRCVEN, 0))) <> 0
ORDER BY forecast_value DESC, customer_code ASC
```

`{qty_expr}`:

| `quantity_basis` | Expressão |
|------------------|-----------|
| `planned` | `C6.C6_QTDVEN` |
| `open` | `(C6.C6_QTDVEN - ISNULL(C6.C6_QTDENT, 0))` (+ filtro saldo `> 0`) |

## Realizado no mesmo período

Preferir a rota/use case canônico:

```text
GET /commercial/rol/by-branch  (ou get_rol / by-customer)
  start_date / end_date = mesmo period civil
  customer_segment = new_business | weg
  branch = 01 | 02 | omitido
```

Âncora: `D2_EMISSAO` (não `C6_ENTREG`).  
Gross de NF: família billing-series (`F2_VALBRUT` / `D2_TOTAL`) — só se o contrato declarar `nature=gross`.

## Composição do snapshot

```text
previous_period.by_branch[]:
  branch, forecast_value, realized_value, variance_value

current_period_forecast[]:
  customer_code, customer_name, branch, forecast_value
```

Entity: `WeeklyPortfolioSnapshot`.

## Decisões de contrato (antes de expor rota)

| Decisão | Opções | Nota |
|---------|--------|------|
| `nature` | `order_gross` \| `rol` | Excel operacional ≈ `order_gross`; KPIs TV ≈ `rol` |
| `quantity_basis` | `planned` \| `open` | Semana corrente costuma ser `open`; histórico `planned` |
| `as_of` | live SC6 \| snapshot persistido | Sem snapshot, «previsto passado» é aproximação |
| Âncora de semana | seg→dom \| dom→sáb | Declarar no `meta`; homologação usou **seg→dom** |

Path sugerido (ainda não implementado): `GET /commercial/weekly-billing-portfolio` — identifiers em inglês.

## Homologação (set/2026) — `/system` + `/data/sql`

### Metadados (`GET /system/tables/.../columns/search`)

| Campo | Tabela | Descrição SX3 |
|-------|--------|---------------|
| `C6_ENTREG` | SC6010 | Data da Entrega |
| `C6_PRCVEN` | SC6010 | Preço Unitário Líquido |
| `C6_QTDVEN` / `C6_QTDENT` | SC6010 | Qtd vendida / entregue |
| `D2_EMISSAO` | SD2010 | Data de Emissão |

### Evidência de match com Excel histórico

O print «Carteira Semanal» **não era do mês vigente** (set/2026). Varredura jan–ago/2026:

| Valor Excel | Evidência TOTVS (SC6 live) |
|-------------|----------------------------|
| Filial previsto semana anterior **R$ 66.571,05** | **Match exato** — Wanke `000223`, semana **2026-08-10 → 2026-08-16** |
| Schulz **R$ 10.829,32** | Match — semana **2026-08-24 → 2026-08-30** |
| Pfiffner **R$ 34,29** | Match — mesma semana 24/08 |
| Menegotti **R$ 2.652,39** / G-Meyer **R$ 1.395,74** | Match em semanas de ago/2026 |

Valores pontuais do print (Franklin `48.971,72`, Wanke atual `20.550,35`, total Matriz `88.468,84`) **não** se reconstroem 1:1 no SC6 atual — esperado sem snapshot `as_of` (linhas já entregues/alteradas).

Conclusão da homologação: **a fórmula bate**; divergência de totais = snapshot histórico + drift do ERP, não regra errada.

### Como reproduzir

1. `GET /system/tables/SC6010/columns/search?q=ENTREG` (e `PRCVEN`, `QTDVEN`).
2. `POST /data/sql` com o SQL de previsto acima (whitelist: SC5/SC6/SA1).
3. Comparar realizado com `GET /commercial/rol/by-branch` no mesmo intervalo.

Permissão: `api-delpi.data` / `api-delpi.system` / `api-delpi.access.full`.

## Anti-padrões (regressão)

- Reativar FCT declarado no commercial-api sem ADR.
- Embutir `include=portfolio` de volta na composta ROL descontinuada.
- Misturar postergação de carteira ([pedido-venda-postergacao.md](../pedido-venda-postergacao.md)) com forecast semanal.
- Usar `nature=open_order_value` em billing-series (já rejeitado em teste).

## Próximo passo de produto

Expor use case + rota simples (não composta), registrar em OpenAPI / `route_contract_registry`, apontar esta seção na doc da rota — sem copiar tabelas inteiras.
