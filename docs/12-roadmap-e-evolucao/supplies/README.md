# Portal Suprimentos — documentação mestra

> **Status (set/2026):** baseline + **E1–E6 concluídas (2026-09-08)** · MFE `plugins/supplies` + GATE-RBAC local  
> **Readiness:** **GATE-E1 + GATE-ARCH + GATE-AUTHZ + GATE-RBAC PASS (local)**  
> **Modo de entrega:** **uma página por vez até DoD** — não abrir a próxima enquanto a atual não estiver fechada  
> **Página em foco:** **Solicitações de compras (WF-04)** — revalidar DoD C1  
> **Última fechada:** **OTD analytics (WF-OTD-A)** + polish Overview **WF-02R** — DoD fechado  
> **Fila após SC:** Pedidos de compra (E7) → Entregas → …  
> **Id técnico:** `supplies` · **basePath:** `/apps/supplies`  
> **API:** `supplies-api` · gateway `/apps/supplies-api/`  
> **Classe CSS root:** `.dashboard-supplies-portal`

O Portal Suprimentos é o hub operacional, analítico e gerencial do domínio de Suprimentos na Minha DELPI. Substitui progressivamente a experiência fragmentada por jornadas coesas, preservando bounded contexts, RBAC central, paridade e rollback.

**Esta pasta é contrato de produto/arquitetura. Não autoriza implementação, cutover ou remoção de legados sem pedido explícito do Product Owner.**

---

## 1. Readiness atual

| Item | Estado |
|---|---|
| Baseline de produto | concluída |
| Arquitetura alvo | concluída |
| **E1 (descoberta + freeze)** | **concluída 2026-09-08** |
| **E2 (supplies-api foundation)** | **concluída 2026-09-08** — Flask, GATE-AUTHZ, schema `supplies`, gateway api-delpi, `/me/capabilities` |
| **E3 (MFE + RBAC coexistência)** | **concluída 2026-09-08** — `plugins/supplies`, client BFF-only, shell capability-driven, manifest Core, papéis canônicos |
| **E4 (Home + Ajuda inicial)** | **concluída 2026-09-08** — `/home/attention`, Home capability-driven, Manual/Quero→onde/FAQ/glossário |
| **E5 (Overview)** | **concluída 2026-09-08** — overview + série OTD + MFE kit; **WF-02 FECHADA**; polish **WF-02R** + **WF-OTD-A** (gauges `/analytics/otd`) |
| **E6 (SC C1)** | **concluída 2026-09-08** — BFF `/purchase-requests*` → PR-api; lista/detalhe/export no Portal; evidência C2 |
| RBAC alvo | revisado; menor catálogo suficiente (ADR-007) |
| Authz Core-first | **GATE-AUTHZ PASS** (fail-closed na fronteira; não usa claims JWT) |
| Framework supplies-api | Flask — pacote `supplies-api/` no monorepo |
| BIs externos | dump **local** 0/6 documentado (ADR-005); **dump prod** obrigatório antes do cutover |
| Papéis SC/ES | papéis canônicos provisionados no Core local; Comprador ES = N/A_LOCAL até usuário operacional |
| KPIs Overview P0 | **7 CONFIRMADOS**; cobertura/PO-LATE fora do Overview |
| Manifest draft | **`schemaVersion 1.0.0`** registrado no Core local |
| P-13 | **FECHADO** — Core `/me.id` UUID |
| Implementação MFE | **modo página-a-página** · **Início + Visão geral + OTD analytics fechados** · foco = **SC**; E7+ só após fechar a fila |

### Gates

| Gate | Estado |
|---|---|
| **GATE-E1** | **PASS** |
| **GATE-ARCH** | **PASS** |
| **GATE-AUTHZ** | **PASS** (E2.S2) |
| **GATE-API** | **PASS** parcial — health/gateway/Compose + Overview + SC BFF C1; ops ainda E7+ |
| **GATE-RBAC** | **PASS (local 2026-09-08)** — papéis canônicos + evidence `evidence/e3-s5-rbac-smoke-local.json`; persona negativa user-level pendente de user não-superadmin |

### Protocolo de entrega — uma página por vez

**Regra:** não iniciar implementação de uma página nova enquanto a página em foco não estiver **fechada** (DoD abaixo). Polimento transversal do shell só entra se for material à página em foco.

