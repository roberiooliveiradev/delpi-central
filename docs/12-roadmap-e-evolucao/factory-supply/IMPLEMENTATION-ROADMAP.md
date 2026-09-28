# Factory Supply — Implementation Roadmap (Documentation 5/5)

> **Status:** SPECIFICATION PROGRAM COMPLETE — plano mestre de implementação. **Não** é evidência de runtime, release ou produto entregue.
> **Escopo:** consolida Docs 1–4 em plano executável por incrementos, com requirement ledger, gates, fases, testes e Definition of Done.
> **Limite:** DOCUMENTATION-ONLY. Nenhuma tarefa deste roadmap foi executada aqui.

**Classificadores:** `PROVEN` (evidência auditável no working tree) · `TARGET` (decisão congelada nas specs) · `PLANNED` (plano consistente) · `TO_INVENTORY` (lacuna de evidência).
**Estados de execução:** `PASS` · `FAIL` · `PENDING` · `INCONCLUSIVE` · `TEST_NOT_RUN` · `STALE_EVIDENCE`.

---

## 1. Purpose and status

Plano mestre que permite a sessões futuras de implementação executar Factory Supply em incrementos pequenos e revisáveis sem redescobrir decisões de produto/arquitetura. Toda tarefa referencia requirements (§5), depende de gates explícitos (§8–9) e retorna o relatório-padrão (§36).

**Nada aqui autoriza implementação, commit ou release.**

## 2. Accepted specification baseline

| Documento | Arquivo | Conteúdo aceito |
|---|---|---|
| 1/5 | `README.md` | produto, arquitetura, topologia, limites |
| 2/5 | `DOMAIN-MODEL.md` | `SupplyMission`+`SupplyMissionItem[]`, dimensões, idempotência, evidência ERP |
| 3/5 | `UX-SPEC.md` | superfícies, Kanban mission-grain, backend-stage, plugin-ui, a11y |
| 4/5 | `TECHNICAL-CONTRACTS.md` | `factory-supply-api`, schema `factory_supply`, envelope, idempotência+fingerprint, `expected_version`, evidência ERP, RBAC user/service, matrizes, coexistence |

Invariantes (não reabrir): `factory-supply-api` BFF dedicado · MFE nunca chama api-delpi · api-delpi = única fronteira TOTVS (READ-ONLY) · sem writes TOTVS · sem dependência em `production-control-api` · sem event bus/outbox agora · `NEW_API_DELPI_ROUTES_REQUIRED = NO`.

## 3. Current evidence state

| Item | Estado |
|---|---|
| Convenções de bounded API (envelope, `ok/fail`, `ApplicationError`, `Idempotency-Key`, `idempotency_keys`, migrations `V00N`, mount `/apps/*-api`, schema próprio, `.{view|manage}`+`.view.filial-*`) | `PROVEN` |
| Caminhos/operationIds api-delpi consumidos (gateway PCP) | `PROVEN` |
| Campos internos das respostas api-delpi necessárias (internal-movements, operation-materials) | `PROVEN` — FS-C0.T1 (§8.1 T1/T2 `DONE`) |
| ~~Escopo de **escrita** por filial~~ — RESOLVIDO FS-C0.T3: `.view.filial-*` é escopo de filial e gateia writes (`assert_can_view_branch` em mutações Line Feeder, `PROVEN`); modelo de usuário FROZEN = 3 permissões (TC §40-A) | `PROVEN` (mecanismo) |
| Cadeia de registro de permissões (manifesto→`sync_module`→roles→`/me` resolver→middleware `load_user_rbac`→`has_permission`; default DENY; claims fallback = `permissions[]`) | `PROVEN` — FS-C0.T4 |
| Decisões de produto: reconciliação pedido×sinal, regra de devolução, prioridade | `TO_INVENTORY` (product gates) |
| ~~Identidade de serviço~~ — RESOLVIDO FS-C0.T5: jobs in-process + `API_DELPI_INTERNAL_SERVICE_TOKEN`+`X-Delpi-Caller-App`; sem service account/permissões Core (TC §40-B) | `PROVEN` (mecanismo) |
| ~~Algoritmo de `request_fingerprint`~~ | `PROVEN` contrato — canonical-JSON+SHA-256 (FS-C0.T6) |

## 4. Unresolved blockers

Consolidado de `TECHNICAL-CONTRACTS.md` §43–44 — todos tratados como gates C0 ou tarefas de inventário, nunca resolvidos por inferência:

1. ~~Campos de `get_product_internal_movements`~~ — RESOLVIDO FS-C0.T1 (`NO_STABLE_MOVEMENT_ID_EXPOSED`; fingerprint composto congelado em TC §25)
2. ~~Campos de `list_production_order_operation_materials(_batch)`~~ — RESOLVIDO FS-C0.T1 (SD4: `original_qty`=empenho original, `open_qty`=saldo do empenho, `consumed_qty`, `commitment_count`; sem cap de batch → FS auto-chunk)
3. ~~Escopo de escrita por filial~~ — RESOLVIDO FS-C0.T3 (`.view.filial-*` = escopo filial leitura+escrita, `PROVEN`)
4. ~~Registro das 3 permissões usuário~~ — RESOLVIDO FS-C0.T4 (contrato de manifesto, `sync_module` declarativo, atribuição `rbac.manage`+`roles.manage`, resolver `/me`, default DENY — TC §40-A; resta apenas execução na implantação)
5. ~~Identidade de serviço~~ — RESOLVIDO FS-C0.T5 (in-process jobs + `API_DELPI_INTERNAL_SERVICE_TOKEN`; sem service account — TC §40-B)
6. ~~Algoritmo `request_fingerprint`~~ — RESOLVIDO FS-C0.T6 (canonical-JSON tipado + SHA-256; escopo `(key,route,actor)`; single-tx; falha não consome key — TC §10/§39)
7. ~~Conversão de unidades~~ — RESOLVIDO FS-C0.T7: `AUTHORITATIVE_TOTVS_UNIT` (`B1_UM` em todos os contratos — §51); `UNIT_CONVERSION_*=NOT_REQUIRED`; divergência de unidade → `UNIT_DIVERGENCE`/falha fechada
8. Reconciliação pedido operador×sinal planejado — **PRODUTO** (gate Product Master)
9. Regra de quantidade de devolução — **PRODUTO** (gate; ver escopo §21)
10. Política de prioridade — **PRODUTO** (gate; default factual ordering)
11. Header de correlação no gateway portal→api-delpi — **técnico**
12. Retenção de `idempotency_keys`/`supply_events`/`integration_outbox` — **técnico**
13. `SYNC_CADENCE` benchmark — **técnico** (carga/fan-out api-delpi validada antes de fixar; TC §33)
14. Categorias de notificação FS no catálogo canônico Core (`notification-catalog-preferences`) — **técnico** (registro junto ao manifesto C7.T1)

## 5. Requirement ledger

Status: `ACCEPTED` (congelado na spec) / `GATED` (depende de C0/produto). Owner: `FS` = factory-supply-api, `MFE` = plugin, `DELPI` = api-delpi, `CORE` = plataforma.

