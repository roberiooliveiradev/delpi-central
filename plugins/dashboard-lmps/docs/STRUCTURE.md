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
    ├── App.tsx                             # configureHttpClient + página
    ├── index.css                           # estilos (prefixo .dashboard-lmps)
    ├── api/
    │   ├── httpClient.ts
    │   └── lmpApi.ts
    ├── types/
    │   └── lmp.ts
    ├── hooks/
    │   └── useLmpsDashboard.ts
    ├── pages/
    │   └── DashboardLmpsPage.tsx           # única rota / tela
    ├── components/
    │   ├── FilterBar.tsx
    │   ├── KpiCard.tsx
    │   └── ChartCard.tsx
    └── constants/
        └── chartColors.ts
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
| Rotas internas | Página única | Várias (`/ppm`, `/kaizen`, …) |
| Filtros na URL | Não | Sim (`date_start`, `branch`, sessionStorage) |
| API | `/engineering/lmps/*` | `/quality/*` |
| Auto-refresh | 2 min | Não (manual) |
