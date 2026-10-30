# IMPLEMENTATION-PLAN — Portal Suprimentos

> **Atualização (2026-10-30):** writes de fornecedor POST/PUT **liberadas em produção** — verificação de runtime `SURI-MCP-SUPPLIERS-WRITE-001` (gates `=true`, UPDATE end-to-end até REST, CREATE gate aberto). As notas históricas «Escrita Protheus continua OFF»/«sem escrita ERP» deste documento referem-se ao período X4.PROD-C1 anterior ao cutover. SURI MCP publicou `execute(entity=suppliers, create|update)` no contract freeze rev.3.
> **Status (revalidado 2026-09-21, `4f3ed59483`):** plano executável revisado segundo `evidence-driven-execution.mdc`, `plan-construction.mdc` e `plan-execution.mdc`.
> **Entregue:** E1–E8 (incluindo E8 / WF-06 detalhe do pedido). GATE-FEATURE WF-06 = **PASS** ([evidência](./evidence/e8-wf06-federated-runtime-gate.md)).
> **Entregue adicional:** E9 / WF-07 — **GATE-FEATURE WF-07 = PASS** após recovery redeploy ([evidência](./evidence/e9-wf07-federated-runtime-gate.md)).
> **Em foco:** **E10 / WF-15 Controle de Estoques** — **IN PROGRESS** · S1–S3 PASS · **E10.S4 INCONCLUSIVE** (Help+BFF local PASS; federated deploy pending).
> **Próxima receita:** deploy federado MFE supplies → re-smoke → GATE E10 — **não iniciar E11**.
> **Reconciliação 2026-10-22:** **E13 / WF-09** e **E14 / WF-10** entregues fora de ordem sob a autorização de frente prioritária `FORNECEDORES-RETOMADA-IMPLEMENTACAO-2026-10-20.md` (lista, ficha, inclusão e edição com gates; E2E backend/runtime ACCEPT em `X3-RUNTIME-EVIDENCE-20261022.md`). E10 permanece inalterado e não foi promovido. X4 é incremento de E14 — não página nova.
> **Modo:** uma página user-facing por vez; etapas futuras abaixo são fila/grafo, não autorização automática.

Referências: [README](./README.md), ADR-001..ADR-007, [WIREFRAMES](./WIREFRAMES.md), [API-ROUTES](./API-ROUTES.md), [DECISOES_FUNCIONAIS_PENDENTES](./DECISOES_FUNCIONAIS_PENDENTES.md), [HOMOLOGACAO-PARIDADE](./HOMOLOGACAO-PARIDADE.md).

---

## 1. Objetivo e arquitetura alvo

Entregar o Portal Suprimentos como hub capability-driven sem romper boundaries:

```text
Portal
→ MFE supplies
→ supplies-api (Flask)
→ Core /me + /me/apps
→ api-delpi / strategic-indicators-api / purchase-requests-api / contextos autorizados
```

Invariantes:

- MFE não chama `api-delpi` diretamente;
- JWT identifica; Core resolve effective permissions;
- autorização = capability + unit + resource scope/ownership + business rule;
- não espelhar TOTVS no Postgres;
- não inflar RBAC por CRUD;
- `@delpi/plugin-ui` primeiro para componente reutilizável;
- Ajuda acompanha a feature;
- C1 → C2 → paridade → C3 para Purchase Requests;
- não usar `/me/routes`; validar rotas autorizadas em `/me/apps` (`apps[].routes`).

---

## 2. Ledger de requisitos do programa

| RQ | Requisito | Estado no plano |
|---|---|---|
| RQ-01 | Hub único de Suprimentos com shell capability-driven | ATENDIDO — E3/E4 |
| RQ-02 | MFE BFF-only | ATENDIDO — E3 |
| RQ-03 | AuthZ Core-first e fail-closed | ATENDIDO — E2; revalidar por feature |
| RQ-04 | Unit/resource scope coerente | HERDADO transversalmente; testar em cada página |
| RQ-05 | Overview/OTD com KPIs e metas SI canônicas | ATENDIDO — E5 |
| RQ-06 | SC C1 funcional + DoD da página | ATENDIDO — E6.S1–S5 |
| RQ-07 | Pedidos de Compra (lista) | ATENDIDO — E7 |
| RQ-08 | Detalhe do Pedido | ATENDIDO — E8 implementado; GATE-FEATURE WF-06 `PASS` |
| RQ-09 | Entregas/Atrasos | ATENDIDO_NO_PLANO — promoção + P0 freeze; implementação = receita E9.S* |
| RQ-10 | Estoque | BLOQUEADO pela fila — E10 |
| RQ-11 | ESTSEG | BLOQUEADO pela fila — E11 |
| RQ-12 | Análise de Consumo | BLOQUEADO pela fila — E12 |
| RQ-13 | Fornecedores / Supplier 360 / OTD | PARCIAL — lista E13 + ficha E14 entregues (frente prioritária, reconciliado 2026-10-22); OTD fornecedor = E15 na fila; P-11 limita Qualidade |
| RQ-14 | Produtos / Product 360 / where-used / preços | BLOQUEADO pela fila |
| RQ-15 | Savings/Negociações | BLOQUEADO pela fila |
| RQ-16 | Indicadores como página distinta | BLOQUEADO até revalidar necessidade/escopo ao promover |
| RQ-17 | Minhas Atividades | BLOQUEADO pela fila |
| RQ-18 | Administração | BLOQUEADO pela fila |
| RQ-19 | Ajuda sincronizada por feature | HERDADO por `feature-help-sync`; auditoria final em E23 |
| RQ-20 | Paridade mensurável | E24/E26 |
| RQ-21 | C2 sem dual writer + reconciliação | E25 |
| RQ-22 | Cutover reversível | E27/E28 |
| RQ-23 | Verify-final do objetivo original | E29 |

Nenhum RQ futuro é autorização automática de implementação.

---

## 3. Decisões travadas

| Decisão | Evidência |
|---|---|
| id `supplies`, base `/apps/supplies`, CSS `.dashboard-supplies-portal` | ADR-004 |
| `supplies-api` Flask | ADR-001 + instruções oficiais |
| MFE somente `supplies-api` | ADR-001 / boundaries |
| effective permissions via Core | ADR-001/006 |
| capabilities do Portal: `supplies.access` e `supplies.manage` | ADR-008 + ADR-009 |
| unidade = filtro de dados `01`/`02`, não permission | ADR-009 (supersede ADR-006) |
| SC C0→C1→C2→paridade→C3 | ADR-002 |
| target saudável antes de redirect | CUTOVER-RUNBOOK |
| Home ≠ Overview | DESIGN-IA |
| Help no mesmo entregável | `feature-help-sync.mdc` |
| uma página por vez | README + WIREFRAMES |
| `/me/apps` é a superfície de apps/rotas autorizadas; sem `/me/routes` | contrato Core atual |

---

## 4. Protocolo de execução por página

Antes de promover qualquer E*.S* futuro:

```text
reler regras
→ inspecionar working tree
→ reler código/contratos atuais
→ criar ledger da página
→ classificar evidência READY_CONFIRMED / READY_BOUNDED / NOT_READY
→ atualizar receita executável
→ READY_TO_EXECUTE
→ implementar menor escopo correto
→ positive + sibling + negative
→ revisão adversarial
→ smoke/tema/responsivo quando material
→ GATE-FEATURE
```

`EXECUTION_DRIFT` interrompe somente o subgrafo afetado. Não adaptar código para obedecer documentação obsoleta.

---

## 5. Gates

### GATE-AUTHZ — PASS atual
JWT válido; Core resolve effective permissions; Core indisponível falha fechado; filial/recurso negados no backend.

### GATE-RBAC — PASS local
Manifest/papéis canônicos locais e `/me` + `/me/apps`. Persona negativa real em HML/prod continua pendente quando depender de usuário real.

### GATE-FEATURE
Por página: contrato + kit + AuthZ + estados + Help + testes + docs + URL/F5 quando aplicável + responsividade/tema/acessibilidade + smoke federado quando material.

### GATE-C2
Um único writer no schema `purchase_requests`, jobs transferidos, reconciliação e rollback conhecidos.

### GATE-PARITY
Comparação quantitativa de dados, filtros, permissions, URLs, performance e Ajuda; gaps críticos aceitos explicitamente ou corrigidos.

### GATE-CUTOVER
GATE-C2 + GATE-PARITY + BIs/legados em estado final permitido + target saudável + RBAC + redirects + rollback.

---

# E1 — Descoberta e freeze — COMPLETED

E1.S1–S5 concluídas em 2026-09-08. Dump Core produção dos BIs externos permanece residual para cutover e não reabre E1.

# E2 — Fundação supplies-api/AuthZ — COMPLETED

E2.S1–S6 concluídas: Flask, erros/observabilidade, schema supplies, gateway api-delpi, Core-first AuthZ e `/me/capabilities`.

# E3 — MFE + RBAC coexistência — COMPLETED

E3.S1–S5 concluídas: Module Federation, BFF-only, shell, manifest e RBAC coexistente local.

# E4 — Home + Ajuda + Perfil — COMPLETED

E4.S1–S4 concluídas: catálogo, Ajuda inicial, `/users/:userId`, preferências e avatar Core. (`/home/attention` removido no HOME-ATTENTION.P3 — ver decisão abaixo.)

# E5 — Overview + OTD analytics — COMPLETED

Overview/OTD fechados com filtros/URL, 7 KPIs, metas SI, charts/gauges e Ajuda.

---

# E6 — Solicitações de Compras C1 — COMPLETED

## E6.S1 — Gateway PR-api — COMPLETED

**Entregue:** BFF C1 preservando CC fail-closed e unit scope.
**Teste de referência:** `pytest supplies-api/tests/infrastructure/gateways/test_purchase_requests_gateway.py -q` + BFF route tests.

## E6.S2 — Lista/detalhe SC — COMPLETED FUNCIONAL

**Entregue:** lista e detalhe via MFE BFF-only.
**Teste de referência:** `cd plugins/supplies && npm test -- PurchaseRequests`.

## E6.S3 — Export — COMPLETED

**Entregue:** export da SC do Portal segue a mesma visibilidade do acompanhamento global (`supplies.access` + S2S). O standalone continua com o próprio RBAC de export.

## E6.S4 — Evidência C2 — COMPLETED DOCUMENTAL

**Entregue:** inventário de schema/writers/jobs/cursors/subscriptions e estratégia single-writer.
**Evidência:** [evidence/e6-s4-c2-migration-evidence.md](./evidence/e6-s4-c2-migration-evidence.md).
**Residual:** medir volumes HML/prod antes de E25.

## E6.S5 — Revalidar GATE-FEATURE WF-04 — COMPLETED 2026-09-11

**Entregue:** kit-first (`PagePath`/`PageHero`/`FilterBar`/`SectionCard`/`ActionButton`), mapper 403, Help nos filtros, URL/F5, estados loading/empty/error/404, testes MFE estruturais + BFF/security verdes.
**Residual:** smoke federado Portal = `INCONCLUSIVE` neste ambiente; DataTable kit do `plugin-ui` fica para quando houver 2+ páginas tabulares no Portal (lista SC usa tabela de domínio com CSS de layout apenas).
**Teste:** `cd plugins/supplies && npm test -- --run src/features/purchase-requests` · `supplies-api/.venv/bin/pytest tests/interface/http/test_purchase_requests_bff.py tests/security/test_purchase_request_export.py tests/infrastructure/gateways/test_purchase_requests_gateway.py -q`.
**Commit sugerido:** `fix(supplies): fechar DoD de solicitações de compras`

---

