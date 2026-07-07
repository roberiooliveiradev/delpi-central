# Painéis TV (`tv-dashboard`)

Plugin MFE para **gerenciar programações rotativas** exibidas em TVs corporativas.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)

---

## Funcionalidades

- CRUD de programações (playlists) e telas (slides)
- Telas **nativas** (OEE, OTD, PPM, estoque, comunicado) e **externas** (iframe)
- Reordenação (drag-and-drop), duplicar, pausar tela
- **Pré-visualização** fullscreen (`/playlists/{id}/preview`)
- **Link público** sem login: `/p/tv-dashboard/present/{token}`
- Copiar link, QR, regenerar token, desativar / excluir
- Status «TV online» via heartbeat na rota pública
- Catálogo de presets e importação de telas prontas
- RBAC por filial e visão consolidada

---

## Rotas do plugin

| Rota | Página |
|---|---|
| `/` | Lista de programações |
| `/playlists/new` | Nova programação |
| `/playlists/{id}` | Editor |
| `/playlists/{id}/preview` | Preview (motor compartilhado) |
| `/playlists/{id}/share` | Compartilhar |

Base gateway: `/apps/tv-dashboard/`

---

## Dependências

| Pacote | Uso |
|---|---|
| `tv-dashboard-api` | Backend (`/apps/tv-dashboard-api/`) |
| `@delpi/tv-dashboard-presentation` | `usePresentationEngine`, `NativeSlideView`, CSS `tdp-*` |
| `@delpi/plugin-ui` | Tooltips, labels, abas (`HelpTooltip`, `FieldLabel`, …) |
| `public-hub` | View pública `present` (rebuild separado ao alterar apresentação) |

Alias Vite: `../tv-dashboard-presentation/src/index.ts`, `../plugin-ui/src/index.ts`  
Module Federation: `shared: ["react", "react-dom"]` (React único via portal).

---

## API admin (resumo)

```http
GET    /apps/tv-dashboard-api/playlists
POST   /apps/tv-dashboard-api/playlists
GET    /apps/tv-dashboard-api/playlists/{id}
PATCH  /apps/tv-dashboard-api/playlists/{id}
DELETE /apps/tv-dashboard-api/playlists/{id}
GET    /apps/tv-dashboard-api/playlists/{id}/preview-payload
GET    /apps/tv-dashboard-api/playlists/{id}/slides
POST   /apps/tv-dashboard-api/playlists/{id}/slides
PATCH  /apps/tv-dashboard-api/playlists/{id}/slides/{slideId}
DELETE /apps/tv-dashboard-api/playlists/{id}/slides/{slideId}
POST   /apps/tv-dashboard-api/playlists/{id}/slides/reorder
GET    /apps/tv-dashboard-api/content/ui
GET    /apps/tv-dashboard-api/native-screens
```

---

## Registro no portal

```bash
TOKEN="<jwt com apps.manage>" bash scripts/register-manifest.sh
```

Permissões: `tv-dashboard.read`, `.write`, `.manage`, `.view.filial-*`, `.view.consolidated`.

---

## Build e testes

```bash
npm install
npm run build
npm test          # routing vitest
```

Docker: contexto `plugins/` (ver `Dockerfile`). Copiar **`plugin-ui`** + `tv-dashboard-presentation` no build. Container: `delpi-tv-dashboard`.

---

## Deploy

Alterou **só o admin** → rebuild `tv-dashboard`.  
Alterou **preview + link público** (pacote `tv-dashboard-presentation` ou view no `public-hub`) → rebuild **`public-hub`** também.

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build -d tv-dashboard public-hub tv-dashboard-api
```

Antes do merge (regressão Docker):

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
bash scripts/ci/build-tv-dashboard.sh
```
