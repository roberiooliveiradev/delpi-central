# Estrutura de pastas — Dashboard Qualidade

```text
plugins/dashboard-quality/
├── README.md
├── dashboard-quality.manifest.json
├── package.json
├── vite.config.ts
├── Dockerfile
├── docs/
│   ├── DOCUMENTACAO.md          # guia principal do plugin
│   ├── API_MAPPING.md
│   ├── TESTING.md
│   ├── ROADMAP.md
│   ├── IMPROVEMENTS_ROADMAP.md
│   └── STRUCTURE.md
├── scripts/
│   └── register-manifest.sh
└── src/
    ├── main.tsx
    ├── bootstrap.tsx
    ├── App.tsx
    ├── index.css                  # estilos + @media print
    ├── api/
    │   ├── httpClient.ts
    │   ├── query.ts
    │   ├── qualityApi.ts
    │   └── validateQualityResponse.ts
    ├── types/
    ├── hooks/
    │   ├── useQualityFilters.ts   # URL + sessionStorage
    │   ├── useQualityDashboard.ts
    │   ├── useQualityQueries.ts
    │   ├── usePpmChartSeries.ts
    │   └── ...
    ├── pages/
    │   ├── DashboardQualityPage.tsx
    │   ├── PpmPage.tsx
    │   ├── NonconformitiesPage.tsx
    │   ├── KaizenPage.tsx
    │   └── Audit5sPage.tsx
    ├── components/
    │   ├── FilterBar.tsx
    │   ├── QualityPageHeader.tsx
    │   ├── QualityNav.tsx
    │   ├── PrintReportButton.tsx
    │   ├── PrintReportSummary.tsx
    │   ├── ChartCard.tsx
    │   ├── PpmEvolutionChart.tsx
    │   └── ...
    ├── constants/
    │   ├── routes.ts
    │   ├── chartColors.ts
    │   └── ppmReferenceLines.ts
    └── utils/
        ├── filterUrl.ts
        ├── navigation.ts
        ├── dates.ts
        ├── chartAggregation.ts
        └── chartSeriesExport.ts
```

## Convenções

| Tópico | Convenção |
|--------|-----------|
| ID no manifesto | `dashboard-quality` |
| `basePath` / Vite `base` | `/apps/dashboard-quality/` |
| Container Docker | `delpi-dashboard-quality` |
| HTTP | `/apps/api-delpi/quality/...` |
| Filtros | `date_start`, `date_end`, `branch` na URL + `sessionStorage` |
| Impressão | `dq-print-root` na página; `dq-no-print` / `dq-screen-only` |

Build de produção: `dist/assets/remoteEntry.js`.
