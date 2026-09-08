# IMPLEMENTATION-PLAN — Portal Suprimentos

> **Status:** plano executável revisado · set/2026 · **E1–E6 concluídas** · E7+ não iniciar sem autorização explícita  
> **Readiness atual:** **E1–E6 + E4.S4 perfil + GATE-AUTHZ + GATE-RBAC PASS (local)**  
> **Modo:** **uma página por vez** · **Início + Visão geral fechados** · **foco = SC (WF-04)** · E7 só após fechar a fila até Pedidos  
> Referências: ADR-001..ADR-007, `plan-construction.mdc`, `evidence-driven-execution.mdc`, README § Protocolo página-a-página.

---

## 1. Objetivo

Entregar o Portal Suprimentos como hub capability-driven:

```text
Portal
→ MFE supplies
→ supplies-api (Flask)
→ Core /me + api-delpi + SI + contextos autorizados
```

sem bypass de api-delpi pelo MFE, sem espelho TOTVS, sem autorização por permissions dos claims JWT e sem inflar RBAC por CRUD.

---

## 2. Decisões travadas

| Decisão | Referência |
|---|---|
| id `supplies`, base `/apps/supplies`, CSS `.dashboard-supplies-portal` | ADR-004 |
| API própria `supplies-api` em Flask | ADR-001 |
| JWT identifica; Core `/me` resolve effective permissions | ADR-001/006 |
| MFE só fala com supplies-api | ADR-001 |
| capabilities mínimas, não CRUD | ADR-007 |
| unidade ortogonal `supplies.unit.filial-{TOTVS}` | ADR-006 |
| SC: C0 → C1 → C2 → paridade final → C3 | ADR-002 |
| BIs externos não podem ficar `LEGADO_A_VALIDAR` no GO | ADR-005 |
| target saudável antes de redirect | CUTOVER-RUNBOOK |
| Home ≠ Overview | DESIGN-IA |
| Páginas generalistas = padrão Comercial (shell, Home, Ajuda, perfil `/users/:userId`; prefs no perfil) | WIREFRAMES WF-HELP/WF-USER · DESIGN-IA §2 |
| **Uma página por vez até DoD** — não paralelizar páginas user-facing nem antecipar E7 enquanto houver foco aberto | README § Protocolo · DESIGN-IA §1 |

---

## 2.1 Protocolo página-a-página (obrigatório)

```text
escolher 1 página da fila
→ plano só dessa página (+ Ajuda satélite se user-facing)
→ BFF/UI/AuthZ/estados/Ajuda/testes/docs
→ DoD fechado (GATE-FEATURE)
→ só então abrir a próxima
```

| # | Página | Etapa canônica | Estado |
|---|---|---|---|
| 1 | Início | E4 + polish shell/Favoritos/helps | **FECHADA (DoD)** |
| 2 | Visão geral | E5 + série OTD + kit FilterBar/Chart | **FECHADA (DoD)** |
| 3 | Solicitações de compras | E6 C1 | **EM FOCO** — revalidar DoD |
| 4 | Pedidos de compra | E7.S* | aguardando |
| 5 | Entregas | E7.S* | aguardando |
| … | demais | E8+ | fila |

**Anti-padrões:** iniciar E7.S1 enquanto o Início estiver em foco; misturar duas UIs no mesmo plano; marcar página “concluída” com placeholder interno.

DoD resumido: contrato + UI kit + AuthZ + estados L/E/E/403/404 + Ajuda + testes + docs (detalhe no README).

## 3. Gates

### GATE-AUTHZ

Passa somente quando:

- JWT validado;
- effective permissions vêm do Core;
- nenhuma autorização nova usa `claims.permissions`/`claims.is_superadmin` como fonte final;
- Core indisponível = fail-closed **na fronteira** da supplies-api (não só em alguns decorators);
- testes positivo, negativo e filial cruzada verdes.

**Não copiar:** `shared/delpi_auth/middleware/flask_auth.py` nem o fallback FastAPI `rbac_lookup_unavailable_using_token_claims` / `_rbac_from_claims` (ADR-001 DRIFT-AUTHZ-01).