### FS-PR — Product

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-PR-01 | Rastreabilidade operacional completa need→prepare→collect→deliver→return por ator/tempo/filial | Doc1 §produto | FS | C2+ | ACCEPTED | Cenário A | FS-DM-01 |
| FS-PR-02 | Necessidade planejada e pedido humano são fatos distintos, nunca reescritos | Doc1 §invariante | FS | C4 | ACCEPTED | teste de reconciliação | FS-DM-04, C0.P1 |
| FS-PR-03 | Coexistência com Line Feeder sem dual-write/migração silenciosa | Doc4 §30 | FS | sempre | ACCEPTED | gate cutover §35 | — |
| FS-PR-04 | Cockpit integra por contrato semântico, sem internals/DB | Doc4 §28 | FS | C10 | ACCEPTED | contrato+teste | C0.P1 |
| FS-PR-05 | Devolução sem quantidade inventada; estado "não estabelecida" suportado | Doc3/4 | FS | C9 | GATED→C0.P2 | Cenário G | C0.P2 |
| FS-PR-06 | Prioridade factual (`due_at`,`overdue`,`time_to_need`) até política existir | Doc4 §49 | FS | C2+ | ACCEPTED | projeção sem score | C0.P3 |
| FS-PR-07 | Métricas operacionais ≠ scoring de trabalhador | Doc1, Doc4 §32 | FS | C8 | ACCEPTED | revisão métricas | — |

### FS-AR — Architecture

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-AR-01 | Backend dedicado `factory-supply-api`/`factory_supply_app` mount `/apps/factory-supply-api` | Doc4 §4–5 | FS | C1 | ACCEPTED | serviço responde /health | — |
| FS-AR-02 | MFE consome apenas `/apps/factory-supply-api/v1/**` | Doc4 §7 | MFE | C7 | ACCEPTED | residual grep §19 | FS-AR-01 |
| FS-AR-03 | api-delpi = única fronteira TOTVS; somente contratos tipados; sem SQL genérico | Doc4 §27,47 | FS | C3 | ACCEPTED | gateway typed tests | — |
| FS-AR-04 | Zero escrita TOTVS — nenhuma rota/capacidade de write ERP | Doc4 §36 | FS | sempre | ACCEPTED | residual grep + review | — |
| FS-AR-05 | Sem dependência runtime em `production-control-api` | Doc4 §30 | FS | sempre | ACCEPTED | import/grep gate | — |
| FS-AR-06 | Camadas domain/application/infrastructure/interface/composition; domain sem framework | Doc4 §46 | FS | C1–C2 | ACCEPTED | import-linter/arq tests | FS-AR-01 |
| FS-AR-07 | Sem event bus/outbox (gatilhos documentados para reabrir) | Doc4 §33 | FS | sempre | ACCEPTED | review | — |

### FS-DM — Domain

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-DM-01 | Agregado `SupplyMission`+`SupplyMissionItem[]` = fronteira de consistência | Doc2 | FS | C2 | ACCEPTED | unit tests | — |
| FS-DM-02 | Grão missão = destino×janela×contexto×atribuição; grão item = material×unidade×dimensões | Doc2 | FS | C2 | ACCEPTED | unit tests | FS-DM-01 |
| FS-DM-03 | Dimensões de item: preparation/collection/delivery/erp-evidence/return com parciais | Doc2 | FS | C2 | ACCEPTED | unit tests | FS-DM-01 |
| FS-DM-04 | `DemandSignal` distinguível por origem; dedup por `signal_key`; replay-safe sync | Doc2/4 §19 | FS | C4 | ACCEPTED | sync tests | FS-DM-01 |
| FS-DM-05 | `overall_stage` derivado no backend, determinístico, fechado (5 estágios) | Doc4 §16 | FS | C5 | ACCEPTED | projeção testada | FS-DM-03 |
| FS-DM-06 | `available_actions` semânticas por estado — advisory, não AuthZ | Doc4 §48 | FS | C5 | ACCEPTED | unit tests | FS-DM-05 |
| FS-DM-07 | Replanejamento/cancelamento preservam história (sem reescrita) | Doc2 | FS | C6 | ACCEPTED | Cenário C | FS-DM-01 |
| FS-DM-08 | `version` monotônica por agregado; `expected_version` em toda transição | Doc4 §11 | FS | C2 | ACCEPTED | conflict tests | FS-DM-01 |
| FS-DM-09 | Quantidades NUMERIC+unit; null ≠ 0; sem soma entre unidades incompatíveis | Doc4 §51 | FS | C2 | ACCEPTED | unit tests | C0.T7 |
| FS-DM-10 | Handoff = fato separado de custódia (collection/delivery/return) | Doc4 §20 | FS | C6 | ACCEPTED | unit tests | FS-DM-03 |

### FS-UX — UX/MFE

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-UX-01 | IA: Visão geral / Abastecimento (Kanban·Necessidades·Minha coleta·Próximos períodos) / Almoxarifado / Devoluções / Histórico | Doc3 | MFE | C7 | ACCEPTED | pages renderizadas | FS-UX-* restantes |
| FS-UX-02 | Kanban cards = missão; estágio = `overall_stage` backend; DnD desabilitado | Doc3/4 | MFE | C7 | ACCEPTED | KanbanBoard read-only | FS-DM-05 |
| FS-UX-03 | Minha coleta = fluxo de execução focado (missão→item→local→qty→confirm) | Doc3 | MFE | C7 | ACCEPTED | flow test | FS-DM-03 |
| FS-UX-04 | Almoxarifado/Devoluções = híbridos table/board; quantidades item-grão | Doc3 | MFE | C7 | ACCEPTED | toggle test | FS-DM-03 |
| FS-UX-05 | Detalhe de missão = DrawerShell + deep-link `?mission=` | Doc3 | MFE | C7 | ACCEPTED | drawer test | — |
| FS-UX-06 | Mobile: stage selector + cards verticais; breakpoints canônicos | Doc3 | MFE | C7 | ACCEPTED | responsive test | FS-UX-02 |
| FS-UX-07 | plugin-ui first; zero CSS duplicado de kit; escopo de CSS no root | Doc3 | MFE | C7 | ACCEPTED | CSS grep + review | — |
| FS-UX-08 | A11y: teclado, foco, labels, sem cor-só, ≥44px, reduced-motion, drawer focus | Doc3/§37 | MFE | C7 | ACCEPTED | a11y checklist | — |
| FS-UX-09 | Separação visual fato operacional vs evidência ERP | Doc3 | MFE | C8 | ACCEPTED | labels distintas | FS-DM-03 |
| FS-UX-10 | Frontend nunca deriva estado/permissão; consome `overall_stage`,`available_actions`,`can_*` | Doc3/4 | MFE | C7 | ACCEPTED | grep + tests | FS-DM-05,06 |
| FS-UX-11 | Realtime: WS→toast/outcome+estado; área de exceções persistente p/ divergências (nunca toast-only); presença = socket FS, não Portal | Doc3 §28, Doc4 §33 | MFE | C7.T8 | ACCEPTED | WS+UX tests | C4.T1b |

