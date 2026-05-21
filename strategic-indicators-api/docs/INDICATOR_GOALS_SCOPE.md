# Metas por escopo (consolidado / filial)

**Migration:** `V016__indicator_goals_scope_branch.sql`

## Regra global

| `scope_type` do indicador | Metas permitidas |
|---------------------------|------------------|
| `consolidated` | Consolidado (`''`) + filial `01` + filial `02` (cada uma `standard` ou `monthly_curve`) |
| `per_unit` | Apenas consolidado (`''`) — metas por unidade usam indicadores separados (ex.: ROL Matriz / ROL Filial) |

Aplica-se a **todos os departamentos** (Comercial, Financeiro, Produção, etc.), não só ao Comercial.

## Tabela `indicator_goals`

- `goal_scope_branch`: `''` | `01` | `02`
- Índice único: uma meta ativa por `(indicator_id, goal_year, goal_scope_branch)`

## Resolução no painel

- API com `branch=01` ou `02` → meta da filial; fallback para consolidado se não existir
- API sem `branch` (visão **Consolidado**), departamentos com `aggregation_mode = average_of_units` (RH, Qualidade):
  - **Cada indicador:** nota = média das notas das filiais 01 e 02 (realizado da unidade × meta da unidade)
  - **IDD do departamento:** média aritmética do IDD calculado separadamente para filial 01 e filial 02
- Demais departamentos (`aggregation_mode = consolidated`):
  - Meta consolidada (`''`) quando existir; senão fallback de metas 01/02 só para listar indicadores

## Cadastro (admin)

No formulário de metas, escolher **Escopo da meta**: Consolidado, Filial 01 ou Filial 02.

`supports_branch_goals` em `department_indicators` é sincronizado automaticamente: `TRUE` quando `scope_type = consolidated`.