### GATE-E1

**PASS (2026-09-08)** quando:

- dump dos BIs externos concluído (local documentado; prod residual para cutover);
- papéis SC/ES mapeados;
- KPIs P0 homologados ou explicitamente bloqueados.

### GATE-ARCH

**PASS (2026-09-08)** quando:

- ADRs 001–007 revisados;
- `MANIFEST-DRAFT.md` validado contra runtime real (`schemaVersion 1.0.0`);
- catálogo de permissions mínimo aprovado (ADR-007).

### GATE-RBAC

**PASS (local 2026-09-08)** quando:

- permissions canônicas provisionáveis (manifest registrado);
- papéis canônicos criados (`plugins/supplies/scripts/provision-rbac-coexistence.sh`);
- smoke `GET /me` + `GET /me/apps` (rotas embutidas — Core **não** expõe `/me/routes`);
- evidence: `evidence/e3-s5-rbac-smoke-local.json`.

Persona negativa em user não-superadmin e Comprador ES operacional ficam para HML/prod com usuários reais.

### GATE-C2

- supplies-api assumiu ownership/jobs de `purchase_requests`;
- reconciliação concluída;
- rollback/roll-forward conhecido.

### GATE-PARITY

- comparação quantitativa concluída;
- nenhum gap crítico sem aceite.

### GATE-CUTOVER

- GATE-C2 + GATE-PARITY;
- nenhum BI externo em `LEGADO_A_VALIDAR`;
- target saudável;
- RBAC canônico ativo;
- redirects fechados e rollback testado.

---

## 4. Matriz transversal

| Fluxo | Capability | Unit | Resource scope | API | Ajuda |
|---|---|---|---|---|---|
| Abrir Home | portal | não para shell | próprio usuário | supplies-api | sim |
| Overview | analytics | sim | — | api-delpi + SI | sim |
| SC | purchase-requests | sim | CC fail-closed | PR-api C1 / PG C2 | sim |
| Export SC | purchase-requests + export | sim | CC/view-all | BFF | sim |
| PC/entregas | operations | sim | PC no recorte | api-delpi | sim |
| Fornecedor 360 | operations | sim | fornecedor/branch | composição | sim |
| Nota fornecedor | operations | sim | fornecedor + ownership/política equipe | PG | sim |
| Produto 360 | operations | sim | item/branch | composição | sim |
| Estoque/ESTSEG | operations | sim | branch | api-delpi | sim |
| Task/follow-up | portal + capability do recurso | quando ref exigir | ownership/equipe | PG | sim |
| Administração | administration | quando aplicável | unidade administrada | PG/PR-api | sim |

---

# E1 — Descoberta residual e freeze de contratos

## E1.S1 — Dump Core dos BIs externos

**Objetivo:** identificar id/path/type/permissions reais dos 6 apps do PO.

**Fazer:** consultar Core/admin/SQL autorizado; atualizar inventário, ADR-005 e paridade.

**Não fazer:** inventar redirect ou alias.

**Evidência:** tabela 6/6 preenchida ou “não encontrado” com data.

**Teste:** checklist documental `HOMOLOGACAO-PARIDADE.md` seção BIs.

**Pronto quando:** P-01, P-03, P-04 e P-07 atualizados.

## E1.S2 — Mapear papéis reais

**Objetivo:** confirmar composição SC/ES e comprador ES.

**Evidência:** papel × permissions × units.

**Teste:** comparação com `/core-api/me`, `/me/apps`, `/me/routes` de usuários de homologação.

**Pronto quando:** P-02 fechado ou explicitamente não aplicável.

## E1.S3 — Homologar KPI P0

**Objetivo:** fechar ≤8 KPIs do Overview e suas janelas temporais.

**Evidência:** `KPI-FICHAS.md` sem fórmula P0 ambígua.

**Teste:** revisão owner Suprimentos + fonte canônica.

## E1.S4 — Validar Manifest Draft e RBAC mínimo

**Objetivo:** congelar route × capability × unit sem CRUD inflation.