### FS-API — Contracts

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-API-01 | Envelope `{success,message,data}`; erros `data:{code,field?}` estáveis | Doc4 §8–9 | FS | C1 | ACCEPTED | contract tests | FS-AR-01 |
| FS-API-02 | Rotas query §15 (11) e comandos §14 (13) com operationIds TARGET | Doc4 §38 | FS | C4–C9 | ACCEPTED | contract tests | FS-API-01 |
| FS-API-03 | `Idempotency-Key` obrigatório em comandos; `422 idempotency_required` | Doc4 §10 | FS | C2 | ACCEPTED | adversarial §29 | FS-API-01 |
| FS-API-04 | `request_fingerprint` persistido; mesmo escopo+fingerprint → replay; divergente → `409 idempotency_conflict` — **RESOLVIDO FS-C0.T6** (canonical-JSON tipado+SHA-256; single-tx claim; falha não consome key) | Doc4 §10 | FS | C2 | ACCEPTED | §18 tests | FS-API-03 |
| FS-API-05 | `expected_version` em comandos; `409 version_conflict` + `current_version`; sem last-write-wins | Doc4 §11 | FS | C2 | ACCEPTED | §19 tests | FS-DM-08 |
| FS-API-06 | Paginação: page/page_size (≤200) listas; cursor history; sem endpoint ilimitado | Doc4 §50 | FS | C4+ | ACCEPTED | contract tests | FS-API-01 |
| FS-API-07 | `branch` query/body obrigatório, validado server-side | Doc4 §12,20 | FS | C2 | ACCEPTED | branch tests | C0.T3 |
| FS-API-08 | 401/403 downstream → `downstream_access_denied` — nunca evidência ERP | Doc4 §9,26 | FS | C8 | ACCEPTED | §28 tests | — |
| FS-API-09 | Resposta de comando expõe estado+versão+`overall_stage` resultante | Doc4 §14 | FS | C5+ | ACCEPTED | postcondition tests | FS-DM-05 |
| FS-API-10 | Projeção Kanban §16 completa (stage, contagens, actions, version, urgency factual) | Doc4 §16 | FS | C5 | ACCEPTED | projection tests | FS-DM-05 |

### FS-DATA — Persistence

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-DATA-01 | Schema `factory_supply`; PKs UUID; TIMESTAMPTZ; branch em fatos | Doc4 §22 | FS | C2 | ACCEPTED | migration tests | C0.T* |
| FS-DATA-02 | 8 tabelas §39 (missions, items, signals, links, handoffs, erp_observations, supply_events, idempotency_keys) | Doc4 §39 | FS | C2 | ACCEPTED | DDL+tests | FS-DATA-01 |
| FS-DATA-03 | UNIQUE dedup: `signal_key` ativo; `(mission_item_id,evidence_fingerprint)`; `(key,route,actor)` | Doc4 §23 | FS | C2 | ACCEPTED | constraint tests | FS-DATA-02 |
| FS-DATA-04 | `supply_events` append-only na mesma transação do agregado | Doc4 §31 | FS | C2 | ACCEPTED | atomicity test | FS-DATA-02 |
| FS-DATA-05 | Snapshots `_at_decision` ≠ verdade corrente; sem shadow inventory | Doc4 §24 | FS | C2 | ACCEPTED | review+tests | — |
| FS-DATA-06 | Migrations `V00N` append-only, imutáveis, checksum, sem reset prod | regras canônicas | FS | C2 | ACCEPTED | migration tests §32 | — |
| FS-DATA-07 | Version INT em missions; compare-update atômico | Doc4 §22–23 | FS | C2 | ACCEPTED | §19 tests | FS-DATA-02 |
| FS-DATA-08 | `request_fingerprint`+`response_status` em idempotency_keys — **RESOLVIDO FS-C0.T6** (`UNIQUE(key,route,actor_user_id)`+fingerprint dentro do escopo) | Doc4 §10,39 | FS | C2 | ACCEPTED | constraint test | FS-DATA-02 |

### FS-SEC — Security/RBAC

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-SEC-01 | 3 permissões USER §40-A FROZEN (Product Master, FS-C0.T3): `factory-supply.access` + `view.filial-01` + `view.filial-02`; sem permissão por comando/superfície; registro/execução em C7.T1 | Doc4 §40-A | CORE+FS | C7.T1 | ACCEPTED | §35 tests | C0.T3,T4 (DONE) |
| FS-SEC-02 | 2 jobs internos §40-B (`demand_signal_sync`, `erp_evidence_reconcile`) — in-process, actor `system/factory-supply-api`, service token api-delpi; **não** são permissões Core | Doc4 §40-B | FS | C4,C8 | ACCEPTED | §35 tests | C0.T5 (DONE) |
| FS-SEC-03 | JWT identifica; permissão resolve server-side a cada request; UI visível ≠ autorizado | Doc4 §36 | FS | sempre | ACCEPTED | adversarial §29 | — |
| FS-SEC-04 | Branch fail-closed: `branch_access_denied` em filial não autorizada | Doc4 §20,36 | FS | C2 | ACCEPTED | §29 tests | C0.T3 |
| FS-SEC-05 | Nenhum token/JWT persistido; ator = `id/sub` + display snapshot | Doc4 §21 | FS | C2 | ACCEPTED | §35 tests | — |
| FS-SEC-06 | Service capability nunca excede read-only ERP | Doc4 §40-B | FS | sempre | ACCEPTED | review+tests | FS-SEC-02 |
| FS-SEC-07 | Credenciais só no backend; bearer propagado à api-delpi | Doc4 §36 | FS | C3 | ACCEPTED | §35 tests | — |

### FS-INT — Integrations

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-INT-01 | Reuso api-delpi: 13 rotas tipadas §38 + batch obrigatório (anti-N+1) | Doc4 §38,37 | FS | C3 | ACCEPTED | gateway tests | FS-AR-03 |
| FS-INT-02 | Timeouts explícitos, retry limitado só em GET, backoff+jitter, classificação de erro | Doc4 §37 + regra | FS | C3 | ACCEPTED | resilience tests | FS-INT-01 |
| FS-INT-03 | Correlação/request-id propagado MFE→BFF→api-delpi | Doc4 §32 | FS | C3 | GATED→C0.T11 | trace test | C0.T11 |
| FS-INT-04 | Evidência ERP: matched/not_found/unknown/unavailable/divergent; dedup fingerprint | Doc4 §25–26 | FS | C8 | GATED→C0.T1 | §28 tests | C0.T1 |
| FS-INT-05 | Cockpit: `request-material` `source=operator_cockpit`+correlation+key | Doc4 §28 | FS+Cockpit | C10 | GATED→C0.P1 | contract tests | C0.P1 |
| FS-INT-06 | Evolve `get_product_internal_movements` somente se C0.T1 provar lacuna | Doc4 §27 | DELPI | C8 | GATED→C0.T1 | decisão C0 | C0.T1 |

### FS-OBS — Observability/Audit

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-OBS-01 | Logs estruturados: request_id, operationId, actor, branch, duration, outcome; sem secrets | Doc4 §32 | FS | C1+ | ACCEPTED | §36 | — |
| FS-OBS-02 | Métricas: latência/erro rota+downstream, evidence-status counts, conflict/replay rates, sync results | Doc4 §32 | FS | C6+ | ACCEPTED | §36 | FS-OBS-01 |
| FS-OBS-03 | Auditoria de domínio completa §31 (ator, prev→new, qty, motivo, key, correlação) | Doc4 §31 | FS | C2 | ACCEPTED | §39 tests | FS-DATA-04 |

