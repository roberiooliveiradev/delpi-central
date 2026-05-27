# Microfrontend — `plugins/strategic-indicators`

**Última atualização:** 2026-05-27

## Papel

Interface React (Vite + Module Federation) do painel **Indicadores Estratégicos**, carregada pelo portal MinhaDelpi.

## Manifesto

`strategic-indicators.manifest.json`:

| Campo | Valor |
|-------|-------|
| `id` | `strategic-indicators` |
| `basePath` | `/apps/strategic-indicators` |
| `backend.baseUrl` | `/apps/strategic-indicators-api/strategic-indicators` |
| `ui.renderMode` | `federated` |

Registro na Core API: `POST /core-api/admin/apps/register` — ver [registrar-plugin.md](../../docs/10-guias-operacionais/registrar-plugin.md).

## Estrutura `src/`

```text
data/
  api/                    # Clientes HTTP por rota
  api/strategicIndicatorsApiBase.ts
  cache/                  # Cache browser + chaves por competência/filial
  adapters/               # DTO API → view models
state/hooks/              # React hooks (SWR, prefetch)
ui/pages/                 # Executive, Departments, Trends, Settings…
ui/components/            # Filtros, cards, grids, erros padronizados
ui/components/StrategicIndicatorsPageError.tsx
ui/shared/indicatorValueFormatter.ts  # Formatação de meta/realizado/nota
data/errors/strategicIndicatorsError.ts
data/api/strategicIndicatorsApiErrors.ts
```

## Indicadores sem medição na UI

Quando a API retorna `has_value: false` ou `value` / `score` `null`:

- Texto padrão: **Sem dados preenchidos** (`MISSING_VALUE_LABEL` em `indicatorValueFormatter.ts`).
- Cards (`IndicatorDetailCard`), tabela analítica e resumos não tratam ausência como nota `0` nem como excelência em `lower_is_better`.
- `realized` pode trazer chaves com `null` por filial; cada unidade é formatada com o mesmo rótulo de ausência.
- Médias de departamento/unidade na UI consideram apenas indicadores com `hasValue` e `score` numérico.
- Metas e gaps multi-filial na visão consolidado: **`01: valor | 02: valor`** (código da filial, sem prefixo "Un.") — `formatBranchScopedMetric` em `indicatorValueFormatter.ts`.
- Admin de metas: escopo da meta com rótulos `01`, `02` (`getGoalScopeBranchLabel`); modo **Padrão** / **Curva** (`getGoalModeLabel`).
- Settings **Visão geral**: painel export/import JSON (`AdminConfigImportExportPanel`).
- Settings **Metas**: formulário sem valor consolidado em curva; grade redimensiona ao mudar periodicidade (`curveTargets.ts`, `goalFormValidation.ts`).

Contrato da API: [API.md](./API.md). Metas e backup: [ADMIN_GOALS_AND_CONFIG.md](./ADMIN_GOALS_AND_CONFIG.md), [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md). Cálculo: [ARCHITECTURE.md](./ARCHITECTURE.md).

## Rótulos da visão (consolidado vs filial)

O filtro global **Visão** (`StrategicIndicatorsReferenceFilters`) define se os painéis leem a API com ou sem `branch`.

| `viewMode` | Rótulo na UI | Query na API |
|------------|--------------|--------------|
| `consolidated` | **Consolidado** | sem `branch` |
| `branch` + filial `01`/`02` | **Filial 01** / **Filial 02** | `branch=01` ou `02` |

Helpers:

| Arquivo | Função |
|---------|--------|
| `ui/shared/strategicIndicatorsFilters.ts` | `getFilterViewScopeLabel`, `resolveStrategicIndicatorsBranch` |
| `ui/presentation/labels.ts` | `getGoalScopeBranchLabel` (cadastro de metas) |
| `data/departmentTreeScopes.ts` | `Filial 01` / `Filial 02` no organograma |

**Página Indicadores** (`IndicatorsPage`): cada linha recebe `viewScopeLabel` — usado na coluna **Escopo**, no subtítulo (`strategicDescription`) e repassado ao detalhe rápido.

**Valor atual / gap** (`indicatorValueFormatter.ts`): com filtro por filial, `formatIndicatorRealizedDisplay` e `formatIndicatorGapDisplay` recebem `IndicatorDisplayContext` (`filterViewScopeLabel`, `activeBranch`) para substituir o prefixo **`Consolidado:`** por **`Filial 01:`** (ou `02`) quando o payload traz a chave `consolidated` no mapa `realized`/`gaps`.

**Sem meta na filial:** a API envia `goal_label` como *Sem meta para filial XX*; classificação **Sem meta para esta visão** quando há realizado mas não há meta para o escopo (ver [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md)).

## Breakpoints de layout (SI)

Constantes compartilhadas em `ui/shared/strategicIndicatorsLayout.ts` (alinhadas ao CSS do plugin):

