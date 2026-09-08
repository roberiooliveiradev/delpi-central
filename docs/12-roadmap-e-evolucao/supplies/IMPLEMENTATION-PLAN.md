# IMPLEMENTATION-PLAN — Portal Suprimentos

> **Status:** plano executável revisado · set/2026 · **não implementar sem autorização explícita**  
> **Readiness atual:** BLOQUEADO até E1 + gates P0  
> Referências: ADR-001..ADR-007, `plan-construction.mdc`, `evidence-driven-execution.mdc`.

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

---

## 3. Gates

### GATE-AUTHZ

Passa somente quando:

- JWT validado;
- effective permissions vêm do Core;
- nenhuma autorização nova usa `claims.permissions`/`claims.is_superadmin` como fonte final;
- Core indisponível = fail-closed para decisão nova;
- testes positivo, negativo e filial cruzada verdes.

### GATE-E1

- dump dos BIs externos concluído;
- papéis SC/ES mapeados;
- KPIs P0 homologados ou explicitamente bloqueados.

### GATE-ARCH

- ADRs 001–007 revisados;
- `MANIFEST-DRAFT.md` validado contra runtime real;
- catálogo de permissions mínimo aprovado.

### GATE-RBAC

- permissions canônicas provisionáveis;
- migração de papéis definida;
- `/me/apps` e `/me/routes` cobertos por testes/smoke.

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

**Pronto quando:** GATE-E1 + GATE-ARCH.

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

**Fazer:** validar JWT; resolver effective permissions no Core; fail-closed; request context.

**Não fazer:** confiar em permissions/is_superadmin do JWT.

**Testes futuros:**

```bash
pytest supplies-api/tests/security/test_effective_permissions.py -q
pytest supplies-api/tests/security/test_unit_authorization.py -q
```

**Pronto quando:** GATE-AUTHZ.

## E2.S3 — Envelope, erros e observabilidade

**Teste futuro:**

```bash
pytest supplies-api/tests/interface/http/test_error_contract.py -q
pytest supplies-api/tests/observability/test_request_context.py -q
```

## E2.S4 — Alembic schema `supplies`

Criar somente preferences P0. Nada de clone TOTVS.

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
/core-api/me/apps
/core-api/me/routes
```

Casos: comprador SC, analista, usuário sem supplies, superadmin e comprador ES se existir.

**Pronto quando:** GATE-RBAC.

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

## E6.S1 — Gateway purchase-requests-api

Preservar CC fail-closed.

```bash
pytest supplies-api/tests/infrastructure/gateways/test_purchase_requests_gateway.py -q
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

---

# E7 — Operações: pedidos e entregas

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

Manual, FAQ, glossário, tooltips e Quero→onde para todas as features entregues.

```bash
cd plugins/supplies && npm test -- help
```

---

# E15 — Paridade inicial C1

Comparar dashboard, SC, ESTSEG e demais jornadas implementadas quantitativamente.

**Não fazer:** cutover.

---

# E16 — Purchase Requests C2

## E16.S1 — Expand para supplies-api

Preparar leitura do schema existente sem quebrar PR-api.

## E16.S2 — Migrar ownership/jobs

Jobs de notificações/cursors passam à supplies-api de forma controlada.

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

Reexecutar `HOMOLOGACAO-PARIDADE.md` com C2 ativo.

BIs externos precisam estar em estado final permitido.

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

Cada feature vira subetapa própria somente após aprovação:

- E20.S1 supplier-scorecard;
- E20.S2 supplier-concentration;
- E20.S3 purchase-approvals (se workflow comprovado);
- E20.S4 imports (se contrato comprovado);
- E20.S5 slow-moving/obsolescence.

Não agrupar quatro produtos numa mesma subetapa.

---

# E21 — Verify final

## E21.S1 — Pipeline real

Rebuild sequencial, smoke da matriz P0, authz, mobile/light/dark, partial failure e redirects.

## E21.S2 — Revisão objetivo original

Confirmar que experiência fragmentada foi substituída sem tomar ownership indevido e sem quebrar contratos.

