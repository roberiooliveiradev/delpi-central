# Pedido de venda — postergação vs disponível

A view de pedidos em aberto **não traz** campo TOTVS de «data original × data vigente» nem flag de postergação (SC6).

## Heurística do Portal Comercial (ago/2026)

Classificação no **commercial-api** (`OpenOrderAvailabilityClassificationService`), reusando os buckets de `KPI-CARTEIRA-HORIZON` (`data_entrega`, TZ `America/Sao_Paulo`):

| `availability` | Buckets | Significado operacional |
|----------------|---------|-------------------------|
| `available` | `overdue` + `current_month` | Precisa de ação neste mês (atrasado ou prometido no mês) |
| `postponed` | `next_1_3_months` + `later` | Entrega prometida **após** o mês corrente |
| `undated` | `undated` | Sem `data_entrega` |

Deep link: `/open-orders?postponed=1`.

## O que **não** fazer

- Inventar SQL de postergação em SC5/SC6 sem coluna homologada.
- Tratar programação PCP/OP como «postergado comercial».
- Somar carteira postergada com ROL.

## Quando enriquecer

Se a Delpi passar a gravar data original de entrega, substituir a heurística por campo real e atualizar este arquivo + testes do BFF.
