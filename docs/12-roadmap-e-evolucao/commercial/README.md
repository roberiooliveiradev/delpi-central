# Portal Comercial — documentação

> **Status (set/2026):** Wave G+ + consolidação nativa em curso · **F2c executado** (MFEs PVA e propostas-comerciais removidos; redirects ativos) — [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md) · [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) · carteiras multi-membro [WIREFRAMES.md](./WIREFRAMES.md) WF-05R · [HOMOLOGACAO-CARTEIRAS-MULTI.md](./HOMOLOGACAO-CARTEIRAS-MULTI.md) · refino visual [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md)  
> **Nome ao usuário:** **Portal Comercial**  
> **Id técnico:** `commercial` · **basePath:** `/apps/commercial`  
> **API:** `commercial-api` · gateway `/apps/commercial-api/`

O **Portal Comercial** é a UX canônica: carteira (N membros), pedidos, Meu dia, **Gestão à vista**, **Propostas documento (ADY)** e Sala. Reads TOTVS na **api-delpi** (via BFF); estado Delpi na **commercial-api**. **Zero hosteamento** de outros MFEs.

**Legado:** apenas `dashboard-commercial` permanece coexistente (referência até Gestão nativa fechar). Os MFEs `pedidos-venda-abertos` e `propostas-comerciais` foram **retirados** do Compose e do código; deep links redirecionam para `/apps/commercial/*` ([F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)).

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| **[MANUAL-USUARIO-PORTAL-COMERCIAL.md](./MANUAL-USUARIO-PORTAL-COMERCIAL.md)** | **Manual do usuário** — “Quero…” → onde ir + FAQ |
| **[GLOSSARIO-TERMOS.md](./GLOSSARIO-TERMOS.md)** | **Termos relacionados** — Incoterm (EXW/FOB/CIF), data de entrega × despacho × OP × faturamento |
| **[TREINAMENTO-PORTAL-COMERCIAL-1H.md](./TREINAMENTO-PORTAL-COMERCIAL-1H.md)** | **Roadmap treinamento 1h** — mapa de funcionalidades, agenda, FAQ por tópico |
| **[GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)** | **Norte consolidação** — nav, perms, DoD, filtros, OV vs ADY |
| **[PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)** | Playbook mestre — matriz dores, fases, gates |
| **[IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md)** | Status executável F0–F2 + consolidação nativa |
| **[DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md)** | Design de IA / navegação / princípios UX |
| **[UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md)** | UX polish + tarefas P0–P2 **entregues**; P3 reminder backlog |
| **[ROADMAP-INTERACTION-ROOM.md](./ROADMAP-INTERACTION-ROOM.md)** | Sala de interação — layout Teams / fill / composer markdown (**entregue** E1–E7; ver roadmap) |
| **[PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)** | Papéis Minha Delpi × permission codes (Wave G + E5.1) |
| **[HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md)** | Checklist / smoke Wave G+ (P0 + P1) |
| **[HOMOLOGACAO-CARTEIRAS-MULTI.md](./HOMOLOGACAO-CARTEIRAS-MULTI.md)** | Smoke MVP multi-membro (E5.2) + comandos de regressão |
| **[HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md)** | Checklist de paridade (assinatura Comercial/QA) |
| **[F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)** | **F2c executado** — remoção MFEs + redirects + comandos prod |
| **[KPI-FICHAS.md](./KPI-FICHAS.md)** | Fichas KPI (F0) — Onda A C1 (baseline código; assinatura formal opcional) |
| **[KPI-HOMOLOGACAO-ONDA-A.md](./KPI-HOMOLOGACAO-ONDA-A.md)** | Workshop homologação ROL / carteira / hit rate |
| **[API-ROUTES.md](./API-ROUTES.md)** | Catálogo commercial-api + api-delpi |
| **[DATA-MODEL.md](./DATA-MODEL.md)** | Tabelas Postgres schema `commercial` (`seller_portfolio_members`) |
| **[crm-sigatec.md](../../../../api-delpi/docs/api/padroes-totvs/crm-sigatec.md)** | Censo vivo SIGATEC (19 ago 2026): 3767 OVs, funil COMPONENTES 82%, `AD8` vazio — [playbook SX3](../../../../api-delpi/docs/api/padroes-totvs/playbooks/playbook-crm-totvs-dicionario.md) |
| **[WIREFRAMES.md](./WIREFRAMES.md)** | Wireframes WF-01–10 (+ WF-01R / Meu dia / WF-05R multi-membro) |
| **[playbook-mfe-page-excellence.md](../../05-plugin-system/playbook-mfe-page-excellence.md)** | Excelência lista+detalhe MFE (P0–P2) — caso Pedidos / WF-02R |
| **[PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)** | Fronteira api-delpi × commercial-api |
| **[INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)** | Baseline de rotas, plugins e gaps |
| **[ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md)** | Ata × Portal — temos/falta/onde acessar + ondas A–E + **ecossistema MFEs** (§7) |
| **[ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md](./ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md)** | Follow-up ata — pedidos/Kanban, carteira YoY, Meu Dia×frota, perfis/notif, colaboração Teams/Outlook |
| **[ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md)** | **Ata alinhamento 2** — meta proporcional, rename faturamento, confirmação, sala, Diretoria, MyVEG; **GR → TV Dashboard** |
| **[PARCIAL-INVENTARIO.md](./PARCIAL-INVENTARIO.md)** | **Inventário Parcial** deduplicado — W0 (implementação) + backlog W1–W5 + Homolog/Fora |
| **[HELP-COVERAGE.md](./HELP-COVERAGE.md)** | Cobertura de help (`hint` / `headerHint`) no MFE |
| **[adr/ADR-001-commercial-api.md](./adr/ADR-001-commercial-api.md)** | ADR — API própria e migração carteira |
| **[adr/ADR-002-deprecar-pedidos-venda-abertos.md](./adr/ADR-002-deprecar-pedidos-venda-abertos.md)** | ADR — depreciação Portal do Vendedor |
| **[GAV-TV-FEED.md](./GAV-TV-FEED.md)** | Fontes Overview → TV Dashboard (GR); Comercial só Link |