# Fila futura — uma página por vez

As etapas abaixo estão **BLOCKED_BY_QUEUE**. Antes de executar qualquer uma, substituir o resumo por receita completa conforme `plan-construction.mdc`, revalidando código, API e decisões pendentes.

## E7 — WF-05 Pedidos de Compra — COMPLETED 2026-09-11

**Entregue:**
- E7.S1 api-delpi `GET /supplies/purchase-orders` (`list_supplies_purchase_orders`) — SC7 aberto paginado;
- E7.S2 BFF `GET /purchase-orders` (`supplies.access` + filtro `01`/`02`);
- E7.S3 MFE kit-first + URL/F5 + seleção de linha (detalhe completo fora);
- E7.S4 Help + docs GATE-FEATURE; smoke federado `INCONCLUSIVE`.

**Decisão:** lista = SC7 aberto, **não** OTD panel.

**Teste:** api-delpi `pytest tests/test_purchase_orders_list_*.py` · supplies-api `pytest tests/interface/http/test_purchase_orders_bff.py` · MFE `npm test -- --run src/features/purchase-orders`.

## E8 — WF-06 Detalhe do Pedido

**Executado 2026-09-16** (autorização PO 2026-09-15, registrada neste plano). Producer api-delpi + BFF + MFE ficha read-only. O ledger YAML marca a entrega como `completed`. GATE-FEATURE WF-06 = **PASS** em 2026-09-21, com residual de 403 de unidade não executado.

Pré-condição: autorização explícita PO (E7 já PASS). Contrato de detalhe + resource scope + itens/prometida/recebimentos/SC origem + follow-up apenas se recurso/capability permitirem. Fechar GATE-FEATURE próprio.

## E9 — WF-07 Entregas/Atrasos

**Promoção AUTHORIZED** (Product Owner) + **P0 CONTRACT FROZEN** em 2026-09-21 — [evidence/e9-wf07-p0-contract-freeze.md](./evidence/e9-wf07-p0-contract-freeze.md).

Pré-condições satisfeitas: E8 GATE-FEATURE PASS; autorização PO persistida; producer `GET /supplies/purchase-order-otd/panel` revalidado no HEAD.

Contrato resumido:

- BFF: `GET /deliveries/late` (gateway `/apps/supplies-api/deliveries/late`)
- AuthZ: `supplies.access` + filtro `01`/`02` (ADR-009); sem permission de entregas
- Semântica: `DIAS < 0` = late; período = `DT_DIGITACAO`; grão = recebimento MP
- Todas ≠ omitir `branch` no producer (merge BFF 01+02)
- MFE: `/apps/supplies/deliveries`; **NO DRILL P0** para ficha E8
- P-03: não bloqueia a página nativa; bloqueia paridade/depreciação do BI

### E9.S1 — Verificar producer + wiring BFF (sem mudar TOTVS) — COMPLETED

Producer `GET /supplies/purchase-order-otd/panel` revalidado sem mudança TOTVS. Read `SuppliesDelpiReads.get_purchase_order_otd_panel` exige `branch` concreto.

**Teste:** `tests/application/test_late_deliveries_composition.py` (gateway exige branch).

### E9.S2 — BFF `GET /deliveries/late` — COMPLETED

Rota Flask + composição AuthZ/`01`/`02`/defaults/merge consolidado (fetch completo por filial + sort global + slice). Uma perna falha → 502. Sem omitir branch no producer para Todas.

**Teste:** `tests/application/test_late_deliveries_composition.py` + `tests/interface/http/test_deliveries_bff.py`.

### E9.S3 — MFE página kit-first — COMPLETED

Rota `/apps/supplies/deliveries` substitui placeholder; client BFF-only `GET /deliveries/late`; filtros Unidade/Período(digitação)/Status; sort e paginação server-side; estados loading/empty/error/403/retry; **NO DRILL P0**; sem cálculo local de `DIAS`.

**Teste:** `features/deliveries/*.test.ts` (query/client + structural).

### E9.S4 — Help + estados + URL — COMPLETED

Sync Manual / Quero→onde / FAQ / tooltips / glossário; «atrasos do dia» removido; período = digitação; URL shareable com pushState + popstate; empty com CTA Limpar/Ajuda. Manifest `showInMenu=false` preservado (padrão interno; discoverability via Início/catálogo).

**Teste:** `features/deliveries/*` + `userManual.structural` + `helpTooltips.structural`.

### E9.S5 — Suites + GATE-FEATURE WF-07 — COMPLETED (GATE PASS após recovery)

Suites API (41 PASS) + MFE (156 PASS) + build PASS. Smoke inicial: BFF prod **404** → GATE FAIL documentado. Recovery 2026-09-21: redeploy `supplies-api` em `srv-api` (`up-prod-sequential.sh --pull --build supplies-api`); re-smoke federado **200** (Todas/01/02, late/on_time, empty, sort, page 2).

**Evidência:** [e9-wf07-federated-runtime-gate.md](./evidence/e9-wf07-federated-runtime-gate.md) (FAIL preservado + seção Recovery).

**GATE-FEATURE WF-07 = PASS.** E9 / WF-07 = **FECHADA**. E10 permanece candidata sem autorização de implementação.

## E10 — WF-15 Controle de Estoques — COMPLETED (residual visual)

Página própria de posição física (`B2_QATU`). Não misturar ESTSEG. Capability: `supplies.access` + filtro `01`/`02` (ADR-009).

### E10.S1 — api-delpi stock-balances — PASS

Contrato producer estendido (`only_positive=false` default path). SHA `abf47ec1cb`.

### E10.S2 — BFF supplies-api — PASS

`GET /inventory/stock-balances/summary` + `GET /inventory/stock-balances/items`. SHA `379ac45937`. Residual `S2_AUTHENTICATED_BFF_SMOKE` **resolvido em S4 (local PASS)**.

### E10.S3 — MFE `/apps/supplies/inventory` — PASS

Placeholder removido; página **Controle de Estoques** kit-first; BFF-only; Hero Produtos/Armazéns/Valor; filtros Unidade+Armazém; tabela preserva zero/negativo/UM null/armazém sem label/código vazio; sort allowlist; paginação server-side; URL/F5. Help final = S4.

### E10.S4 — Help + smoke + GATE — PASS_DEPLOYED