### FS-TST — Testing

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-TST-01 | Pirâmide completa §28 (domain→application→persistence→HTTP→gateway→MFE→cross) | §28 | FS+MFE | todas | ACCEPTED | suíte por fase | — |
| FS-TST-02 | Adversariais §29 (20 casos) implementados | §29 | FS | por fase | ACCEPTED | casos verdes | — |
| FS-TST-03 | Segurança §35 (11 asserts) implementados | §35 | FS | C7+ | ACCEPTED | security suite | — |
| FS-TST-04 | Cenários de aceite §30 (A–G) executáveis | §30 | FS | C9–C11 | ACCEPTED | aceite | — |

### FS-REL — Release

| ID | Statement | Fonte | Owner | Fase | Status | Aceite | Deps |
|---|---|---|---|---|---|---|---|
| FS-REL-01 | Rollout staged §33 (dark→read-only→pilotos→evidência→devoluções→cockpit) | §33 | FS | C11 | ACCEPTED | release plan | — |
| FS-REL-02 | Sem workflow dual autoritativo; Line Feeder não depreciado sem gate §35 | Doc4 §30 | FS | C11 | ACCEPTED | cutover gate | FS-PR-03 |
| FS-REL-03 | Rollback por fase classificado §34; sem delete silencioso de registros | §34 | FS | sempre | ACCEPTED | plano por fase | — |
| FS-REL-04 | Migração de dados legados: NÃO por default; workstream separado se provado | §32 | FS | C11 | ACCEPTED | decisão documentada | — |

**Total: 76 requirement IDs** — PR 7 · AR 7 · DM 10 · UX 10 · API 10 · DATA 8 · SEC 7 · INT 6 · OBS 3 · TST 4 · REL 4.

## 6. Requirement traceability

Mapeamento condensado (ID → fase → teste/aceite principal). Detalhe por ID na coluna Aceite de §5.

| Família | Fase(s) | Verificação primária |
|---|---|---|
| FS-PR-* | C4–C11 | cenários A–G, gates de produto |
| FS-AR-* | C1–C3 | residual greps, import tests, review |
| FS-DM-* | C2, C4–C6 | unit tests de domínio |
| FS-UX-* | C7–C8 | MFE structural/responsive/a11y tests |
| FS-API-* | C1–C9 | HTTP contract tests |
| FS-DATA-* | C2 | migration/constraint/atomicity tests |
| FS-SEC-* | C0→C7+ | security suite §35 |
| FS-INT-* | C3, C8, C10 | gateway/resilience/contract tests |
| FS-OBS-* | C1–C6 | observability acceptance §36 |
| FS-TST-* | todas | a própria suíte |
| FS-REL-* | C11 | release/cutover gates |

Regra: tarefa sem requirement = suspeita; requirement sem tarefa/teste = incompleto — revisado a cada fechamento de fase.

## 7. Dependency graph

```text
PRODUCT DECISIONS (C0.P)                    TECHNICAL INVENTORY (C0.T)
 C0.P1 reconciliação pedido×sinal ──┐        C0.T1 internal-movements ──→ FS-INT-04/06 → C8
 C0.P2 regra de devolução ──────────┼──→ só bloqueia C9 (returns)      C0.T2 op-materials ────→ signal sync → C4
 C0.P3 prioridade além do factual ──┘        C0.T3 branch-write scope ──→ FS-API-07/SEC-04 → C2+
                                             C0.T4 RBAC seeding ───────→ FS-SEC-01 → C7
                                             C0.T5 service identity ───→ FS-SEC-02 → C4,C8
                                             C0.T6 fingerprint algo ───→ FS-API-04/DATA-08 → C2
                                             C0.T7 unit conversion ────→ FS-DM-09 → C2
                                             C0.T11 correlation header → FS-INT-03 → C3
                                             C0.T12 retention ─────────→ data tasks → C2

IMPLEMENTATION
 C0.READY(scoped) → C1 foundation → C2 persistence+domain+idempotency+concurrency
   → C3 ERP gateways → C4 needs/signals → C5 warehouse slice → C6 feeder slice
   → C7 MFE → C8 ERP evidence → C9 returns(gated) → C10 cockpit(gated) → C11 acceptance/cutover
RELEASE: staged §33; cutover gate §35 independente de C9/C10.
```

**Não-bloqueios explícitos:** C0.P2 não bloqueia C1–C8 (returns é slice tardio); C0.P1 só bloqueia `request-material` com `source=cockpit` e reconciliação — não bloqueia pedido manual já saneado… **correção:** C0.P1 bloqueia também o comportamento de pedido humano que colide com sinal existente; pedidos sem colisão prosseguem. C10 e C9 são paralelos ao tronco pós-C7.

## 8. C0 — Implementation readiness / contract closure

Primeira fase obrigatória — só evidência e decisão, **sem código de produto**. Numerada `FS-C0.*`.

### 8.1 Technical inventory tasks (C0.T)

| Task | Escopo | Evidência esperada | Desbloqueia | Stop |
|---|---|---|---|---|
| FS-C0.T1 | ~~Verificar `get_product_internal_movements`~~ — **`DONE`**: SD3 canônico verificado; sem ID estável → fingerprint composto (TC §25); pairing DE0/RE0 = `DETERMINISTIC_DERIVATION`; campos/filtros/paginação/erros documentados | PROVEN | FS-INT-04 (parcial: RECNO evolve opcional) | — |
| FS-C0.T2 | ~~Verificar `list_production_order_operation_materials(_batch)`~~ — **`DONE`**: SD4 SQL canônico verificado; sem CT/scheduling (produtor = machine-load); batch sem cap → auto-chunk FS | PROVEN | signal sync C4 | — |
| FS-C0.T3 | ~~Inventariar convenção de escopo de escrita por filial + persistir modelo RBAC~~ — **`DONE`**: modelo Product Master congelado (3 permissões, TC §40-A); `.view.filial-*` PROVEN em writes (`BranchAccessService`/`close_pick_plan`); cadeia manifesto→Core→middleware→`has_permission` verificada | PROVEN | FS-SEC-01/04 | — |
| FS-C0.T4 | ~~Registro mínimo RBAC~~ — **`DONE`**: cadeia completa PROVEN — manifesto `{code,name,description,module}` → `register`+`sync_module` (declarativo, versionado; remoção de código deleta do catálogo) → `rbac.manage`+`roles.manage` atribui a roles → `PermissionResolver`/`/me` → middleware `load_user_rbac` → `has_permission`; default DENY; sem gap arquitetural | PROVEN | FS-SEC-01 | — |
| FS-C0.T5 | ~~Identidade de serviço~~ — **`DONE`**: IN_PROCESS jobs asyncio (precedentes pc-poller/outbox/notification-loops); api-delpi auth = `API_DELPI_INTERNAL_SERVICE_TOKEN`+`X-Delpi-Caller-App` (identity `internal-service` is_superadmin na superfície read-only, `PROVEN`); sem service account, sem permissões Core, sem endpoints internos; multi-instância por env-flag. **Correção realtime (T5-bounded):** `OUTBOX_REQUIRED_NOW=YES` + hub WS local + diff/checkpoint + presence `FACTORY_SUPPLY_APP` + cold-start anti-flood (TC §33; padrão Commercial `PROVEN`) | PROVEN | FS-SEC-02 | — |
| FS-C0.T6 | ~~Congelar `request_fingerprint`~~ — **`DONE`**: SHA-256 sobre canonical-JSON do comando tipado (chaves ordenadas, Decimal→string `normalize()`, nulos/default por semântica tipada, UTF-8); input = operation+path+branch+campos de domínio+`expected_version`; escopo `UNIQUE(key,route,actor_user_id)`; claim+mutation+audit+outbox+snapshot em **uma tx** (elimina janela do requests-api); UNIQUE-wait resolve corrida; falha não consome key; AuthZ reavaliado no replay; helper **local** (sem consumidor cruzado provado) | TC §10/§39 | FS-API-04/DATA-08→ACCEPTED | — |
| FS-C0.T7 | ~~Conversão de unidades~~ — **`DONE`**: unidade autoritativa `B1_UM` PROVEN em operation-materials, internal-movements, stock-balances (`unit_of_measure`); `get_product_stock` omite unit → compõe via master data; `UNIT_CONVERSION_*=NOT_REQUIRED`; Decimal `NUMERIC(18,6)` + comparação exata; `accepted_unit` estável; re-sync com unit diferente → `UNIT_DIVERGENCE`; ERP qty+unit divergentes → `divergent` não `matched`; unit ausente → `unknown`/fail-closed em writes | PROVEN (contratos) | FS-DM-09→ACCEPTED | — |
| FS-C0.T11 | Header de correlação aceito pelo gateway portal→api-delpi | convenção documentada | FS-INT-03 | — |
| FS-C0.T12 | Retenção: idempotency_keys, supply_events | política | data tasks | — |

