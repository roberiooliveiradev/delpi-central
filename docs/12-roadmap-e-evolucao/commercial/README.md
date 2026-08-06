# Portal Comercial — documentação

> **Status:** playbook oficial + F0–F2b harden + **Wave G** (shell/IA, Meu dia, worklist) em `main`; F2c pendente de homologação  
> **Nome ao usuário:** **Portal Comercial**  
> **Id técnico:** `commercial` · **basePath:** `/apps/commercial`  
> **API:** `commercial-api` · gateway `/apps/commercial-api/`

O **Portal Comercial** concentra jornadas de carteira, pedidos em aberto, Meu dia (worklist) e admin de vendedores. Reads TOTVS ficam na **api-delpi**; estado Delpi (carteira/avatar/tasks) na **commercial-api**.

O plugin `pedidos-venda-abertos` (Portal do Vendedor) **coexiste** até F2c. A UX operacional (KPIs, filtros, Excel, previsão OP, check-up) está no Portal Comercial — [runbook F2c](./F2C-CUTOVER-RUNBOOK.md).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| **[PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)** | Playbook mestre — matriz dores, fases, gates |
| **[IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md)** | Status executável F0–F2c + Wave G |
| **[DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md)** | Design de IA embarcada no Portal Comercial |
| **[PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)** | Papéis Minha Delpi × permission codes (Wave G) |
| **[HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md)** | Checklist / smoke Wave G |
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
| Wave G — Meu dia / worklist / tasks / activities + shell UI | **Entregue** (M2 parcial `V003`) |
| Compose + gateway + volume `commercial-avatars` | **Entregue** |
| `COMMERCIAL_PORTFOLIO_SOURCE=commercial` (default Compose) | **Entregue** — ops: backfill/reconcile |
| Homologação Comercial § 2.1.1 | **Pendente** (assinatura Comercial/QA) |
| F2c (ocultar PVA + redirects) | Artefatos prontos — flip após homologação |

## Pacotes e URLs

| Pacote | Papel | URL |
|--------|--------|-----|
| `commercial-api/` | Backend carteira/avatar | `/apps/commercial-api` |
| `plugins/commercial/` | MFE Portal Comercial | `/apps/commercial` |

Registrar manifesto: `TOKEN=… ./plugins/commercial/scripts/register-manifest.sh`  
README do plugin: [`plugins/commercial/README.md`](../../../plugins/commercial/README.md)

## Fronteira (resumo)

```text
MFEs analíticos + reads TOTVS de pedidos
  → api-delpi → TOTVS

Portal Comercial (carteira Delpi, admin, avatars)
  → commercial-api → Postgres (+ volume avatars)
  → commercial-api → api-delpi (search / enrichment)
```

**HTTPS:** clients usam paths relativos; `commercial-api` com `redirect_slashes=False` (evita Mixed Content atrás do TLS). Pedidos TOTVS na api-delpi usam barra final em `pedidos-venda-abertos/`.

## Ativos existentes

| Plugin | Papel | Destino |
|--------|--------|---------|
| `commercial` | **Portal Comercial** (entrada canônica da paridade) | Ativo |
| `dashboard-commercial` | Cockpit KPIs / OTD / propostas OV | Permanece |
| `pedidos-venda-abertos` | Portal do Vendedor | **Ativo** (coexiste até F2c real) |
| `propostas-comerciais` | Propostas ativas + PDF | Permanece |

## Fases

| Fase | Entrega | Status |
|------|---------|--------|
| F0–F2 | Docs, API, migrations, dual-read | Concluído |
| F2b | Paridade UX | **Concluído** (port PVA → commercial) |
| F2c | Depreciar PVA | Pendente homologação |
| F3–F4 | Runtime módulo + composição | Fora do escopo atual |
| F5–F7 | CRM / forecast / amostras | Fora do escopo atual |

## Referências

- [Checklist novo MFE](../../05-plugin-system/novo-plugin-mfe-checklist.md)
- [Registrar plugin](../../10-guias-operacionais/registrar-plugin.md)
- [Infra ambiente](../../../infra/README-ambiente.md) (volume avatars)
- Legado PVA: [pedidos-venda-abertos](../pedidos-venda-abertos/README.md)