Help sync PASS; suites PASS; BFF autenticado local PASS (Todas/01/02/03→422; negativo/zero/UM null/warehouse vazio amostrados). O bloqueio federado histórico foi superado: deploys posteriores já servem a página — bundle `App-SSmBJjdj.js` contém `stock-balances` e os endpoints respondem 401 protegidos em runtime (re-verificação R1, 2026-10-23). `GATE-FEATURE E10 = PASS_DEPLOYED`; residual `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Evidência: [e10-wf15-s4-final-acceptance.md](./evidence/e10-wf15-s4-final-acceptance.md) + [ROADMAP-REBASELINE-R1](./ROADMAP-REBASELINE-R1-20261023.md).

## E11 — WF-16 Estoque de Segurança — READY_WITH_RESIDUAL

Página própria, read-only neste roadmap. Inventário R1 (2026-10-23): contratos api-delpi completos (`/supplies/safety-stock/*`, consumption-analysis, supplier price history, branch-gate), app legado `estoque-seguranca` de referência, rota `/safety-stock` já no manifest; faltam BFF `supplies-api` + página MFE + decisões de escopo (vs E12/E17/E18). Receita E11.P0/S1–S5 proposta em [ROADMAP-REBASELINE-R1](./ROADMAP-REBASELINE-R1-20261023.md). **E11.P0 executado (2026-10-23):** contratos congelados em [E11-P0-SAFETY-STOCK-CONTRACT-FREEZE.md](./E11-P0-SAFETY-STOCK-CONTRACT-FREEZE.md) — `BRANCH_AUTHZ_RECONCILIATION = COMPATIBLE` (bypass BFF já existe no produtor), 5 rotas BFF congeladas, `E11_S1_READY_TO_AUTHORIZE = YES`. **Não iniciar S1 sem autorização.**

## E12 — WF-17 Análise de Consumo

Página própria ou satélite somente se a promoção provar que é extensão inseparável do WF-16; não assumir herança sem evidência.

## E13 — WF-09 Fornecedores — IMPLEMENTADA (frente prioritária)

`/apps/supplies/suppliers` real: lista paginada server-side, busca `query`, filtros `state`/`blocked`, URL/F5, estados loading/empty/error/403/404. Owner `features/suppliers/SuppliersPage.tsx`. AuthZ `supplies.access` efetiva via Core; BFF-only. Entregue sob `FORNECEDORES-RETOMADA-IMPLEMENTACAO-2026-10-20.md` — reconciliado 2026-10-22.

## E14 — WF-10 Fornecedor 360 — IMPLEMENTADA (frente prioritária; incrementos X4)

`/apps/supplies/suppliers/{code}/{store}` real: ficha por seções (`SUPPLIER_FIELD_REGISTRY`), inclusão POST e edição PUT restrita com diff/confirm, outcome ACK≠persistência, assistente de CEP. Composição TOTVS + PG. **Qualidade permanece fora enquanto P-11 não estiver resolvido.** AuthZ `supplies.access`, sem permission própria. X4 = seção `#enrichment` (comparação SA2×BrasilAPI → revisão S2 → decisões → prepare-update draft-only), contrato em `X4-P0-SUPPLIER-ENRICHMENT-UX-INVENTORY-CONTRACT-FREEZE-20261022.md`. **X4.S1 IMPLEMENTADO (2026-10-22):** módulo `features/suppliers/enrichment/` — consulta explícita, comparação 16 campos, decisões individual/bulk idempotentes, histórico paginado por ator e rascunho draft-only; sem rota nova, sem permission nova, sem escrita ERP. Evidência: `X4-S1-SUPPLIER-ENRICHMENT-UI-IMPLEMENTATION-20261022.md`.

## E15 — WF-11 OTD Fornecedores

Página analítica distinta do OTD geral e de Entregas. Validar ranking/meta/evolução e relação com BI legado antes de paridade.

## E16 — WF-12 Produtos / MP

Busca/lista de produtos; não misturar 360 completo.

## E17 — WF-13 Produto / MP 360

Composição por blocos autorizados, com partial explícito.

## E18 — WF-14 Onde Usado e WF-19 Histórico de Preços

Não executar os dois automaticamente juntos. Ao chegar nesta fila, decidir se Histórico de Preços permanece seção do 360 ou página própria e promover **uma superfície por vez**. Where-used só declara paridade do BI após comparação real.

## E19 — WF-18 Savings / Negociações

SI continua owner de meta; sem dual write; Help explica realizado × meta.

## E20 — WF-20 Indicadores

Antes de executar, revalidar se `/indicators` ainda agrega valor além da Overview e deep links SI. Se não houver jornada distinta comprovada, marcar `FORA_DO_ESCOPO_COM_JUSTIFICATIVA` em vez de criar página redundante.

## E21 — WF-03 Minhas Atividades

Migration + API + worklist somente depois de contratos de recursos referenciados necessários estarem estáveis. AuthZ pelo recurso; sem `tasks.view/write` preventivo.

## E22 — WF-21 Administração

Scopes/mappings/settings tipados + auditoria; administração não concede automaticamente todas as units.

## E23 — Auditoria final de Help/onboarding

Não é entrega tardia de Help. Audita cobertura acumulada de tooltips, Manual, Quero→onde, FAQ e glossário de todas as páginas já fechadas.

## E24 — Paridade inicial C1

Comparar quantitativamente os legados/jornadas incorporados. Não fazer cutover nem C2 aqui.

## E25 — Purchase Requests C2

### E25.S1 — Precondições e snapshot
Medir volumes HML/prod, confirmar janela operacional, owner e rollback.

### E25.S2 — Expand/read readiness
Preparar `supplies-api` para leitura do schema existente sem quebrar PR-api.

### E25.S3 — Transferir writers/jobs
Um único writer: desligar writers/jobs PR-api antes de ligar equivalents na `supplies-api`. Zero dual-write prolongado.

### E25.S4 — Reconciliação
Comparar counts, subscriptions, cursors/eventos e smoke CC/list/detail/export.

### E25.S5 — Freeze PR-api
Somente bug/security durante coexistência final. GATE-C2 ao final.

## E26 — Paridade final pós-C2

Reexecutar matriz com C2 ativo. BIs externos devem sair de `LEGADO_A_VALIDAR` antes do GO.

## E27 — Preparar cutover C3

Fechar destinos/redirects, telemetria, rollback, known consumers e smoke do target antes de redirecionar.

## E28 — Cutover C3

Staging → produção somente com GATE-CUTOVER → observação → remoção posterior segundo critérios; não remover legado no mesmo instante do primeiro redirect.

## E29 — Verify-final

Rebuild/runtime/smoke da matriz P0, authz, unit/resource scope, mobile/light/dark, partial failures, redirects e revisão do objetivo original.

---

## 6. Backlog P1/P2/P3 fora da linha executável P0

- supplier scorecard;
- supplier concentration;
- purchase approvals/alçadas;
- importações;
- slow moving/obsolescência;
- lead time real × cadastrado;
- price variance;
- previsão de atraso;
- follow-up automático externo;
- escrita ESTSEG no Protheus.

Cada item só vira E*.S* após evidência de contrato, decisão funcional e autorização próprias. Não bloqueia E29.

---

## 7. Todos YAML

```yaml
todos:
  - id: e1-discovery-freeze
    status: completed
    dependsOn: []
  - id: e2-api-authz-foundation
    status: completed
    dependsOn: [e1-discovery-freeze]
  - id: e3-mfe-rbac
    status: completed
    dependsOn: [e2-api-authz-foundation]
  - id: e4-home-help-profile
    status: completed
    dependsOn: [e3-mfe-rbac]
  - id: e5-overview-otd
    status: completed
    dependsOn: [e4-home-help-profile]
  - id: e6-s1-pr-gateway
    status: completed
    dependsOn: [e3-mfe-rbac]
  - id: e6-s2-pr-list-detail
    status: completed
    dependsOn: [e6-s1-pr-gateway]
  - id: e6-s3-pr-export
    status: completed
    dependsOn: [e6-s2-pr-list-detail]
  - id: e6-s4-c2-evidence
    status: completed
    dependsOn: [e6-s1-pr-gateway]
  - id: e6-s5-wf04-feature-gate
    status: completed
    dependsOn: [e6-s2-pr-list-detail, e6-s3-pr-export, e6-s4-c2-evidence]

  - id: e7-purchase-orders-list
    status: completed
    dependsOn: [e6-s5-wf04-feature-gate]
  - id: e8-purchase-order-detail
    status: completed
    dependsOn: [e7-purchase-orders-list]
  - id: e9-deliveries
    status: pending
    dependsOn: [e8-purchase-order-detail]
  - id: e9-s1-producer-wiring
    status: completed
    dependsOn: [e9-deliveries]
  - id: e9-s2-bff-deliveries-late
    status: completed
    dependsOn: [e9-s1-producer-wiring]
  - id: e9-s3-mfe-page
    status: pending
    dependsOn: [e9-s2-bff-deliveries-late]
  - id: e9-s4-help-url-states
    status: pending
    dependsOn: [e9-s3-mfe-page]
  - id: e9-s5-feature-gate
    status: pending
    dependsOn: [e9-s4-help-url-states]
  - id: e10-inventory
    status: blocked
    dependsOn: [e9-s5-feature-gate]
  - id: e11-safety-stock
    status: blocked
    dependsOn: [e10-inventory]
  - id: e12-consumption-analysis
    status: blocked
    dependsOn: [e11-safety-stock]
  - id: e13-suppliers-list
    status: blocked
    dependsOn: [e12-consumption-analysis]
  - id: e14-supplier-360
    status: blocked
    dependsOn: [e13-suppliers-list]
  - id: e15-supplier-otd
    status: blocked
    dependsOn: [e14-supplier-360]
  - id: e16-products-list
    status: blocked
    dependsOn: [e15-supplier-otd]
  - id: e17-product-360
    status: blocked
    dependsOn: [e16-products-list]
  - id: e18-product-drills
    status: blocked
    dependsOn: [e17-product-360]
  - id: e19-negotiations
    status: blocked
    dependsOn: [e18-product-drills]
  - id: e20-indicators-decision
    status: blocked
    dependsOn: [e19-negotiations]
  - id: e21-my-tasks
    status: blocked
    dependsOn: [e20-indicators-decision]
  - id: e22-administration
    status: blocked
    dependsOn: [e21-my-tasks]
  - id: e23-help-audit
    status: blocked
    dependsOn: [e22-administration]
  - id: e24-initial-parity
    status: blocked
    dependsOn: [e23-help-audit]
  - id: e25-purchase-requests-c2
    status: blocked
    dependsOn: [e24-initial-parity, e6-s4-c2-evidence]
  - id: e26-final-parity
    status: blocked
    dependsOn: [e25-purchase-requests-c2]
  - id: e27-cutover-prep
    status: blocked
    dependsOn: [e26-final-parity]
  - id: e28-cutover-c3
    status: blocked
    dependsOn: [e27-cutover-prep]
  - id: e29-verify-final
    status: blocked
    dependsOn: [e28-cutover-c3]
```

`blocked` significa fila/precondição não satisfeita, não falha técnica.

---

## 8. Revisão adversarial obrigatória antes de promover próxima página

- A página anterior realmente fechou GATE-FEATURE?
- Há alguma decisão `NOT_READY` disfarçada de “se necessário/quando autorizado”?
- Producer e consumers do contrato foram lidos?
- Algum componente já existe no `plugin-ui`?
- A etapa mistura duas páginas?
- AuthZ/unit/resource scope está no backend?
- Help está na mesma entrega?
- URL/F5/deep link foram considerados?
- Positive + sibling + negative provam o comportamento?
- Docs/status/todos refletem o código atual?
- Há dependência em `/me/routes` ou outro contrato inexistente?
- O próximo agente conseguiria executar sem redescobrir decisão material?

Se qualquer resposta material for negativa, a etapa ainda não está READY_TO_EXECUTE.

---

## Nota de coordenação (2026-10-22) — SHARED-INTEGRATIONS-01 / X4.P0

X0–X3.E2E da integração CNPJ/fornecedores estão aceitos **apenas no boundary backend/runtime**, com BrasilAPI ativa, S1/S2, decisões e draft-only exercitados em produção. Evidência e decisão: [X3-E2E-CLOSURE-AND-X4-UI-READINESS](../shared-integrations/X3-E2E-CLOSURE-AND-X4-UI-READINESS-20261022.md). Residuais LGPD/ROPA e skips de teste permanecem visíveis. Escrita Protheus continua OFF.

**X4.P0 AUTORIZADO SOMENTE PARA INVENTÁRIO, CONTRATO DE UI E RECONCILIAÇÃO DA FILA.** O status histórico E10/WF-15 `INCONCLUSIVE` acima não foi revalidado por esta atualização; E13/WF-09 e E14/WF-10 não são promovidas automaticamente. A implementação da interface exige P0 aceito + evidência atual do gate da página em foco + autorização explícita da etapa. Não modificar manifest, RBAC, MFE ou deploy no P0.

**X4.S1 EXECUTADO (2026-10-22, autorização «PORTAL SUPRIMENTOS — X4.S1»):** E14 comprovada implementada + contrato X4.P0 aceito → incremento de enriquecimento materializado como seção `#enrichment` dentro da ficha existente (`EnrichmentSection` + `enrichment/` module), sem rota/manifest/permission novos e com write gate OFF respeitado (prepare-update = draft-only). Relatório completo: `X4-S1-SUPPLIER-ENRICHMENT-UI-IMPLEMENTATION-20261022.md`. **X4.S1.R1:** retry idempotente com payload imutável (mesma operação, mesma chave). **X4.S2:** verificação de produção — bundle já continha R1, deploy dispensado; smoke real com `rober`/fornecedor `002469/01` (review `1989ff2c`, decisões, bulk, replay, 409s, draft-only) — `X4-S2-FEDERATED-DEPLOY-RUNTIME-ACCEPTANCE-20261022.md`. Residual: smoke visual interativo INCONCLUSIVE.

**X4.UX-R1.P0 CONCLUÍDO (2026-10-23):** inventário + contract freeze do cadastro assistido (3 entradas na `SupplierCreatePage`) e conferência E13. Contratos candidatos congelados: `POST /suppliers/creation-preview`, `GET /suppliers/external-search`, `POST /suppliers/enrichment-summaries` (batch, read-model PG — sem N+1). Lacuna registrada: duplicate-check exato por CNPJ não existe na api-delpi (só `LIKE` textual) — menor contrato proposto `GET /supplies/suppliers?tax_id=`. R1.S1 `READY_TO_AUTHORIZE`; R1.S3 `BLOCKED` até homologação de provider nominal (CNPGolden/ZenPJ/Nume/CNPJota catalogados, nenhum escolhido). Doc: `X4-UX-R1-P0-INVENTORY-CONTRACT-FREEZE-20261023.md`.

**X4.UX-R1.S1 CONCLUÍDO (2026-10-23):** `POST /suppliers/creation-preview` implementado em supplies-api — sugestões com proveniência via `CompanyRegistryProvider` existente + duplicate-check exato (nova cláusula `tax_id` digito-normalizada em api-delpi `GET /supplies/suppliers`; `CLEAR` só com match exato e total=0, falha → `INCONCLUSIVE`). Draft-only, zero escrita, 425 testes supplies-api verdes. Doc: `X4-UX-R1-S1-CREATION-PREVIEW-BACKEND-20261023.md`.

**X4.UX-R1.S2 CONCLUÍDO (2026-10-23):** MFE `SupplierCreatePage` ganhou seletor de três inícios no mesmo formulário — consulta por CNPJ (consome S1 via BFF, sugestões com proveniência por campo, aplicação somente explícita, `applicable=false` nunca aplicado, proteção contra resposta obsoleta via abort+sequência, 429 com `Retry-After` sem retry automático), busca por razão social exibida como **indisponível** (R1.S3 segue `BLOCKED` — sem pesquisa falsa) e preenchimento manual preservado. Draft compartilhado reconcilia estados SUGGESTED/CONFIRMED/MANUALLY_CHANGED/UNAVAILABLE (UX-only). Revisão final e `POST /suppliers` intactos; preview nunca grava. 319 testes verdes (21 novos), typecheck e build OK; lint sem erro novo. Smoke federado não executado. Doc: `X4-UX-R1-S2-CREATION-ASSISTED-FRONTEND-20261023.md`. **S2.R1 (rework pós-revisão) CONCLUÍDO:** corrigidos sobrescrita silenciosa de identidade (confirmação explícita para `tax_id`/`person_type` divergentes) e invalidação de preview obsoleto ao mudar os dígitos do CNPJ (`activeTaxId` + coerência de identidade bloqueia aplicação de sugestões de outra empresa; valores digitados preservados). 330 testes verdes. **S2.R2 (rework final) CONCLUÍDO:** coerência de identidade agora exige CNPJ **e** tipo de pessoa coerentes com a consulta ativa — cancelamento por `person_type` divergente mantém sugestões bloqueadas (guarda visual + handlers); `activePersonType` rastreia a identidade do preview vigente. 333 testes verdes. **X4.UX-R1.S7 CONCLUÍDO (2026-10-23):** deploy federado executado em `srv-api` — api-delpi `12cda95ea1d2`, supplies-api `84d02964a88f`, MFE supplies `6b3130be529f` (bundle `App-5YYpsuZ3.js` com marcadores S2+R1+R2, BFF-only). Runtime verificado: 401/422, `CLEAR` + `POSSIBLE_MATCH` reais via gateway, proveniência BrasilAPI, zero escrita ERP, regressão E13/E14 verde. Visual: `INCONCLUSIVE` (sem browser). Doc: `X4-UX-R1-S7-FEDERATED-RUNTIME-ACCEPTANCE-20261023.md`. R1.S3 permanece `BLOCKED`; S4–S6 não autorizados.

**X4.UX-R1.S8 CONCLUÍDO (2026-10-23):** conferência de cadastros existentes por CNPJ — o preview ganhou `duplicate_check.total` (aditivo) e o BFF expõe `GET /suppliers/existing-suppliers?tax_id=&page=&page_size=≤50` (read-only, mesma capability, só api-delpi — nunca BrasilAPI). O MFE passou a listar **todos** os registros com `SuppliesCompactPagination`, código/loja/nome/UF/bloqueado e «Conferir cadastro» abrindo E14 em **nova aba** — rascunho preservado sem persistência no browser; banner POSSIBLE_MATCH virou informativo (não bloqueante), sem regra de unicidade e sem escrita ERP. api-delpi não foi alterada (contrato já tinha paginação + `total` + ordenação estável). Gap de auditoria de visualização documentado (owner: Core/segurança). ~230 testes supplies-api + 337 MFE verdes, typecheck/build OK; visual e runtime `INCONCLUSIVE/TEST_NOT_RUN`. Doc: `X4-UX-R1-S8-EXISTING-SUPPLIERS-REVIEW-20261023.md`. **X4.UX-R1.S8.D1 CONCLUÍDO (2026-10-23):** deploy federado em srv-api — supplies-api `acc772fa65fa`, MFE supplies `37dee5f0450d` (bundle `App-CwatapS_.js` com todos os marcadores S8, BFF-only); api-delpi/external-data/core não tocados. Runtime verificado via gateway: 401/422, `existing-suppliers` 200 com `total` real e página vazia honesta, preview aditivo (`POSSIBLE_MATCH` + `total`), zero BrasilAPI na paginação, zero escrita supplier, E13/E14/enrichment verdes. Visual `INCONCLUSIVE`; auditoria de visualização `TO_INVENTORY`. Doc: `X4-UX-R1-S8-D1-FEDERATED-RUNTIME-ACCEPTANCE-20261023.md`.


## Plano derivado X4.UX-R1 — cadastro assistido / conferência (2026-10-23)

[**Plano full-stack X4.UX-R1 (frontend, BFF, External Data, api-delpi e deploy)**](./X4-UX-R1-IMPLEMENTATION-PLAN-FRONTEND-BACKEND-20261023.md): **PLANNED**, sem autorização automática de implementação. Preserva a criação manual; propõe fluxo assistido CNPJ e busca por razão social com seleção humana → lookup CNPJ, além de status/contagem acionável em E13. Grafo R1.P0 (freeze) → S1 BFF prévia → S2 MFE CNPJ/manual; S3 provider nominal → S4 nome BFF/MFE; S5 resumo E13 → S6 lista; S7 aceites federados por fatia. A busca por nome e as rotas novas são `TARGET/TO_INVENTORY`; E10 mantém gate independente, X4.S2 visual permanece inconclusivo, e o gate de escrita ERP segue OFF. **Próxima autorização a decidir: somente X4.UX-R1.P0.**

**X4.UX-R1.S8.V1 EVIDÊNCIA VISUAL PARCIAL (2026-10-23):** PO forneceu capturas autenticadas do novo fornecedor após consulta do CNPJ de EXPRESSO SÃO MIGUEL, mostrando **dois registros com mesmo código `000905`, lojas `01` e `04`**, aviso informativo não bloqueante, ações de conferência e fichas E14 individualizadas para ambas as lojas; diferenças visíveis de endereço/CEP. Fluxo multiloja em produção **PASS visual no cenário de dois registros**. **Não** comprova paginação >10, retorno ao draft preenchido, mobile/tema claro/teclado/F5; esses pontos seguem `INCONCLUSIVE/TEST_NOT_RUN`. Auditoria de visualização `TO_INVENTORY`, ERP write OFF, **GATE-FEATURE S8 integral INCONCLUSIVE**. Detalhes: `X4-UX-R1-S8-D1-FEDERATED-RUNTIME-ACCEPTANCE-20261023.md` (seção «Evidência visual adicional do Product Owner»); capturas foram compartilhadas na conversa, não versionadas no GitHub.

**X4.UX-R1.S8.V1 RETORNO MANUAL PO (2026-10-23):** PO informou **9/9 PASS** para preservação de rascunho, troca de CNPJ, cancelamento de substituição, paginação >10, F5/navegação E14, mobile, temas, teclado/foco e estado de erro, testados no navegador. Classificação precisa: **`PASS (PO-reported, manual)`**, sem anexos ou comprovação independente dos nove cenários, particularmente total/documento/páginas do caso >10. As capturas anteriores evidenciam diretamente somente o cenário de duas lojas. Registro detalhado e sugestões de evidências: `X4-UX-R1-S8-D1-FEDERATED-RUNTIME-ACCEPTANCE-20261023.md`, seção S8.V1. **S8 = `ACCEPT_WITH_RESIDUAL`**; auditoria de visualização `TO_INVENTORY`; gate integral não promovido automaticamente a PASS; escrita ERP OFF, sem deploy/código novo.

**X4.UX-R1.S9 CONCLUÍDO (2026-10-23):** UX polish MFE-only do cadastro assistido — (A) input CNPJ da consulta com máscara progressiva `00.000.000/0000-00`, normalização a dígitos, `inputMode="numeric"` e caret controlado (edição no meio/remoção de separadores); identidade continua sendo os 14 dígitos — máscara não invalida preview, dígitos sim; consulta segue manual e exige verificadores válidos. (A′) `tax_id` do formulário ganhou `SupplierTaxIdField`: apresentação CNPJ (J) / CPF (F) / dígitos sem máscara ambígua quando tipo indefinido — **draft e payload seguem só dígitos** (`body.tax_id` canônico preservado). (B) `formatRetrievedAt` agora projeta o instante em `America/Sao_Paulo` via `Intl.DateTimeFormat` → `dd/mm/aaaa às hh:mm (horário de Brasília)`, sem mutar `retrieved_at`. (C) `providerDisplayName` centralizado em `creation/content.ts`: «BrasilAPI — dados públicos de terceiros», fallback honesto, `provider_id` técnico preservado no contrato e acessível via `title`. Zero mudança de backend/contrato/RBAC; sem deploy; ERP write OFF. Help/manual/glossário sincronizados. 363 testes MFE verdes (22 novos: máscara/caret, fuso, provedor, estruturais S9), `tsc -b` e `vite build` OK, lint escopado limpo. Browser interativo `TEST_NOT_RUN`. Doc: `X4-UX-R1-S9-SUPPLIER-CREATION-UX-POLISH-20261023.md`.

**X4.FIELDS.E1 CONCLUÍDO (2026-10-23):** experimento local controlado de ampliação de campos de fornecedor na api-delpi — inventário do de-para (71 campos PUBLIC_DICTIONARY) contra contrato vigente (24 POST / 22 PUT / 26 GET). **35 candidatos** de negócio isolados em `protheus_supplier_extended_fields.py` (specs SX3 + regra condicional CNAE×person_type) — **não conectados a nenhuma rota**; allowlist publicada segue rejeitando-os (testado). Bloqueados documentados: bancários (sensíveis/LGPD), `address_complement`/`group_code` (owner/contexto), system/`DO_NOT_SEND`. Refactor compatível `normalize_supplier_field_value(..., specs=None)`. 55 testes novos + 37 de regressão verdes; zero escrita ERP, zero deploy, gate OFF. Homologação REST `TEST_NOT_RUN` — promoção exige contract evolution + ensaio autorizado (E1.H1 `NOT_AUTHORIZED`). Doc: `X4-FIELDS-E1-SUPPLIER-EXTENDED-FIELDS-EXPERIMENT.md`.

**X4.UX-R1.S9.D1 CONCLUÍDO (2026-10-23):** gate federado do polish S9 — o bundle S9 **já estava publicado** no inventário (imagem `infra-supplies 1eb05c40f27f`, criada 14:22Z do checkout `43d5c61965` que contém S9); rebuild dispensado conforme regra da task — **nenhum deploy executado**. Bundle real verificado: `remoteEntry → expose_App-Brmm4idS.js → App-DJfMgiUV.js` (271 KB, 200) com marcadores `America/Sao_Paulo`, `horário de Brasília`, `dados públicos de terceiros`, `existing-suppliers`, `inputMode`; zero marcadores proibidos (`api-delpi`, `brasilapi.com.br`, `s2s_`, `client_secret`). Smoke: preview e existing-suppliers 401 sem token, 0 unhealthy, 0 erro nginx, ERP write OFF confirmado no env de api-delpi e supplies-api. Imagem de rollback S8 pruned — reversão por rebuild do SHA `1c7a96ce33`. **VISUAL/INTERATIVO `TEST_NOT_RUN` — GATE-FEATURE S9 = INCONCLUSIVE.** Doc: `X4-UX-R1-S9-D1-FEDERATED-VISUAL-ACCEPTANCE-20261023.md`.

**X4.FIELDS.E1.P1 CONCLUÍDO (2026-10-23, READ-ONLY):** diagnóstico REST×SQL executado com provas live — `REST ambiente=1 (192.168.1.233:8701)` escreve em **`DELPI_TST01`** (correlação REST GET `00387801` ↔ SQL TST01 provada); Portal lê `DELPI` (mesmos códigos, fornecedores reais distintos). `REST_SQL_BASE_DIVERGENCE` permanece `BLOCKED` para produção, par de homologação identificado. `TAX_ID_DIVERGENCE = PARTIALLY_RESOLVED` (ambiente descartado; perda upstream confirmada live — `00387401` retorna `tax_id=""` vs sibling persistido). 35 candidatos reconciliados: 18 READY / 1 condicional / 5 NEEDS_REVIEW / 11 lookup-dependent / 12 BLOCKED. Lookups mapeados (ACJ/AIA/SA2/SA4/SX5-T3/CC1/SAE/SA1/SRA/S049BR — sem adapters, valores via TST01 ou owner). Plano E1.H1 com 5 lotes e protocolo read-after-write preparado. **`E1.H1_READY = NO`** — pendências de owner/autorização. Doc: `X4-FIELDS-E1-P1-REST-SQL-DIAGNOSTIC-AND-HOMOLOGATION-READINESS.md`.

**X4.UX-R1.S9.R1 CONCLUÍDO (2026-10-23):** evidência PO — E14 (`002469/01`) exibia `brasilapi-cnpj-v1` + ISO UTC brutos. Formatadores S9 extraídos para `features/suppliers/externalSourceFormat.ts` (fonte canônica única); `EnrichmentSection` e `EnrichmentHistoryTable` passam a exibir «BrasilAPI — dados públicos de terceiros» + `America/Sao_Paulo`, com proveniência técnica preservada via `title`. Frontend-only, zero contrato/backend/permissão. 365 testes PASS · typecheck/build/lint verdes. Visual `TEST_NOT_RUN` (mesmo residual de S9). Doc: `X4-UX-R1-S9-R1-ENRICHMENT-SOURCE-DATETIME-UX.md`.

**S9.R1 DEPLOY (2026-10-23, autorizado):** MFE `delpi-supplies` republicado via `up-prod-sequential.sh --fase mfe --build supplies` — checkout `6a0b1b49e2`, imagem `5ab977562c44`, bundle `App-c4IDFO4D.js` (200, markers S9+R1). Smoke 401/healthy/gates OFF. Somente o MFE; demais serviços intocados. Rollback por rebuild `f4e56918c5`. Visual `TEST_NOT_RUN` — gate S9 `INCONCLUSIVE`.

**X4.FIELDS.E2 CONCLUÍDO (2026-10-23, ACCEPT_WITH_RESIDUAL):** implementação + homologação real em `DELPI_TST01` autorizada pelo PO. **CNPJ root cause `PROVEN`:** api-delpi serializa `tax_id` corretamente — o endpoint upstream/Execauto **descarta silenciosamente** CNPJ com DV inválido (`003874` usava `98887766000396`/`98887766000477`, ambos inválidos); CNPJ válido `98887766020089` persistiu em `A2_CGC` (`003876/01`, REST GET + SQL). Descoberta operacional: upstream exige `rohs_indicator`, `accounting_account`, `bacen_country_code`, `payment_method_code`, `financial_nature_code`, `payment_condition_code` (todos já no contrato publicado). Execução: script auditável `protheus_supplier_extended_homologation.py` + `field_normalizer` injetável no use case (default = publicado; rota pública inalterada). 7 fornecedores `ZZ HOMOLOG E2*` criados, 8 operações tracked (7 CONFIRMED + 1 REJECTED inicial). **33 candidatos testados: 29 `PERSISTENCE_PROVEN` / 4 `IGNORED`** (`person_category`→A2_TPESSOA, `payee_code`/`payee_store`→A2_CODFAV/A2_LOJFAV, `generic_supplier`→A2_YFGEN — handoff Gabriel) / **3 `TEST_NOT_RUN`** (`country_calling_code`, `link_type_code` sem lookup em TST01; `esocial_category_code` semântica S049BR pendente). Gates: exec-env apenas, flags prod confirmadas `false`, zero resíduo em `DELPI`, zero deploy/MFE/RBAC. Campos permanecem experimentais — promoção exige contract evolution. Doc: `X4-FIELDS-E2-EXTENDED-SUPPLIER-HOMOLOGATION-20261023.md`.

**X4.FIELDS.E3 CONCLUÍDO (2026-10-23, ACCEPT_WITH_RESIDUAL):** expansão full-stack autorizada pelo PO dos 29 campos `PERSISTENCE_PROVEN` do E2. **P0:** reconciliação programática — 36 candidatos = 29 promovidos + 4 IGNORED + 3 TEST_NOT_RUN; derivação perigosa neutralizada (allowlist PUT congelada em constante explícita **antes** da promoção — criável ≠ editável). **S1 api-delpi:** 29 specs SX3 promovidas ao `SUPPLIER_FIELD_SPECS` (53 campos POST), `PUT_EDITABLE_FIELDS` explícito (22, F3.3 inalterado), módulo experimental reduzido aos 7 sem evidência. **S2 supplies-api:** `POST_SUPPLIER_FIELDS` 53, `PUT_SUPPLIER_FIELDS` 22 congelado, `_DETAIL_SECTION_FIELDS` +29 nas 5 seções canônicas; LGPD/minimização preservada. **S3 MFE:** `SupplierCreateDraft` +29, `SupplierPostOnlyFieldKey` excluído de editável (type-level), registry +29 specs `put:"readonly"`/`evidence:"post-matrix"` distribuídos (identification 1/address 2/contact 4/fiscal 13/purchasing 9), revisão automática, FAQ/manual sincronizados; catálogos de referência sem seletor inventado (residual). **S4:** matriz PUT preparada sem escrita — `PUT_EXTENDED_FIELDS = NOT_AUTHORIZED`. Testes: api-delpi 122 / supplies-api 438+21skip / MFE 370 — tsc/build verdes, lint escopado limpo. Gates ERP OFF, zero deploy, zero permission nova, zero escrita real. Smoke federado `TEST_NOT_RUN`. Doc: `X4-FIELDS-E3-FULLSTACK-SUPPLIER-FIELDS-IMPLEMENTATION.md`.

**X4.FIELDS.E5 CONCLUÍDO (2026-10-23, ACCEPT_WITH_RESIDUAL):** habilitação controlada de PUT para os 29 campos E3, autorizada pelo PO. **H1 homologação real em `DELPI_TST01`** (script `protheus_supplier_put_extended_homologation.py`, read-after-write REST+SQL, tracker, 7 operações, fornecedores `003877/01`–`003882/01`): **26 `PUT_PERSISTENCE_PROVEN`** (mudança de valor comprovada REST+SQL), **2 `PUT_INCONCLUSIVE`** (`simp_regime_code` — sem prova de mudança controlada, `"0"` rejeitado 400; `linked_customer_code` — SA1 TST01 sem 2º cliente válido), **1 `PUT_IGNORED`** (`linked_customer_store` — upstream descarta). `untouched_preserved` e `delpi_untouched` em 100% dos lotes. **S1 api-delpi:** `PUT_EDITABLE_FIELDS` 22→48 explícito (não derivado), condicional `cnae_code`×`person_type=F` no PUT parcial, 3 pendentes seguem `PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE`. **S2 supplies-api:** `PUT_SUPPLIER_FIELDS` 22→48 espelhado, AuthZ inalterada. **S3 MFE:** registry 26 campos `put:"editable"`/`evidence:"put-homologated"` (novo membro da union), `SupplierPostOnlyFieldKey` 29→3, `SupplierExtendedFieldKey` exportado; edição E14/diff/revisão cobertas via registry-driven sem código duplicado; FAQ/manual sincronizados. Testes: api-delpi 124 / supplies-api 439+21skip / MFE 371 — tsc/build verdes, lint escopado 0 erros. Gates ERP produtivos OFF; publicação ≠ ativação de escrita. Doc: `X4-FIELDS-E5-SUPPLIER-EXTENDED-PUT-EDITING.md`.

**X4.FIELDS.E6 CONCLUÍDO (2026-10-23, ACCEPT_WITH_RESIDUAL):** finalização da edição + catálogos de referência, autorizado pelo PO. **S1 reteste TST01** (lotes 6a–6d, script `protheus_supplier_put_extended_homologation.py`): `simp_regime_code` **PUT_PERSISTENCE_PROVEN** (1→2, REST+SQL); `linked_customer_store` **PUT_PERSISTENCE_PROVEN** somente no par composto (loja sozinha é ignorada); `linked_customer_code` **PUT_IGNORED** — upstream nunca altera `A2_CLIENTE` em update (veredito 6d). Semântica congelada: loja editável com companion `linked_customer_code` injetado pela api-delpi a partir do cadastro vigente; divergência → 422 `PROTHEUS_SUPPLIER_LINKED_CUSTOMER_IMMUTABLE`; código sozinho → `PROTHEUS_SUPPLIER_LINKED_PAIR_REQUIRED`. PUT 48→51 nas duas camadas; frontend 28/29 E3 editáveis (`linked_customer_code` readonly). **S2 catálogos api-delpi** (+6 kinds allowlist/read-only/parametrizados): `carriers` SA4, `segments` SX5-T3, `administrators` SAE, `customers` SA1 (par `A1_COD`+`A1_LOJA`, filtro exato `code`), `employees` SRA, `price-tables` AIA. `tax-groups`/`risk-codes` **BLOCKED** sem de-para confirmado (handoff TOTVS). **S3 BFF:** kinds espelhados + forward de `code`, AuthZ fail-closed inalterada, zero permissão nova. **S4 MFE:** specs `catalogCodeParam`/`catalogValueField`/`catalogPairField`, combo com dedup por valor, seletores compartilhados create+E14, `legal_entity_type` enum, help/manual sincronizados. Testes: api-delpi 441 escopo (4 falhas externas DAVI/GPT pré-existentes) / supplies-api 442+21skip / MFE 372 — tsc/build verdes, lint 0 erros. Gates ERP OFF; `DELPI` intocado. Residual: aceite visual `INCONCLUSIVE`, código do cliente imutável (handoff), `003882/01` com loja `06` aguardando cleanup. Doc: `X4-FIELDS-E6-SUPPLIER-PUT-AND-REFERENCE-CATALOGS.md`.

**X4.FIELDS.E7 CONCLUÍDO (2026-10-23, ACCEPT_WITH_RESIDUAL):** help funcional completo + investigação do cliente vinculado + catálogos pendentes, autorizado pelo PO. **Frente A:** 54 helps do `SUPPLIER_FIELD_REGISTRY` reescritos em PT-BR funcional com referência física validada `(TOTVS: SA2.A2_*)` contra o dicionário canônico `cadastro-fornecedor.md` (54/54 PROVEN, zero `UNRESOLVED_MAPPING`); jargão de implementação banido por teste; overrides legados `SP_HELP.suppliersEditName/ShortName` removidos — inclusão e edição compartilham o mesmo help do registry; tooltip `FieldLabel`/`HelpTooltip` (plugin-ui) já é acessível (foco por teclado, Escape, clamp de viewport, `role="tooltip"`). **Frente B:** mutação de `A2_CLIENTE` investigada — ensaios E6-6b (400 MATA020), E6-6d e E7-B (`A2_VINCULA=2`, HTTP 200 sem persistência) provam que **não existe contrato upstream** para trocar o código do cliente vinculado; veredito `BLOCKED` com handoff técnico formal ao Gabriel (payload sanitizado, hipótese MATA020/ExecAuto, mudança necessária). **Frente C:** `tax-groups` (SX5-21 com 6 linhas não cobre domínio SA2) e `risk-codes` (SX3 sem `X3_F3`) confirmados `BLOCKED` sem fonte confiável — campos permanecem inputs honestos com help funcional. Zero diff funcional em api-delpi/supplies-api. Testes: MFE **375 pass** (+3 E7), tsc/build verdes. Gates ERP OFF; `DELPI` intocado. Doc: `X4-FIELDS-E7-SUPPLIER-BUSINESS-HELP-AND-CATALOG-COMPLETION.md`.

**X4.UX-R1.S10 CONCLUÍDO (2026-10-23, ACCEPT_WITH_RESIDUAL):** hierarquia de ajuda hero/seção/campo nos formulários de fornecedor (MFE-only). **Causa-raiz:** `SupplierCreatePage` injetava `SP_HELP.suppliersCreateFields` (texto genérico) em todas as 5 `SuppliesSectionCard` — componente canônico correto, conteúdo errado. **Implementação:** heroes contextuais distintos (`createDescription` criação / `editHint` edição, ambos sem prometer escrita); `supplierSectionDescriptions` como fonte única em `content.ts` (5 descrições funcionais do spec) renderizadas via prop nativa `subtitle` do `SuppliesSectionCard` — visível sem hover, `<h2>` semântico preservado; keys mortas `suppliersCreateFields`/`suppliersIdentification` removidas; residual E7.V1 fechado (`Máximo de X caracteres.`); jargão `do backend`/`contrato do ERP` removido de 4 textos UX. 54 helps E7 + refs TOTVS intactos. **Testes:** +6 S10, MFE **381 pass**, tsc/build verdes, lint 0 erros. Zero backend. Deploy MFE-only. `E10_VISUAL = INCONCLUSIVE` sem sessão autenticada. Doc: `X4-UX-R1-S10-SUPPLIER-HELP-HIERARCHY.md`.

**X4.PROD-C1 CONCLUÍDO-PARCIAL (2026-10-23, ACCEPT_WITH_RESIDUAL):** separação REST por ambiente + ensaio completo local. **S1:** guarda fail-closed `PROTHEUS_REST_EXPECTED_BASE_URL` + `assert_protheus_write_target` nos use cases create/update (UNVERIFIED/MISMATCH antes de token/tracking); convenção `AMBIENTE=1`→prod, `AMBIENTE=2`→homologação; local dev fixado em amb=2. **T2/T3 DELPI_TST01:** POST **53/53 PERSISTED** (fornecedor `003884/01`, código/loja upstream, tracking CONFIRMED) e PUT **51/51 provados** (42 diretos + 4 re-provados com valores válidos + 5 coerência-fixados documentados); identidade preservada, omitidos estáveis, `DELPI` zerado. **CUTOVER PRODUTIVO BLOQUEADO EM G8:** `restall` produtiva viva, porém rota `/delpi/api/v1/suppliers` ausente (404 vs 401 TST) e credencial `api.delpi` rejeitada (401) — handoff Gabriel; `URL_REST@1` mantido em TST para não quebrar o GET de detalhe E14. api-delpi deployado com pino `231:8061` e gates OFF (write tenta → TARGET_MISMATCH). Limite `CONTEUDO varchar(30)` contornado por origem+pseudônimo `/restall` nos paths. Doc: `X4-PROD-C1-SUPPLIER-PRODUCTION-REST-CUTOVER.md`.


**X4.PROD-C1 HANDOFF/PAUSA (2026-10-23):** o PO determinou **aguardar a resposta do Gabriel/TOTVS**. O estado operacional de referência para qualquer chat futuro está em [X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md](./X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md). `LOCAL_ASSAY=ACCEPT_WITH_RESIDUAL` (POST 53/53; PUT 51 campos com 5 `UNCHANGED_REQUIRED`); `G8=FAIL` (suppliers 404 + token 401 na REST produtiva); `CUTOVER=EXECUTION_DRIFT/BLOCKED`; `CREATE/UPDATE PROD=OFF`; `URL_REST@1` ainda na REST TST por dependência de GET E14, com escrita fail-closed por pin; publicação parcial da guarda registrada como drift. **Próxima ação não autorizada até reply:** revalidar G8 somente leitura após resposta do Gabriel, sem flip ou escrita antecipados.


**HOME-ATTENTION — EXECUTADO (2026-10-23):** os sete atalhos genéricos da seção Atenção da Home foram substituídos por **situações reais com contagem comprovada, prévia ≤3 e alvo contextual**: `purchase_requests_ordering`/`purchase_requests_receiving` (buckets do summary de `purchase-requests-api`), `purchase_orders_late` (`late_lines` da api-delpi), `late_deliveries` (Σ `late_lines` OTD do mês corrente por unidade) e `safety_stock_below` (Σ `below_safety_stock`, deep link para `/apps/estoque-seguranca` gated por `estoque-seguranca.access`). Falha de origem = `unavailable` + `partialFailures`, nunca zero; `count=0` confirmado = omissão. `my_tasks`, `overview` e `administration` removidos como alertas (residual `TO_INVENTORY` em my_tasks por falta de owner). Resultado completo: [HOME-ATTENTION-REAL-DATA-RESULT-20261023.md](./HOME-ATTENTION-REAL-DATA-RESULT-20261023.md). Esta frente não altera o estado `X4.PROD-C1` aguardando Gabriel/TOTVS.


**HOME-ATTENTION — GO de execução (2026-10-23):** PO autorizou Devin a percorrer **A0 inventário → A1 contract freeze → A2 BFF/owners autorizados → A3 MFE Atenção → A4 testes + commit/push + deploy + smoke**, sem pausas artificiais para aprovação, conforme [plano atualizado](./HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md). Deploy só se gates técnicos e de segurança passarem. Fontes sem evidência ficam excluídas, sem bloquear fontes independentes. Não alterar demais seções/páginas da Home, RBAC, fornecedores PROD-C1 nem flags ERP. Status `AUTHORIZED_FOR_EXECUTION`, runtime `PENDING`.


**HOME-ATTENTION.P3 — REMOVE_ATTENTION (2026-10-23):** inventário da fonte de tarefas concluiu que **não existe serviço canônico de tarefas atribuídas ao usuário**: `my_tasks` é placeholder navegacional ("será composta nas jornadas seguintes"); Core `/me/notifications` é caixa de entrada informativa ao destinatário (read≠pendência a executar; dispatchers de `purchase-requests-api` notificam o solicitante sobre mudanças de estado, não atribuem ação); `assigned_to` só existe em contextos alheios (helpdesk, LNF). Decisão: **remoção integral da seção Atenção** — `GET /home/attention` (BFF), `HomeAttentionService`, client/store MFE e o destaque "Atenção" do hero (que derivava dos cards) foram removidos. A Home passa a abrir sem nenhuma chamada operacional (SC summary, PCs atrasados, OTD, ESTSEG); essas fontes seguem servindo as páginas de destino. `my_tasks` permanece na navegação. Resultado completo no §12 de [HOME-ATTENTION-REAL-DATA-RESULT-20261023.md](./HOME-ATTENTION-REAL-DATA-RESULT-20261023.md).

**PR.IDENTITY.S1 — Solicitante com nome Minha DELPI (2026-10-23):** a coluna Solicitante de Solicitações de Compras (tabela, cards e ficha) passa a exibir o **nome oficial da plataforma** quando o `requester.protheus_user_id` (`C1_USER`) possui vínculo `mapped` na Core `user_protheus_identities`. Resolução determinística no BFF: `POST /integrations/protheus-identities/lookup` (S2S, batch ≤50) → `POST /me/directory/users/lookup` (Bearer do usuário) → `requester.display_name`. Sem matching por nome; sem N+1 (2 chamadas por página, dedup); fallback honesto ao nome/código TOTVS quando não há vínculo ou a Core falha; nenhuma permission nova, nenhum endpoint novo. Detalhes em [PR-IDENTITY-S1-REQUESTER-CORE-RESOLUTION.md](./PR-IDENTITY-S1-REQUESTER-CORE-RESOLUTION.md).

**PR.IDENTITY.S2 + PR.FILTERS.S1 — Foto real e filtros completos (2026-10-23):** identidade do solicitante agora mostra foto real Minha DELPI (quando `has_photo` no perfil Core — proxy BFF `/purchase-requests/requesters/{pid}/photo` resolve o vínculo `mapped` e busca os bytes S2S, sem expor UUID/token), nome oficial (`display_name`) ou, sem vínculo, o nome de origem TOTVS — **nome único** (PR.IDENTITY.S3 removeu a linha secundária; `requester.name` permanece no contrato como fallback); fallback visual para iniciais. Filtros novos na lista: **Solicitante** (seletor pelo nome oficial via facet `/requesters` enriquecido, envia `requester_user_id`=`protheus_user_id`) e **Centro de custo** (novo facet `cost-centers` `C1_CC`+`CTT_DESC01` em api-delpi→PR-api→BFF, com `cc_scope`/scope carriers e sem auto-filtro). Facets seguem branches+período; filtros serializam na URL e resetam página. Produto/SC = match exato; período = `C1_EMISSAO` (abertura) — documentado. Detalhes em [PR-IDENTITY-S2-FILTERS-S1-REQUESTER-PHOTO-AND-LIST-FILTERS.md](./PR-IDENTITY-S2-FILTERS-S1-REQUESTER-PHOTO-AND-LIST-FILTERS.md).

**PR.UI.S4 — Scroll do MultiSelect portaled (2026-10-23):** o dropdown do filtro Centro de custo não rolava — os wildcards `[class*="-select__*"]` do `select-control.css` capturavam as classes `-multi-select__*` por substring, impondo `overflow:hidden` no painel e `max-height:none` na lista (itens do fim fisicamente cortados, sem região de scroll). Correção no owner (`@delpi/plugin-ui`): wildcards do select negados com `:not(...multi-select...)` e o multi-select portaled passou ao contrato canônico — painel capado em `min(70vh, 480px)`, busca/ações fixas, só a lista rola. Beneficia todos os consumidores do `createDashboardMultiSelectField` via remote `plugin_ui/styles`. Detalhes em [PR-UI-S4-MULTISELECT-SCROLL-FIX.md](./PR-UI-S4-MULTISELECT-SCROLL-FIX.md).

**PR.IDENTITY.S4 — Identidade consistente lista↔ficha (2026-10-23):** a ficha da SC exibia o nome TOTVS (`ELAINE`) enquanto a lista já resolvia o nome oficial — `_requester_refs` do `RequesterIdentityService` não descia em `header.requester` (payload real `{header, lines, timeline}`). Correção de uma linha no owner enriquece header com `display_name`+`photo_url`; inventário portal-wide classificado (comprador `C7_COMPRA` e aprovador sem vínculo SYS_USR comprovado → origem preservada; avatar próprio/fornecedor fora do escopo pessoa). Detalhes e matriz completa em [PR-IDENTITY-S4-PORTAL-WIDE-CONSISTENCY.md](./PR-IDENTITY-S4-PORTAL-WIDE-CONSISTENCY.md).

**SUPPLIERS.NAV.S1 — Links contextuais para a ficha E14 (2026-10-24):** avatar e nome do fornecedor viraram **uma única área navegável** nas páginas operacionais que já exibiam `SuppliesSupplierIdentity` — lista/cards/detalhe de Pedidos de Compra e lista de Entregas/Atrasos. Navegação centralizada no componente (prop `basePath`): com `supplier_code`+`supplier_store` do contrato real, `SuppliesEntityLink` (kit) + `buildSupplierDetailPath` + `navigatePluginPath` abrem `/suppliers/:code/:store`; sem código ou loja, identidade permanece informativa — nunca loja `01` presumida, nome ou CNPJ como chave. `DeliveriesListTable` ganhou prop `basePath` (repassada da página). Zero diff backend/produtor (todos os consumidores já tinham a chave composta), zero permission nova (mesma policy `can_use_operations` do destino), escrita ERP intocada. Guard estrutural impede regressão a URL ad hoc; manual/FAQ sincronizados. `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Detalhes em [SUPPLIERS-NAV-S1-CONTEXTUAL-SUPPLIER-LINKS.md](./SUPPLIERS-NAV-S1-CONTEXTUAL-SUPPLIER-LINKS.md).

**USERS.PROFILE.S1 — Ficha do usuário + navegação por avatar (2026-10-24):** decisão de reúso — a ficha `/apps/supplies/users/:userId` (view `user_profile`, kit `createDashboardPortalUserProfilePage`, política self|admin no BFF) já existia; `/people/:code` descartada (chave canônica = `user_id` opaco Core). **BFF:** gateway Core generalizado p/ `user_ids` no lookup bidirecional; `RequesterIdentityService` projeta `user_id` no `PersonRef`; rotas novas `GET /users/:id/related-requests` (SCs do vínculo target — `user_id`→`protheus_user_id` mapped→`requester_user_id`; `branch` opcional validado por `require_units` só quando fornecido — fix do empty-list 403; paginação máx 20; degrade parcial) e `GET /users/:id/photo` (proxy S2S, 404 fail-closed). **MFE:** `SuppliesPersonIdentity` com `basePath` opt-in → `SuppliesEntityLink`→`buildUserProfileHref` quando `user_id`+`canAccessUserProfile`; wiring lista/cards/detalhe SC + detalhe PC; seção «Solicitações de compra relacionadas» paginada com «Ver todas» (filtro `requester_user_id` já existente); foto do target via BFF. Tarefas/Pedidos por papel `BLOCKED` (sem contrato/vínculo). Zero permission nova, zero ERP write. 452 BFF + 391 MFE testes, tsc/build verdes, lint 0 erros. `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Detalhes em [USERS-PROFILE-S1-USER-OPERATIONAL-CONTEXT.md](./USERS-PROFILE-S1-USER-OPERATIONAL-CONTEXT.md).

**USERS.PROFILE.S2 — E-mail real e SCs relacionadas na ficha (2026-10-24):** duas causas-raiz provadas e corrigidas. **A (e-mail `p***@`):** a máscara era produzida pela Core (`/me/directory/users/lookup` mascara por padrão) — `_identity_for` agora envia `reveal_email=true`, flag autorizada do próprio contrato («perfis de portal precisam do endereço real»); requester-enrichment segue mascarado (minimização). **B (lista vazia):** o produtor exige `branch` (`Query(...)`); o BFF omitia sem filtro → 422 mascarado como `relatedEmpty` pelo MFE. Fix: universo default = `allowed_units(actor)` (nunca amplia), `date_from="2000-01-01"` explícito (eliminado o lookback silencioso de 90 dias do api-delpi), `data.error` agora vira estado de erro distinto no MFE, lookup Core indisponível → `identity_lookup_unavailable` (não `requester_unmapped`). Evidência: `c8ef4b53`↔`000304` mapped; SC 178764 `C1_USER=000304` filial 01. 455 BFF + 390 MFE testes, tsc/lint/build verdes. Doc: `USERS-PROFILE-S2-EMAIL-AND-RELATED-REQUESTS-FIX.md`.

**USERS.PROFILE.S3 — Tabela real de SC na ficha do usuário (2026-10-24):** a seção «Solicitações de compras» da ficha deixou a listinha simplificada e passou a renderizar a **mesma** `PurchaseRequestsListTable` da listagem principal — reuso real de componente, colunas, identidade do solicitante, badges, ordenação server-side e `SuppliesCompactPagination` (25/50/100; cap BFF 20→100, dentro do teto 200 do produtor). Grão reconciliado sem adaptador: `items: PurchaseRequestListItem[]` já era o mesmo contrato/grão (linha de item) da lista. `canExport=false` na ficha (sem contrato de export por solicitante); «Ver todas» preservado com `requester_user_id`+`date_from`. BFF ganhou passthrough `sort_by`/`sort_dir` validado pela allowlist do produtor. CSS morto `sp-user-profile__related*` removido; zero CSS novo. +1 teste BFF (sort passthrough) + 1 guard MFE de reuso real. Suíte: 481 BFF + 391 MFE, tsc/build verdes, lint sem problemas novos (32 pré-existentes em main). `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Doc: `USERS-PROFILE-S3-REUSABLE-PURCHASE-REQUESTS-TABLE.md`.

**SUPPLIES-TOPBAR-PURCHASE-ORDERS-LABEL (2026-10-24):** correção de navegação — o item da topbar «Operações» passa a «Pedidos de compra», seu destino real (`/purchase-orders`, inalterado). O `PluginNavId` `operations` foi renomeado para `purchase_orders` e o estado ativo restrito a lista+detalhe de pedidos — Entregas/Fornecedores/Produtos/Estoque/Estoque de Segurança deixam de ativar o item (sem associação falsa; nenhum item ativo nessas páginas). O agrupamento «Operações» da Home (`pluginRouteCatalog`) permanece integral. Owner: `plugins/supplies` (shell do MFE — zero Core/RBAC/permission). Help nav + bullet do Manual sincronizados. **438 testes verdes; tsc/build OK; lint delta 0.** `VISUAL_AUTHENTICATED=INCONCLUSIVE`.

**E11.S9 — Cards de indicadores interativos Estoque de Segurança (2026-10-24):** os seis cartões do hero filtram a tabela (clique/Enter/Espaço, `aria-pressed`, um ativo por vez); a barra de chips S8 foi removida — sem dois sistemas de filtro. **Card composto com suporte contratual real:** «Com estoque de segurança» = `includeWithoutSafetyStock=false` → `status <> 'without_safety_stock'` no produtor (união abaixo/no/acima) — sem filtro fictício nem recálculo; «Materiais» restaura o recorte completo; cards de status único preservam o toggle (regra S8). **Kit canônico:** `PageHeroHighlight` ganhou `onSelect`/`active`/`ariaLabel` aditivos (`role="button"`, `--interactive`/`--pressed`, mesmo padrão `SimpleKpiCard`) — zero breaking change. Fonte única com `query.status`/`includeWithoutSafetyStock`; URL/F5/back/forward intactos; `page: 1` na troca. Contadores mantêm semântica de recorte (nunca totais independentes). Help/Manual/FAQ sincronizados sem vestígio da barra. **438 testes MFE + 7 PageHero verdes; tsc/build OK; lint feature zerada.** `VISUAL_AUTHENTICATED=INCONCLUSIVE`; `GATE-FEATURE E11` segue **INCONCLUSIVE**. Doc: [E11-S9-INTERACTIVE-SUMMARY-CARDS.md](./E11-S9-INTERACTIVE-SUMMARY-CARDS.md).

**E11.S8 — Filtros rápidos por situação Estoque de Segurança (2026-10-24):** barra de chips «Situação» entre os indicadores do hero e a FilterBar — padrão comprovado do Portal Comercial (`attentionChips` + `createDashboardScopeChipBar`, kit `plugin-ui`), via `SuppliesScopeChipBar` canônico (mesmo componente das listas SCs/POs, zero import cross-context). **Fonte única:** os cinco botões aplicam apenas `patchQuery({ status, page: 1 })` — chips e select Status são duas visões do mesmo `query.status` (sync bidirecional estrutural: botão↔select↔URL↔F5/back/forward); um ativo por vez derivado do estado; filial, grupo, UM, busca, toggles e ordenação preservados por omissão. **Contadores omitidos:** `fetch_summary` do produtor aplica `status` no `WHERE` do resumo — contadores são do recorte ativo, não totais; a task autoriza omissão e o hero já exibe os números do recorte. Ajuda sincronizada (hint `SP_HELP.safetyStockQuickFilters` + Manual + FAQ). **438 testes verdes (+1 estrutural); tsc/build OK; lint feature zerada, baseline inalterada.** `VISUAL_AUTHENTICATED=INCONCLUSIVE`; `GATE-FEATURE E11` segue **INCONCLUSIVE**. Doc: [E11-S8-SAFETY-STOCK-QUICK-FILTERS.md](./E11-S8-SAFETY-STOCK-QUICK-FILTERS.md).

**E11.S7 — Detalhe em página + seleção de filial Estoque de Segurança (2026-10-24):** decisão do PO implementada com diff mínimo. **Página:** `SafetyStockDetailPage` substitui o modal (arquivo removido, sem detalhe paralelo) em rota interna canônica `safety-stock/{branch}/{productCode}` — mesmo padrão de PO/SC/Fornecedor, **sem manifest/Core novo**. `SuppliesPagePath` («Estoque de Segurança») retorna à listagem com recorte preservado via `?from=`; deep links legados `item`/`itemBranch` redirecionam. **Seleção:** `branch=all` abre `SafetyStockBranchChoiceDialog` (01/02 explícitos, sem default, «Cancelar», confirmar desabilitado até escolher, zero request antes); `01`/`02` navegam direto; o filtro da listagem nunca é alterado pela escolha. **Invariantes preservadas:** dois GETs BFF existentes, filial concreta sempre (nunca `all`), dois canais independentes, abort/identidade chaveada, retry, guards de payload, zero N+1, zero permissão nova, cálculo do produtor intacto. **437 testes verdes (+4); tsc/build OK; feature lint zerada; baseline global inalterada.** `VISUAL_AUTHENTICATED=INCONCLUSIVE`; `GATE-FEATURE E11` segue **INCONCLUSIVE** (aguarda jornada autenticada do PO). Doc: [E11-S7-DETAIL-PAGE-IMPLEMENTATION.md](./E11-S7-DETAIL-PAGE-IMPLEMENTATION.md).

**E11.S6 — Correção UX pós-deploy Estoque de Segurança (2026-10-24):** evidência visual do PO tratada com diff mínimo. **Terminologia:** `ESTSEG` eliminado de toda a UX (indicadores, coluna, toggles, detalhe, projeção, tooltips, Manual/FAQ) — glossário mantém a sigla como referência do campo Protheus. **Filial:** investigado o contrato — `materials_base_cte` agrega por produto com `SUM` no escopo; `branch="all"` na linha é recorte consolidado legítimo (sem `EXECUTION_DRIFT`); `formatSuppliesUnitName` traduz `all` → «Todas as Filiais» em todos os consumidores. **Cabeçalhos:** `headerHint` do kit nas 11 colunas + ação `Detalhes`, textos em `SP_HELP` sem redefinir cálculo; ordenação/paginação/URL intactos. **Toggles:** causa raiz = `FilterCheckboxField` (label + checkbox «Incluir») → `SuppliesFilterCheckbox` (`NativeCheckboxControl` + hint tooltip) com um único rótulo. **Tabela:** coluna Status com `min-width` + badge `nowrap`; CSS isolado em `.sp-safety-stock*`. **Testes:** 433 pass (+3), tsc/build OK, `LINT_DELTA=0`. `VISUAL_AUTHENTICATED=INCONCLUSIVE`; `GATE-FEATURE E11` segue **INCONCLUSIVE** (aguarda jornada autenticada do PO). Doc: [E11-S6-UX-CORRECTION-PO-SCREENSHOTS.md](./E11-S6-UX-CORRECTION-PO-SCREENSHOTS.md).

**E11.S5 — Deploy federado + Runtime Gate Estoque de Segurança (2026-10-24):** deploy canônico em produção (`srv-api`) — `git pull --ff-only` → `553a19a0`, `up-prod-sequential.sh --fase api --build supplies-api` (imagem `aa60c1c3`, antes `289c0c45`) e `--fase mfe --build supplies` (imagem `6f01d3dc`, antes `67ad9c89`), ordem BFF→MFE. Verificado: `remoteEntry.js` via gateway md5 `3310dd17…` idêntico ao container, bundle contém markers E11 (detalhe, identidade, Manual), container BFF contém `_require_safety_stock_dict`, 5 rotas → 401 anônimo (fail-closed), logs limpos. Lint: 10 erros classificados `PREEXISTING_OTHER_SCOPE` (P2, não corrigidos por conveniência); `LINT_E11=PASS`, delta 0. Rollback documentado (SHA/imagens anteriores). `E11_DEPLOY_STATUS=PASS_DEPLOYED`; **`GATE-FEATURE E11=INCONCLUSIVE`** — smoke autenticado e QA visual dependem de sessão real. Doc: [E11-S5-DEPLOY-RUNTIME-GATE.md](./E11-S5-DEPLOY-RUNTIME-GATE.md).

**E11.S4 — Aceite funcional Estoque de Segurança (2026-10-24):** residuais da revisão GPT S3 corrigidos nos owners corretos. **Identidade:** `detailMatchesTarget` no MFE — match estrito `product_code+branch` (strings, zeros significativos, sem parcial/irmã); divergência → `SafetyStockContractError`. **Envelope BFF:** `_require_safety_stock_dict` nos 5 métodos safety-stock de `SuppliesDelpiReads` — `data` não-dict ou sem chaves contratuais → `DelpiApiGatewayError` → 502 (nunca `{}`/200); empty legítimo e 404 preservados; demais métodos intactos. **Lint E11:** modal e listagem refatorados para estado chaveado (sem `setState` síncrono em efeito) — `safety-stock/` zerada no lint; baseline global 10 erros inalterada. **Help:** seção Manual «Estoque de segurança» (13 bullets) + 5 FAQs + tooltip do detalhe ligado; sem promessa de feature futura nem permission por filial. **Testes:** MFE 430 pass (+testes de identidade negativos), BFF 505 pass/21 skip (+envelope malformado ×5 rotas), tsc+build OK. `VISUAL_AUTHENTICATED=INCONCLUSIVE`, `FEDERATED_SMOKE=TEST_NOT_RUN`. Doc: [E11-S4-SAFETY-STOCK-ACCEPTANCE.md](./E11-S4-SAFETY-STOCK-ACCEPTANCE.md). **E11.S5 (smoke federado) pronta para avaliação.**

**E11.S3 — Detalhe do item Estoque de Segurança (2026-10-24):** modal `SuppliesModal` de detalhe implementado — abertura por «Ver detalhes» (botão com aria-label por produto) e `onRowClick` da tabela. Consome apenas `items/{code}/details` + `items/{code}/suppliers` com **filial concreta** (identidade `product_code + branch` da linha; `all` nunca é enviado). Seções reais do produtor: identificação, saldos + `purchase_coverage`, pedidos/SCs/empenhos em aberto (badge «UM divergente»), `stock_projection` (resumo + extrato com `date_status`), consumo mensal + comparação anual, fornecedores (code+store, última compra). Dois canais independentes (detalhe × fornecedores), abort na troca/fechamento, retry por canal, 401/403/404/422/502 tratados, guards de shape contra envelope malformado. Detalhe endereçável por URL (`item`+`itemBranch`) sem rota/manifest novo. Zero N+1, zero recálculo no MFE. **+12 testes (37 na feature); suíte 428 pass; tsc+build OK; erros de lint idênticos à baseline.** Doc: [E11-S3-SAFETY-STOCK-ITEM-DETAIL-IMPLEMENTATION.md](./E11-S3-SAFETY-STOCK-ITEM-DETAIL-IMPLEMENTATION.md). **E11.S4 pronta para avaliação.**

**E11.S2 — MFE Estoque de Segurança (2026-10-24):** página monitor implementada em `plugins/supplies/src/features/safety-stock/` e ligada no App (placeholder removido). FilterBar (filial `all|01|02` select único, status, grupo, UM, busca debounce, toggles blocked/sem-ESTSEG), hero com 6 contadores de classificação, seção «Cobertura do recorte» (saldo principal/em processo + déficit por UM), DataTable server-side (9 campos sort, page_size ≤200). URL/F5 completa, estados parciais por canal, guards de shape para o residual de envelope do BFF, zero N+1 (detalhe é E11.S3). Filial = filtro (`branch_catalog`, sem `authorized_branches`). **27 testes novos; suíte 418 pass; tsc+build OK.** Doc: [E11-S2-SAFETY-STOCK-MFE-IMPLEMENTATION.md](./E11-S2-SAFETY-STOCK-MFE-IMPLEMENTATION.md). **E11.S3 (detalhe do item) pronta para avaliação.**

**E11.S1 — Backend/BFF Estoque de Segurança (2026-10-23):** 5 rotas read-only implementadas no `supplies-api` (`/safety-stock/{filters,summary,items,items/<code>/details,items/<code>/suppliers}`) — `safety_stock_bp` + `SafetyStockService` + extensão de `SuppliesDelpiReads` (3 métodos novos). AuthZ `can_use_operations` (Core-first); `branch` = filtro `all|01|02` sem fan-out; detalhe exige filial concreta; `authorized_branches` upstream substituído por `branch_catalog = OPERATIONAL_UNITS`; trusted-BFF via caller + service token (sem bypass novo; `BranchAccessGate` intacto). Correção de contrato: sort upstream `sortBy`/`sortDirection`. **18 testes novos; suíte supplies-api 499 pass/21 skip**; zero frontend/deploy. Doc: [E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md](./E11-S1-SAFETY-STOCK-BFF-IMPLEMENTATION.md). **E11.S2 (MFE) pronta para autorização.**

**E11.P0 — Contract freeze Estoque de Segurança (2026-10-23):** inventário read-only do produtor (`safety_stock_router`: filters/summary/items/details/suppliers/price-history + consumption-analysis), do legado `estoque-seguranca` (SafetyStockPage monitor + ConsumptionAnalysisPage) e do kit. `BRANCH_AUTHZ_RECONCILIATION = COMPATIBLE` — `is_trusted_supplies_bff_call()` já bypassa `BranchAccessGate` para o Portal (precedente ativo no Overview KPI-CRITICAL-MP); filial = filtro `all|01|02` validado no BFF contra `OPERATIONAL_UNITS`. BFF: 5 rotas congeladas espelhando `inventory_routes` (filters/summary/items/details/suppliers); `authorized_branches` upstream não consumido. Escopo: página monitor ESTSEG; consumption-analysis = E12; price history dedicado = E18; Product 360 link = E17. `E11_S1_READY_TO_AUTHORIZE = YES`. Doc: [E11-P0-SAFETY-STOCK-CONTRACT-FREEZE.md](./E11-P0-SAFETY-STOCK-CONTRACT-FREEZE.md).

**BRANCH-AUTHZ.DOCS.R1 — Reconciliação global «filial é filtro, nunca autorização» (2026-10-23):** auditoria documental transversal por decisão do PO (registrada em `611cb8c0dc`, que já reconciliou o ROADMAP-R1 — filial como filtro, sem `supplies.unit.*`). Corrigidos: INTEGRACOES (`allowedUnits` = catálogo operacional do domínio, não grants derivados de permissions), HELP (403 nunca é «permissão de filial»), WIREFRAMES, DECISOES_FUNCIONAIS_PENDENTES e README (§7 desatualizado + tabela ADRs com 008/009); banner SUPERSEDED adicionado ao 00-DIAGNOSTICO. ADR-006/007/MANIFEST-DRAFT/PLAYBOOK/PERSONA/INVENTARIO/HOMOLOGACAO/DUPLICIDADES = históricos preservados sob banners já existentes. Contextos alheios preservados (`purchase-requests.unit.*`, `travel-expenses.unit.*`, `cipa.unit.*`, `estoque-seguranca.access`, `BranchAccessGate` do produtor). Manifest e código já conformes — `MANIFEST_BRANCH_PERMISSION_DRIFT = NONE`. Relatório: [BRANCH-AUTHZ-DOCS-R1-GLOBAL-RECONCILIATION.md](./BRANCH-AUTHZ-DOCS-R1-GLOBAL-RECONCILIATION.md).

**ROADMAP.REBASELINE.R1 — Inventário E1–E29 + gate E10 + readiness E11 (2026-10-23):** reconciliação documental read-only. E10 promovida: bloqueio federado superado (bundle servido contém `stock-balances`, rotas 401 protegidas, S1–S3 ancestrais, 23 testes focados) → `GATE-FEATURE E10 = PASS_DEPLOYED`, residual `VISUAL_AUTHENTICATED=INCONCLUSIVE`. E11 classificada `READY_WITH_RESIDUAL`: produtor api-delpi completo, manifest já declara `/safety-stock`, faltam BFF supplies-api + página MFE + recorte vs E12/E17/E18 — receita E11.P0/S1–S5 proposta. Drifts corrigidos: fila de páginas (`/deliveries`, `/inventory`, `/suppliers`), API-ROUTES ganhou `/users/{id}/related-requests` e `/users/{id}/photo`. X4.PROD-C1 e P-01/03/04/06/07/10/11/14/15 preservados; zero código/permission/flag/deploy alterados. Doc canônico: [ROADMAP-REBASELINE-R1-20261023.md](./ROADMAP-REBASELINE-R1-20261023.md).


## Revisão GPT — SUPPLIES-TOPBAR-PURCHASE-ORDERS-LABEL (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`.** Conferidos no source `f89e73376c`: `src/content/shellNav.ts` (item `purchase_orders`, rótulo “Pedidos de compra”, capability de navegação `operations` preservada), `src/app/PluginShell.tsx` (destino e Help atualizados), `src/app/pluginRoutes.ts` e testes. `resolveActiveNavId` destaca apenas `purchase_orders` e `purchase_order_detail`; Entregas, Fornecedores, Produtos, Estoque e Estoque de Segurança deixam de destacar um destino falso. O agrupamento «Operações» permanece na Home, sem alterar contratos Core/manifest/RBAC. Testes 438 PASS, tsc/build e deploy do MFE (imagem `sha256:08c58d180dba`, bundle `App-B5RqSPpY.js`) são evidências reportadas pelo executor, não reexecutadas pelo GPT.

**Residual:** smoke autenticado e verificação visual desktop/mobile/teclado `INCONCLUSIVE`. Confirmar em produção o rótulo e clique da topbar, a seleção ativa na lista e detalhe de pedidos e ausência de destaque falso nas outras páginas; confirmar agrupamento da Home. A correção é transversal de UX e não fecha, por si, `GATE-FEATURE E11`.

## PROC-0076 — Inteligência de Mercado — DEPLOYED com GATE-FEATURE INCONCLUSIVE (2026-10-26/27)

Entrega dedicada fora da fila WF (PR #111 documental + implementacao em main + rework R1 em fix/proc-0076-r1).

**Camadas:** external-data-api e owner do historico de mercado (schema canonico fixo external_data, migrations V001-V003 checksum+advisory lock, boot degradado, providers PTAX ODbL e World Bank Pink Sheet CC BY 4.0, ingestao opt-in EXTERNAL_DATA_FEED_* OFF em producao). supplies-api e o BFF (/market-intelligence/{filters,summary,series,monthly-averages}, supplies.access, S2S para external-data-api, Decimal, medias mensais, cobertura, conversao USD->BRL por media PTAX mensal, freshness por cadencia de publicacao — consulta historica nao vira stale; unidade exibida BRL/metric ton quando convertido com native/conversion auditaveis). plugins/supplies renderiza o contrato (kit-first, URL/F5/back-forward, estados 401/403/404/422/429/502-504, banner stale com evidencia temporal, Help/Manual/FAQ/Glossario sincronizados).

**Correcoes R1:** frescor separado em periodo consultado x cadencia do provedor x ultima ingestao (datas congeladas em testes); unidade monetaria corrigida sem taxa sintetica; schema external_data tornado constante canonica (isolamento por database); testes PostgreSQL reais em banco descartavel (antes TEST_NOT_RUN); V003 registra proveniencia LME das series Pink Sheet + escopo no_redistribution_pending_lme_review; MFE passa a tipar freshness/native/conversion e a exibir unidade correta nos KPIs.

**Pendencias reais:** GATE-FEATURE = INCONCLUSIVE — E11 nao reconciliado (link de navegacao fora do hub/palette por decisao do plano), smoke federado autenticado INCONCLUSIVE (sem credenciais), feed PTAX com HTTP 403 no egress de producao (WAF BCB; sem bypass; conversao BRL indisponivel ate solucao operacional), ingestao EXTERNAL_DATA_FEED_* OFF ate autorizacao operacional. Fontes sem licenca (LME direto, Shockmetais) permanecem fora do catalogo.

Commits: e1c7974327 (feat P0), 660ddd3983/fecb855107 (fixes producao), 3b13494c69/ebe1f54ee4/4f81f9c233/313c5469da (R1).