### 8.2 Product decision gates (C0.P)

| Gate | Decisão | Dono | Bloqueia |
|---|---|---|---|
| FS-C0.P1 | Reconciliação pedido×sinal existente: link / adiciona qty / trabalho separado / por intenção | Product Master | `request-material` com colisão; C10 |
| FS-C0.P2 | Regra/fórmula autoritativa de quantidade de devolução (ou confirmar manual+`null`) | Product Master | C9 auto-qty; NÃO bloqueia C1–C8 |
| FS-C0.P3 | Prioridade além de `due_at/overdue/time_to_need` necessária no MVP? (default: não) | Product Master | — se "não" |

## 9. Readiness gates (capability-scoped)

Nenhum gate global único. Cada fase exige só seu subconjunto:

| Gate | Exige | Libera |
|---|---|---|
| C0.G-BASE | C0.T6, C0.T7 decididos | C1–C2 |
| C0.G-DATA | C0.T3, C0.T12 | C2 migrations |
| C0.G-ERP | C0.T1, C0.T2 (+T11 para correlação) | C3, C4, C8 |
| C0.G-RBAC | C0.T3 ✅, C0.T4 ✅ — **PASS** (modelo FROZEN + registro/enforcement PROVEN; execução do registro ocorre dentro de C7.T1) | C7 (MFE com writes) |
| C0.G-SVC | C0.T5 ✅ — **PASS** (in-process + service token PROVEN; cadências `TO_DESIGN` são decisão ops, não gate) | sync/reconcile em C4, C8 |
| C0.G-REQ | C0.P1 | request-material com colisão; C10 |
| C0.G-RET | C0.P2 | C9 (se qty automática for MVP) |

`C0.READY` por gate = `PASS` quando a evidência correspondente existe e está registrada em relatório.

## 10. Implementation phase map

| Fase | Nome | Conteúdo | Gate de entrada | Slice |
|---|---|---|---|---|
| C0 | Readiness/contract closure | §8 | — | — |
| C1 | Backend foundation | pacote, bootstrap, health, auth mw, ok/fail, error map, request-id, composition, config, migration runner | C0.G-BASE | — |
| C2 | Persistence + domain core | migrations V001 (8 tabelas), agregado+dimensões, version, idempotency+fingerprint, audit, UoW | C0.G-BASE+G-DATA | — |
| C3 | ERP read gateways | clients tipados §38, timeouts/retry, batch, error map, correlação | C0.G-ERP(parcial: T2) | — |
| C4 | Needs/signals + mission creation | sync replay-safe, mission create/link, snapshots, `request-material` (sem colisão enquanto P1 aberto) | C0.G-ERP+G-SVC | **SLICE A** |
| C5 | Warehouse slice | work-queue, start/record preparation, ready/handoff, parciais, exceções | C2+C4 | **SLICE B** |
| C6 | Feeder slice | my-collection, collection, handoff, delivery, parciais | C5 | **SLICE C** |
| C7 | MFE | manifesto, routing, client, todas superfícies read+execução, plugin-ui, a11y | C0.G-RBAC + contratos do slice | — |
| C8 | ERP evidence | correlação, erp_observations, refresh, UI badges | C0.G-ERP (T1) + C6 | — |
| C9 | Returns | worklist, record-return (manual/null até P2), UI | C6 (+G-RET se auto) | — |
| C10 | Operator Cockpit | contrato semântico, integração, reconciliação | C0.G-REQ + C7 | — |
| C11 | Coexistence/cutover/acceptance | paridade, cenários A–G, release gates | acumulado | — |

**Vertical slice mais cedo:** SLICE A (necessidade autoritativa → sinal → missão persistida → leitura read-only) prova backend+persistência+gateway+MFE mínimo antes dos comandos operacionais. Ordem de MFE pode antecipar uma página read-only dentro de C4–C5 se G-RBAC fechar cedo — opcional, não obrigatório.

## 11. Backend foundation (C1)

| Task | Escopo | Reqs | Deps | Testes | Stop |
|---|---|---|---|---|---|
| FS-C1.T1 | Skeleton `factory-supply-api`: `factory_supply_app/` camadas §46 TC, `main.py`, settings, `/health` | AR-01/06 | C0.G-BASE | health test | — |
| FS-C1.T2 | `core/responses.py` ok/fail + `ApplicationError` + handlers (validation 422, unhandled 500) | API-01 | T1 | envelope tests | — |
| FS-C1.T3 | `middleware/auth_middleware.py` JWT + `get_current_user`; request/correlation id | SEC-03, OBS-01 | T1 | auth tests | — |
| FS-C1.T4 | Composition root + migration runner `V00N` (`run_migrations_on_startup`) | AR-06, DATA-06 | T1 | startup test | — |
| FS-C1.T5 | Gateway HTTP client base (timeout/retry/config, bearer propagation) | INT-01/02, SEC-07 | T1 | unit | — |

## 12. Domain implementation (C2)

| Task | Escopo | Reqs | Deps | Testes |
|---|---|---|---|---|
| FS-C2.T1 | Entidades `SupplyMission`, `SupplyMissionItem` + invariantes + grãos | DM-01/02 | C1 | unit: grão, invariants |
| FS-C2.T2 | Dimensões de item + parciais + `null`≠0 + unidade | DM-03/09 | T1, C0.T7 | unit: qty/unit |
| FS-C2.T3 | Lifecycle missão + transições + cancel/close + replan histórico | DM-07 | T1 | unit: transitions |
| FS-C2.T4 | `overall_stage` derivation + `available_actions` spec | DM-05/06 | T2–T3 | unit: projection determinística |
| FS-C2.T5 | `DemandSignal` + `signal_key` dedup + origem distinta | DM-04 | T1 | unit: dedup |
| FS-C2.T6 | Handoff facts + custódia | DM-10 | T2 | unit |
| FS-C2.T7 | `version` + expected_version semantics | DM-08 | T1 | unit: stale |