---

## 5. Critérios de pronto por subetapa

Toda E*.S* de implementação deve conter no PR/tarefa:

```text
Objetivo
Fazer
Não fazer
Evidência
Teste com comando e arquivo exatos
Pronto quando
Commit sugerido
DependsOn
```

Não aceitar “teste: unit”, “pytest stock” ou equivalente vago.

---

## 6. Todos YAML

```yaml
todos:
  - id: e1-s1-core-bi-dump
    status: pending
    dependsOn: []
  - id: e1-s2-real-roles
    status: pending
    dependsOn: []
  - id: e1-s3-kpi-freeze
    status: pending
    dependsOn: []
  - id: e1-s4-manifest-rbac
    status: pending
    dependsOn: [e1-s1-core-bi-dump, e1-s2-real-roles]
  - id: e1-s5-architecture-freeze
    status: pending
    dependsOn: [e1-s3-kpi-freeze, e1-s4-manifest-rbac]

  - id: e2-s1-flask-scaffold
    status: pending
    dependsOn: [e1-s5-architecture-freeze]
  - id: e2-s2-core-first-authz
    status: pending
    dependsOn: [e2-s1-flask-scaffold]
  - id: e2-s3-errors-observability
    status: pending
    dependsOn: [e2-s2-core-first-authz]
  - id: e2-s4-alembic
    status: pending
    dependsOn: [e2-s1-flask-scaffold]
  - id: e2-s5-delpi-gateway
    status: pending
    dependsOn: [e2-s2-core-first-authz]
  - id: e2-s6-capabilities
    status: pending
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

  - id: e4-home-help
    status: pending
    dependsOn: [e3-s5-rbac-coexistence, e2-s5-delpi-gateway]
  - id: e5-overview
    status: pending
    dependsOn: [e4-home-help, e1-s3-kpi-freeze]
  - id: e6-purchase-requests-c1
    status: pending
    dependsOn: [e3-s5-rbac-coexistence]
  - id: e7-purchase-orders
    status: pending
    dependsOn: [e2-s5-delpi-gateway]
  - id: e8-inventory-safety-stock
    status: pending
    dependsOn: [e2-s5-delpi-gateway]
  - id: e9-supplier-360
    status: pending
    dependsOn: [e7-purchase-orders, e2-s4-alembic]
  - id: e10-product-360
    status: pending
    dependsOn: [e8-inventory-safety-stock]
  - id: e11-negotiations
    status: pending
    dependsOn: [e5-overview]
  - id: e12-my-tasks
    status: pending
    dependsOn: [e2-s4-alembic, e6-purchase-requests-c1, e7-purchase-orders]
  - id: e13-administration
    status: pending
    dependsOn: [e6-purchase-requests-c1]
  - id: e14-help-complete
    status: pending
    dependsOn: [e9-supplier-360, e10-product-360, e12-my-tasks, e13-administration]
  - id: e15-initial-parity
    status: pending
    dependsOn: [e5-overview, e6-purchase-requests-c1, e8-inventory-safety-stock, e14-help-complete]

  - id: e16-purchase-requests-c2
    status: pending
    dependsOn: [e15-initial-parity, e6-purchase-requests-c1, e13-administration]
  - id: e17-final-parity
    status: pending
    dependsOn: [e16-purchase-requests-c2]
  - id: e18-cutover-prep
    status: pending
    dependsOn: [e17-final-parity]
  - id: e19-cutover-c3
    status: pending
    dependsOn: [e18-cutover-prep]
  - id: e20-future-features
    status: pending
    dependsOn: [e17-final-parity]
  - id: e21-final-verify
    status: pending
    dependsOn: [e19-cutover-c3]
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

---

## 7. Fora do escopo sem novo ADR

- escrita TOTVS;
- absorver Financeiro/Qualidade/PCP/Chat/TV;
- IA preditiva;
- e-mail automático a fornecedor;
- remover legado sem telemetria/paridade;
- criar permission por CRUD sem justificativa ADR-007.
