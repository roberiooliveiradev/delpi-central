# 35 — Contratos, Regras, Scripts e Test Matrix — Gate V2

## Estado

**Evidência e gate pós-merge vigente:** [38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md) (`A15=INCONCLUSIVE` até contratos/testes verificados).

**TARGET / A15 HISTORICAL_CONSOLIDATION / POSTMERGE_REVALIDATION_INCONCLUSIVE / CONTRACT_BINDINGS_TO_INVENTORY**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO
DOCUMENTATION_CLOSURE_COMPLETE = NO
```

Este documento consolida A15 após a revisão transversal A14.

Authorities detalhadas continuam nos documentos de cada página; este arquivo é o índice de fechamento e não duplica integralmente cada contrato.

## 1. Page readiness

| Etapa | Página | Gate V2 |
|---|---|---|
| A01 | Página do usuário | READY_FOR_IMPLEMENTATION_BRIEF |
| A02 | Início | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A03 | Visão geral | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A04 | Minhas tarefas | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A05 | Sala de interação | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A06 | Administração | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A07 | Ajuda | READY_FOR_IMPLEMENTATION_BRIEF |
| A08 | P1 Cockpit da Competência | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A09 | P2 Checklist e Documentos | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A10 | P3 Estoque e Conciliação | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY / STOP T03 |
| A11 | P4 Classificações e Pendências | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A12 | P5 Pacote, Finalização e Envio | C2 / P5-A..J / DEC-01..04 PO_APPROVED; CORE_ELIGIBILITY_AND_BINDINGS_TO_INVENTORY |
| A13 | P6 Administração / Configuração | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |

A12 tem decisões de produto aprovadas: C2, D-P5-01..05 refinadas por P5-A..J, DEC-01..04. Rejeição, reatribuição, quorum por área/versão e não reversão estão definidos semanticamente no doc 37; os contratos físicos de elegibilidade, persistência, estados, concorrência, eventos e consumers permanecem TO_INVENTORY.

## 2. Contrato arquitetural transversal

```text
plugins/controllership-finance
→ /apps/controllership-finance-api
→ owner canônico
```

Owners:
- Core → identidade, apps, effective permissions, RBAC, users, notifications;
- api-delpi → SQL/regras TOTVS/Protheus;
- strategic-indicators-api → metas/indicadores estratégicos;
- controllership-finance-api → estado/regras próprios + composição/adapters;
- plugin-ui → chrome/componentes reutilizáveis.

Proibido:

```text
browser → Core
browser → api-delpi
browser → strategic-indicators-api
browser → DB vizinho
```

## 3. Contratos semânticos por página

Os nomes abaixo são operações semânticas, não endpoint names obrigatórios.

### A01 — Página do usuário

```text
getUserProfile
getUserPhoto
resolveViewerEffectiveAccess
resolveTargetAppMembership
```

Owners:
- Core Directory;
- Core Person Profile;
- Core PermissionResolver.

Writes de identidade não pertencem ao Portal.

### A02 — Início

```text
resolveViewerContext
getActiveCompetenceSummary
getMyTaskPreview
getBlockerSummary
getAttentionEvents
getFavorites/saveFavorites [inventory]
routeCatalog [MFE]
recentViews [MFE local]
```

Home compõe; não cria regra owner.

### A03 — Visão geral

```text
getFinancialKpis
getFinancialOperationalContext
getStrategicPerformance
getIndicatorSeries
getIndicatorDrilldown
resolveViewerAccess
```

A BFF normaliza shape/provenance; não recalcula fórmula/score.

### A04 — Minhas tarefas

```text
getMyTaskProjections
→ source registry
→ owner adapters
→ validated owner deep links
```

```text
TaskProjection != TaskEntity
WORKLIST_SCOPE = MINE_ONLY
```

### A05 — Sala de interação

```text
listRooms
resolveRoomByContext
getRoom
list/post/edit/softDeleteMessage
readState
mentionSuggest
reaction/pin
sharedItems
findInRoom
attachments [inventory]
realtime [inventory]
```

```text
MESSAGE != BUSINESS_DECISION
ROOM_MEMBER != AUTHORIZATION_GRANT
```

### A06/A13 — Administração / P6

```text
getAdministrationSummary
list/get/create/update template draft
startReview
publishTemplate
listCatalogRegistry
list/get/create/update/inactivateCatalogItem
resolveEligiblePeople
listAdministrationAudit
notifyBusinessEvent via Core Notifications adapter
```

Sem user/RBAC write.

### A07 — Ajuda

```text
MFE content registry
→ createDashboardUserManual
→ capability/permission filtered sections
```

Sem BFF/DB/CMS V1.

### A08 — P1

```text
resolveClosingContext
composeStockAxis
composeDocumentsAxis
composePackageAxis
listPriorityPendencies
listClosingHistory
composeBlockers
```

P1 é read-model/composição.

### A09 — P2

```text
list/get checklist items
attachEvidence
validateEvidence
reverseRejection
mark/revertNotApplicable
create/update/cancelExceptionalItem
request/reviewStructuralCorrection
promoteToMaster
listItemHistory
resolveEligiblePeople
```

### A10 — P3

```text
getStockClosingState
confirmCutoff
revalidateStockInputs
getReconciliation
getReconciliationDrilldown
getStockClosingHistory
```

```text
STOCK_CLOSED = terminal no P3 Portal V1
```

Portal não executa sacramentação ERP.

### A11 — P4

```text
list/getPendencies
claim/reassign
startAnalysis
waitExternal
resolve
dismiss
getClassificationSuggestion
confirmClassification
listPendencyHistory
```

IA sugere; humano confirma.

### A12 — P5

```text
list/getRecipientPackages
finalizePackage
reopenFinalizedPackageBeforeSubmit
submitPackageForReview
getReviewerPackage
startReview
requestChanges
acceptReview
createComplementOrNewVersion
list/resolveClarifications
getPackageHistory
notifyUserAboutPackageEvent
deriveMonthlyClosingCompletion [decision pending]
```

```text
PACKAGE_FINALIZED
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING
→ REVIEW_IN_PROGRESS
→ REVIEW_ACCEPTED | CHANGES_REQUESTED
```

Package permanece na Minha DELPI. E-mail é notification only.

Residual:
- `D-P5-REVIEW-COMPLETION`.

## 4. AuthZ contract

```text
JWT
→ identity/context

