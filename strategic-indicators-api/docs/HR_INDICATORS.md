# Indicadores RH — Integração SI + Portal RH

## Catálogo (após V019)

| ID | Nome | Peso | Unidade | Meta 2026 Filial 01 | Meta 2026 Filial 02 |
|----|------|------|---------|----------------------|----------------------|
| `hr-absenteeism` | Absenteísmo | 25% | % | 3% | 2% |
| `hr-turnover` | Turnover | 25% | % | 5% | 4,5% |
| `hr-satisfaction` | Satisfação Interna | 20% | % | 80% | 80% |
| `hr-pdi` | Número de PDI's Ativos | 10% | contagem | 15 | 8 |
| `hr-performance-reviews` | % Avaliações Desempenho Concluídas | 10% | % | 90% | 90% |
| `hr-training-hours` | Horas Treinamento / Colaborador | 10% | horas/mês | 2 | 2 |

Metas usam `goal_scope_branch` (`01`, `02`). O departamento permanece `consolidated`; o score por filial usa a meta do escopo correspondente.

Na visão **Consolidado** (`aggregation_mode = average_of_units`):

- Nota de cada indicador = média das notas das filiais 01 e 02.
- **Nota IDD do RH** = média entre o IDD da filial 01 e o IDD da filial 02.

## Fontes Portal RH (`indicators_indicator.code`)

| Indicador SI | Código Portal | Realizado |
|--------------|---------------|-----------|
| `hr-pdi` | `PDI_ATV` | Soma de `actual_value` (PDIs ativos) no período |
| `hr-performance-reviews` | `AVA_DES` | `(SUM concluídas / SUM meta) * 100` |
| Demais | `ABS_*`, `TUR_*`, `TRN_*`, `SAT_INT` | Média/agregação existente no snapshot |

Se `AVA_DES` não existir no Portal RH, o indicador não entra no snapshot SI até o cadastro no banco.

## API Delpi (`/hr`)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/hr/snapshot` | Snapshot completo (inclui `active_pdi_count` e `performance_reviews_completion_pct`) |
| GET | `/hr/active-pdi-count` | Contagem de PDIs ativos por filial |
| GET | `/hr/performance-reviews-completion` | % de avaliações concluídas por filial |
| GET | `/hr/branches` | Filiais ativas |

Parâmetros opcionais: `branch`, `start_date`, `end_date` (formato Portal RH, ex. `DD-MM-YYYY`).

## Strategic Indicators API

O provider `hr_indicators_snapshot_provider` alimenta medições reais para o cálculo de scores:

- **PDI:** valor consolidado = soma das filiais (contagem).
- **Avaliações:** valor consolidado = média das filiais (%).

Após deploy, executar `refresh_period_scores.py` para o departamento `hr`.