Domain não importa FastAPI/ORM/HTTP — teste de dependência/estrutura obrigatório.

## 13. Persistence implementation (C2)

| Task | Escopo | Reqs | Deps | Testes |
|---|---|---|---|---|
| FS-C2.P1 | `V001__factory_supply_schema.sql` — schema + 8 tabelas §39 + constraints + índices | DATA-01..03 | C0.G-DATA | migration clean DB |
| FS-C2.P2 | Repositories postgres_* + UoW; transação agregado+evento | DATA-04/07 | P1 | atomicity, version CAS |
| FS-C2.P3 | `idempotency_keys` repo + fingerprint store/replay/conflict | API-03/04, DATA-08 | P1, C0.T6 | §18 test matrix |
| FS-C2.P4 | `supply_events` append-only writer | DATA-04, OBS-03 | P1 | append-only test |
| FS-C2.P5 | Repos signals/links/observations + dedup uniques | DATA-03, INT-04 | P1 | constraint tests |

Sem SQL aqui; DDL detalhada só na implementação com §39 como fonte.

## 14. API DELPI integration (C3)

| Task | Escopo | Reqs | Deps | Testes |
|---|---|---|---|---|
| FS-C3.T1 | `ProductionReadGateway` (pcp-orders, machine-load ops/CTs, orders/{op}, op-materials+batch) | INT-01 | C1.T5 | typed mapping, batch limits |
| FS-C3.T2 | `StockReadGateway` (stock-balances items/summary, physical-locations, inventory-blocks) | INT-01 | C1.T5 | mapping, filters |
| FS-C3.T3 | `MovementReadGateway` (internal-movements) + `MasterDataGateway` (products) | INT-01/06 | C0.T1 | mapping, unknown fields |
| FS-C3.T4 | Error map: timeout/5xx→unavailable, 401/403→`downstream_access_denied`, parcial→erro controlado | API-08, INT-02 | C3.T* | §28/§29 casos |
| FS-C3.T5 | Correlação request-id outbound + métricas downstream | INT-03, OBS-02 | C0.T11 | trace/metrics |

Nenhuma rota nova api-delpi (decisão §27 TC). Evolve internal-movements **somente** se T1 provar lacuna → então vira tarefa DELPI separada com checklist `new-api-route-checklist`.

## 15. Needs/mission slice (C4 — SLICE A)

| Task | Escopo | Reqs | Deps | Stop |
|---|---|---|---|---|
| FS-C4.T1 | `demand_signal_sync` job in-process (§40-B/§33): batch machine-load+materials → checkpoint/diff → signals (dedup/supersede) + `integration_outbox` enqueue mesma tx; env-flag single-replica | DM-04, SEC-02, INT-01 | C0.G-SVC ✅, C3 | — |
| FS-C4.T1b | `integration_outbox`+`integration_checkpoints` migrations+repositórios; flush worker (outbox→hub WS + portal notif, split online/offline, dedupeKey, rate-limit defer) | SEC-02 | C4.T1 | contract+replay tests |
| FS-C4.T2 | Queries `list_supply_needs`, `list_upcoming_supply_needs`, `get_factory_supply_overview`, `list_supply_missions` | API-02/06 | C2 | contract tests |
| FS-C4.T3 | `request_supply_material` (cria missão+itens+auditoria; sem colisão até P1) | PR-01/02, API-02/03/05 | C2, P1 p/ colisão | colisão → bloquear ou linkar só após P1 |
| FS-C4.T4 | `plan/replan/cancel/close` comandos + pós-condições | DM-07, API-09 | C2 | transitions tests |
| FS-C4.T5 | `get_supply_mission` agregado completo + `get_supply_lookup_metadata` | API-02 | C2 | contract |

Regra: leituras ERP viram **sinais/missões só via decisão da aplicação** — nunca persistir todo resultado de leitura como missão. Snapshot `_at_decision` gravado na criação do item.

## 16. Warehouse slice (C5 — SLICE B)

`list_warehouse_work_queue` (+`group_by=stage`), `start_item_preparation`, `record_item_preparation` com pickup location snapshot, parciais, exceções, handoff implícito, EV+key+audit. **Teste explícito: `prepared != ERP reserved`** — nenhum efeito de estoque inferido.

## 17. Feeder slice (C6 — SLICE C)

`list_my_collection`, `record_item_collection`, `record_item_handoff`, `record_item_delivery` (recebido_por CT), parciais, exceções, mobile-first payload enxuto, auditoria. **Testes: `collected != ERP transferred`, `operational delivery != ERP movement`.**

## 18. Kanban/overview (C5–C7)

Projeção §16 TC implementada em application service; testada deterministicamente contra dimensões de item (matriz de casos: todo-pending→a_preparar, etc.). MFE renderiza `overall_stage`/`available_actions` sem recomputar. Sem DnD — ações são comandos semânticos.

## 19. MFE (C7)

| Task | Escopo | Reqs | Stop |
|---|---|---|---|
| FS-C7.T1 | Plugin `factory-supply`: manifesto com as 3 permissões §40-A (`access`, `view.filial-01`, `view.filial-02`), rotas portal, cliente `/apps/factory-supply-api/v1`, httpClient envelope+errors | UX-01, AR-02, SEC-01 | sem G-RBAC → não registrar permissões |
| FS-C7.T2 | Visão geral + Abastecimento/Kanban (`KanbanBoard`, stage selector mobile, cards missão) | UX-01/02/06 | — |
| FS-C7.T3 | Necessidades + Próximos períodos (DataTableSection) | UX-01 | — |
| FS-C7.T4 | Minha coleta execução (step-flow, qty confirm, command envelope, key+EV) | UX-03, API-03/05 | — |
| FS-C7.T5 | Almoxarifado + Devoluções híbridos | UX-04 | — |
| FS-C7.T6 | Drawer detalhe + timeline + deep-link + Histórico | UX-05 | — |
| FS-C7.T7 | Estados: loading/empty/error/forbidden + a11y + help (§27) | UX-08, help | — |
| FS-C7.T8 | Realtime client: WS `/v1/realtime` (ping, reconnect, eventos §33), toasts de outcome, atualização de estado, área de exceções persistente (divergências/sync) | UX §28, TC §33 | entrega só em réplica com hub; MVP = 1 réplica |

**Residual grep gate (obrigatório em todo PR MFE):** `apiDelpiUrl|API_DELPI_BASE|apps/api-delpi` = zero ocorrências fora de testes/docs de proibição.

## 20. ERP evidence (C8)

`erp_evidence_reconcile` (job §40-B — hook pós-delivery + passo periódico) + observações dedup + eventos `supply_transfer.*` (§33) + badges UI. Semântica §26 TC congelada. Matriz de teste §28: lookup ok+zero→NOT_FOUND; timeout/5xx→UNAVAILABLE; insuficiente→UNKNOWN; compatível→MATCHED; conflito→DIVERGENT; **403→`downstream_access_denied` + NADA persistido**. Divergências alimentam a área de exceções persistente (§33), nunca toast-only.

## 21. Returns (C9)