**Evidência:** ADR-007 + MANIFEST-DRAFT aprovados.

**Teste:** validar draft contra schema/registrador real do Core.

## E1.S5 — Freeze arquitetural

**Objetivo:** declarar GATE-E1 + GATE-ARCH e liberar o caminho documental para E2.

**Feito em 2026-09-08:**

| Gate | Veredito | Evidência |
|---|---|---|
| GATE-E1 | **PASS** | ADR-005 dump local; PERFIS E1.S2; KPI-FICHAS E1.S3 (7 KPIs) |
| GATE-ARCH | **PASS** | ADRs 001–007; MANIFEST-DRAFT `1.0.0` dry-run vs schema Core |

**Residuais explícitos (não reabrem E1):**

- Dump Core **produção** dos 6 BIs — obrigatório antes de `GATE-CUTOVER` (P-01/P-03/P-04/P-07).
- Smoke `/me` de personas supplies — E3.S5 (Core local sem apps supplies).
- Aceite nominal PO nas fichas KPI — Assinatura em KPI-FICHAS.
- GATE-AUTHZ / código Flask — E2.S2.
- P-13 — antes de E2.S4.

**Pronto quando:** GATE-E1 + GATE-ARCH — **atingido**.

**Não fazer nesta subetapa:** scaffold Flask; marcar GATE-AUTHZ/GATE-RBAC verdes.

---

# E2 — Fundação supplies-api e authz

## E2.S1 — Scaffold Flask

**Fazer:** criar `supplies-api/` em Flask com Clean Architecture, `/health`, `/ready`, config e testes.

**Não fazer:** copiar framework FastAPI do commercial-api.

**Teste futuro:**

```bash
pytest supplies-api/tests/interface/http/test_health.py -q
```

## E2.S2 — AuthN/AuthZ Core-first

**Objetivo:** JWT identifica; Core `/me` autoriza; Core fora = 503/401 na fronteira.

**Fazer:** middleware Flask próprio da supplies-api; request context; testes positivo/negativo/filial.

**Não fazer:** copiar `flask_auth.py`; copiar `fastapi_auth.py` (`rbac_lookup_unavailable_using_token_claims`, `_rbac_from_claims`, stale cache como AuthZ nova); confiar em `claims.permissions` / `claims.is_superadmin`.

**Evidência:** ADR-001 DRIFT-AUTHZ-01 + INTEGRACOES §2.

**Testes futuros:**

```bash
pytest supplies-api/tests/security/test_effective_permissions.py -q
pytest supplies-api/tests/security/test_unit_authorization.py -q
```

**Pronto quando:** GATE-AUTHZ.

**Commit:** `feat(supplies-api): autorizar pelo Core, não por claims JWT`

## E2.S3 — Envelope, erros e observabilidade

**Teste futuro:**

```bash
pytest supplies-api/tests/interface/http/test_error_contract.py -q
pytest supplies-api/tests/observability/test_request_context.py -q
```

## E2.S4 — SQL schema `supplies`

Criar somente preferences P0 via `migrations/V001__*.sql` (padrão plugins). Nada de clone TOTVS. Nada de Alembic.

**Teste futuro:**

```bash
pytest supplies-api/tests/infrastructure/test_migrations.py -q
```

## E2.S5 — Gateway api-delpi

Timeout explícito, caller, sem retry não seguro.

**Teste futuro:**

```bash
pytest supplies-api/tests/infrastructure/gateways/test_delpi_api_gateway.py -q
```

## E2.S6 — `/me/capabilities`

Mapear effective permissions + aliases temporários para flags mínimas e `allowedUnits`.

**Teste futuro:**

```bash
pytest supplies-api/tests/application/test_capability_resolution.py -q
```

---

# E3 — Shell MFE + RBAC de coexistência

## E3.S1 — Scaffold MFE

Module Federation + plugin-ui, root CSS isolado.

**Teste futuro:**

```bash
cd plugins/supplies && npm run build
```

## E3.S2 — Cliente HTTP BFF-only

**Teste futuro:**

