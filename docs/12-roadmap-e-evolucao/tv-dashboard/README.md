# Painéis TV — documentação da aplicação

> **Status:** v1.5+ em produção (jul/2026) — editor deck + Onda 4A–4O + **dois escopos** global/parte no palco (§19.19)
> **Playbooks:** [Excelência](./PLAYBOOK-EXCELENCIA.md) · [Power Query M](./PLAYBOOK-POWER-QUERY-M.md) (**Fase 1 concluída; M desativado**) · [status Fase 1](./FASE-1-STATUS-M-DELPI.md) · [ADR M DELPI v1](./ADR-M-DELPI-V1.md)

Sistema de **programações rotativas** para TVs corporativas: gestão autenticada no portal e **link público sem login** para exibição em loop (modo kiosk).

---

## Visão geral

| Superfície | Quem usa | Onde | Login |
|---|---|---|---|
| **Admin** | Gestor (produção, qualidade, etc.) | Portal → «Painéis TV» | Sim (Keycloak) |
| **Apresentação na TV** | Navegador da TV / totem | `/p/tv-dashboard/present/{token}` | Não |

O gestor monta uma **programação** (playlist) com telas nativas DELPI (OEE, OTD, comunicado…) e/ou URLs externas (Power BI, sites). Slides **Personalizado** (`custom_message`) usam um **editor visual estilo PowerPoint** (blocos, formas, mídia, ribbon de formatação). Gera um link ou QR; a TV abre o link e roda em autoplay com **atualização imediata via WebSocket** (fallback: polling `globalRefreshSec`).

---

## Arquitetura

