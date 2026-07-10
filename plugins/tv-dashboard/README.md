# Painéis TV (`tv-dashboard`)

Plugin MFE para **gerenciar programações rotativas** exibidas em TVs corporativas.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)  
Roadmap editor Canva/PPT: [playbook §17](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#17-editor-de-slides-personalizados--paridade-canva--powerpoint)  
Indicadores live api-delpi: [playbook §18](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#18-indicadores-live-api-delpi-em-slides-personalizados)

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
- **Editor visual v1.3** (slide Personalizado): undo/redo, multi-seleção, camadas, templates, biblioteca de mídia, crop, ícones Lucide, indicadores api-delpi (parcial)

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
| `@delpi/plugin-ui` | Tooltips, labels, abas — **remote MF** (`delpi-plugin-ui`) |
| `public-hub` | View pública `present` (rebuild separado ao alterar apresentação) |

Integração: `@delpi/tv-dashboard-presentation` bundled (`COPY` no Dockerfile); `@delpi/plugin-ui` via `pluginUiRemote()` + `preparePluginUiRemote()`. Ver [module-federation.md](../plugin-ui/docs/module-federation.md).

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
GET    /apps/tv-dashboard-api/playlists/{id}/media          # listar assets (biblioteca)
POST   /apps/tv-dashboard-api/playlists/{id}/media          # upload
GET    /apps/tv-dashboard-api/playlists/{id}/media/{assetId}
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
npm test          # vitest (routing, snap, alinhar, grouping, slideCardPreview)
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
