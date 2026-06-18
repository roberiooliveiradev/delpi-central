# Estrutura — Inspeções de Entrada (MFE)

```text
plugins/inspecoes-entrada/
├── inspecoes-entrada.manifest.json   # Core API: permissões, rotas menu
├── README.md
├── docs/
│   ├── DOCUMENTACAO.md
│   ├── API_MAPPING.md
│   └── TESTING.md
├── scripts/register-manifest.sh
├── src/
│   ├── App.tsx                       # bootstrap + configureHttpClient
│   ├── bootstrap.tsx                 # mount federado
│   ├── main.tsx                      # dev standalone
│   ├── index.css                     # tokens ie-* / dashboard-inspecoes-entrada
│   ├── api/
│   │   ├── httpClient.ts
│   │   └── inspecoesEntradaApi.ts
│   ├── constants/branch.ts
│   ├── hooks/
│   │   ├── useDebouncedValue.ts
│   │   ├── useInspecoesEntradaDashboard.ts
│   │   ├── useInspecoesEntradaHistorico.ts
│   │   └── useInspecoesEntradaHistoricoDetalhe.ts
│   ├── pages/
│   │   ├── FilialAppPage.tsx         # shell + abas
│   │   ├── DashboardPage.tsx
│   │   └── HistoricoPage.tsx
│   ├── components/
│   │   ├── AppHeader.tsx / AppTabs.tsx
│   │   ├── SummaryCards.tsx / KpiCard.tsx
│   │   ├── SupplierPendingList.tsx
│   │   ├── RejectedProductsList.tsx
│   │   ├── PendingInspectionsTable.tsx
│   │   ├── HistoricoFilterBar.tsx / HistoricoTable.tsx
│   │   ├── HistoricoDetailModal.tsx / InspecaoTestCard.tsx
│   │   └── Pagination.tsx / ResultBadge.tsx
│   ├── types/                        # espelham DTOs api-delpi
│   └── utils/                        # badges, certificado, tabs URL, format
├── vite.config.ts                    # Module Federation
└── Dockerfile
```

## Backend relacionado (api-delpi)

```text
api-delpi/app/
├── interface/http/routes/inspecoes_entrada/inspecoes_entrada_router.py
├── application/
│   ├── dto/inspecoes_entrada/
│   └── use_cases/inspecoes_entrada/
├── domain/ports/inspecoes_entrada/
├── infrastructure/persistence/totvs/inspecoes_entrada/
├── composition/inspecoes_entrada_composer.py
└── scripts/validate_inspecoes_entrada_views.py
```

## Fluxo de dados

```text
FilialAppPage
  ├─ tab overview → DashboardPage → useInspecoesEntradaDashboard
  │     → resumo | pendentes | pendentes-fornecedor | rejeitadas-produto
  └─ tab historico → HistoricoPage → useInspecoesEntradaHistorico
        → historico (+ modal → useInspecoesEntradaHistoricoDetalhe)
```