| # | Página | Rota | Estado |
|---|---|---|---|
| 1 | **Início** | `/apps/supplies` | **FECHADA (DoD)** |
| 2 | **Visão geral** | `/overview` | **FECHADA (DoD)** · **WF-02R** |
| — | **OTD analytics** | `/analytics/otd` | **FECHADA (DoD)** · **WF-OTD-A** (satélite analytics; ≠ WF-11) |
| 3 | Solicitações de compras | `/purchase-requests` | **EM FOCO** — revalidar DoD C1 |
| 4 | Pedidos de compra | `/purchase-orders` | placeholder → E7 |
| 5 | Entregas | `/deliveries` | placeholder → E7 |
| 6 | Demais ops/analíticos/admin | ver WIREFRAMES | fila após E7 |

**DoD de página (GATE-FEATURE):**

1. Contrato/BFF no owner (ou composição explícita) quando a página lê/escreve dados.
2. UI kit-first (PagePath/PageHero/SectionCard/estados) no padrão Comercial.
3. AuthZ backend-first + UX de 403/empty coerente.
4. Estados: loading, empty, error, partial (se aplicável), 403, 404.
5. Ajuda no mesmo entregável (`feature-help-sync`: tooltips + Quero→onde/FAQ se conceito novo).
6. Testes positive + sibling + negative (API e/ou MFE estrutural).
7. Docs de readiness/WIREFRAMES/API-ROUTES atualizados; sem “entra depois” na página fechada.
8. Sem abrir subtarefas da **próxima** página no mesmo PR/plano, salvo satélite explícito (ex.: Ajuda).

**Não fazer:** paralelo de duas páginas user-facing; “já deixar E7 esqueleto” enquanto o Início estiver em foco; misturar cutover/C2 com UI da página atual.

### Próximo passo operacional

1. **Revalidar Solicitações de compras (WF-04)** contra o DoD C1.
2. Depois **E7 Pedidos de compra** (uma de cada vez).
3. E7+ continua exigindo autorização explícita do Product Owner **e** página anterior fechada na fila.

**Visão geral (WF-02 / WF-02R) — DoD fechado:** BFF `/analytics/overview` + `/analytics/otd/series`, PageHero + FilterBar MultiSelect Unidade (SC/ES) + URL sync, 7 KPIs, ChartViewShell OTD completo + CTA «Abrir OTD», comparativo valor×meta, Ajuda, testes API+MFE.

**OTD analytics (WF-OTD-A) — DoD fechado:** BFF `GET /analytics/otd`, página `/analytics/otd` com SpeedometerGauge por unidade + série, filtros compartilhados com Overview, Ajuda Quero→onde/FAQ.

**Início (WF-01) — DoD fechado:** BFF `/home/attention`, PageHero + hub kit, Favoritos TopBar (localStorage P0), helps, loading/error/partial/empty, AuthZ portal, testes API+MFE.

Dump Core de produção **não** bloqueia a fila de páginas; bloqueia decisão final de redirects/BIs no cutover.

---

## 2. Identidade congelada

| Superfície | Valor |
|---|---|
| Plugin id | `supplies` |
| basePath MFE | `/apps/supplies` |
| API | `supplies-api` · `/apps/supplies-api` |
| Framework API | **Flask** conforme instrução oficial vigente |
| CSS root | `.dashboard-supplies-portal` |
| Prefixo tokens | `--sp-*` → `--delpi-ui-*` |
| Permission de entrada | `supplies.portal.access` |

ADRs principais: [ADR-001](./adr/ADR-001-supplies-api.md) · [ADR-004](./adr/ADR-004-plugin-identity-and-css-root.md) · [ADR-006](./adr/ADR-006-unit-permissions.md) · [ADR-007](./adr/ADR-007-permission-minimization.md).

---

## 3. Arquitetura alvo

```text
Browser
  → Minha DELPI Portal
    → plugins/supplies
      → supplies-api
          ├── Core API /me (effective permissions)
          ├── PostgreSQL próprio (estado Minha DELPI)
          ├── purchase-requests-api (C1, até absorção C2)
          ├── strategic-indicators-api
          ├── contextos irmãos quando autorizado
          └── api-delpi → TOTVS
```

Regras:

- MFE nunca chama api-delpi direto;
- JWT identifica/autentica; Core resolve permissions efetivas;
- autorização = capability + unidade + resource scope/ownership + business rule;
- SQL/regra TOTVS permanecem na api-delpi;
- estado do produto pertence à supplies-api;
- capabilities não devem espelhar CRUD.

---