Core PermissionResolver
→ effective permissions

BFF ALLOW
= capability
AND resource_scope / ownership
AND business_rule
```

Permission codes:

```text
controllership-finance.access
controllership-finance.manage
```

Nenhum outro permission code do produto.

Administração/P6:
- MANAGE é capability administrativa;
- MANAGE não implica ACCESS às superfícies operacionais.

Unidade/filial:
- dimensão de dado/contexto;
- nunca permission code.

## 5. Regras canônicas

Authority:
- [04-regras-de-negocio-consolidadas.md](./04-regras-de-negocio-consolidadas.md).

Invariantes principais:

```text
ATTACHED != VALIDATED
NO_MOVEMENT != NOT_APPLICABLE
PRELIMINARY != FINAL
SOURCE_UNAVAILABLE != ZERO
PENDING_SINCE != SLA
AI_SUGGESTION != HUMAN_DECISION
MESSAGE != BUSINESS_DECISION
BLOCKER != MY_TASK
TASK_PROJECTION != TASK_ENTITY
READY_TO_CLOSE != STOCK_CLOSED
FINALIZE != SEND
PACKAGE_FINALIZED != PACKAGE_SUBMITTED_FOR_REVIEW
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
DOCUMENTED != IMPLEMENTED
```

Paridade:

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
TOLERANCIA_MONETARIA = NONE
```

## 6. Estados de experiência

