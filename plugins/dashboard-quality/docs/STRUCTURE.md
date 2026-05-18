# Estrutura de pastas — Dashboard Qualidade

Árvore prevista (espelha `dashboard-lmps` + abas por domínio):

```text
plugins/dashboard-quality/
├── README.md
├── dashboard-quality.manifest.json    # registro Core API
├── package.json
├── package-lock.json
├── vite.config.ts                       # federation name: dashboard-quality
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── index.html
├── Dockerfile
├── .gitignore
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── docs/
│   ├── ROADMAP.md
│   ├── API_MAPPING.md
│   └── STRUCTURE.md                     # este arquivo
└── src/
    ├── main.tsx                         # dev standalone
    ├── bootstrap.tsx                    # expõe App para federation
    ├── App.tsx                          # shell + rotas internas
    ├── App.css
    ├── index.css
    ├── api/
    │   ├── httpClient.ts
    │   ├── query.ts
    │   └── qualityApi.ts                # 7 endpoints tipados
    ├── types/
    │   ├── api.ts
    │   ├── pagination.ts
    │   ├── ppm.ts
    │   ├── nonconformity.ts
    │   ├── kaizen.ts
    │   ├── audit5s.ts
    │   └── index.ts
    ├── hooks/
    │   ├── useQualityResource.ts        # fetch genérico + AbortController
    │   ├── useQualityQueries.ts         # hooks por endpoint (Fase 1)
    │   └── useQualityDashboard.ts       # home: summaries paralelos (Fase 2)
    ├── pages/
    │   ├── DashboardQualityPage.tsx     # layout + abas
    │   ├── PpmPage.tsx
    │   ├── NonconformitiesPage.tsx
    │   ├── KaizenPage.tsx
    │   └── Audit5sPage.tsx
    ├── components/
    │   ├── FilterBar.tsx
    │   ├── KpiCard.tsx
    │   ├── ChartCard.tsx
    │   ├── DataTable.tsx
    │   └── EmptyState.tsx
    ├── constants/
    │   └── chartColors.ts
    └── assets/
```

## Convenções

| Tópico | Convenção |
|---|---|
| IDs no manifesto | `dashboard-quality` |
| `basePath` / Vite `base` | `/apps/dashboard-quality/` |
| Container Docker | `delpi-dashboard-quality` |
| Chamadas HTTP | paths relativos `/apps/api-delpi/quality/...` |
| Estado de filtros | Context ou URL search params (decidir na Fase 2) |

## Fase 0

Scaffold Vite/React implementado em `src/`; build em `dist/assets/remoteEntry.js`.
