# Painéis TV — documentação da aplicação

> **Status:** v1 em produção (jul/2026)  
> **Playbook detalhado:** [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md)

Sistema de **programações rotativas** para TVs corporativas: gestão autenticada no portal e **link público sem login** para exibição em loop (modo kiosk).

---

## Visão geral

| Superfície | Quem usa | Onde | Login |
|---|---|---|---|
| **Admin** | Gestor (produção, qualidade, etc.) | Portal → «Painéis TV» | Sim (Keycloak) |
| **Apresentação na TV** | Navegador da TV / totem | `/p/tv-dashboard/present/{token}` | Não |

O gestor monta uma **programação** (playlist) com telas nativas DELPI (OEE, OTD, comunicado…) e/ou URLs externas (Power BI, sites). Gera um link ou QR; a TV abre o link e roda em autoplay com refresh periódico dos dados nativos.

---

## Arquitetura

```text
┌──────────────────── PORTAL (JWT) ────────────────────────────────────┐
│  Plugin MFE tv-dashboard                                            │
│    • CRUD programações / telas / ordem                              │
│    • Preview fullscreen (/apps/tv-dashboard/playlists/:id/preview)  │
│    • Copiar link, QR, desativar token                               │
│         │                                                           │
│         ▼                                                           │
│  tv-dashboard-api  (/apps/tv-dashboard-api/)                        │
│    • Postgres schema tv_dashboard                                   │
│    • Agrega payload + dados nativos (api-delpi)                     │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────── TV (sem login) ────────────────────────────────┐
│  GET /p/tv-dashboard/present/{token}                                │
│         │                                                           │
│         ▼                                                           │
│  public-hub (chrome: kiosk)                                         │
│    • GET /apps/tv-dashboard-api/public/present/{token}              │
│    • PresentationEngine + NativeSlideView                           │
│    • POST …/heartbeat (status «TV online» no admin)                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Pacotes no monorepo

| Pacote | Caminho | Função |
|---|---|---|
| **API** | `tv-dashboard-api/` | CRUD, token público, catálogo nativo, RBAC filial |
| **Plugin admin** | `plugins/tv-dashboard/` | UI no portal (Module Federation) |
| **Shell público** | `plugins/public-hub/src/apps/tv-dashboard/` | View `present` para a TV |
| **Motor compartilhado** | `plugins/tv-dashboard-presentation/` | `usePresentationEngine`, telas nativas, CSS `tdp-*` |

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

Exemplo produção: `https://minhadelpi.com.br/p/tv-dashboard/present/{token}`  
Exemplo local: `http://localhost/p/tv-dashboard/present/{token}`

### API (`tv-dashboard-api`)

| Escopo | Prefixo | Exemplos |
|---|---|---|
| Admin (JWT) | `/apps/tv-dashboard-api/` | `GET /playlists`, `POST /playlists/{id}/slides` |
| Público | `/apps/tv-dashboard-api/public/` | `GET /present/{token}`, `POST /present/{token}/heartbeat` |
| Conteúdo UI | `/apps/tv-dashboard-api/content/` | `GET /ui`, `GET /slide-presets` |

Envelope padrão: `{ success, message, data }`.

---

## Telas nativas (v1)

| `screenKey` | Descrição |
|---|---|
| `custom_message` | Comunicado (título + subtítulo) |
| `production_oee_overview` | OEE + meta |
| `production_otd_summary` | OTD + meta |
| `quality_ppm_summary` | PPM + meta |
| `supplies_stock_value` | Valor de estoque |

Telas **externas**: URL + `sandbox` opcional em iframe.

Catálogo e presets: `GET /native-screens`, `GET /content/slide-presets`.  
Textos PT-BR: `tv-dashboard-api/tv_app/content/tv_dashboard_content.json`.

---

## Permissões RBAC

| Permissão | Uso |
|---|---|
| `tv-dashboard.read` | Listar / visualizar |
| `tv-dashboard.write` | Criar/editar programações e telas |
| `tv-dashboard.manage` | Link público, desativar, excluir |
| `tv-dashboard.view.filial-01` / `.filial-02` | Escopo filial nas telas nativas |
| `tv-dashboard.view.consolidated` | Visão consolidada |

Registro do plugin: `bash scripts/register-manifest.sh` (ver README do plugin).

---

## Ambiente e deploy

### Containers

| Serviço Compose | Container | Quando rebuild |
|---|---|---|
| `tv-dashboard-api` | `delpi-tv-dashboard-api` | API, migrations, gateways TOTVS |
| `tv-dashboard` | `delpi-tv-dashboard` | Plugin admin |
| `public-hub` | `delpi-public-hub` | **Qualquer** alteração na view pública ou no pacote `tv-dashboard-presentation` |

### Variáveis relevantes

| Variável | Onde | Descrição |
|---|---|---|
| `PUBLIC_BASE_URL` | `tv-dashboard-api` | Base do link copiado no admin (ex.: `https://minhadelpi.com.br`) |
| `TV_DASHBOARD_PUBLIC_PATH` | `tv-dashboard-api` | Default `/p/tv-dashboard/present` |
| `PLUGINS_DB_*` | `tv-dashboard-api` | Postgres `tv_dashboard` |
| `DELPI_API_URL` | `tv-dashboard-api` | api-delpi para KPIs nativos |

### Comandos típicos

```bash
# Produção / servidor
cd infra
git pull
docker compose -f docker-compose.dev.yml up --build -d public-hub tv-dashboard-api tv-dashboard

# Stack mínimo local (chat + api-delpi + TV)
bash scripts/up-minimal-dev.sh
docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --env-file .env \
  up -d --build public-hub tv-dashboard-api tv-dashboard gateway
```

Após deploy do `public-hub`, testar em aba anônima com **hard refresh** (Ctrl+Shift+R).

---

## Desenvolvimento local

```bash
# API
cd tv-dashboard-api
pip install -r requirements.txt && pip install -e ../shared[fastapi]
pytest tests/ -q

# Pacote compartilhado
cd plugins/tv-dashboard-presentation
npm test

# Public-hub (view TV)
cd plugins/public-hub
npm run build

# Plugin admin
cd plugins/tv-dashboard
npm run build
```

**Build Docker:** contexto `plugins/` (inclui `tv-dashboard-presentation`). Ver `plugins/public-hub/Dockerfile`.

---

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| Página branca, `#root` vazio | Duas cópias do React no bundle | `dedupe` + alias em `public-hub/vite.config.ts`; rebuild `public-hub` |
| `useState` null / hooks quebrados | Idem | Idem |
| «Programação não encontrada» | Token inválido, link desativado ou DB diferente | **Novo link** no editor; conferir `is_active` |
| Preview OK, link público falha | `public-hub` desatualizado | Rebuild `delpi-public-hub` |
| Build Docker falha no `tsc` | Tipos React no pacote compartilhado | Manter `npm install` em `tv-dashboard-presentation` no Dockerfile |
| KPIs `—` na TV | api-delpi sem dados / filial | Normal em dev; conferir escopo RBAC e TOTVS |
| iframe externo em branco | Site bloqueia embed | Power BI «Publicar na Web» ou fallback na UI |

---

## Referências

- [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md) — north star, ondas, critérios de aceite
- [tv-dashboard-api/README.md](../../../tv-dashboard-api/README.md)
- [plugins/tv-dashboard/README.md](../../../plugins/tv-dashboard/README.md)
- [plugins/tv-dashboard-presentation/README.md](../../../plugins/tv-dashboard-presentation/README.md)
- [plugins/public-hub/README.md](../../../plugins/public-hub/README.md) — contrato `PublicPageDefinition`
