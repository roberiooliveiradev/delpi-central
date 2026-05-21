# Indicadores Comercial (SI)

**Última atualização:** 2026-05-21  
**Migration:** `V015__restructure_commercial_indicators.sql`

## Catálogo ativo (2026)

| ID | Nome | Peso | Escopo | Meta | `source_key` | Rota / dados |
|----|------|------|--------|------|--------------|--------------|
| `commercial-rol-matrix` | ROL Matriz | 25% | por unidade | Curva mensal R$ | `commercial_head_office_rol_target` | TOTVS filial 01 |
| `commercial-rol-branch` | ROL Filial | 25% | por unidade | Curva mensal R$ | `commercial_branch_rol_target` | TOTVS filial 02 |
| `commercial-closing-rate` | Taxa de Fechamento de Negócios | 15% | consolidado | 10% | `commercial_sales_conversion_rate` | Existente |
| `commercial-sales-order-otd` | OTD de Pedidos de Venda | 15% | consolidado | 95% | `commercial_sales_order_otd` | **A criar** — snapshot retorna `null` |
| `commercial-new-business-rol` | % ROL de Novos Negócios | 15% | consolidado | Curva mensal % | `commercial_new_business_rol_pct` | **A criar** — hoje usa query legada `new_clients_rol_pct` |

**Inativos:** `commercial-new-clients`, `commercial-new-rol` (substituído por `commercial-new-business-rol`).

Soma dos pesos no catálogo: **95%** (ajuste opcional no admin para 100%).

## Próximos passos (rotas TOTVS)

1. `GET` OTD pedidos de venda → preencher `sales_order_otd_pct` no `CommercialMetricsSnapshotService`.
2. `GET` % ROL novos negócios (definição de negócio + SQL) → substituir uso provisório de `GetNewClientsRolPctUseCase`.
3. Após deploy: `python scripts/run_migrations.py up` e `refresh_period_scores.py`.

## Planilha do usuário

A segunda linha “ROL Matriz” na planilha foi interpretada como **ROL Filial** (25% + 25%), alinhado ao modelo anterior (filiais 01/02).
