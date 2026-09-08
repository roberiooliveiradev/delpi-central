# Portal Suprimentos — MFE

Microfrontend federado do **Portal Suprimentos** (`id: supplies`, `basePath: /apps/supplies`). Consome exclusivamente a BFF [`supplies-api`](../../supplies-api/) em `/apps/supplies-api`.

Documentação de produto: [docs/12-roadmap-e-evolucao/supplies/](../../docs/12-roadmap-e-evolucao/supplies/).

## Identidade

| Campo | Valor |
|---|---|
| Plugin id | `supplies` |
| CSS root | `.dashboard-supplies-portal.dashboard-page` |
| Tokens | `--sp-*` → `--delpi-ui-*` |
| API | `/apps/supplies-api` |
| Permission de entrada | `supplies.portal.access` |

Não reutilizar `.dashboard-supplies` (cockpit legado).

## Build

```bash
cd plugins/supplies && npm ci && npm test && npm run build
```

Container Compose: `delpi-supplies`. Subir com scripts sequenciais (`--fase mfe --build supplies`), nunca `docker compose up --build` em lote.

## Registro no Core

Ver `scripts/register-manifest.sh` (E3.S4). Homologação usa o mesmo script com `BASE_URL`.
