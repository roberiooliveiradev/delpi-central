# Portal Comercial — documentação

> **Status:** Wave G+ em `main` + **consolidação nativa** (Gestão / Propostas ADY / elevar operacional) — ver [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)  
> **Nome ao usuário:** **Portal Comercial**  
> **Id técnico:** `commercial` · **basePath:** `/apps/commercial`  
> **API:** `commercial-api` · gateway `/apps/commercial-api/`

O **Portal Comercial** é a UX canônica a evoluir: carteira, pedidos, Meu dia, **Gestão à vista** (páginas nativas) e **Propostas documento**. Reads TOTVS na **api-delpi**; estado Delpi na **commercial-api**. **Zero hosteamento** de MFEs irmãos.

Plugins `pedidos-venda-abertos`, `dashboard-commercial` e `propostas-comerciais` **coexistem** no menu (decisão 5C); remoção só no futuro. F2c cutover **não** é pré-requisito da consolidação.

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| **[GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)** | **Norte consolidação** — nav, perms, DoD, filtros, OV vs ADY |
| **[PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)** | Playbook mestre — matriz dores, fases, gates |
| **[IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md)** | Status executável F0–F2 + consolidação nativa |
| **[DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md)** | Design de IA / navegação / princípios UX |
| **[UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md)** | UX polish entregue + backlog tarefas (obs./responsável/anexos) |
| **[PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)** | Papéis Minha Delpi × permission codes (Wave G) |
| **[HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md)** | Checklist / smoke Wave G+ (P0 + P1) |
| **[HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md)** | Checklist de paridade (assinatura Comercial/QA) |
| **[F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)** | Ocultar PVA + redirects (após homologação) |
| **[KPI-FICHAS.md](./KPI-FICHAS.md)** | Fichas KPI (F0) |
| **[API-ROUTES.md](./API-ROUTES.md)** | Catálogo commercial-api + api-delpi |
| **[DATA-MODEL.md](./DATA-MODEL.md)** | Tabelas Postgres schema `commercial` |
| **[WIREFRAMES.md](./WIREFRAMES.md)** | Wireframes WF-01–10 (+ WF-01R / Meu dia) |
| **[PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)** | Fronteira api-delpi × commercial-api |
| **[INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)** | Baseline de rotas, plugins e gaps |
| **[adr/ADR-001-commercial-api.md](./adr/ADR-001-commercial-api.md)** | ADR — API própria e migração carteira |
| **[adr/ADR-002-deprecar-pedidos-venda-abertos.md](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)** | ADR — depreciação Portal do Vendedor |

## Estado da implementação (ago/2026)

| Entrega | Estado |
|---------|--------|
| `commercial-api/` (health, JWT, portfolios, avatars, proxy search/enrich) | **Entregue** |
| `plugins/commercial/` (home, open-orders, customers, detail, seller-portfolios) | **Entregue** (paridade F2b harden) |
| Wave G+ — Meu dia CRM / Conta follow-up / Home gestão / UnderlineNav | **Entregue** (P0+P1; M2 parcial `V003`) |
| UX polish Home + Meu dia (PageHero, anti-redundância) | **Entregue** — [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 1 |
| Tasks: observação UI · responsável · anexos | **Backlog** P0–P2 — mesmo doc § 3 |
| Compose + gateway + volume `commercial-avatars` | **Entregue** |
| `COMMERCIAL_PORTFOLIO_SOURCE=commercial` (default Compose) | **Entregue** — ops: backfill/reconcile |
| Homologação Comercial § 2.1.1 | **Pendente** (assinatura Comercial/QA) |
| **Consolidação nativa** (Gestão + ADY + elevar ops) | **Em curso** — [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) |
| F2c (ocultar PVA + redirects) | **Adiado** — só após Comercial ≥ PVA + pedido |

## Pacotes e URLs

| Pacote | Papel | URL |
|--------|--------|-----|
| `commercial-api/` | Backend carteira/avatar | `/apps/commercial-api` |
| `plugins/commercial/` | MFE Portal Comercial | `/apps/commercial` |

Registrar manifesto: `TOKEN=… ./plugins/commercial/scripts/register-manifest.sh`  
README do plugin: [`plugins/commercial/README.md`](../../../plugins/commercial/README.md)

## Fronteira (resumo)

```text
Portal Comercial (páginas nativas)
  → commercial-api → Postgres (carteira / Meu dia / avatars)
  → api-delpi → TOTVS (pedidos, KPIs, OTD, OV, ADY)

MFEs irmãos (legado coexistente)
  → api-delpi → TOTVS
```

**HTTPS:** clients usam paths relativos; `commercial-api` com `redirect_slashes=False` (evita Mixed Content atrás do TLS). Pedidos TOTVS na api-delpi usam barra final em `pedidos-venda-abertos/`.

## Ativos existentes

| Plugin | Papel | Destino |
|--------|--------|---------|
| `commercial` | **Portal Comercial** (entrada canônica da paridade) | Ativo |
| `dashboard-commercial` | Cockpit KPIs / OTD / OV (legado coexistente) | Referência até Gestão nativa |
| `pedidos-venda-abertos` | Portal do Vendedor | **Ativo** (coexiste; cutover F2c adiado) |
| `propostas-comerciais` | Propostas ADY + PDF (legado) | Referência até Propostas nativas |

## Fases

| Fase | Entrega | Status |
|------|---------|--------|
| F0–F2 | Docs, API, migrations, dual-read | Concluído |
| F2b | Paridade UX operacional | **Concluído** (port PVA → commercial) |
| **Consolidação nativa** | Gestão + Propostas ADY + elevar ops | **Em curso** — [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) |
| F2c | Depreciar PVA | **Adiado** (só após Comercial superar + pedido) |
| P3 CRM | Reminder/checklist avançado | **Bloqueado** até consolidação |
| F3–F4 | Runtime módulo | Fora do escopo atual |

## Referências

- [Checklist novo MFE](../../05-plugin-system/novo-plugin-mfe-checklist.md)
- [Registrar plugin](../../10-guias-operacionais/registrar-plugin.md)
- [Infra ambiente](../../../infra/README-ambiente.md) (volume avatars)
- Legado PVA: [pedidos-venda-abertos](../pedidos-venda-abertos/README.md)
