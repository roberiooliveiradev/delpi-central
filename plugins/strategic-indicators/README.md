# Plugin — Indicadores Estratégicos (MFE)

Microfrontend React do painel **Indicadores Estratégicos** (Module Federation + Vite).

## Documentação

Documentação **completa do módulo SI** (API + MFE + ops):

**[strategic-indicators-api/docs/README.md](../../strategic-indicators-api/docs/README.md)**

Guia específico do front: [docs/MFE.md](../../strategic-indicators-api/docs/MFE.md).

## Resumo

| Item | Valor |
|------|-------|
| Manifesto | `strategic-indicators.manifest.json` |
| `basePath` | `/apps/strategic-indicators` |
| API | `/apps/strategic-indicators-api/strategic-indicators` |
| Container | `delpi-strategic-indicators` |

## Desenvolvimento

```bash
npm install
npm run dev
npm run build
```

Variável opcional: `VITE_STRATEGIC_INDICATORS_API_BASE`.

## Erros na UI

Páginas analíticas usam o card **`StrategicIndicatorsPageError`** (causas, sugestões, detalhe técnico, “Tentar novamente”). Implementação em `src/data/errors/strategicIndicatorsError.ts` e `src/ui/components/StrategicIndicatorsPageError.tsx`. Ver [MFE.md](../../strategic-indicators-api/docs/MFE.md) e [OPERATIONS.md](../../strategic-indicators-api/docs/OPERATIONS.md).

## Filtro consolidado vs filial

- Rótulos de visão: `getFilterViewScopeLabel` → **Consolidado** ou **Filial 01/02** (tabela de indicadores, detalhe rápido, `realized`/`gaps`).
- Regras de meta e realizado na API: [INDICATOR_GOALS_SCOPE.md](../../strategic-indicators-api/docs/INDICATOR_GOALS_SCOPE.md).
- Breakpoints responsivos: `src/ui/shared/strategicIndicatorsLayout.ts` (documentados em [MFE.md](../../strategic-indicators-api/docs/MFE.md)).
