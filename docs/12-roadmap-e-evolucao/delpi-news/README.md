# DELPI News — fundação arquitetural

> **Status:** Etapa 1 (fundação, contratos conceituais e prova visual).  
> **Não** é produto completo: coleta RSS, curadoria admin e API pública real ficam para etapas seguintes.  
> **Fora de escopo permanente nesta linha:** app Android TV / APK / gestão de dispositivos (projeto suspenso). Exibição = navegador HTTPS no Adeus Pendrive.

**Identificadores técnicos:** inglês (`delpi-news`, `rss_source`, `news_item`). Textos ao usuário: pt-BR.

---

## 1. Objetivo do produto

Ferramenta corporativa para selecionar, gerenciar e apresentar notícias de fontes RSS em página web personalizada, exibida continuamente nas TVs corporativas via Adeus Pendrive.

Fluxo alvo:

```text
Fontes RSS
→ coleta (serviço dono)
→ normalização e filtros
→ curadoria editorial
→ notícias publicadas
→ página HTML pública (public-hub)
→ Adeus Pendrive (navegador)
→ TV corporativa
```

---

## 2. Superfícies

| Superfície | Auth | Responsabilidade | Etapa |
|---|---|---|---|
| **Admin** (Minha DELPI) | Keycloak + RBAC Core | Fontes RSS, categorias, filtros, aprovação, destaques, publicação | Futura |
| **Pública** (`public-hub`) | Sem login interativo; token de board | Apresentação kiosk das notícias autorizadas | **E1: prova visual com fixture** |
| **Canal TV opcional** | Token TV Dashboard | Embutir URL do board como slide `external` allowlisted | Futura (não obrigatória no MVP) |

---

## 3. Ownership e fronteiras

| Fronteira | Owner legítimo | Não duplicar em |
|---|---|---|
| Domínio editorial + ingestão RSS | **`delpi-news-api`** (BC novo, PLANNED) | `external-data-api`, `tv-dashboard-api`, Core, Portal |
| Persistência de fontes/itens/publicação | Schema próprio do BC News | Banco de outro app |
| Página pública kiosk | `plugins/public-hub` app `delpi-news` | Novo container `*-public`, Portal autenticado |
| Admin MFE | `plugins/delpi-news` (PLANNED) | Reimplementar RBAC no cliente |
| AuthN/AuthZ admin | Keycloak + Core permissions | Middleware ad hoc no hub |
| Playlist/slides Adeus genéricos | `tv-dashboard` + `tv-dashboard-api` | Virar owner de RSS |
| Shell HTTPS `/p/*` | `public-hub` + gateway `^~ /p/` | Nova `location` por app |

### Decisão travada — `external-data-api`

| Campo | Valor |
|---|---|
| Mandato atual | Consultas cadastrais externas S2S (MVP CNPJ / BrasilAPI) |
| `EXISTING_EQUIVALENT` (RSS) | **NO** |
| `REUSE_DECISION` | **NEW** BC News — **não** ampliar `external-data-api` sem ADR e mudança de mandato |

Evidência: `external-data-api/docs/README.md`, freeze X0 em `docs/12-roadmap-e-evolucao/shared-integrations/`.

### Decisão travada — TV Dashboard

| Capacidade | Equivalente | Decisão |
|---|---|---|
| Kiosk Adeus / fit / token / heartbeat | YES | **REUSE** padrões de chrome `kiosk` e URL pública |
| Playlist / motor de slides | PARTIAL | **REUSE** só se News for URL embutida; **não** owner do feed |
| Agregação RSS / curadoria | NO | **NEW** em `delpi-news-api` |

---

## 4. Inventário de reuso (HEAD da Etapa 1)

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION | Owner | Evidência |
|---|---|---|---|---|
| Página pública HTTPS sem auth | YES | EXTEND `public-hub` | `plugins/public-hub` | README hub; `registry.ts` |
| Kiosk Adeus (chrome/fit) | YES (TV) | REUSE padrão `chrome: "kiosk"` | hub + TV presentation | `tv-dashboard/pages.tsx` |
| Coleta RSS/Atom | NO | NEW | `delpi-news-api` | Sem `feedparser`/ingestão no monorepo |
| HTTP externo resiliente | PARTIAL | EXTEND padrões no BC News | regra `http-integration-resilience` + caller | `.cursor/rules/http-integration-resilience.mdc` |
| Scheduler/cron | YES (por domínio) | REUSE padrão in-process no BC | jobs do BC News | schedulers em core/commercial/pulse/etc. |
| Cache editorial de feed | NO | NEW (TTL no BC) | `delpi-news-api` | Query cache api-delpi ≠ feed |
| Persistência editorial TV | PARTIAL | NEW se pipeline News | `delpi-news-api` | TV = slides, não artigos RSS |
| Auditoria | PARTIAL | EXTEND no BC | `delpi-news-api` | Trails por domínio |
| `plugin-ui` / marca pública | YES | REUSE tokens `--pub-*` | shell hub | `shell.css` |
| Auth compartilhada | YES | REUSE `shared/delpi_auth` no BC | admin API | `shared/delpi_auth` |

---

## 5. Arquitetura-alvo (alto nível)

```text
┌─────────────────────┐     JWT + RBAC      ┌──────────────────┐
│ Portal / MFE admin  │ ──────────────────▶ │  delpi-news-api  │
│ (plugins/delpi-news)│                     │  (PLANNED)       │
└─────────────────────┘                     │  sources · items │
                                            │  curation · board│
┌─────────────────────┐   token board       └────────┬─────────┘
│ public-hub          │ ◀── GET /public/boards/{t} ──┘
│ apps/delpi-news     │
│ /p/delpi-news/board │
└──────────┬──────────┘
           │ HTTPS
           ▼
    Adeus Pendrive (browser) → TV
```

Opcional futuro: TV Dashboard slide `external` → mesma URL do board (allowlist same-origin).

---

## 6. Entregáveis da Etapa 1

| Entrega | Path |
|---|---|
| Este índice + ownership | `docs/12-roadmap-e-evolucao/delpi-news/README.md` |
| Contratos conceituais (sem operações OpenAPI prematuras) | [`CONTRACTS.md`](./CONTRACTS.md) |
| Aceite / rastreio da etapa | [`STAGE-01.md`](./STAGE-01.md) |
| Prova visual navegável (fixture) | `plugins/public-hub/src/apps/delpi-news/` → `/p/delpi-news/board/aberto` |

### Explicitamente fora da Etapa 1

- Criação de `delpi-news-api` e migrations
- Rotas OpenAPI / Action Catalog
- MFE admin e permissões Core
- Coleta real de RSS
- Integração playlist TV Dashboard
- Android / APK / device management

---

## 7. Referências

- `plugins/public-hub/README.md` — shell público canônico
- `docs/05-plugin-system/` — manifesto / MFE (admin futuro)
- `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
- `.cursor/rules/platform-architecture-boundaries.mdc`
- `.cursor/rules/english-code-identifiers.mdc`
