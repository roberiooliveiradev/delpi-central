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

O manifesto canônico é [`supplies.manifest.json`](./supplies.manifest.json) (`schemaVersion: 1.0.0`). Registro **não** concede acesso aos usuários — isso é RBAC (E3.S5).

```bash
# Dev local (token via infra/.env.local — ver docs/10-guias-operacionais/registrar-plugin-dev-local.md)
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/supplies/scripts/register-manifest.sh

# Homologação — mesmo artefato
BASE_URL="https://<hml-host>" TOKEN="<jwt-apps.manage>" bash plugins/supplies/scripts/register-manifest.sh
```

Atualizar manifesto já registrado: `PUT $BASE_URL/core-api/admin/apps/supplies/manifest` com o mesmo JSON (guia [registrar-plugin.md](../../docs/10-guias-operacionais/registrar-plugin.md)).

## RBAC de coexistência

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/supplies/scripts/provision-rbac-coexistence.sh
```

Cria papéis `Portal Suprimentos - Analista|Comprador SC|Solicitante SC|Admin` com capabilities canônicas. **Não** remove permissions legadas. Atribuição a usuários reais é passo Admin separado.

Evidence local: [docs/12-roadmap-e-evolucao/supplies/evidence/e3-s5-rbac-smoke-local.json](../../docs/12-roadmap-e-evolucao/supplies/evidence/e3-s5-rbac-smoke-local.json).
