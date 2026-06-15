# Estrutura de pastas — Dashboard LMPs

```text
plugins/dashboard-lmps/
├── README.md
├── dash-lmps-microfrontend.manifest.json   # registro Core API
├── package.json
├── vite.config.ts                          # federation: dashboard-lmps
├── Dockerfile                              # build Vite + nginx
├── docs/
│   ├── DOCUMENTACAO.md
│   ├── API_MAPPING.md
│   ├── STRUCTURE.md
│   └── TESTING.md
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx                            # dev standalone
    ├── bootstrap.tsx                       # mount/unmount (federation)
    ├── App.tsx                             # roteamento lista vs detalhe OV
    ├── index.css                           # estilos + @media print
    ├── api/
    │   ├── httpClient.ts
    │   ├── lmpApi.ts
    │   └── productApi.ts                   # BOM / estrutura de produto
    ├── content/
    │   └── helpTooltips.ts                 # catálogo de tooltips (ⓘ)
    ├── types/
    │   ├── lmp.ts
    │   ├── chart.ts
    │   ├── productStructure.ts
    │   └── richTree.ts
    ├── hooks/
    │   ├── useLmpsDashboard.ts
    │   ├── useLmpDetail.ts
    │   ├── useLmpProductStructures.ts
    │   ├── useLmpsRouterPath.ts
    │   ├── useClientTableSort.ts
    │   ├── useClientPagination.ts
    │   └── useDebouncedValue.ts
    ├── pages/
    │   ├── DashboardLmpsPage.tsx           # lista + KPIs + gráficos + tabela
    │   └── LmpDetailPage.tsx               # detalhe OV /ov/{sale_number}
    ├── components/
    │   ├── FilterBar.tsx
    │   ├── KpiCard.tsx
    │   ├── ChartCard.tsx
    │   ├── DataTable.tsx
    │   ├── DataTableSection.tsx
    │   ├── HelpTooltip.tsx                 # tooltip inline ou fixed (portal)
    │   ├── MultiSelectField.tsx
    │   ├── Pagination.tsx
    │   ├── DetailCard.tsx
    │   ├── DetailFieldGrid.tsx
    │   ├── LmpHistorySection.tsx           # filtros + toggle timeline/tabela
    │   ├── LmpHistoryTimeline.tsx
    │   ├── HistoryEventGantt.tsx           # mini-Gantt por evento
    │   ├── HistoryGlobalGantt.tsx          # Gantt global multi-revisão
    │   ├── LmpProductStructuresSection.tsx
    │   ├── ProductStructureTree.tsx
    │   ├── StructureLegend.tsx
    │   └── RichTree.tsx
    ├── utils/
    │   ├── filterUrl.ts                    # syncLmpsFiltersToUrl
    │   ├── routeParser.ts                  # /ov/{sale_number}
    │   ├── historyFormatting.ts
    │   ├── historyGlobalGantt.ts
    │   ├── historyPreferences.ts           # localStorage view/filter
    │   ├── productStructureTree.ts
    │   ├── lmpCharts.ts
    │   └── exportLmpsCsv.ts
    └── constants/
        ├── chartColors.ts
        ├── filterOptions.ts
        └── routes.ts
```

## Convenções

| Tópico | Convenção |
|--------|-----------|
| ID no manifesto | `dashboard-lmps` |
| `basePath` / Vite `base` | `/apps/dashboard-lmps/` |
| Container Docker | `delpi-dashboard-lmps` |
| Classe raiz CSS | `.dashboard-lmps` |
| Prefixo utilitário CSS | `lmps-*` (ex.: `lmps-kpi-grid`) |
| HTTP | paths absolutos `/apps/api-delpi/engineering/...` |
| Rotas internas | `/` (lista) e `/ov/{sale_number}` (detalhe) |
| Filtros na URL | Sim — `date_start`, `date_end`, `branch`, `status`, `listing_type`, `page`, `page_size` (`filterUrl.ts`) |
| Preferências histórico | `localStorage`: `dashboard-lmps:history-view`, `dashboard-lmps:history-filter` |

## Module Federation

| Campo | Valor |
|-------|--------|
| `name` | `dashboard-lmps` |
| `exposes` | `./App` → `bootstrap.tsx` |
| `shared` | `react`, `react-dom` |

Build: `dist/assets/remoteEntry.js`.

## Diferenças em relação ao dashboard-quality

| Aspecto | LMPs | Qualidade |
|---------|------|-----------|
| Rotas internas | Lista + detalhe OV | Várias (`/ppm`, `/kaizen`, …) |
| Filtros na URL | Sim (`filterUrl.ts`) | Sim (`date_start`, `branch`, sessionStorage) |
| API | `/engineering/lmps/*` | `/quality/*` |
| Auto-refresh | 2 min | Não (manual) |
| Histórico / Gantt | Timeline AIJ010 + Gantt global | N/A |
