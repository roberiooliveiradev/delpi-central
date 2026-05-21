# Microfrontend — `plugins/strategic-indicators`

**Última atualização:** 2026-05-21

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
ui/components/            # Filtros, cards, grids
ui/shared/indicatorValueFormatter.ts  # Formatação de meta/realizado/nota
```

## Indicadores sem medição na UI

Quando a API retorna `has_value: false` ou `value` / `score` `null`:

- Texto padrão: **Sem dados preenchidos** (`MISSING_VALUE_LABEL` em `indicatorValueFormatter.ts`).
- Cards (`IndicatorDetailCard`), tabela analítica e resumos não tratam ausência como nota `0` nem como excelência em `lower_is_better`.
- `realized` pode trazer chaves com `null` por filial; cada unidade é formatada com o mesmo rótulo de ausência.
- Médias de departamento/unidade na UI consideram apenas indicadores com `hasValue` e `score` numérico.

Contrato da API: [API.md](./API.md) e regras de cálculo: [ARCHITECTURE.md](./ARCHITECTURE.md).

## Rotas da UI (portal)

| Path | Página | Permissão |
|------|--------|-----------|
| `/apps/strategic-indicators` | Painel executivo | `strategic-indicators.view` |
| `.../departments` | Departamentos | `strategic-indicators.departments.view` |
| `.../indicators` | Indicadores | `strategic-indicators.indicators.view` |
| `.../trends` | Tendências | `strategic-indicators.trends.view` |
| `.../alerts` | Alertas | `strategic-indicators.alerts.view` |
| `.../presentation` | Apresentação | `strategic-indicators.presentation.view` |
| `.../settings` | Admin | `strategic-indicators.settings.manage` |

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
- **Visão** — consolidado vs filial (`branch`)

Helpers: `ui/shared/strategicIndicatorsFilters.ts`.

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