```bash
rg -n "api-delpi|API_DELPI_BASE|apiDelpiUrl" plugins/supplies/src
```

Esperado: zero ocorrências de chamada direta.

## E3.S3 — Shell capability-driven

TopBar, nav, palette, estados e theme.

**Teste futuro:**

```bash
cd plugins/supplies && npm test -- routeCatalog
```

## E3.S4 — Registrar manifest em homologação

Usar contrato validado do `MANIFEST-DRAFT.md`.

## E3.S5 — Provisionar RBAC de coexistência

Adicionar permissions canônicas aos papéis/grupos sem remover legadas.

**Smoke obrigatório:**

```text
/core-api/me
/core-api/me/apps   # rotas filtradas em apps[].routes — Core não expõe /me/routes
```

Casos: comprador SC, analista, usuário sem supplies, superadmin e comprador ES se existir.

**Pronto quando:** GATE-RBAC (local documentado em `evidence/e3-s5-rbac-smoke-local.json`).

---

# E4 — Home e Ajuda inicial

## E4.S1 — Catálogo de rotas

Usar capabilities mínimas; não roles.

## E4.S2 — `/home/attention`

Compor apenas cards autorizados. Partial failure permitido para bloco auxiliar.

**Teste futuro:**

```bash
pytest supplies-api/tests/application/test_home_attention.py -q
cd plugins/supplies && npm test -- Home
```

## E4.S3 — Ajuda esqueleto

Manual + Quero→onde + FAQ inicial.

## E4.S4 — Perfil usuário (generalista, padrão Comercial)

**Objetivo:** página `/users/:userId` (WF-USER) alinhada ao Comercial — identidade Core + preferências `supply_user_preferences` + atalhos por capability.

**Fazer:**
1. Rotas MFE `users/:userId` + `UserProfilePage` (PagePath/PageHero; prefs só self).
2. BFF `GET/PATCH /users/{id}/profile` (compose Core + preferences); PATCH só self na P0.
3. Entrada UX: atalho self (shell/hero) sem poluir UnderlineNav.
4. Ajuda: Quero→onde «alterar filial padrão / tema» → Perfil; distinguir `/profile` do Portal host.
5. Testes: self ok; outro usuário sem admin → 403; admin leitura ok; prefs default_branch fora de allowedUnits → 422.

**Não fazer:** volume de avatar dedicado; cargo/carteiras comerciais; bloquear E6; segunda página `/preferences`.

**Wireframes:** [WF-USER](./WIREFRAMES.md) · [DESIGN-IA §2 generalistas](./DESIGN-IA-SUPRIMENTOS.md).

**Teste futuro:**
```bash
pytest supplies-api/tests/application/test_user_profile.py -q
cd plugins/supplies && npm test -- UserProfile
```

**Pronto quando:** perfil self utilizável; admin lê terceiros; prefs no mesmo lugar que o Comercial (perfil do plugin).

**Status:** **concluída** (BFF + MFE `/users/:userId` + avatar TopBar + Ajuda).

**Não bloqueia:** E6 SC C1.

---

# E5 — Overview

## E5.S1 — BFF Overview

6–8 KPIs homologados; somente allowedUnits; fan-out resiliente.

**Teste futuro:**

```bash
pytest supplies-api/tests/application/test_overview.py -q
pytest supplies-api/tests/application/test_partial_composition.py -q
```

## E5.S2 — Página Overview

Mostrar natureza temporal de cada KPI.

**Teste futuro:**

```bash
cd plugins/supplies && npm test -- Overview
```

---

# E6 — Solicitações de Compras C1

> **Concluída 2026-09-08** — gateway BFF + lista/detalhe/export + evidência C2 documental.

## E6.S1 — Gateway purchase-requests-api

Preservar CC fail-closed.

```bash
pytest supplies-api/tests/infrastructure/gateways/test_purchase_requests_gateway.py -q
pytest supplies-api/tests/interface/http/test_purchase_requests_bff.py -q
```

## E6.S2 — Lista/detalhe SC

```bash
cd plugins/supplies && npm test -- PurchaseRequests
```

