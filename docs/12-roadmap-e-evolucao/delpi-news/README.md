# DELPI News — fundação arquitetural

> **Status:** Etapa 1 fechada (prova visual segura). **Etapa 2.S1:** inventário + proposta ADR —  
> estado `ARCHITECTURE_DECISION_REQUIRED` (sem scaffold de API).  
> **Fora de escopo permanente nesta linha:** app Android TV / APK / gestão de dispositivos (projeto suspenso).

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
| **Pública** (`public-hub`) | Sem login interativo; token de board | Apresentação kiosk das notícias autorizadas | **E1: prova visual (demo gated)** |
| **Canal TV opcional** | Token TV Dashboard | Embutir URL do board como slide `external` allowlisted | Futura (não obrigatória no MVP) |

### Demonstração pública (E1)

| Item | Valor |
|---|---|
| Rota demo | `/p/delpi-news/board/demo` |
| Habilitação | `import.meta.env.DEV` **ou** `VITE_DELPI_NEWS_DEMO=1` |
| Produção padrão | mock **bloqueado** (404) |
| Token legado `aberto` | rejeitado |
| Conteúdo | fictício, banner inequívoco de demonstração |

---

## 3. Ownership e fronteiras

| Fronteira | Owner proposto | Estado | Não duplicar em |
|---|---|---|---|
| Domínio editorial + ingestão RSS | **`delpi-news-api`** (BC novo) | **PLANNED / TARGET** — **não** aprovado formalmente; exige decisão arquitetural da autoridade competente antes de criar o serviço | `external-data-api`, `tv-dashboard-api`, Core, Portal |
| Persistência | Schema próprio do BC News (se aprovado) | PLANNED | Banco de outro app |
| Página pública kiosk | `plugins/public-hub` app `delpi-news` | E1 parcial (demo) | Novo container `*-public` |
| Admin MFE | `plugins/delpi-news` | PLANNED | RBAC no cliente |
| AuthN/AuthZ admin | Keycloak + Core permissions | Padrão plataforma | Middleware ad hoc no hub |
| Playlist/slides Adeus | `tv-dashboard` + `tv-dashboard-api` | Existente (não owner de RSS) | — |
| Shell HTTPS `/p/*` | `public-hub` + gateway `^~ /p/` | Existente | Nova `location` por app |

### Decisão pendente — criação de `delpi-news-api`

Proposta formal para a autoridade competente:

- **[`adr/ADR-001-delpi-news-api-ownership.md`](./adr/ADR-001-delpi-news-api-ownership.md)** — status **PROPOSTO** (não é aprovação)
- Acompanhamento: [`STAGE-02.md`](./STAGE-02.md)

Até constar `STATUS: APPROVED` no ADR (com authority/data), `delpi-news-api` permanece hipótese.  
**E2.S2+ estão bloqueadas.**

### Decisão travada — `external-data-api`

| Campo | Valor |
|---|---|
| Mandato atual | Consultas cadastrais externas S2S (MVP CNPJ / BrasilAPI) |
| `EXISTING_EQUIVALENT` (RSS) | **NO** |
| `REUSE_DECISION` | **NEW** BC News **se** aprovado — **não** ampliar `external-data-api` sem ADR e mudança de mandato |

### Decisão travada — TV Dashboard

| Capacidade | Equivalente | Decisão |
|---|---|---|
| Kiosk Adeus / fit / token / heartbeat | YES | **REUSE** padrões de chrome `kiosk` e URL pública |
| Playlist / motor de slides | PARTIAL | **REUSE** só se News for URL embutida; **não** owner do feed |
| Agregação RSS / curadoria | NO | **NEW** no BC News **se** aprovado |

---

## 4. Inventário de reuso

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION | Owner | Evidência |
|---|---|---|---|---|
| Página pública HTTPS sem auth | YES | EXTEND `public-hub` | `plugins/public-hub` | README hub; `registry.ts` |
| Kiosk Adeus (chrome/fit) | YES (TV) | REUSE padrão `chrome: "kiosk"` | hub + TV presentation | `tv-dashboard/pages.tsx` |
| Gate de demo frontend | YES (DéLIA) | REUSE padrão `DEV` / `VITE_*_DEMO=1` | app `delpi-news` | `demoMode.ts` |
| Coleta RSS/Atom | NO | NEW (após decisão) | BC News (PLANNED) | Sem ingestão no monorepo |
| HTTP externo resiliente | PARTIAL | EXTEND no BC | regra resilience + caller | `http-integration-resilience.mdc` |

---

## 5. Arquitetura-alvo (condicional à aprovação do BC)

```text
┌─────────────────────┐     JWT + RBAC      ┌──────────────────┐
│ Portal / MFE admin  │ ──────────────────▶ │  delpi-news-api  │
│ (PLANNED)           │                     │  (PLANNED)       │
└─────────────────────┘                     └────────┬─────────┘
┌─────────────────────┐   token board                │
│ public-hub          │ ◀── GET /public/boards/{t} ──┘
│ apps/delpi-news     │
└─────────────────────┘
```

---

## 6. Entregáveis da Etapa 1

| Entrega | Path |
|---|---|
| Este índice + ownership | `README.md` |
| Contratos conceituais | [`CONTRACTS.md`](./CONTRACTS.md) |
| Aceite / fechamento E1 | [`STAGE-01.md`](./STAGE-01.md) |
| E2.S1 — decisão / inventário | [`STAGE-02.md`](./STAGE-02.md) · [`adr/ADR-001…`](./adr/ADR-001-delpi-news-api-ownership.md) |
| Homologação Adeus | [`HOMOLOGACAO-ADEUS-PENDRIVE.md`](./HOMOLOGACAO-ADEUS-PENDRIVE.md) |
| Prova visual (demo gated) | `plugins/public-hub/src/apps/delpi-news/` → `/p/delpi-news/board/demo` |

### Explicitamente fora da Etapa 1

- Criação de `delpi-news-api` e migrations
- Rotas OpenAPI / Action Catalog
- MFE admin e permissões Core
- Coleta real de RSS
- Integração playlist TV Dashboard
- Android / APK / device management

---

## 7. Referências

- `plugins/public-hub/README.md`
- `docs/05-plugin-system/`
- `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
- `.cursor/rules/platform-architecture-boundaries.mdc`
- `.cursor/rules/english-code-identifiers.mdc`
