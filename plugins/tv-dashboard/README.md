# Painéis TV (`tv-dashboard`)

Plugin MFE para **gerenciar programações rotativas** exibidas em TVs corporativas.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)  
Roadmap editor Canva/PPT: [playbook §17](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#17-editor-de-slides-personalizados--paridade-canva--powerpoint)  
Indicadores live api-delpi: [playbook §18](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#18-indicadores-live-api-delpi-em-slides-personalizados)  
Gráfico composto / subseleção no palco: [playbook §19](../../docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md#19-gráfico-composto-por-primitivos--edição-no-palco-onda-4g)

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
- **Editor visual v1.4** (slide Personalizado): undo/redo, multi-seleção, camadas, templates, biblioteca de mídia, crop, ícones Lucide
- **Dados live api-delpi (4F):** painel Dados, `data_source` + `chart_view` / `table_view`, catálogo 206 rotas GET, gráficos com elementos configuráveis (legenda, eixos, grade, tabela de dados)
- Filmstrip: prévia centralizada (`CenteredScaledPreview`), menu de contexto nas telas

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
| `@delpi/plugin-ui` | Tooltips, labels, `DataRouteCatalogPanel`, `FormatPaneShell`, `ContextMenu`, `CenteredScaledPreview` — **remote MF** |
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
GET    /apps/tv-dashboard-api/data/routes
GET    /apps/tv-dashboard-api/data/routes/{operationId}
POST   /apps/tv-dashboard-api/data/preview-block
GET    /apps/tv-dashboard-api/content/ui
GET    /apps/tv-dashboard-api/native-screens
```

### Editor — blocos de dados (slide Personalizado)

| Aba / painel | Função |
|---|---|
| **Inserir → Dados** | Catálogo de rotas GET (`DataRouteCatalogPanel`) → insere `data_source` |
| **Inserir → Gráficos / Tabelas** | Insere `chart_view` ou `table_view` |
| **Elemento → Conexão de dados** | Dropdown **Fonte de dados** (`dataSourceId`) |
| **Elemento → Elementos do gráfico** | Título, legenda, eixos, rótulos, grade, tabela de dados, marcadores (`chartOptions`) |
| **Dados** (painel lateral) | Busca e configuração de parâmetros da fonte |

Atalhos: botão **Abrir fontes de dados** no inspetor; clique na fonte no palco conecta visual selecionado.

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
npm run check:css-scope   # gate anti-vazamento CSS (.dashboard-tv-dashboard)
npm test                  # vitest
npm run typecheck         # tsc (tsconfig.build.json)
npm run build             # typecheck + vite build
npm run ci                # circular + css + lint + test + build
```

Docker: contexto `plugins/` (ver `Dockerfile`). Bundled: **`tv-dashboard-presentation`** apenas. **`plugin-ui`** entra via Module Federation (`pluginUiRemote()` + `preparePluginUiRemote()`), sem `COPY plugin-ui`. Container: `delpi-tv-dashboard`.

---

## Deploy

Alterou **só o admin** → rebuild `tv-dashboard` (fase **mfe**).  
Alterou **preview + link público** (`tv-dashboard-presentation` ou view no `public-hub`) → rebuild **`public-hub`** também.  
Alterou **`plugin-ui`** → rebuild remote **antes** dos MFEs consumidores.

```bash
# Preferir scripts sequenciais (evita OOM e garante ordem remote → mfe)
./infra/scripts/up-dev-sequential.sh --fase remote
./infra/scripts/up-dev-sequential.sh --fase mfe
```

Antes do merge (regressão Docker):

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
python3 scripts/ci/check_tv_dashboard_css_scope.py --check
bash scripts/ci/build-tv-dashboard.sh
```