Worklist + `record_item_return` com `returned_qty` **manual/nullável** + handoff `direction=return` + eventos. **Quantidade automática só após C0.P2 provar regra/dono**; se MVP exigir auto-qty → P2 vira release gate. UI mostra "não estabelecida" — nunca inventa (Cenário G).

## 22. Operator Cockpit (C10)

Somente após C0.P1: contrato `request-material` `source=operator_cockpit`+`correlation_ref`+key do Cockpit; FS valida tudo; testes de contrato + reconciliação. Cockpit não importa código/DB FS.

## 23. Line Feeder coexistence

Invariantes contínuas (cada fase re-verifica): sem import/http a `production-control-api`; sem leitura/escrita em `production_control.*`; sem dual-write; grep residual em CI do backend. Cutover só via §35.

## 24. RBAC/security (transversal)

Implementação por fase: C0.T3+T4 (DONE — modelo FROZEN 3 permissões; cadeia manifesto→Core sync→roles→`/me`→`has_permission` 100% PROVEN) → registro executado em C7.T1 (manifesto inicial + roles); enforcement por `_authorize(user, branch)` padrão PROVEN (`BranchAccessService.assert_can_view_branch` = `access` + `.view.filial-*`, já aplicado a writes no Line Feeder); cada write: AuthN→AuthZ→branch→`aggregate.branch`→precondition→mutation→audit→postcondition. Service capabilities via mecanismo §40-B (não decoradores de usuário).

## 25. Idempotency/concurrency (C2 + contínuo)

Matriz de teste §18:

| Caso | Esperado |
|---|---|
| mesma key+rota+ator+fingerprint | replay snapshot, `idempotent_replay:true`, efeito único |
| mesma key+fingerprint divergente | `409 idempotency_conflict` |
| key diferente | nova execução |
| mesmo ator, rota diferente, mesma key | execuções independentes |
| retry após sucesso com resposta perdida | replay converge |
| retry em boundary de falha (commit incerto) | sem efeito duplicado |
| dois requests simultâneos mesma key+fingerprint | UNIQUE-wait → 1 mutação + 1 replay (zero dupla mutação) |
| dois requests simultâneos mesma key+fingerprints distintos | 1 mutação + 1 `409 idempotency_conflict` |
| falha validação/AuthZ/transitória → retry mesma key | key não consumida → nova tentativa executa normal |
| mesma key, ator diferente | escopo independente — snapshot de um ator nunca vaza p/ outro |
| replay com AuthZ revogada após sucesso | `403` (AuthZ reavaliado antes do replay) |
| retry pós-`version_conflict` com versão corrigida, mesma key | `409 idempotency_conflict` (expected_version no fingerprint) — cliente usa nova key |
| `expected_version` stale | `409 version_conflict`+`current_version` |
| dois workers mesma transição | 1 sucesso + 1 conflito — zero last-write-wins |
| comando qty com unidade ≠ `accepted_unit` | `422 domain_rule_violation` (igualdade exata, não "conversível") |
| unidade autoritativa indisponível + write de qty | fail-closed; `unit_unknown` explícito |
| Decimal 1 / 1.0 / 1.000 | igualdade semântica (mesmo fingerprint T6, mesmo valor) |
| re-sync retorna unidade diferente p/ item operado | `UNIT_DIVERGENCE` — histórico preserva unit registrada |
| ERP movimento qty igual + unit diferente | `divergent`, nunca `matched` |
| ERP movimento sem unit | `unknown`, nunca `matched` |
| card de missão multi-unidade | agrega itens (inteiros), nunca soma qty entre units |
| formatação PT-BR `126,895 MT` | exibição apenas — valor persistido inalterado |

## 26. Audit/observability

`supply_events` por comando (mesma tx). Logs §32 TC. Métricas: latência rota, downstream lat/erro por operationId, evidence-status counts, conflict/replay rates, sync outcomes. Sem PII/token. Sem métrica de desempenho de pessoas.

## 27. Help/documentation

Conteúdo junto das fases MFE (não no fim): o que é Abastecimento Fabril; fato operacional vs evidência ERP; fluxo almoxarifado/coleta/devoluções; exceções; por que botões somem (permissão); estados de quantidade desconhecida. Regra `feature-help-sync`.

## 28. Test strategy

Pirâmide por camada (resumo — detalhe em §33–35, 39–40):

- **Domain unit:** invariantes, transições, parciais, stage, cancel/close, exceções, unidades.
- **Application:** use cases, AuthZ orchestration, idempotência, concorrência, audit, downstream mapping.
- **Persistence:** migrations, constraints, CAS version, tx, dedup, audit atomic, branch isolation.
- **HTTP contract:** envelope, operationId, erros, paginação, filtros, headers key+EV, AuthN/Z.
- **Gateway:** mapping, timeout, 5xx, 401/403, batch limits, campos ausentes.
- **MFE:** boundary grep, rotas, estados, permissão→visibilidade, kanban, responsive, a11y.
- **Cross:** MFE→FS (mock), FS→PG, FS→api-delpi double.
- **Acceptance:** §30 A–G.

## 29. Adversarial tests (obrigatórios)

1. pedido operador duplicado → dedup/conflito documentado (P1)
2. mesmo `Idempotency-Key` → replay
3. mesma key + payload diferente → `idempotency_conflict`
4. `expected_version` stale → `version_conflict`
5. dois workers mesmo item → um conflita
6. unidade divergente → `domain_rule_violation`
7. saldo desconhecido → fail-closed na criação
8. downstream timeout → `downstream_unavailable`/evidence `unavailable` (se observação)
9. api-delpi 403 → `downstream_access_denied` — **nunca** `not_found`
10. movimento ERP ausente (lookup ok) → `not_found`
11. movimento divergente → `divergent`
12. necessidade reagendada pós-preparo → história preservada, sem reescrita
13. cancelar missão pós-coleta → invariantes + rastro
14. entrega parcial + close → `domain_rule_violation`/close parcial conforme regra Doc2
15. devolução qty desconhecida → `null` persistido, UI explícita
16. branch forjada pelo cliente → 403
17. botão visível sem permissão → 403 backend
18. frontend envia `overall_stage`/`can_*` → ignorado/400
19. re-sync planejado → zero sinais duplicados
20. observação ERP repetida → zero correlações duplicadas
21. mesma key simultânea, mesmo fingerprint → 1 mutação+1 replay; fingerprints distintos → 1 mutação+1 `idempotency_conflict`
22. falha transitória → key livre p/ retry (não envenenada)
23. replay com permissão revogada → `403` (sem vazamento de snapshot)
24. mesma key em ator diverso → escopo independente
25. replay não duplica `supply_events` nem evento outbox/notificação
26. qty com unidade adulterada no body → `422` (backend compara com `accepted_unit`, MFE não valida)
27. movimento ERP numericamente igual com unit divergente → `divergent` (sem conversão)
28. re-sync que troca unidade do material → `UNIT_DIVERGENCE`, nunca reescrita silenciosa
29. unidade autoritativa ausente → `unit_unknown` + fail-closed no write (nunca "UN" default)

## 30. Acceptance scenarios