Baseline de todas as páginas:

```text
LOADING
SUCCESS
EMPTY
PARTIAL
UNAVAILABLE
ERROR
403
404
```

Adicionais quando aplicável:

```text
REFRESHING
VALIDATION_ERROR
CONFLICT
CONNECTION_DEGRADED
STALE_ITEM
```

`UNAVAILABLE_SOURCE` pode qualificar uma source, mas a experiência continua classificada como `UNAVAILABLE`/PARTIAL conforme contract.

## 7. plugin-ui / frontend pattern

Authority:
- [30-plugin-ui-reuse-map.md](./30-plugin-ui-reuse-map.md);
- current `plugins/plugin-ui/src/index.ts`.

A14 confirmou exports para:
- charts;
- collaboration;
- task workspace;
- user manual;
- user profile;
- layout/data/forms/feedback/help/action primitives.

```text
PLUGIN_UI_FIRST = REQUIRED
LOCAL_CLONE = FORBIDDEN
```

Se gap real:
- prove gap;
- preferir contribuição no kit;
- não recriar chrome local.

## 8. Scripts / validators planejados

Nenhum script abaixo deve ser criado na FASE A.

### A01
- `USER-PROFILE-CONTRACT-VALIDATOR`
- `USER-PROFILE-PLUGIN-UI-REUSE-CHECK`
- `USER-PROFILE-STATE-MATRIX`
- `USER-PROFILE-DEEP-LINK-SMOKE`

### A02
- `validate-home-route-catalog`
- `validate-home-favorites`
- `validate-home-deep-links`
- `validate-home-help`

### A03
- `validate-overview-indicator-catalog`
- `validate-overview-route-contracts`
- `validate-overview-filter-url`
- `validate-overview-source-states`
- `validate-overview-help`

### A04
- `validate-task-projection-registry`
- `validate-task-projection-ownership`
- `validate-task-projection-coverage`
- `validate-task-projection-due`
- `validate-task-projection-links`
- `validate-task-help`

### A05
- `validate-interaction-context-registry`
- `validate-interaction-route-contracts`
- `validate-interaction-authz`
- `validate-interaction-message-policy`
- `validate-interaction-attachment-boundary`
- `validate-interaction-help`

### A06/A13
- `validate-admin-catalog-registry`
- `validate-admin-template-lifecycle`
- `validate-admin-snapshot-immutability`
- `validate-admin-effective-dates`
- `validate-admin-authz`
- `validate-admin-identity-boundary`
- `validate-admin-audit`
- `validate-admin-help`
- `validate-p6-notification-adapter`
- `validate-p6-core-people-boundary`

### A07
- `validate-help-route`
- `validate-help-section-registry`
- `validate-help-tool-links`
- `validate-help-capability-gating`
- `validate-help-contextual-links`
- `validate-help-terminology`
- `validate-help-sync`
- `validate-help-plugin-ui`

### A08
- `validate-p1-axis-contracts`
- `validate-p1-blockers`
- `validate-p1-deep-links`
- `validate-p1-authz`
- `validate-p1-help`
- `validate-p1-plugin-ui`

### A09
- `validate-p2-state-machine`
- `validate-p2-snapshot`
- `validate-p2-evidence-history`
- `validate-p2-authz`
- `validate-p2-attachment-boundary`
- `validate-p2-notifications`
- `validate-p2-help`
- `validate-p2-plugin-ui`

### A10
- `validate-p3-monetary-parity`
- `validate-p3-state-machine`
- `validate-p3-source-readiness`
- `validate-p3-owner-boundary`
- `validate-p3-authz`
- `validate-p3-deep-links`
- `validate-p3-help`
- `validate-p3-plugin-ui`

### A11
- `validate-p4-state-machine`
- `validate-p4-human-decision`
- `validate-p4-ownership`
- `validate-p4-source-boundary`
- `validate-p4-authz`
- `validate-p4-deep-links`
- `validate-p4-help`
- `validate-p4-plugin-ui`

