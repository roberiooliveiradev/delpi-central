# Painéis TV — documentação da aplicação

> **Status:** v1.3 em produção (jul/2026) — editor deck + Onda 4A/4B/4D (produtividade, visual, layout)  
> **Playbook detalhado:** [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md) · **Editor Canva/PPT:** §17 · **Indicadores api-delpi:** §18

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
- **Backlog:** indicadores live (KPI/gráfico/tabela) de rotas api-delpi no mesmo slide — [§18](./PLAYBOOK-EXCELENCIA.md#18-indicadores-live-api-delpi-em-slides-personalizados)

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
cd infra
git pull
docker compose -f docker-compose.dev.yml up --build -d gateway tv-dashboard-api tv-dashboard public-hub
```

---

## Backlog

### Telas nativas (v2)

- Gráficos Recharts em telas OEE/OTD/PPM

### Editor personalizado — Onda 4 (ver playbook §17)

**Concluído v1.3:** undo/redo, duplicar, atalhos, snap, alinhar, biblioteca de mídia, templates, temas, gradientes, sombras, crop, ícones, multi-seleção, agrupar, camadas, rotação, zoom, links em mídia/forma.

| Fase | Foco | Status |
|------|------|--------|
| **4A** | Produtividade editor | ✅ exc. 4A.9 cleanup |
| **4B** | Templates, temas, visual | ✅ |
| **4C** | Rich text, bullets, estilos nomeados | ❌ backlog |
| **4D** | Layout avançado | ✅ |
| **4E** | Animações, master slide, export PNG | ❌ backlog |
| **4F** | **Indicadores live api-delpi** — KPI, gráfico, tabela em blocos | ⚠ parcial (§18) |

---

## Referências

- [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md)
- [tv-dashboard-api/README.md](../../../tv-dashboard-api/README.md)
- [plugins/tv-dashboard/README.md](../../../plugins/tv-dashboard/README.md)
- [plugins/tv-dashboard-presentation/README.md](../../../plugins/tv-dashboard-presentation/README.md)