## Estado da implementação (set/2026)

| Entrega | Estado |
|---------|--------|
| `commercial-api/` (health, JWT, portfolios, avatars, proxy search/enrich) | **Entregue** |
| `plugins/commercial/` (home, open-orders, customers, detail, seller-portfolios, proposals, overview) | **Entregue** (paridade F2b + ADY nativo) |
| **E5 multi-membro** — `V005`, lista full-page, detalhe `/seller-portfolios/:id`, org, escopo | **Entregue** — [WIREFRAMES.md](./WIREFRAMES.md) · [HOMOLOGACAO-CARTEIRAS-MULTI.md](./HOMOLOGACAO-CARTEIRAS-MULTI.md) |
| **E6 mercado** — overlapping, carga, timeline, badge Conta, bulk+Excel | **Entregue** — [WIREFRAMES.md](./WIREFRAMES.md) WF-05R · [API-ROUTES.md](./API-ROUTES.md) |
| Wave G+ — Meu dia CRM / Conta follow-up / Home gestão / UnderlineNav | **Entregue** (P0+P1; M2 parcial `V003`) |
| UX polish Home + Meu dia (PageHero, anti-redundância) | **Entregue** — [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 1 |
| Tasks: observação UI · responsável · anexos | **Entregue** P0–P2 — mesmo doc § 3; P3 reminder backlog |
| Compose + gateway + volume `commercial-avatars` | **Entregue** |
| `COMMERCIAL_PORTFOLIO_SOURCE=commercial` (default Compose) | **Entregue** — ops: backfill/reconcile |
| Homologação Comercial § 2.1.1 (assinatura QA) | **Pendente** (checklist técnico [x]; assinatura Comercial/QA) |
| **Consolidação nativa** (Gestão + ADY + elevar ops) | **Em curso** — [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) |
| **F2c** (remover PVA + propostas MFE + redirects) | **Executado** (set/2026) — [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md) |
| **E7** mapa · AI carve · rotate leads · inbox e-mail | **Backlog futuro** — [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 6 |
| **Sala de interação** — fill, chips, drawer, composer markdown | **Entregue** (E1–E7) — [ROADMAP-INTERACTION-ROOM.md](./ROADMAP-INTERACTION-ROOM.md) |
| Dívida E6 — gap «sem cobertura» + agregação TOTVS no `load-summary` | **Entregue** — universo = clientes com pedido aberto; `filter=uncovered` + métricas no load-summary |
| **Refino visual + IA** — Início apps\|eventos, Overview BI, filtro carteira, Equipe→Admin, Conta Opp, CM_HELP, C17 row→detalhe | **Entregue** — [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md) · [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) § Homologação |
| **Onda A cockpit C1** — presets período, carteira aberta, série hit rate, fichas | **Entregue** (baseline) — [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) § 4 · [KPI-FICHAS.md](./KPI-FICHAS.md) |
| **Onda B YoY Overview** — overlay ano anterior em ROL + conversão | **Entregue** — [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) § 4 · [WIREFRAMES.md](./WIREFRAMES.md) WF-OV |
| **MVP KPI-CARTEIRA-HORIZON** — gap vs meta + buckets + deep links | **Entregue** — BFF `open-portfolio-horizon` · [KPI-FICHAS.md](./KPI-FICHAS.md) · [API-ROUTES.md](./API-ROUTES.md) |
| **B-fecho docs** — matriz rotas×WF + README/GESTAO/helps + polish carteira≠PCP | **Entregue** — [WIREFRAMES.md](./WIREFRAMES.md) matriz · [HELP-COVERAGE.md](./HELP-COVERAGE.md) |
| **Ata alinhamento 2** — inventário meta/rename/confirmação/sala/Diretoria/MyVEG; GR→TV | **Entregue (docs)** — [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) |
| **Inventário Parcial + W0** — meta SI, labels, rename, filtros Conta, OTD copy, favoritos | **Existe** (W0) + revisão código + **§ Bloqueado por `.cursor`** — [PARCIAL-INVENTARIO.md](./PARCIAL-INVENTARIO.md) |
| **Próximo produto** — Ondas C–E (SLA operacional, FNE, confirmação) | **Backlog** — [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) § 4 · [PARCIAL-INVENTARIO.md](./PARCIAL-INVENTARIO.md) |

Helps do MFE (incl. chip **Escopo** = identidade da sessão, não filtro) vivem em `plugins/commercial/src/content/helpTooltips.ts`. Catálogo ao usuário (definição + onde aparece): Ajuda `/help` · `userManualTermCatalog.ts`.

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
  → commercial-api → Postgres (carteira N:N / Meu dia / avatars / sala)
  → commercial-api → api-delpi → TOTVS (pedidos, KPIs, OTD, OV, ADY)

dashboard-commercial (legado coexistente)
  → api-delpi → TOTVS
```

**HTTPS:** clients usam paths relativos; `commercial-api` com `redirect_slashes=False` (evita Mixed Content atrás do TLS). Paths TOTVS na api-delpi (ex. `pedidos-venda-abertos/`, `propostas-comerciais/`) permanecem como contrato BFF — **não** como app MFE.

## Ativos existentes

| Plugin | Papel | Destino |
|--------|--------|---------|
| `commercial` | **Portal Comercial** (UX canônica) | **Ativo** |
| `dashboard-commercial` | Cockpit KPIs / OTD / OV (legado) | Referência até Gestão nativa |
| `pedidos-venda-abertos` | Portal do Vendedor | **Removido** (F2c) — redirects → `/apps/commercial/*` |
| `propostas-comerciais` | Propostas ADY legado | **Removido** (F2c) — redirects → `/apps/commercial/proposals` |

## Fases

| Fase | Entrega | Status |
|------|---------|--------|
| F0–F2 | Docs, API, migrations, dual-read | Concluído |
| F2b | Paridade UX operacional | **Concluído** (port PVA → commercial) |
| **E5.1** | Carteiras multi-membro (lista + detalhe + org + escopo) | **Concluído** (MVP) |
| **Consolidação nativa** | Gestão + Propostas ADY + elevar ops | **Em curso** — [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) |
| **F2c** | Remover MFEs PVA + propostas; redirects | **Executado** (set/2026) — [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md) |
| Ondas C–E | SLA ofertas, FNE, confirmação, sensíveis | **Próximo** — [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) |
| P3 CRM | Reminder/checklist avançado | **Bloqueado** / backlog |
| F3–F4 | Runtime módulo | Fora do escopo atual |

## Referências

- [Checklist novo MFE](../../05-plugin-system/novo-plugin-mfe-checklist.md)
- [Registrar plugin](../../10-guias-operacionais/registrar-plugin.md)
- [Infra ambiente](../../../infra/README-ambiente.md) (volume avatars)
- Histórico PVA (docs): [pedidos-venda-abertos](../pedidos-venda-abertos/README.md)
- Cutover: [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md)
