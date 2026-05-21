# Indicadores Comercial (SI)

**Última atualização:** 2026-05-21  
**Migration:** `V015__restructure_commercial_indicators.sql`

## Catálogo ativo (2026)

| ID | Nome | Peso | Escopo | Meta | `source_key` | Rota / dados |
|----|------|------|--------|------|--------------|--------------|
| `commercial-rol-matrix` | ROL Matriz | 25% | por unidade | Curva mensal R$ | `commercial_head_office_rol_target` | TOTVS filial 01 |
| `commercial-rol-branch` | ROL Filial | 25% | por unidade | Curva mensal R$ | `commercial_branch_rol_target` | TOTVS filial 02 |
| `commercial-closing-rate` | Taxa de Fechamento de Negócios | 15% | consolidado | 10% | `commercial_sales_conversion_rate` | Existente |
| `commercial-sales-order-otd` | OTD de Pedidos de Venda | 15% | consolidado | 95% | `commercial_sales_order_otd` | `SC6010` + `SC5010` (`SalesOrderOtdRepository`) |
| `commercial-new-business-rol` | % ROL de Novos Negócios | 15% | consolidado | Curva mensal % | `commercial_new_business_rol_pct` | ROL não-WEG / ROL total (`NewBusinessRolPctRepository`) |

**Inativos:** `commercial-new-clients`, `commercial-new-rol` (substituído por `commercial-new-business-rol`).

Soma dos pesos no catálogo: **95%** (ajuste opcional no admin para 100%).

## Metas por escopo

Comercial usa a regra global de metas por filial — ver [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md).

## % ROL de Novos Negócios (regra)

- **ROL total:** faturamento líquido no período (mesma base do comercial: `SD2010` + TES `F4_DUPLIC = 'S'`, menos devolução, desconto e impostos).
- **ROL novos negócios:** soma do ROL de clientes **não WEG** no período (não usa “primeira OV”).
- **Cliente WEG:** `A1_COD = '000001'` ou nome/reduzido contendo `WEG` (`SA1010`).
- **%:** `new_business_rol / total_rol × 100`; `null` se `total_rol = 0`.

Validação jan/2026 consolidado: total ~3,82M, não-WEG ~456k, WEG ~3,36M → **~11,95%**.

## OTD de Pedidos de Venda (regra)

- **Unidade:** linha de pedido (`SC6010`: filial + número + item), com cabeçalho ativo em `SC5010`.
- **Período:** `C6_ENTREG` (data prevista de entrega) no intervalo consultado.
- **Considera:** linha totalmente entregue (`C6_QTDENT >= C6_QTDVEN`, `C6_QTDVEN > 0`), com `C6_DATFAT` preenchida; exclui bloqueios (`C6_BLQ`, `C6_BLOQUEI`).
- **No prazo:** `C6_DATFAT <= C6_ENTREG` (último faturamento até a data prometida).
- **%:** `linhas_no_prazo / linhas_entregues × 100`; `null` se não houver linhas no período.

Rotas HTTP (api-delpi / dashboard):

- `GET /commercial/sales-order-otd?start_date=&end_date=&branch=`
- `GET /commercial/new-business-rol-pct?start_date=&end_date=&branch=`

## Deploy

Após publicar: `run_migrations.py up` (se pendente) e `refresh_period_scores.py`.

## Planilha do usuário

A segunda linha “ROL Matriz” na planilha foi interpretada como **ROL Filial** (25% + 25%), alinhado ao modelo anterior (filiais 01/02).