### A12
- `validate-p5-package-lifecycle`
- `validate-p5-versioning`
- `validate-p5-completion-rule`
- `validate-p5-notification-boundary`
- `validate-p5-submission-review-contract` — cobre submissão in-portal, unanimidade, versionamento e falhas de AuthZ
- `validate-p5-authz`
- `validate-p5-help`
- `validate-p5-plugin-ui`

Localização/tecnologia dos scripts seguem o padrão vigente do HEAD quando a implementação for autorizada.

## 9. Test matrix padrão

Toda página/slice deve provar quatro famílias.

### Positive

Exemplos:
- happy path autorizado;
- zero real;
- transição válida;
- deep link válido;
- F5;
- owner/source disponível.

### Sibling

Provar isolamento:
- recurso A não altera B;
- source A falhando não apaga B;
- recipient A não avança B;
- usuário A não vê/projeta trabalho de B;
- mudança de filtro não reutiliza stale data de sibling.

### Negative

Obrigatório conforme página:
- sem permission;
- permission errada;
- scope/ownership inválido;
- direct URL;
- state transition inválida;
- source unavailable convertido em zero/empty;
- hard delete/overwrite histórico;
- open redirect;
- UI action sem backend authorization;
- permission proliferation;
- capability futura não implementada.

### Experiência

```text
LOADING
SUCCESS
EMPTY
PARTIAL
UNAVAILABLE
ERROR
403
404
desktop
mobile
light
dark
keyboard/focus
deep-link/F5
Help
```

Adicionar REFRESHING/VALIDATION_ERROR/CONFLICT/etc quando aplicável.

## 10. Testes transversais

Authority:
- [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md).

A15 normalizou RQ-SEC-01..06 e RQ-UX-01..06 para conter:
- aceite;
- teste mínimo;
- dependência;
- estado.

Nenhum RQ pode ser PASS por associação.

## 11. Inventários que não reabrem produto

Quando não houver evidence incompatível:

- E01 — bank/account seed/source;
- E05 — attachment roles seed;
- E06 — rejection reason seed;
- T01 — api-delpi physical bindings;
- T02 — Core notification product adapter;
- T03 — canonical STOCK_CLOSED owner;
- T05 — Core resource scope/effective access bindings;
- H/TSK/R/ADM/HELP inventories físicos definidos nas páginas.

Se a evidence invalidar owner/semântica:
- `EXECUTION_DRIFT`;
- não adaptar silenciosamente.

## 12. Residual vigente para o freeze transversal

O antigo inventário E04/T04 de envio externo por e-mail é `CLOSED / NOT_REQUIRED_IN_V1`. C2 e as decisões P5-A..J / DEC-01..04 foram aprovadas; não existe nova escolha C1/C2/C3 a solicitar.

```text
PRODUCT_DECISIONS_P5 = PO_APPROVED
CORE_EFFECTIVE_ACCESS_S2S = PROVEN (source controller, no live smoke)
CORE_CORPORATE_GROUP_FUNCTION_ATTRIBUTE = TO_INVENTORY
P5_AREA_ELIGIBILITY_BINDING = TO_INVENTORY
P5_REVIEW_STATE_DTO_EVENTS_AND_OCC = TO_INVENTORY
P6_REQUIRED_AREAS_VERSIONING_BINDING = TO_INVENTORY
A12_POSTMERGE = INCONCLUSIVE
```

Os contratos semânticos aprovados são rastreados no doc 37 e no ledger 23. Revalidar os producer/consumer bindings antes de converter planos de scripts em evidências de execução.

## 13. Freeze readiness após A15

