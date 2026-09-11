# IMPLEMENTATION-PLAN — Portal Suprimentos

> **Status (2026-09-10):** plano executável revisado segundo `evidence-driven-execution.mdc`, `plan-construction.mdc` e `plan-execution.mdc`.  
> **Entregue:** E1–E5 + E6.S1–S4.  
> **Em foco:** E6.S5 — revalidar e fechar o GATE-FEATURE do WF-04 Solicitações de Compras.  
> **Próxima página candidata:** E7 WF-05 Pedidos de Compra, bloqueada até E6.S5 PASS + autorização explícita do Product Owner.  
> **Modo:** uma página user-facing por vez; etapas futuras abaixo são fila/grafo, não autorização de execução.

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
| RQ-06 | SC C1 funcional + DoD da página | PARCIAL — E6.S1–S4 feitos; E6.S5 aberto |
| RQ-07 | Pedidos de Compra | BLOQUEADO pela fila — E7 |
| RQ-08 | Detalhe do Pedido | BLOQUEADO pela fila — E8 |
| RQ-09 | Entregas/Atrasos | BLOQUEADO pela fila — E9 |
| RQ-10 | Estoque | BLOQUEADO pela fila — E10 |
| RQ-11 | ESTSEG | BLOQUEADO pela fila — E11 |
| RQ-12 | Análise de Consumo | BLOQUEADO pela fila — E12 |
| RQ-13 | Fornecedores / Supplier 360 / OTD | BLOQUEADO pela fila; P-11 limita Qualidade |
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
| capabilities mínimas | ADR-007 |
| unit `supplies.unit.filial-{TOTVS}` | ADR-006 |
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

E4.S1–S4 concluídas: catálogo, `/home/attention`, Ajuda inicial, `/users/:userId`, preferências e avatar Core.

# E5 — Overview + OTD analytics — COMPLETED

Overview/OTD fechados com filtros/URL, 7 KPIs, metas SI, charts/gauges e Ajuda.

---

# E6 — Solicitações de Compras C1 — EM FOCO

## E6.S1 — Gateway PR-api — COMPLETED

**Entregue:** BFF C1 preservando CC fail-closed e unit scope.  
**Teste de referência:** `pytest supplies-api/tests/infrastructure/gateways/test_purchase_requests_gateway.py -q` + BFF route tests.

## E6.S2 — Lista/detalhe SC — COMPLETED FUNCIONAL

**Entregue:** lista e detalhe via MFE BFF-only.  
**Teste de referência:** `cd plugins/supplies && npm test -- PurchaseRequests`.

## E6.S3 — Export — COMPLETED

**Entregue:** export condicionado a access + export + unit + CC/view-all.

## E6.S4 — Evidência C2 — COMPLETED DOCUMENTAL

**Entregue:** inventário de schema/writers/jobs/cursors/subscriptions e estratégia single-writer.  
**Evidência:** [evidence/e6-s4-c2-migration-evidence.md](./evidence/e6-s4-c2-migration-evidence.md).  
**Residual:** medir volumes HML/prod antes de E25.

## E6.S5 — Revalidar GATE-FEATURE WF-04 — PENDING / NEXT

**Objetivo:** fechar a página atual contra o DoD vigente sem misturar E7.

**Requisitos cobertos:** RQ-04, RQ-06, RQ-19.

**Fazer:**
- inspecionar `plugins/supplies` e `supplies-api` atuais da jornada SC;
- criar baseline da UI/estados e inventário de componentes;
- confirmar kit-first (`PagePath`, `PageHero`, `SectionCard`, filtros/tabela/estados do `plugin-ui` quando aplicáveis);
- validar loading/empty/partial/error/403/404;
- validar filtros, query/URL, F5 e detalhe;
- validar access/export/view-all/unit/CC fail-closed;
- sincronizar Help e wireframe da página;
- executar testes positive + sibling + negative e smoke federado quando ambiente permitir.

**Não fazer:** implementar Pedidos, Entregas, C2 ou cutover; criar componente duplicado do kit; enfraquecer CC/unit scope.

**Evidência de ownership:** ADR-002, API-ROUTES e código C1 atual.

**Dependências:** E6.S1–S4 completas.

**Teste:** descobrir e executar os comandos reais atuais de `plugins/supplies` e `supplies-api`; no mínimo suíte PurchaseRequests + BFF/security relacionada + build do MFE. Não declarar smoke PASS se o ambiente não permitir.

**Pronto quando:** GATE-FEATURE WF-04 = PASS e README/WIREFRAMES/API-ROUTES refletem o estado final.

**Commit sugerido:** `fix(supplies): fechar DoD de solicitações de compras`

---

# Fila futura — uma página por vez

As etapas abaixo estão **BLOCKED_BY_QUEUE**. Antes de executar qualquer uma, substituir o resumo por receita completa conforme `plan-construction.mdc`, revalidando código, API e decisões pendentes.

## E7 — WF-05 Pedidos de Compra

Pré-condição: E6.S5 PASS + autorização explícita PO. Ler/fixar DTOs PO necessários à **lista**, criar BFF da lista, UI/estados/Help/testes e fechar GATE-FEATURE. Não implementar detalhe nem Entregas na mesma etapa.

## E8 — WF-06 Detalhe do Pedido

Pré-condição: E7 PASS. Contrato de detalhe + resource scope + itens/prometida/recebimentos/SC origem + follow-up apenas se recurso/capability permitirem. Fechar GATE-FEATURE próprio.

## E9 — WF-07 Entregas/Atrasos

Pré-condição: E8 PASS. Comparar regra do BI Atraso quando evidência produtiva existir; isso bloqueia **depreciação/paridade**, não necessariamente a construção da página nativa se o contrato PO-OTD estiver confirmado. Fechar GATE-FEATURE.

## E10 — WF-15 Controle de Estoques

Página própria. Não misturar ESTSEG. Confirmar política de capability da rota de stock-value antes de executar.

## E11 — WF-16 Estoque de Segurança

Página própria, read-only neste roadmap.

## E12 — WF-17 Análise de Consumo

Página própria ou satélite somente se a promoção provar que é extensão inseparável do WF-16; não assumir herança sem evidência.

## E13 — WF-09 Fornecedores

Busca/lista. Se busca SA2/contrato fornecedor não estiver comprovada, manter `BLOCKED_WITH_EVIDENCE`.

## E14 — WF-10 Fornecedor 360

Composição TOTVS + PG. **Qualidade fica fora do P0 enquanto P-11 não estiver resolvido**; não usar “quando autorizada” como receita ambígua. Notas seguem operations + unit + resource + ownership/política de equipe, sem permission CRUD preventiva.

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
    status: pending
    dependsOn: [e6-s2-pr-list-detail, e6-s3-pr-export, e6-s4-c2-evidence]

  - id: e7-purchase-orders-list
    status: blocked
    dependsOn: [e6-s5-wf04-feature-gate]
  - id: e8-purchase-order-detail
    status: blocked
    dependsOn: [e7-purchase-orders-list]
  - id: e9-deliveries
    status: blocked
    dependsOn: [e8-purchase-order-detail]
  - id: e10-inventory
    status: blocked
    dependsOn: [e9-deliveries]
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