## E6.S3 — Export

Capability separada enquanto risco/auditoria justificar.

```bash
pytest supplies-api/tests/security/test_purchase_request_export.py -q
```

## E6.S4 — Evidência para C2

Medir rows, jobs, cursors, subscriptions e estratégia de reconciliação.

Evidência: [evidence/e6-s4-c2-migration-evidence.md](./evidence/e6-s4-c2-migration-evidence.md).

---

# E7 — Operações: pedidos e entregas

> **Pré-condição de execução:** página em foco anterior fechada na fila (Início → Overview → SC) **e** autorização explícita do PO.  
> Não abrir E7.S* em paralelo com polish do Início.

## E7.S1 — Ler/fixar DTOs PO-OTD

Fechar KPI-PO-LATE e comparação BI atraso.

## E7.S2 — BFF PC/entregas

```bash
pytest supplies-api/tests/application/test_purchase_orders.py -q
```

## E7.S3 — UI PC/detalhe/atrasos

```bash
cd plugins/supplies && npm test -- PurchaseOrders Deliveries
```

---

# E8 — Estoque e ESTSEG

## E8.S1 — BFF inventory/stock balances

```bash
pytest supplies-api/tests/application/test_inventory.py -q
```

## E8.S2 — BFF safety-stock/consumption

```bash
pytest supplies-api/tests/application/test_safety_stock.py -q
```

## E8.S3 — UI estoque/ESTSEG/consumo

```bash
cd plugins/supplies && npm test -- Inventory SafetyStock
```

---

# E9 — Fornecedor 360

## E9.S1 — BFF Supplier 360

Composição api-delpi + PG; Qualidade somente quando autorizada.

```bash
pytest supplies-api/tests/application/test_supplier_360.py -q
```

## E9.S2 — Notas internas sem permission CRUD extra

`operations.access` + unit + resource scope + ownership/política de equipe.

```bash
pytest supplies-api/tests/security/test_supplier_notes_scope.py -q
```

## E9.S3 — UI Supplier 360

```bash
cd plugins/supplies && npm test -- Supplier360
```

---

# E10 — Produto / MP 360

## E10.S1 — BFF Product 360 + where-used

```bash
pytest supplies-api/tests/application/test_product_360.py -q
```

## E10.S2 — UI produto/preço/where-used

```bash
cd plugins/supplies && npm test -- Product360
```

---

# E11 — Negociações e indicadores

## E11.S1 — Savings/SI

Sem dual write de meta.

```bash
pytest supplies-api/tests/application/test_savings.py -q
```

## E11.S2 — UI analytics de negociação

```bash
cd plugins/supplies && npm test -- Negotiations
```

---

# E12 — Minhas Atividades

## E12.S1 — Migration `supply_tasks`

Usar idempotência/partial unique conforme DATA-MODEL.

```bash
pytest supplies-api/tests/infrastructure/test_supply_tasks_migration.py -q
```

## E12.S2 — API tasks

Sem `tasks.view/write`; authz pelo recurso.

```bash
pytest supplies-api/tests/security/test_task_resource_scope.py -q
```

## E12.S3 — UI worklist

```bash
cd plugins/supplies && npm test -- MyTasks
```

---

# E13 — Administração

## E13.S1 — Admin de scopes/mappings C1

`supplies.administration.manage` + unit quando aplicável.

```bash
pytest supplies-api/tests/security/test_administration.py -q
```

## E13.S2 — Settings tipados + audit

```bash
pytest supplies-api/tests/application/test_settings_catalog.py -q
```

---

# E14 — Help/onboarding completo

## E14.S1 — Help/onboarding completo

**Objetivo:** Manual, FAQ, glossário, tooltips e Quero→onde para todas as features entregues (`feature-help-sync`).

**Não fazer:** cutover; texto PT em Python/TS fora dos catálogos de Ajuda.

```bash
cd plugins/supplies && npm test -- help
```

---

# E15 — Paridade inicial C1

## E15.S1 — Paridade inicial C1

Comparar dashboard, SC, ESTSEG e demais jornadas implementadas quantitativamente (`HOMOLOGACAO-PARIDADE.md`).

