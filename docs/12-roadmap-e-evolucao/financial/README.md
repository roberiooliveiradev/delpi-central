# Portal Financeiro — spec e absorção dos plugins legados

> **Status:** P0 entregue (`plugins/financial` + `financial-api`)  
> **Fora do P0:** orçamento, contas a pagar / fluxo de caixa, desativação dos plugins legados

## Resultado

Um MFE federado com rail de subplugins e um BFF próprio, no mesmo padrão do Portal PCP. O BFF reusa os contratos já existentes da api-delpi e lê IDD/IGD no strategic-indicators-api. Nenhuma rota da api-delpi foi alterada.

## Matriz de absorção (legado → portal)

| Plugin legado | Continua no P0? | Superfície no Portal Financeiro | Observação |
|---|---|---|---|
| `dashboard-financial` | Sim | Gestão à vista (`/apps/financial`) | ROL, EBITDA, custo fixo, PMR + IDD |
| `financeiro-inadimplencia` | Sim | Inadimplência (`/apps/financial/delinquency`) | Mesmos paths `/financeiro/inadimplencia/*` |
| `financeiro-centro-custo` | Sim | Despesas por CC (`/apps/financial/cost-centers`) | Mesmos paths `/financeiro/despesas-centro-custo/*` |
| `planejamento-orcamentario` | Fora | Rail `budget` (`coming_soon`) | Permanece no plugin próprio |
| Contas a pagar / fluxo de caixa | Fora | Rail `cash-flow` (`coming_soon`) | Exigiria rotas novas na api-delpi |

Desativar os três plugins legados é decisão operacional futura — o portal não os remove nem altera permissões antigas.

## Gate de filial

| Consulta | Permissão |
|---|---|
| `branch=01` | `financial.view.filial-01` |
| `branch=02` | `financial.view.filial-02` |
| Consolidado / inadimplência | as duas |

## Fontes

- api-delpi: `/financeiro/inadimplencia/*`, `/financeiro/despesas-centro-custo/*`, `/financial/{rol,ebitda_pct,fixed_cost_pct,pmr}`
- strategic-indicators-api: `/integrations/dashboard-department-indicators?department_id=financial`
