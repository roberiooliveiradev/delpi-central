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