**Não fazer:** cutover; C2.

---

# E16 — Purchase Requests C2

## E16.S1 — Expand para supplies-api

Preparar leitura do schema existente sem quebrar PR-api.

## E16.S2 — Migrar ownership/jobs

**Objetivo:** um único writer no schema `purchase_requests`.

**Fazer:** jobs de notificações/cursors passam à supplies-api Flask; desligar writers da `purchase-requests-api` (FastAPI) **antes** dos jobs Flask gravarem.

**Não fazer:** dual-write Flask + FastAPI no mesmo schema; C3 nesta subetapa.

## E16.S3 — Reconciliação

Comparar counts, subscriptions, cursors e eventos.

```bash
pytest supplies-api/tests/integration/test_purchase_requests_c2_reconciliation.py -q
```

## E16.S4 — Freeze PR-api

Somente bug/security enquanto coexistência final ocorre.

**Pronto quando:** GATE-C2.

---

# E17 — Paridade final pós-C2

## E17.S1 — Paridade final pós-C2

Reexecutar `HOMOLOGACAO-PARIDADE.md` com C2 ativo.

BIs externos precisam estar em estado final permitido (nenhum `LEGADO_A_VALIDAR` no GO).

**Pronto quando:** GATE-PARITY.

---

# E18 — Preparar cutover C3

## E18.S1 — Fechar redirects

Nenhum destino `BLOQUEADO` ou “ou rota”.

## E18.S2 — Telemetria/rollback

Definir owner, replacement, startDate, knownConsumers, telemetry, removalCriteria, rollback.

## E18.S3 — Smoke target novo

Target saudável antes de qualquer redirect.

---

# E19 — Cutover C3

## E19.S1 — Staging

Ativar redirects/ocultar launcher em staging, validar favoritos e query params.

## E19.S2 — Produção

Somente com GATE-CUTOVER.

## E19.S3 — Observação e remoção posterior

Não remover código no mesmo instante do primeiro redirect. Esperar critérios de remoção.

---

# E20 — Evoluções futuras atomizadas

Cada feature vira subetapa própria somente após aprovação. Não agrupar quatro produtos numa mesma subetapa. Não bloqueia E21.

## E20.S1 — supplier-scorecard

Somente após evidência de contrato e aceite.

## E20.S2 — supplier-concentration

Somente após evidência de contrato e aceite.

## E20.S3 — purchase-approvals

Somente se workflow comprovado.

## E20.S4 — imports

Somente se contrato comprovado.

## E20.S5 — slow-moving / obsolescence

Somente após evidência de contrato e aceite.

---

# E21 — Verify final

## E21.S1 — Pipeline real

Rebuild sequencial, smoke da matriz P0, authz, mobile/light/dark, partial failure e redirects.

## E21.S2 — Revisão objetivo original

Confirmar que experiência fragmentada foi substituída sem tomar ownership indevido e sem quebrar contratos.

---

## 5. Critérios de pronto por subetapa

`plan-construction.mdc` exige os 7 campos **neste arquivo**, em cada `#### E*.S*`, antes de executar a etapa — não só no PR:

```text
Objetivo
Fazer
Não fazer
Evidência
Teste com comando e arquivo exatos
Pronto quando
Commit sugerido
```

YAML §6 é 1:1 com esses headings (`eN-sM-slug`). Subetapa sem os 7 campos = incompleta para execução delegada: completar o bloco **aqui** no início da etapa, depois copiar o mesmo bloco no PR.

Não aceitar “teste: unit”, “pytest stock” ou equivalente vago.

---

## 6. Todos YAML