```text
PORTAL_DESIGN_FREEZE          = REVALIDATE_POSTMERGE
FRONTEND_PATTERN_FREEZE       = PASS
SECURITY_MODEL_FREEZE         = REVALIDATE_CORE_T05
TEST_STRATEGY_FREEZE          = REVALIDATE_TEST_MATRIX
PRODUCT_CONTRACT_FREEZE       = PENDING_CORE_T05_AND_PHYSICAL_BINDINGS

DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED      = NO
```

Próximo passo:
- C2 já aprovada; completar binding Core T05, normalização de contratos e prova da matriz de testes;
- reexecutar residual search;
- somente então avaliar `PRODUCT_CONTRACT_FREEZE = PASS` e `DOCUMENTATION_CLOSURE_COMPLETE = PASS`.


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. Eventual erro exige processo excepcional separado, formal, auditado e **não autorizado enquanto seu contrato não for aprovado**. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
| **P5-H = A** | P6 configura por tipo de pacote as áreas/especialidades obrigatórias em versão governada; P5 congela a configuração aplicável na submissão. Core fornece identidade, effective permissions e atributos de grupo/função conforme contrato a inventariar. | REVIEW_AREA_SET_SNAPSHOTTED_ON_SUBMISSION |
| **P5-I = B** | Reviewer elegível registra rejeição do pacote em nome da área; uma **autoridade operacional formalmente definida**, distinta da simples permission MANAGE, confirma com justificativa e auditoria a rejeição terminal da competência. | AREA_PACKAGE_REJECTION != TERMINAL_COMPETENCE_REJECTION |
| **P5-J = A** | Após confirmação da rejeição terminal, a competência fica rejeitada e todas as projeções/tarefas de revisão ainda acionáveis deixam de sê-lo; histórico, decisões e autoria permanecem consultáveis conforme AuthZ. | REJECTED_COMPETENCE != MONTHLY_CLOSING_COMPLETED |

### Compatibilidade com regras anteriores

- **C2:** competência concluída somente se TODOS os pacotes aplicáveis foram submetidos, TODAS as áreas obrigatórias aceitaram a PackageVersion vigente e NÃO há esclarecimento aberto. Competência rejeitada nunca satisfaz `MONTHLY_CLOSING_COMPLETED`.
- **P5-A / D-P5-01:** quorum de um aceite por área obrigatória, executado por qualquer usuário elegível; não por indivíduo. Dois elegíveis na mesma área não criam dois aceites necessários.
- **P5-B / D-P5-03 / P5-G:** ninguém sobrescreve aceites; nem o autor pode revertê-los pela UI V1. A referência antiga a “autor pode alterar” é **superseded para aceite P5 na V1**. Reatribuição formal não autoriza mutação de decisões anteriores.
- **P5-C / D-P5-04:** ACCESS efetivo + grupo/função corporativa elegível + escopo do recurso + regra da ação; avaliação server-side fail-closed; reviewer assignment nunca se torna novo permission code.
- **D-P5-02 / P5-E:** esclarecer sem alterar conteúdo preserva versão; qualquer alteração de conteúdo cria nova PackageVersion e **exige novos aceites de todas as áreas obrigatórias**; histórico de versões anteriores preservado.
- **D-P5-05 / P5-D / P5-I:** `CHANGES_REQUESTED` não é `REVIEW_REJECTED`; rejeição da área/pacote não encerra competência automaticamente; só confirmação por autoridade operacional a leva ao estado terminal rejeitado.
- **P5-F / P5-H:** reatribuir elegível não altera aceite já registrado, nem o snapshot de áreas obrigatórias da submissão; edição futura do catálogo P6 não altera snapshots abertos.
- **P5-J:** `TaskProjection != TaskEntity`; P5 continua owner do lifecycle; revisão terminal rejeitada remove acionabilidade, sem hard delete nem apagamento de evidências.

### Trilha de auditoria obrigatória

Preservar identidade Core do ator, data/hora, ação, contexto competência/recipient package, versão, área obrigatória, elegibilidade/scope verificados, motivo/justificativa quando exigidos, estado anterior/posterior, autor original do aceite, referência a reatribuições, confirmação formal da rejeição e correlação da projeção/notificação. Histórico é append-only no nível semântico; **schema físico não definido**.

