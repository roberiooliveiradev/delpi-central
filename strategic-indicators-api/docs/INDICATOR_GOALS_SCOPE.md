# Metas por escopo (consolidado / filial)

**Migrations:** `V016` (coluna e índice), `V017` (supports_branch_goals), `V018`/`V019` (seeds RH/Qualidade), `V020` (agregação consolidada)

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

- API com `branch=01` ou `02` → meta **somente** da filial (`goal_scope_branch` igual à visão); **sem** fallback para consolidado
- Indicador com medição consolidada (ex.: Engenharia, `aggregation_mode = consolidated`, sem `branch_goals`): filtro por filial mantém **valor consolidado**; meta exibe *Sem meta para filial XX* se não houver meta cadastrada para aquela filial
- RH/Qualidade (`average_of_units` ou `branch_goals` preenchido): filtro por filial usa realizado e meta da unidade `01`/`02`
- API sem `branch` (visão **Consolidado**), departamentos com `aggregation_mode = average_of_units` (RH, Qualidade):
  - **Cada indicador:** nota = média das notas das filiais 01 e 02 (realizado da unidade × meta da unidade)
  - **IDD do departamento:** média aritmética do IDD calculado separadamente para filial 01 e filial 02
- Demais departamentos (`aggregation_mode = consolidated`):
  - Meta consolidada (`''`) quando existir; senão fallback de metas 01/02 só para listar indicadores

## Cadastro (admin)

No formulário de metas, escolher **Escopo da meta**: Consolidado, Filial 01 ou Filial 02.

`supports_branch_goals` em `department_indicators` é sincronizado automaticamente: `TRUE` quando `scope_type = consolidated`.

## Implementação (`postgres_indicator_goals_repository`)

- `list_resolved_goals_map` / `list_latest_active_goals_map`: filtram por `goal_scope_branch` e vigência (`valid_from` / `valid_to` no último dia da competência).
- Com `branch=01` ou `02`, o `ORDER BY` prioriza a meta da filial (`CASE WHEN goal_scope_branch = %s`).
- **Importante:** os parâmetros do `CASE` no `ORDER BY` devem ser enviados **depois** dos parâmetros de vigência no array Python — ordem incorreta gerava `operator does not exist: character varying = date` (corrigido em `cbc91c5`).

## Materialização (`period_scores`)

O refresh (`scripts/refresh_period_scores.py`) grava uma linha por combinação:

| `scope_branch` | Significado |
|----------------|-------------|
| `''` | Visão consolidado |
| `01` | Filial 01 |
| `02` | Filial 02 |

Após deploy com metas por filial, rode o refresh manualmente se o job periódico ainda não tiver preenchido `01`/`02` para a competência desejada.

## UI (MFE)

Rótulos de filial na meta, realizado e gap: `01: valor | 02: valor` (sem prefixo "Un."). Ver [MFE.md](./MFE.md).
