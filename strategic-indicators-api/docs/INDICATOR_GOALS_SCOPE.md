# Metas por escopo (consolidado / filial)

**Última atualização:** 2026-05-21

**Migrations:** `V016` (coluna e índice), `V017` (supports_branch_goals), `V018`/`V019` (seeds RH/Qualidade), `V020` (agregação consolidada), `V021` (metas por filial em `per_unit`)

## Regra global

| `scope_type` do indicador | Metas permitidas |
|---------------------------|------------------|
| `consolidated` | Consolidado (`''`) + filial `01` + filial `02` |
| `per_unit` | Consolidado (`''`) + filial `01` + filial `02` (realizado por unidade; meta por filial na mesma estrutura) |

Indicadores separados por unidade (ex.: ROL Matriz / ROL Filial no Comercial) continuam válidos quando cada unidade precisa de **fonte de dado** distinta, não apenas meta distinta.

**Migration V021 (Produção):** metas consolidadas ativas de indicadores `per_unit` do departamento Produção são desativadas e recriadas em duplicata para `goal_scope_branch` `01` e `02` (mesmo `goal_label`, valor e curva mensal). Ajuste valores por filial depois no admin, se necessário.

**Migration V023 (Suprimentos):** mesma lógica para metas 2026 dos indicadores **ativos** de Suprimentos (`supplies-cpv`, `supplies-otd`, `supplies-stock-turnover`, `supplies-stock-value`). Indicador inativo (`supplies-negotiation-savings`) não entra. Requer V022 (`average_of_units`).

Aplica-se a **todos os departamentos** (Comercial, Financeiro, Produção, etc.), não só ao Comercial.

## Tabela `indicator_goals`

- `goal_scope_branch`: `''` | `01` | `02`
- Índice único: uma meta ativa por `(indicator_id, goal_year, goal_scope_branch)`

## Resolução no painel

### Query `branch=01` ou `02` (visão por filial)

| Situação | Meta | Realizado | Nota |
|----------|------|-----------|------|
| Meta cadastrada com `goal_scope_branch` = filial da visão | Meta da filial | Conforme tabela abaixo | Calculada |
| Sem meta para a filial (só consolidado `''`) | `goal_label`: **Sem meta para filial XX** | Conforme tabela abaixo | `null` — classificação **Sem meta para esta visão** |
| Engenharia, Financeiro, Produção, etc. (`aggregation_mode = consolidated`, sem `branch_goals`) | Sem meta para filial (se não cadastrada) | **Valor consolidado** (`measurement.value`) | Sem meta → nota `null` |
| RH, Qualidade (`average_of_units` ou `branch_goals` na competência) | Meta da filial | Realizado da unidade `01`/`02` | Calculada |

Regras de implementação (`goal_scope.py`, `StrategicIndicatorsCalculator`):

- SQL: `list_resolved_goals_map` com `branch` ativo usa `goal_scope_branch = %s` (**sem** `IN ('', %s)`).
- Realizado por filial só quando `indicator_uses_branch_unit_measurement` (metas por unidade preenchidas ou meta resolvida para aquela filial).
- Catálogo: indicadores sem meta na filial continuam listados (`_catalog_item_missing_goal_for_branch_view`).

### Sem `branch` (visão Consolidado)

- Departamentos `average_of_units` (RH, Qualidade, Produção, Suprimentos):
  - **Cada indicador:** nota = média das notas das filiais 01 e 02 (realizado da unidade × meta da unidade)
  - **IDD do departamento:** média aritmética do IDD calculado separadamente para filial 01 e filial 02
- Demais departamentos (`aggregation_mode = consolidated`):
  - Meta consolidada (`goal_scope_branch = ''`) quando existir
  - Se não houver meta consolidada mas existirem metas `01`/`02`, o catálogo monta `branch_goals` para exibição agregada na visão consolidado

## Cadastro (admin)

No formulário de metas, escolher **Escopo da meta**: Consolidado, Filial 01 ou Filial 02.

`supports_branch_goals` em `department_indicators` é sincronizado automaticamente: `TRUE` quando `scope_type` é `consolidated` ou `per_unit`.

## Implementação (`postgres_indicator_goals_repository`)

- `list_resolved_goals_map` / `list_latest_active_goals_map`: filtram por `goal_scope_branch` e vigência (`valid_from` / `valid_to` no último dia da competência).
- Com `branch=01` ou `02`: filtro estrito `goal_scope_branch = %s` (`uses_strict_branch_goal_resolution`).
- Visão consolidado (`branch` vazio): apenas metas com `goal_scope_branch = ''`.
- **Histórico:** versões antigas usavam `IN (%s, '')` + `ORDER BY CASE` (fallback para meta consolidada na filial). Removido para alinhar ao comportamento acima.
- **Importante:** quando o `CASE` no `ORDER BY` era usado, os parâmetros deviam vir **depois** dos de vigência — bug `character varying = date` (corrigido em `cbc91c5`).

## Materialização (`period_scores`)

O refresh (`scripts/refresh_period_scores.py`) grava uma linha por combinação:

| `scope_branch` | Significado |
|----------------|-------------|
| `''` | Visão consolidado |
| `01` | Filial 01 |
| `02` | Filial 02 |

Após deploy com metas por filial, rode o refresh manualmente se o job periódico ainda não tiver preenchido `01`/`02` para a competência desejada.

Se o catálogo/metas mudarem (ex.: V021 desativa meta consolidada e cria metas `01`/`02`), a API **invalida** `period_scores` cujo `catalog_inputs_hash` não bate com o catálogo atual e recalcula na próxima leitura. Se o organograma ainda mostrar *Nenhum indicador neste escopo* em Produção, execute `scripts/refresh_period_scores.py` para a competência.

## UI (MFE)

| Contexto | Rótulo exibido |
|----------|----------------|
| Filtro **Consolidado** | `Consolidado` (`getFilterViewScopeLabel`) |
| Filtro **Por filial** (01/02) | `Filial 01`, `Filial 02` — coluna Escopo, leitura estratégica, prefixo de valor/gap |
| Visão consolidado, várias filiais no `realized` | `01: valor \| 02: valor` (`formatBranchScopedMetric`) |
| Admin — escopo da meta | `01`, `02` (`getGoalScopeBranchLabel`) |

Detalhes: [MFE.md](./MFE.md) — seção *Rótulos da visão*.

## Metas `monthly_curve` (Comercial)

- Meta comparável do período = soma dos `indicator_goal_monthly_targets` do mês da competência.
- Se a curva não vier no catálogo (lista vazia) e `goal_value > 0`, o calculador usa **fallback** para meta padrão do período (evita IDD/nota `0` indevidos).
- Medições da Produção com valor `null` na fonte permanecem **sem dado** (não viram `0.0` artificial).
- Depois de deploy com correção no calculador, execute `scripts/refresh_period_scores.py` para atualizar `period_scores` que ainda guardam IDD zerado.