```text
┌──────────────────── PORTAL (JWT) ────────────────────────────────────┐
│  Plugin MFE tv-dashboard                                            │
│    • CRUD programações / telas / ordem                              │
│    • Editor visual estilo PowerPoint (ribbon, filmstrip, formatação) │
│    • Miniaturas ao vivo nos cards de tela                           │
│    • Preview fullscreen (/apps/tv-dashboard/playlists/:id/preview)  │
│    • Copiar link, QR, desativar token                               │
│         │                                                           │
│         ▼                                                           │
│  tv-dashboard-api  (/apps/tv-dashboard-api/)                        │
│    • Postgres schema tv_dashboard + mídia em disco                  │
│    • Agrega payload + dados nativos (api-delpi)                     │
│    • WebSocket push ao editar programação                           │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────── TV (sem login) ────────────────────────────────┐
│  GET /p/tv-dashboard/present/{token}                                │
│         │                                                           │
│         ▼                                                           │
│  public-hub (chrome: kiosk)                                         │
│    • GET /apps/tv-dashboard-api/public/present/{token}              │
│    • WS  /apps/tv-dashboard-api/public/present/{token}/ws           │
│    • PresentationEngine + NativeSlideView                           │
│    • POST …/heartbeat (status «TV online» no admin)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Pacotes no monorepo

| Pacote | Caminho | Função |
|---|---|---|
| **API** | `tv-dashboard-api/` | CRUD, token público, mídia, WebSocket, RBAC filial |
| **Plugin admin** | `plugins/tv-dashboard/` | UI no portal (Module Federation) |
| **Shell público** | `plugins/public-hub/src/apps/tv-dashboard/` | View `present` para a TV |
| **Motor compartilhado** | `plugins/tv-dashboard-presentation/` | `usePresentationEngine`, `usePresentationRealtime`, telas nativas, CSS `tdp-*` |

---

## URLs e rotas

### Gestão (portal)

| Rota MFE | Descrição |
|---|---|
| `/apps/tv-dashboard/` | Lista de programações |
| `/apps/tv-dashboard/playlists/new` | Nova programação |
| `/apps/tv-dashboard/playlists/{id}` | Editor |
| `/apps/tv-dashboard/playlists/{id}/preview` | Pré-visualização (mesmo motor da TV) |
| `/apps/tv-dashboard/playlists/{id}/share` | Compartilhar link / QR |

### Apresentação pública

```
{PUBLIC_BASE_URL}/p/tv-dashboard/present/{publicToken}
```

### API (`tv-dashboard-api`)

| Escopo | Prefixo | Exemplos |
|---|---|---|
| Admin (JWT) | `/apps/tv-dashboard-api/` | `GET /playlists`, `POST /playlists/{id}/slides`, `POST /playlists/{id}/media` |
| Público | `/apps/tv-dashboard-api/public/` | `GET /present/{token}`, `WS /present/{token}/ws`, `POST /present/{token}/heartbeat` |
| Tempo real (admin) | `/apps/tv-dashboard-api/` | `WS /playlists/{id}/presentation-ws?access_token=…` |
| Conteúdo UI | `/apps/tv-dashboard-api/content/` | `GET /ui`, `GET /slide-presets` |

Envelope padrão: `{ success, message, data }`.

---

## Telas nativas (v1.1)

| `screenKey` | Descrição |
|---|---|
| `custom_message` | Comunicado visual — blocos (título, texto, imagem, vídeo), fundo colorido ou imagem |
| `production_oee_overview` | OEE + meta |
| `production_otd_summary` | OTD + meta |
| `quality_ppm_summary` | PPM + meta |
| `supplies_stock_value` | Valor de estoque |
| `supplies_stock_alert` | Top itens por valor em estoque (máx. 6) |
| `strategic_indicators_hero` | Hero executivo IGD |

Telas **externas**: URL + `sandbox` opcional em iframe.

### Comunicados com mídia (`custom_message` v3)

- Blocos posicionáveis: título, texto, imagem, vídeo, formas (6 tipos)
- Ribbon **Fonte** e **Parágrafo** (alinhamento, entrelinhas, realce, tachado, etc.)
- Drag, resize (8 handles), edição inline, camadas, links, rotação
- Upload admin: `POST /playlists/{id}/media` (JPG, PNG, WEBP, GIF, MP4, WEBM)
- Armazenamento persistente: `${DELPI_DATA_HOST_DIR}/tv-dashboard/media`
- Apresentação pública: `GET /public/present/{token}/media/{assetId}`
- Roadmap paridade Canva/PowerPoint: [PLAYBOOK-EXCELENCIA.md §17](./PLAYBOOK-EXCELENCIA.md#17-editor-de-slides-personalizados--paridade-canva--powerpoint)

### Dados live api-delpi no slide personalizado (Onda 4F — jul/2026)

Arquitetura **fonte + visual** (desacoplada):

```text
Inserir → Dados        → painel lateral (catálogo GET api-delpi) → bloco data_source
Inserir → Gráficos     → chart_view (linhas/colunas)
Inserir → Tabelas      → table_view (grade/minimal/faixas)
Elemento → Conexão     → chart_view/table_view.dataSourceId → data_source
```

| Peça | Onde |
|---|---|
| Catálogo de rotas | `GET /data/routes` — **232** operações GET sincronizadas com OpenAPI (`scripts/generate_tv_data_routes_from_openapi.py`) |
| Painel **Dados** | `DataRoutesSidePanel` + `DataRouteCatalogPanel` (`@delpi/plugin-ui`) |
| Enrichment | `ComunicadoDataEnrichmentService` — resolve `data_source`; vincula `chart_view` / `table_view` |
| Gráfico configurável | `ConfigurableSeriesChart` + `chartParts` / `chartOptions` (título, legenda, eixos, grade, tabela, marcadores) |
| KPI composto | `DelpiKpiCard` + `kpiParts` (card/title/value/hint/icon) — subseleção no palco |
| Tabela composta | `ConfigurableTable` + `tableParts` (frame/header/células) |
| Filmstrip | `CenteredScaledPreview` (miniatura centralizada) + menu contexto (copiar/colar, duplicar, ocultar) |

Doc completa: [PLAYBOOK-EXCELENCIA.md §18](./PLAYBOOK-EXCELENCIA.md#18-indicadores-live-api-delpi-em-slides-personalizados) · [§19.19 escopos](./PLAYBOOK-EXCELENCIA.md#1919-dois-escopos-de-seleção--chrome-de-partes-jul2026)

- **Períodos relativos:** o editor oferece hoje; semana/mês/trimestre/ano atuais; períodos anteriores; últimos 7/30/90/N dias; e datas fixas. Presets relativos são resolvidos novamente a cada fetch.
- **Contrato de séries:** a TV preserva a granularidade da rota. `granularity=day` permanece um ponto por dia — sem converter dias em faixas semanais.
- **Cobertura anual diária:** a api-delpi permite até 366 buckets; assim, «Este ano (até hoje)» entrega todos os dias do ano. Períodos diários acima de um ano continuam limitados por segurança.
- **Tabela de série:** apresenta todos os `points` retornados pela API usando apenas as colunas declaradas (`periodo` e `value`), sem mostrar `label` duplicado ou metadados como `granularity`/`truncated`.
- **M DELPI — Fase 1:** reader dual v1/v2, adapter para plano tipado e formatter M estão prontos. Scripts v2 não são executados enquanto as flags permanecem desligadas; o browser contém apenas DTOs.
- **Onda 4G–4O (§19):** partes selecionáveis; **dois escopos** (global vs parte) para geometria e chrome (§19.19)
- **§19.20:** aplicar estilo a irmãos; séries OEE/OTD/PPM nas nativas (SVG); rate limit `public/present`
- **Backlog:** sombra texto, conectores, paleta recente, PDF/PPTX, colaboração

---

## Atualização em tempo real

Ao salvar telas, reordenar, enviar mídia ou alterar configurações da programação, a API emite `presentation_updated` via WebSocket para:

- TVs no link público (`/public/present/{token}/ws`)
- Preview admin e editor (`/playlists/{id}/presentation-ws`)

O cliente recarrega o payload HTTP; o polling periódico permanece como fallback.

---

## Permissões RBAC

| Permissão | Uso |
|---|---|
| `tv-dashboard.read` | Listar / visualizar |
| `tv-dashboard.write` | Criar/editar programações e telas |
| `tv-dashboard.manage` | Link público, desativar, excluir |
| `tv-dashboard.view.filial-01` / `.filial-02` | Escopo filial nas telas nativas |
| `tv-dashboard.view.consolidated` | Visão consolidada |

---

## Ambiente e deploy

### Containers

| Serviço Compose | Container | Quando rebuild |
|---|---|---|
| `tv-dashboard-api` | `delpi-tv-dashboard-api` | API, migrations, gateways TOTVS |
| `tv-dashboard` | `delpi-tv-dashboard` | Plugin admin |
| `public-hub` | `delpi-public-hub` | **Qualquer** alteração na view pública ou no pacote `tv-dashboard-presentation` |
| `gateway` | `delpi-gateway` | Após alterar proxy WebSocket nginx |

### Variáveis relevantes

| Variável | Onde | Descrição |
|---|---|---|
| `PUBLIC_BASE_URL` | `tv-dashboard-api` | Base do link copiado no admin |
| `TV_DASHBOARD_PUBLIC_PATH` | `tv-dashboard-api` | Default `/p/tv-dashboard/present` |
| `TV_DASHBOARD_MEDIA_UPLOAD_DIR` | `tv-dashboard-api` | Default `/app/data/tv-dashboard/media` |
| `PLUGINS_DB_*` | `tv-dashboard-api` | Postgres `tv_dashboard` |
| `DELPI_API_URL` | `tv-dashboard-api` | api-delpi para KPIs nativos |

### Comandos típicos

```bash
# Executar na raiz; ordem segura e um serviço por vez
git pull
./infra/scripts/up-dev-sequential.sh --fase api --build tv-dashboard-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build tv-dashboard
```

Em produção, após alterar séries/períodos, reconstruir `api-delpi` e `tv-dashboard-api`
com `./infra/scripts/up-prod-sequential.sh --pull --build`, filtrando esses serviços.

---

## Backlog

### Editor / paridade PPT (restante)

- Upload de fonte; reflexo tipográfico
- Conectores entre formas; tabelas canvas simples
- Import/export PPTX; modo apresentador; colaboração

### Editor personalizado — Onda 4 (ver playbook §17)

**Concluído v1.3+:** undo/redo, duplicar, atalhos, snap, alinhar, biblioteca de mídia, templates, temas, gradientes, sombras, crop, ícones, multi-seleção, agrupar, camadas, rotação, zoom, links em mídia/forma.

| Fase | Foco | Status |
|------|------|--------|
| **4A** | Produtividade editor | ✅ completo (incl. 4A.9) |
| **4B** | Templates, temas, visual | ✅ |
| **4C** | Rich text, bullets, estilos nomeados | ✅ (ver playbook §17) |
| **4D** | Layout avançado | ✅ |
| **4E** | Animações, master slide, export PNG | ✅ 4E.1–4E.5 |
| **4F** | **Indicadores live api-delpi** — fonte + gráfico/tabela/KPI | ✅ (§18) |
| **4G–4O** | **Partes compostas** + chrome Office + **dois escopos** global/parte | ✅ (§19 / §19.19) |
| **§19.20** | Apply-all irmãos + séries nativas SVG + rate limit present | ✅ |
| **§19.21** | Sombra/contorno tipográfico + cores recentes + export PDF | ✅ |

---

## Referências

- [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md)
- [PLAYBOOK-POWER-QUERY-M.md](./PLAYBOOK-POWER-QUERY-M.md)
- [ADR-M-DELPI-V1.md](./ADR-M-DELPI-V1.md)
- [FASE-0-BASELINE-M-DELPI.md](./FASE-0-BASELINE-M-DELPI.md)
- [tv-dashboard-api/README.md](../../../tv-dashboard-api/README.md)
- [plugins/tv-dashboard/README.md](../../../plugins/tv-dashboard/README.md)
- [plugins/tv-dashboard-presentation/README.md](../../../plugins/tv-dashboard-presentation/README.md)
