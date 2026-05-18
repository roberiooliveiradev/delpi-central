# Plugin — Indicadores Estratégicos (MFE)

Microfrontend React (Vite + Module Federation) do painel **Indicadores Estratégicos**.

## Integração na plataforma

| Item | Valor |
|------|-------|
| `id` (manifesto) | `strategic-indicators` |
| `basePath` | `/apps/strategic-indicators` |
| Container dev | `delpi-strategic-indicators` |
| API backend | `/apps/strategic-indicators-api/strategic-indicators` |

Variável opcional de build: `VITE_STRATEGIC_INDICATORS_API_BASE` (padrão no código: `/apps/strategic-indicators-api/strategic-indicators`).

## Documentação da API

- [strategic-indicators-api/docs/README.md](../../strategic-indicators-api/docs/README.md)
- Rotas e permissões: [API.md](../../strategic-indicators-api/docs/API.md)

## Estrutura do código

```text
src/
  data/api/          # Clientes HTTP (executive, trends, presentation, admin…)
  data/cache/        # Cache de leitura no browser (SWR)
  state/hooks/       # Hooks React + prefetch após executive
  ui/pages/          # Painel executivo, departamentos, trends, admin…
```

## Comportamento de carregamento (performance)

Implementado no MFE (ver [PERFORMANCE_IMPLEMENTATION.md](../../strategic-indicators-api/docs/PERFORMANCE_IMPLEMENTATION.md) fase 4):

1. **Stale-while-revalidate** — exibe cache local e atualiza em background.
2. **Prefetch** — após `executive-summary`, dispara `departments` e `trends` (6 meses).
3. **Presentation split** — overview com `?include=`; trends em segundo request.

## Desenvolvimento

```bash
cd plugins/strategic-indicators
npm install
npm run dev
```

Build para o gateway:

```bash
npm run build
# Assets em dist/ → servidos em /apps/strategic-indicators/assets/
```

Registro na Core API via `strategic-indicators.manifest.json` — ver [docs/08-plugins/README.md](../../docs/08-plugins/README.md).

## Permissões (exemplos)

- `strategic-indicators.view` — painel
- `strategic-indicators.trends.view` — tendências
- `strategic-indicators.settings.manage` — admin e settings