```yaml
todos:
  - id: e1-s1-core-bi-dump
    status: completed
    dependsOn: []
  - id: e1-s2-real-roles
    status: completed
    dependsOn: []
  - id: e1-s3-kpi-freeze
    status: completed
    dependsOn: []
  - id: e1-s4-manifest-rbac
    status: completed
    dependsOn: [e1-s1-core-bi-dump, e1-s2-real-roles]
  - id: e1-s5-architecture-freeze
    status: completed
    dependsOn: [e1-s3-kpi-freeze, e1-s4-manifest-rbac]

  - id: e2-s1-flask-scaffold
    status: completed
    dependsOn: [e1-s5-architecture-freeze]
  - id: e2-s2-core-first-authz
    status: completed
    dependsOn: [e2-s1-flask-scaffold]
  - id: e2-s3-errors-observability
    status: completed
    dependsOn: [e2-s2-core-first-authz]
  - id: e2-s4-sql-schema
    status: completed
    dependsOn: [e2-s1-flask-scaffold]
  - id: e2-s5-delpi-gateway
    status: completed
    dependsOn: [e2-s2-core-first-authz]
  - id: e2-s6-capabilities
    status: completed
    dependsOn: [e2-s2-core-first-authz]

  - id: e3-s1-mfe-scaffold
    status: pending
    dependsOn: [e2-s1-flask-scaffold]
  - id: e3-s2-bff-only
    status: pending
    dependsOn: [e3-s1-mfe-scaffold]
  - id: e3-s3-shell
    status: pending
    dependsOn: [e2-s6-capabilities, e3-s1-mfe-scaffold]
  - id: e3-s4-manifest-hml
    status: pending
    dependsOn: [e3-s3-shell]
  - id: e3-s5-rbac-coexistence
    status: pending
    dependsOn: [e3-s4-manifest-hml]

  - id: e4-s1-route-catalog
    status: pending
    dependsOn: [e3-s5-rbac-coexistence]
  - id: e4-s2-home-attention
    status: pending
    dependsOn: [e4-s1-route-catalog, e2-s5-delpi-gateway, e2-s6-capabilities]
  - id: e4-s3-help-skeleton
    status: pending
    dependsOn: [e4-s1-route-catalog]

  - id: e5-s1-overview-bff
    status: pending
    dependsOn: [e4-s2-home-attention, e1-s3-kpi-freeze, e2-s5-delpi-gateway]
  - id: e5-s2-overview-page
    status: pending
    dependsOn: [e5-s1-overview-bff, e3-s3-shell]

  - id: e6-s1-pr-gateway
    status: pending
    dependsOn: [e3-s5-rbac-coexistence, e2-s2-core-first-authz]
  - id: e6-s2-pr-list-detail
    status: pending
    dependsOn: [e6-s1-pr-gateway, e3-s2-bff-only]
  - id: e6-s3-pr-export
    status: pending
    dependsOn: [e6-s2-pr-list-detail]
  - id: e6-s4-c2-evidence
    status: pending
    dependsOn: [e6-s1-pr-gateway]

  - id: e7-s1-po-otd-dtos
    status: pending
    dependsOn: [e2-s5-delpi-gateway, e1-s3-kpi-freeze]
  - id: e7-s2-po-bff
    status: pending
    dependsOn: [e7-s1-po-otd-dtos]
  - id: e7-s3-po-ui
    status: pending
    dependsOn: [e7-s2-po-bff, e3-s2-bff-only]

  - id: e8-s1-inventory-bff
    status: pending
    dependsOn: [e2-s5-delpi-gateway]
  - id: e8-s2-safety-stock-bff
    status: pending
    dependsOn: [e2-s5-delpi-gateway]
  - id: e8-s3-inventory-ui
    status: pending
    dependsOn: [e8-s1-inventory-bff, e8-s2-safety-stock-bff, e3-s2-bff-only]

  - id: e9-s1-supplier-360-bff
    status: pending
    dependsOn: [e7-s2-po-bff, e2-s4-sql-schema]
  - id: e9-s2-supplier-notes
    status: pending
    dependsOn: [e9-s1-supplier-360-bff]
  - id: e9-s3-supplier-360-ui
    status: pending
    dependsOn: [e9-s2-supplier-notes, e3-s2-bff-only]

  - id: e10-s1-product-360-bff
    status: pending
    dependsOn: [e8-s1-inventory-bff]
  - id: e10-s2-product-360-ui
    status: pending
    dependsOn: [e10-s1-product-360-bff, e3-s2-bff-only]

  - id: e11-s1-savings-si
    status: pending
    dependsOn: [e5-s1-overview-bff]
  - id: e11-s2-negotiations-ui
    status: pending
    dependsOn: [e11-s1-savings-si, e3-s2-bff-only]

  - id: e12-s1-tasks-migration
    status: pending
    dependsOn: [e2-s4-sql-schema]
  - id: e12-s2-tasks-api
    status: pending
    dependsOn: [e12-s1-tasks-migration, e6-s2-pr-list-detail, e7-s2-po-bff]
  - id: e12-s3-tasks-ui
    status: pending
    dependsOn: [e12-s2-tasks-api, e3-s2-bff-only]

  - id: e13-s1-admin-scopes
    status: pending
    dependsOn: [e6-s1-pr-gateway]
  - id: e13-s2-settings-audit
    status: pending
    dependsOn: [e13-s1-admin-scopes, e2-s4-sql-schema]

  - id: e14-s1-help-complete
    status: pending
    dependsOn:
      - e4-s3-help-skeleton
      - e9-s3-supplier-360-ui
      - e10-s2-product-360-ui
      - e11-s2-negotiations-ui
      - e12-s3-tasks-ui
      - e13-s2-settings-audit

  - id: e15-s1-initial-parity
    status: pending
    dependsOn:
      - e5-s2-overview-page
      - e6-s3-pr-export
      - e8-s3-inventory-ui
      - e14-s1-help-complete

  - id: e16-s1-schema-expand
    status: pending
    dependsOn: [e15-s1-initial-parity, e6-s4-c2-evidence]
  - id: e16-s2-ownership-jobs
    status: pending
    dependsOn: [e16-s1-schema-expand]
  - id: e16-s3-reconciliation
    status: pending
    dependsOn: [e16-s2-ownership-jobs]
  - id: e16-s4-freeze-pr-api
    status: pending
    dependsOn: [e16-s3-reconciliation]

  - id: e17-s1-final-parity
    status: pending
    dependsOn: [e16-s4-freeze-pr-api]

  - id: e18-s1-close-redirects
    status: pending
    dependsOn: [e17-s1-final-parity]
  - id: e18-s2-telemetry-rollback
    status: pending
    dependsOn: [e18-s1-close-redirects]
  - id: e18-s3-target-smoke
    status: pending
    dependsOn: [e18-s2-telemetry-rollback]

  - id: e19-s1-staging
    status: pending
    dependsOn: [e18-s3-target-smoke]
  - id: e19-s2-production
    status: pending
    dependsOn: [e19-s1-staging]
  - id: e19-s3-observe-remove
    status: pending
    dependsOn: [e19-s2-production]

  - id: e20-s1-supplier-scorecard
    status: pending
    dependsOn: [e17-s1-final-parity]
  - id: e20-s2-supplier-concentration
    status: pending
    dependsOn: [e17-s1-final-parity]
  - id: e20-s3-purchase-approvals
    status: pending
    dependsOn: [e17-s1-final-parity]
  - id: e20-s4-imports
    status: pending
    dependsOn: [e17-s1-final-parity]
  - id: e20-s5-slow-moving
    status: pending
    dependsOn: [e17-s1-final-parity]

  - id: e21-s1-pipeline-real
    status: pending
    dependsOn: [e19-s2-production]
  - id: e21-s2-original-objective
    status: pending
    dependsOn: [e21-s1-pipeline-real]
```

### Consistência causal obrigatória

```text
ADR order = roadmap order = dependsOn order
```

Em especial:

```text
C1 → C2 → PARIDADE FINAL → C3
```

Nunca C3 antes de C2.

E20.S* não bloqueia E21 (evoluções futuras após paridade final).

---

## 7. Fora do escopo sem novo ADR

- escrita TOTVS;
- absorver Financeiro/Qualidade/PCP/Chat/TV;
- IA preditiva;
- e-mail automático a fornecedor;
- remover legado sem telemetria/paridade;
- criar permission por CRUD sem justificativa ADR-007.
