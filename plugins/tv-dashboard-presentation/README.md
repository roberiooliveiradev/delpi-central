# `@delpi/tv-dashboard-presentation`

Pacote compartilhado do **motor de apresentação** Painéis TV — usado pelo plugin admin e pelo `public-hub`.

Documentação: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../../docs/12-roadmap-e-evolucao/tv-dashboard/README.md) · Indicadores live: [playbook §18](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#18-indicadores-live-api-delpi-em-slides-personalizados)

---

## Exports

```ts
import {
  usePresentationEngine,
  useFullscreenStage,
  NativeSlideView,
  formatPct,
  formatNumber,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  ComunicadoBlockView,
  ChartViewBlockView,
  TableViewBlockView,
  DataSourceBlockView,
  ConfigurableSeriesChart,
  mergeComunicadoChartOptions,
  CHART_ELEMENT_CATALOG,
  comunicadoImageCropCssProperties,
} from "@delpi/tv-dashboard-presentation";
```

| Export | Função |
|---|---|
| `usePresentationEngine` | Autoplay, transições, refresh periódico, pausa por visibilidade |
| `useFullscreenStage` | Duplo-clique → fullscreen (preview admin) |
| `NativeSlideView` | Render por `screenKey` (OEE, OTD, comunicado…) |
| `ComunicadoBlockView` | Render blocos comunicado (texto, mídia, crop, formas, dados) |
| `ChartViewBlockView` / `TableViewBlockView` | Visuais conectados a `data_source` |
| `DataSourceBlockView` | Ícone de fonte no editor (oculto no palco quando vinculado) |
| `ConfigurableSeriesChart` | Gráfico linhas/colunas com título, legenda, eixos, grade, tabela de dados |
| `CHART_ELEMENT_CATALOG` | Catálogo de elementos configuráveis (estilo Excel) |
| `comunicadoDataArchitecture` | `dataSourceId`, `shouldHideDataSourceOnStage`, helpers de vínculo |
| `comunicadoStageVisibility` | `isBlockHiddenOnStage` — render + hit-test + marquee + seleção (fonte única) |
| `parseComunicadoConfig` / `serializeComunicadoConfig` | Schema v2–v4 (`chartOptions`, `dataSourceId`, `dataBinding`, …) |
| `comunicadoImageCropCssProperties` | CSS viewport para recorte de imagem |
| `native-screens.css` | Layout viewport-fit (`tdp-*`, `tdp-series-chart*`) |

---

## Blocos de dados (Onda 4F)

| Tipo | Persistido | Runtime |
|---|---|---|
| `data_source` | `dataBinding` (operationId, params, refreshSec) | `resolved` com kpi/chart/table |
| `chart_view` | `chartType`, `chartOptions`, `dataSourceId` | `resolved` herdado da fonte |
| `table_view` | `tablePreset`, `maxRows`, `dataSourceId` | `resolved` herdado da fonte |

`chartOptions` inclui: título, legenda (posição), eixos, rótulos de dados, grade H/V, tabela de dados, marcadores, formato R$/% e cor da série.

---

## Consumidores

| App | Import |
|---|---|
| `plugins/tv-dashboard` | Preview admin — Federation `shared: react` |
| `plugins/public-hub` | Link público `/p/tv-dashboard/present/{token}` |

Resolução Vite (ambos):

```ts
"@delpi/tv-dashboard-presentation": path.resolve(__dirname, "../tv-dashboard-presentation/src/index.ts")
```

### public-hub — React único (obrigatório)

O pacote é compilado **do source** no build do `public-hub`. Sem dedupe, o Vite pode embutir **duas cópias** do React → erro `Cannot read properties of null (reading 'useState')`.

`plugins/public-hub/vite.config.ts`:

```ts
resolve: {
  dedupe: ["react", "react-dom"],
  alias: {
    react: path.resolve(__dirname, "node_modules/react"),
    "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
    // … alias do pacote
  },
},
```

Docker: `npm install` em **ambos** (`tv-dashboard-presentation` para tipos TS + `public-hub` para runtime).

---

## CSS

- Prefixo **`tdp-`** (tv-dashboard presentation)
- Gráficos: **`tdp-series-chart*`** (título, legenda, eixos, grade, tabela de dados)
- Modo kiosk público: `.tdp-stage--kiosk` dentro de `.pub-kiosk-root` (public-hub)
- Preview admin: `.tdp-stage--preview-shell`

---

## Testes

```bash
cd plugins/tv-dashboard-presentation
npm test
```

Cobertura: `usePresentationEngine`, comunicado v4, `ConfigurableSeriesChart`, `chartElementCatalog`, enrichment fixtures.

---

## Docker

Build context **`plugins/`** nos Dockerfiles de `tv-dashboard` e `public-hub` — este diretório deve estar no contexto de cópia.