## 4. Documentos

| Documento | Conteúdo |
|---|---|
| [00-DIAGNOSTICO.md](./00-DIAGNOSTICO.md) | cenário atual e dores |
| [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) | ativos e decisões |
| [PERSONA-EXPERIENCE-MAP.md](./PERSONA-EXPERIENCE-MAP.md) | personas × apps × permissions |
| [DUPLICIDADES-E-SOBREPOSICOES.md](./DUPLICIDADES-E-SOBREPOSICOES.md) | overlaps e drifts |
| [MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md) | ownership |
| [PLAYBOOK-MODULO-SUPRIMENTOS.md](./PLAYBOOK-MODULO-SUPRIMENTOS.md) | playbook mestre |
| [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md) | fronteira BFF × TOTVS |
| [DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md) | IA/UX |
| [WIREFRAMES.md](./WIREFRAMES.md) | wireframes |
| [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) | RBAC mínimo + unidade + aliases |
| [MANIFEST-DRAFT.md](./MANIFEST-DRAFT.md) | contrato futuro do plugin |
| [API-ROUTES.md](./API-ROUTES.md) | contratos BFF |
| [DATA-MODEL.md](./DATA-MODEL.md) | estado Postgres |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | indicadores |
| [INTEGRACOES.md](./INTEGRACOES.md) | HTTP, authz, observabilidade |
| [HELP-AND-ONBOARDING.md](./HELP-AND-ONBOARDING.md) | Ajuda |
| [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) | plano executável; deve obedecer C1→C2→C3 |
| [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) | paridade mensurável |
| [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md) | target-first, redirect-last |
| [DECISOES_FUNCIONAIS_PENDENTES.md](./DECISOES_FUNCIONAIS_PENDENTES.md) | pendências reais |

### ADRs

| ADR | Decisão |
|---|---|
| ADR-001 | supplies-api, Flask, authz Core-first |
| ADR-002 | absorção progressiva purchase-requests-api C0→C3 |
| ADR-003 | coexistência/cutover |
| ADR-004 | identidade do plugin/CSS |
| ADR-005 | BIs externos precisam de dump Core |
| ADR-006 | unidade ortogonal |
| ADR-007 | minimização de permissions |

---

## 5. Decisões travadas

1. `supplies` + `supplies-api` + `/apps/supplies`.
2. supplies-api em Flask enquanto a instrução oficial vigente assim determinar.
3. MFE fala apenas com supplies-api.
4. Authz real usa effective permissions do Core; não claims de permission do JWT.
5. RBAC usa **menor catálogo suficiente**, não CRUD por permission.
6. Unidade é eixo ortogonal `supplies.unit.filial-{TOTVS}`.
7. `purchase-requests-api`: C0 coexistência → C1 composição → C2 ownership/jobs → paridade final → C3 cutover.
8. Home ≠ Overview.
9. Páginas generalistas no padrão Comercial: shell, Início, Ajuda (`/help`), perfil do plugin (`/users/:userId`); preferências no perfil (sem `/preferences` dedicado). Perfil global Minha DELPI permanece em `/profile` do host.
10. Kit-first e CSS isolado.
11. Cutover só após paridade e BIs externos classificados.

---

## 6. Gates

| Gate | Critério |
|---|---|
| **GATE-AUTHZ** | Core-first; fail-closed na fronteira; **PASS E2.S2** |
| **GATE-E1** | **PASS** (2026-09-08) — dump local + papéis + KPIs; residual dump prod antes do cutover |
| **GATE-ARCH** | **PASS** (2026-09-08) — ADRs + Manifest Draft `1.0.0` |
| **GATE-RBAC** | permissions canônicas + papéis de coexistência + `/me`/`/me/apps` (rotas embutidas) |
| **GATE-API** | supplies-api saudável e MFE sem api-delpi direto |
| **GATE-MFE** | shell kit-first e CSS isolado |
| **GATE-FEATURE** | contrato + authz + Ajuda + testes |
| **GATE-C2** | ownership SC/jobs reconciliado antes de C3 |
| **GATE-PARITY** | dados/funcionalidades comparados com evidência quantitativa |
| **GATE-CUTOVER** | todos os legados/BIs em estado final + target saudável + RBAC + rollback |

---

## 7. Fora de escopo nesta documentação

- implementação produtiva;
- escrita no TOTVS;
- remoção de legados;
- ativação de redirects;
- mudança de RBAC real;
- migrations produtivas.