| Cenário | Fluxo | Prova |
|---|---|---|
| A — planned supply | sinal→missão→preparo→coleta→entrega→rastro | trilha completa + auditoria |
| B — parcial | 100→80 prep→70 coll→60 deliv→residual→close negado | quantidades + regra close |
| C — replan | necessidade muda pós-preparo | evidência original intacta |
| D — concorrência | dois atores, mesma transição | 1 sucesso, 1 `version_conflict` |
| E — evidência | entrega → lookup → estado correto | §28 matriz |
| F — filial | SC tenta mutar ES | 403 fail-closed |
| G — returns | qty desconhecida | `null` + UI honesta, sem fórmula |

## 31. Performance/fan-out

Budgets como gates de implementação (não SLOs inventados): kanban/overview/work-queue usam **consultas paginadas + batch api-delpi** — proibido 1 chamada por card/item fora de limite explicitamente justificado; sync usa `_batch`; history via cursor. Teste de contagem de chamadas downstream por request (budget documentado na implementação — placeholder `TO_INVENTORY` se plataforma tiver SLO canônico a consultar).

## 32. Migration testing

Clean DB; upgrade de versão anterior; checksum immutability (migration aplicada editada → falha detectada); startup runner; falha de migration não deixa schema meio-aplicado (transação por arquivo); rollback/forward-fix documentado — nunca reset prod.

## 33. Release strategy

| Estágio | Conteúdo | Mecanismo |
|---|---|---|
| 1 | backend dark deploy (rotas sem tráfego) | deploy sem nav/permissões |
| 2 | leitura piloto (Visão geral/Necessidades/Histórico) | `access`+`filial` para grupo piloto; escritas indisponíveis por exposição de rotas/`available_actions` — **não** existe permissão "somente-leitura" (§40-A) |
| 3 | piloto almoxarifado (1 filial/CT) | `access` + `.view.filial-01|02` conforme a filial piloto |
| 4 | piloto coleta/entrega | mesmas 3 permissões; expansão é de exposição/auditoria, não de catálogo |
| 5 | evidência ERP | job `erp_evidence_reconcile` §40-B + badges |
| 6 | devoluções | mesmo RBAC (P2 se qty automática) |
| 7 | cockpit | contrato + P1 |
Flags = permissões/exposição de rotas (padrão repo) — sem workflow dual autoritativo e sem permissões extras em nenhum estágio; o modelo FROZEN §40-A não cria granularidade por fase.

## 34. Rollback/reversibility

| Fase | Classe | Nota |
|---|---|---|
| C1–C3 | reversível | sem dados → remove serviço |
| C2 | migration risk baixo | schema novo, nada depende dele |
| C4–C7 | forward-fix | registros operacionais **nunca** deletados em rollback |
| C8–C9 | reversível dados/forward-fix código | observações/devoluções persistem |
| C10 | external dep | cockpit desliga por contrato |
| C11 | cutover irreversível pós-aceite | requer gate §35 |

TOTVS read-only: rollback FS nunca finge reverter fato ERP.

## 35. Cutover gate

Depreciar Line Feeder **somente** com evidência: cobertura funcional das superfícies usadas; aceite usuário (almoxarifado+alimentador); validação ambas filiais; decisão de acesso histórico (leitura legada vs migração — default: leitura); help/monitoramento; permissões mapeadas; rollback definido; zero lacuna crítica de dados. Nenhuma deleção em implementação inicial.

## 36. Implementation report contract

Toda tarefa futura retorna:

```text
FACTORY SUPPLY EXECUTION REPORT
TASK: | BASE HEAD: | FINAL HEAD: | BRANCH: | PRE-EXISTING STATUS:
FILES INSPECTED: | FILES CHANGED: | FILES CREATED:
REQUIREMENTS COVERED: [FS-* IDs] | CONTRACT IMPACT: | MIGRATIONS: | RBAC IMPACT:
TESTS: [suítes] | RESULTS: PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE
SECURITY CHECKS: | OBSERVABILITY: | POSTCONDITION: | RESIDUAL SEARCH: [greps executados]
GAPS: | DRIFT: | FINAL STATUS:
```

`PASS` exige evidência executável — código escrito ≠ PASS.

## 37. Session/handoff strategy

Workstreams sugeridos por sessão: (1) C0 readiness; (2) foundation+persistence+domain; (3) api-delpi gateways; (4) needs/warehouse/feeder slices; (5) MFE; (6) evidence+returns; (7) cockpit; (8) acceptance/cutover. Cada sessão re-ancora em: HEAD atual, os 4 docs canônicos, regras `.cursor` materiais, `git status` real — nunca em memória de chat.

## 38. Commit strategy

Commits por incremento de tarefa/vertical; **nunca** misturar api-delpi changes + backend FS + MFE + fixes não relacionados num só commit (salvo atomicidade real). Seguir `test-and-commit.mdc`; docs desta fase só comitadas com autorização explícita.

## 39. Definition of Done

Escopo releaseado considera-se entregue quando tiver, cumulativamente: conformidade arquitetural (AR-*), compatibilidade de contrato, testes domain+integração+HTTP+gateway+MFE, segurança §35, a11y §37, isolamento de filial, idempotência+concorrência provadas, auditoria, observabilidade, help, cenários A–G, residual searches limpas, evidência de release. Evidência ERP: correlação autoritativa verificada. Devolução automática: só com regra autoritativa provada.

## 40. Decisions frozen

Tudo de TECHNICAL-CONTRACTS §42 + correções (REUSE_AS_IS warehouses, authz≠evidência, fingerprint, RBAC split) + este roadmap: nomes `FS-C{0..11}.T*`, famílias `FS-*` de requirements, gates C0.G-*, SLICEs A–C, contrato de relatório §36.

## 41. Decisions pending

C0.P1 reconciliação · C0.P2 regra devolução · C0.P3 prioridade · C0.T6 algoritmo fingerprint · C0.T7 conversão de unidade · C0.T11 header correlação · C0.T12 retenção · decisão opcional `movement_recno` (evolve §25 TC). ~~C0.T1/T2/T3/T4/T5~~ — DONE.

## 42. TO_INVENTORY

Lista viva = §4 (12 itens) — cada um com task C0 correspondente; itens resolvidos migram para §40/41 conforme evidência.

## 43. First executable task

```text
FIRST_EXECUTABLE_TASK

TASK ID:      FS-C0.T1 (com FS-C0.T2 agrupado como mesma sessão de inventário)
TITLE:        API DELPI authoritative contract verification —
              internal-movements + operation-materials(-batch)
MODE:         DOCUMENTATION-ONLY investigation (read routes/use cases/DTOs/SQL
              + resposta real ou fixture; sem alterar código)
SCOPE:        operationId exato; campos de resposta; identidade estável de
              movimento (ou prova de ausência → fingerprint composto);
              timestamps; warehouses origem/destino; qty/unit; branch;
              paginação/limites; permissão; erros. Para materials: material,
              OP, operação, CT, empenho/open_qty, janela/contexto, unit, branch.
DEPENDENCIES: nenhuma — pode iniciar imediatamente
EXPECTED      documento de campos verificado (PROVEN) + decisão: correlação por
EVIDENCE:     ID estável vs fingerprint composto; campos de signal cobertos.
STOP          se campos insuficientes para correlação/sinal → documentar lacuna
CONDITION:    exata e propor EVOLVE_EXISTING tipado (não inferir; não usar SQL
              genérico; não implementar).
```

---

*Fim do programa de especificação: 5/5. Este documento prova completude da especificação — não do runtime.*