| Token | Largura | Uso |
|-------|---------|-----|
| `desktopCompact` | ≤1280px | Toolbar / filtros compactos |
| `tablet` | ≤1100px | Empilhamento (organograma, barra flutuante) |
| `phone` | ≤768px | Filtros em 2 colunas |
| `phoneNarrow` | ≤480px | Filtros em 1 coluna; controles de zoom em coluna |

`isSiTabletOrNarrowViewport()` — usado em `usePanZoom` para fit inicial em tablet.

## Erros padronizados (todas as páginas analíticas)

| Página | Superfície (`context.surface`) | Hook |
|--------|-------------------------------|------|
| Painel executivo | Resumo executivo | `useStrategicIndicatorsExecutiveSummary` |
| Departamentos | Departamentos | `useStrategicIndicatorsDepartments` |
| Detalhe departamento | Detalhe do departamento | `useStrategicIndicatorsDepartmentDetails` |
| Indicadores | Lista de indicadores | `useStrategicIndicators` |
| Tendências | Tendências | `useStrategicIndicatorsTrends` |
| Alertas | Lista de alertas | `useStrategicIndicatorsAlerts` |
| Apresentação | Apresentação executiva | `useStrategicIndicatorsPresentation` |

Fluxo:

1. Clientes HTTP (`strategicIndicators*Api.ts`) usam `buildStrategicIndicatorsApiError` em respostas não-OK.
2. Hooks capturam com `captureStrategicIndicatorsError` → `StrategicIndicatorsErrorView`.
3. UI renderiza `StrategicIndicatorsPageError` (modo `load` ou `refresh`).

**Modos de título:**

- Carga sem dados: `Falha em {superfície}` (ex.: *Falha em Lista de indicadores*).
- Atualização com dados antigos na tela: `mode="refresh"` → *Falha ao atualizar {superfície}*.

O card inclui causas heurísticas (plugins, schema, timeout, 502) e sugestões (migrations, refresh, testar outra filial). Admin/settings mantém alertas compactos (`InfoState` / strip) — não usam este card.

Troubleshooting backend: [OPERATIONS.md](./OPERATIONS.md).

## Rotas da UI (portal)

| Path | Página | Permissão |
|------|--------|-----------|
| `/apps/strategic-indicators` | Painel executivo | `strategic-indicators.view` |
| `.../departments` | Departamentos | `strategic-indicators.departments.view` |
| `.../indicators` | Indicadores | `strategic-indicators.indicators.view` |
| `.../trends` | Tendências | `strategic-indicators.trends.view` |
| `.../alerts` | Alertas | `strategic-indicators.alerts.view` |
| `.../presentation` | Apresentação | `strategic-indicators.presentation.view` |
| `.../settings` | Admin (visão geral, metas, departamentos) | `strategic-indicators.settings.manage` |

### Admin — metas e configuração

| Componente | Função |
|------------|--------|
| `ui/pages/SettingsPage.tsx` | Abas; export/import na visão geral |
| `ui/components/admin/AdminConfigImportExportPanel.tsx` | Download/upload do bundle |
| `ui/components/admin/IndicatorGoalForm.tsx` | Cadastro Padrão/Curva |
| `ui/components/admin/AdminGoalsWorkspace.tsx` | Ciclos anuais, duplicar ano, preencher faltantes |
| `ui/utils/goalYearHelpers.ts` | Sugestão de ano destino e origem na duplicação |
| `ui/utils/goalValuePolicy.ts` | Espelha regra de `goal_value` na UI |

Layout do settings: scroll único no container da página (sem scroll aninhado no `main`).

## Cliente HTTP

Base:

```typescript
// strategicIndicatorsApiBase.ts
export const STRATEGIC_INDICATORS_API_BASE =
  import.meta.env.VITE_STRATEGIC_INDICATORS_API_BASE?.trim() ||
  "/apps/strategic-indicators-api/strategic-indicators";
```

Todas as chamadas enviam `Authorization: Bearer <token>` via `getAccessToken` do shell.

## Performance no front (fase 4)

| Comportamento | Implementação |
|---------------|---------------|
| Stale-while-revalidate | `strategicIndicatorsReadCache` + hooks |
| Prefetch | Após executive: `prefetchStrategicIndicatorsDepartments`, `prefetchStrategicIndicatorsTrends` (6 meses) |
| Presentation split | `useStrategicIndicatorsPresentation` com `?include=`; trends em 2º request |

Detalhes: [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md).

## Filtros globais na UI

Componente `StrategicIndicatorsReferenceFilters`:

- **Mês de referência** — `competence` (`YYYY-MM`)
- **Visão** — consolidado vs por filial (`viewMode` + `branch`)
- **Meses para comparar** — em `/departments` (padrão 3 meses)

Helpers: `ui/shared/strategicIndicatorsFilters.ts`, persistência em `strategicIndicatorsFilterUrl.ts`.

## Build e deploy

```bash
npm run build
# Artefatos em dist/ → imagem delpi-strategic-indicators
```

Gateway serve:

```text
/apps/strategic-indicators/assets/remoteEntry.js
```

## Desenvolvimento

Ver [DEVELOPMENT.md](./DEVELOPMENT.md).