### Pendências reais — sem aprovação presumida

1. **PO APPROVED DEC-01/02:** responsável formal de fechamento com ACCESS, vínculo e escopo confirma rejeição; não confirmação mantém competência pendente. Inventariar binding, não reabrir a escolha.
2. **PO APPROVED DEC-03:** correção excepcional de aceite P5 não existe no Portal V1, por UI nem endpoint.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **CONTRACT_PENDING:** mapa versionado tipo de pacote → áreas obrigatórias em P6; regras de publicação/vigência/snapshot, defaults inválidos, configuração ausente e concorrência; não inventar tabelas/migrations.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.

**Matriz P5-F..J (PLANNED / TEST_NOT_RUN):** replacement preserva aceite e autor; tentativa de reversão pela UI falha; novo tipo/template P6 não muda áreas de submissão existente; package rejected não é competência rejeitada até confirmação autorizada; confirmação terminal encerra tasks acionáveis e mantém histórico; Core indisponível bloqueia ações; pacote B não herda efeitos de A; nova versão exige todos os aceites. Incluir desktop/mobile/light-dark/teclado/foco/deep-link/Help.


## Decisões finais do PO — DEC-01 a DEC-04 (16/10/2026)

**TARGET / PO_APPROVED / NOT_IMPLEMENTED.** Vigência: este contrato substitui referências históricas a `DECISION_REQUIRED` sobre autoridade de rejeição, negativa de confirmação, exceção de reversão na V1 e publicador P6. Não equivale a evidence de testes ou freeze.

| ID | Decisão aprovada | Contrato normativo |
|---|---|---|
| DEC-01 | Responsável formal da Controladoria | A pessoa designada para coordenar o fechamento da competência pode confirmar rejeição terminal **somente** com `controllership-finance.access` efetivo, vínculo operacional, escopo do recurso e business rule verificados server-side. `manage` isolado não concede essa autoridade. A designação/substituição deve ser auditada; owner da identidade/permissão é Core; owner do vínculo operacional é o contexto P5. |
| DEC-02 | Rejeição pendente se não confirmada | Rejeição pela área/pacote cria proposta de rejeição da competência; até decisão formal ela não está `MONTHLY_CLOSING_COMPLETED` nem terminalmente rejeitada. Autoridade registra decisão/motivo; pode devolver análise para esclarecimento ou correção nas transições autorizadas. Não apagar evento original. |
| DEC-03 | Sem correção excepcional de aceite P5 na V1 | Aceite P5 é irreversível pela UI e não existe endpoint de reversão/retificação na V1. Incidentes são registrados e encaminhados a processo **fora do fluxo do Portal**, sem presumir ação técnica, override, database edit ou reversão automática. P2 validação de evidência mantém contrato próprio. |
| DEC-04 | P6 publica configuração com MANAGE | Usuário com `controllership-finance.manage` efetivo **e** escopo administrativo publica nova configuração versionada de áreas obrigatórias por tipo de pacote, com justificativa, auditoria e vigência prospectiva. Competências e submissões existentes mantêm snapshots; MANAGE não implica ACCESS operacional. |

### Consistência transversal

C2 continua exigindo todos os pacotes aplicáveis submetidos, **um aceite válido de cada área obrigatória** sobre a versão atual, e nenhuma clarification aberta. Uma competência terminalmente rejeitada é desfecho diferente de conclusão, dependente de confirmação DEC-01. P5-A..J permanecem vigentes: aceites auditados por ator; reatribuição não troca autoria ou invalida aceite vigente; nova versão reinicia aceites obrigatórios; envio é submissão interna; rejeição terminal desativa TaskProjections acionáveis e preserva histórico. `CHANGES_REQUESTED` não é `REVIEW_REJECTED`.

### AC mínimos (PLANNED / TEST_NOT_RUN)

- DEC-01: reviewer de área não consegue encerrar competência; coordenador com ACCESS + vínculo + scope consegue confirmar; MANAGE sem vínculo/ACCESS falha; ausência de Core/elegibilidade falha fechada.
- DEC-02: rejeição de área sem confirmação mantém estado pendente; negativa motivada permanece auditável e permite devolução somente por transição contratada; nenhuma conclusão automática.
- DEC-03: nenhum endpoint ou ação UI V1 altera aceite P5; eventos originais imutáveis e incidentes externos não falsificam C2.
- DEC-04: MANAGE + escopo publica com motivação e versionamento; ACCESS sem MANAGE não publica; submissão anterior não muda; nova submissão adota versão conforme vigência autorizada.

### Pendências técnicas distintas de escolhas PO

**TO_INVENTORY:** contrato Core T05 de effective permissions e atributos corporativos; source do coordenador/vínculo/eligibilidade; owner/contrato físico de persistência e eventos; formato de estados/DTOs, versionamento P6 e CAS/concorrência; UX, notifications, help e projections. **CONTRACT_PENDING:** mapear transições específicas e outcomes da negativa no ledger e testes; identificar .cursor e padrões HEAD aplicáveis. Não declarar `PASS` sem inspeção de código/producers/consumers/testes e reconciliação da branch com main.

`DECISION_REQUIRED_PRODUCT_P5=NONE_IDENTIFIED_AFTER_DEC01_DEC04` (sujeito a inventário material posterior); `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`; `TEST_NOT_RUN`.


## Revisão documental transversal — baseline 16/10/2026

**TARGET / REVIEW_INCONCLUSIVE / NO_RUNTIME_AUTHORIZATION.** Fonte de verdade das decisões P5: documento 37, decisões C2, D-P5-01..05 (conforme refinadas), P5-A..J e DEC-01..04. Quórum = um aceite por área obrigatória configurada e congelada na submissão; nova versão exige todos os aceites; reatribuição mantém autoria e aceite válido; P5 não possui reversão de aceite pela UI/endpoint V1; área pode rejeitar pacote e só o coordenador formal de competência com ACCESS efetivo, vínculo e scope pode confirmar rejeição terminal; não confirmação mantém decisão pendente e registra justificativa; rejeição terminal inativa ações projetadas, não apaga auditoria. P6 MANAGE + administrative_scope publica catálogo versionado prospectivo.

**Correção de interpretação:** menções anteriores a C2 pendente, unanimidade de indivíduos, delivery por e-mail de anexos e DEC-01..04 pendentes são histórico **STALE_EVIDENCE / SUPERSEDED**, não critérios vigentes. Referências `PASS` antigas de A12/A14/A15 ou dos freezes não se revalidam automaticamente por adendo; não usar essas flags para autorizar execução.

**Evidência verificada no GitHub:** `main` e branch documental foram comparados; a branch está divergente e a árvore combinada não foi verificada como limpa. O GitHub connector não fornece `git status` de workspace local. Inventário .cursor, consumers/producers, contratos atuais do Core/T05 e testes do HEAD não estão completos. Não foi executado smoke, e documento não prova runtime.

**Gate vigente:** `DECISION_REQUIRED_PRODUCT_P5=NONE_IDENTIFIED_AFTER_DEC01_DEC04` (reabrir somente com nova evidência); `GIT_INTEGRATION=PR78_MERGED_TO_MAIN_VERIFIED`; `CONTRACTS_AND_TEST_MATRIX=REVALIDATE`; `A12=REVALIDATE`; `A14=STALE_EVIDENCE`; `A15=STALE_EVIDENCE`; `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`. Antes do gate PASS: reconciliar branch com main, inventariar .cursor/T05 e contracts, verificar RQ/AC e teste matrix, harmonizar Help e declarar autorização transversal explícita. `TEST_NOT_RUN`.
