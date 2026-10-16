# 13 — P6 — Administração e Configuração

## Estado

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED      = PASS via 28-administracao.md
CONTRACT_DEFINED         = PASS
AUTHZ_DEFINED            = PASS
PLUGIN_UI_REUSE_DEFINED  = PASS via 28-administracao.md
STATES_DEFINED           = PASS via 28-administracao.md
TEST_MATRIX_DEFINED      = PASS via 28-administracao.md
```

## Contrato da página

A especificação completa de UX, rotas, wireframes desktop/mobile, light/dark, componentes/imports do `@delpi/plugin-ui`, estados, deep links/F5, acessibilidade, Help, RQ/AC, test matrix e scripts planejados está em [28-administracao.md](./28-administracao.md).

Este documento permanece authority das **regras funcionais P6**.

Não duplicar a especificação visual de 28 aqui.

## Responsabilidade, owners e non-goals

| Capability/dado | Owner |
|---|---|
| template mestre do produto | P6 / `controllership-finance-api` |
| versões/snapshots/config catalogs | P6 / `controllership-finance-api` |
| audit dos writes administrativos | P6 / `controllership-finance-api` |
| identities / eligibility / app access | Core |
| effective permissions | Core / PermissionResolver |
| notification delivery | Core Notifications / Minha DELPI |
| regras TOTVS/Protheus | `api-delpi`, quando aplicável |
| page chrome | `@delpi/plugin-ui` via doc 28 |

Não pertence a P6:
- criar/editar usuário;
- criar role/permission;
- administrar RBAC Core;
- escrever diretamente no ERP;
- alterar snapshot de competência aberta;
- hard delete histórico;
- SMTP próprio;
- generic free-form CRUD;
- permission por catálogo/botão/unidade.

## Template mestre

```text
DRAFT
→ REVIEW
→ PUBLISH
→ EFFECTIVE_FROM
```

Salvar não publica.

Publicação:
- cria versão imutável;
- exige `effectiveFrom`;
- registra actor/timestamp;
- não altera competência já aberta.

## Snapshot

```text
COMPETENCE OPEN
→ SNAPSHOT(template version + effective configuration)
```

Competência aberta continua associada à versão vigente na abertura.

Nova publicação não altera:
- competência aberta;
- checklist snapshot;
- histórico;
- pacote existente.

Correção operacional de competência aberta usa fluxo owner específico; não reescreve o mestre/snapshot silenciosamente.

## Inativação

Sem delete físico.

```text
ACTIVE
→ INACTIVE_FROM(date)
```

Exige:
- motivo;
- ator;
- timestamp;
- vigência.

Referência histórica permanece interpretável.

## Publicação

Um usuário com `controllership-finance.manage` pode publicar sozinho com auditoria/versionamento.

Segundo MANAGE não é obrigatório no target atual.

```text
MANAGE != ACCESS
```

MANAGE não concede acesso operacional às demais páginas.

## Catálogos configuráveis

- bancos/contas;
- checklist items;
- requirement;
- origin;
- recipients/reviewer targets;
- operational responsible;
- validator;
- satisfaction rule;
- validation scope;
- notification targets;
- attachment roles;
- extensões de motivos;
- vigência.

```text
CONFIGURABLE != FREE_FORM_EVERYWHERE
```

Cada catálogo possui schema tipado/registry server-side.

ACCESS usa opções existentes; MANAGE administra.

## Lista bancária

```text
BANK_LIST = CONFIGURABLE
HARDCODE = NO
```

E01 define seed/source inicial.

Seed não reabre a arquitetura do catálogo; conflito real de owner/source continua stop condition.

## Pessoas e identidade

```text
RESPONSIBLE / VALIDATOR / RECIPIENT / REVIEWER
= CORE REFERENCE
!= LOCAL USER
```

P6 pode persistir referência estável autorizada.

Não pode:
- criar usuário;
- editar profile;
- conceder ACCESS/MANAGE;
- duplicar nome/e-mail como authority.

Eligibility deve ser resolvida no Core no futuro adapter físico.

## Motivos de rejeição

Modelo:

```text
CORE REASONS
+ MANAGE EXTENSIONS
```

Inativação é prospectiva; histórico preserva códigos usados.

E06 define apenas seed/cobertura inicial.

## Attachment roles

Catálogo reutilizável.

Anexo genérico continua permitido quando business rule não exigir role formal.

E05 define seed e obrigatoriedade real.

### Reviewer targets

P5 recipients/reviewers são referências a identidades Core com app access.

P6 pode configurar targets/eligibility, mas:
- não concede `controllership-finance.access`;
- não cria usuário;
- não cria permission de reviewer;
- não usa e-mail como identity authority;
- reviewer assignment/resource scope é materializado no P5 por competência/package.

## Notification targets

Configuração guarda **alvo lógico**, não infraestrutura.

Exemplos:

```text
OPERATIONAL_RESPONSIBLE
UPLOADER
CONFIGURED_ROLE_OR_RECIPIENT
```

Rebaseline do Core em 09/10/2026 prova:

```text
POST /integrations/notifications
Auth = service token
rate limit = PROVEN
recipient filters / sourceApp / action target = PROVEN
user inbox/history/preferences = PROVEN
```

Logo:

```text
CORE_NOTIFICATION_CAPABILITY = PROVEN
```

Mas o futuro adapter do produto ainda deve definir:
- category/template id;
- payload mínimo;
- recipient resolution;
- required permission filters;
- deep-link/action target;
- treatment de delivery failure.

```text
NOTIFICATION_FAILURE
!= BUSINESS_STATE_CHANGE
```

P6 não cria SMTP, notification center ou preference store.

## Contratos TARGET — MFE → BFF → owners

```text
plugins/controllership-finance
→ controllership-finance-api
   → persistence própria de templates/config
   → Core effective permissions
   → Core Directory/Person references
   → Core /integrations/notifications
```

O browser nunca chama Core diretamente.

Operações semânticas P6:

| Operação | Semântica |
|---|---|
| getAdministrationSummary | versão vigente/draft/future changes |
| listTemplates / getTemplate | versões e conteúdo |
| createDraft / updateDraft | edição governada |
| startReview | DRAFT → REVIEW |
| publishTemplate | versão publicada + effectiveFrom |
| listCatalogs | registry tipado |
| list/get/create/updateCatalogItem | CRUD governado sem free-form schema |
| inactivateCatalogItem | inativação prospectiva |
| resolveEligiblePeople | Core references |
| listAdministrationAudit | histórico read-only |

Contratos físicos permanecem para o futuro OpenAPI.

## Concorrência

Stale write deve ser rejeitado.

```text
client revision N
→ server revision N+1
→ write from N rejected
```

Mecanismo físico (ETag/revision/optimistic lock) permanece ADM07 `TO_INVENTORY`.

Nenhuma sobrescrita silenciosa.

## Auditoria

Eventos mínimos:

- `TEMPLATE_DRAFT_CREATED`
- `TEMPLATE_DRAFT_UPDATED`
- `TEMPLATE_REVIEW_STARTED`
- `TEMPLATE_VERSION_PUBLISHED`
- `MASTER_ITEM_CREATED`
- `MASTER_ITEM_UPDATED`
- `MASTER_ITEM_INACTIVATED`
- `CONFIG_CATALOG_ITEM_CREATED`
- `CONFIG_CATALOG_ITEM_UPDATED`
- `CONFIG_CATALOG_ITEM_INACTIVATED`

Eventos materiais preservam actor/time/entity/action/reason/effective/version e before/after quando aplicável.

## Estados / UX / visual

Authority:
- [28-administracao.md](./28-administracao.md).

Estados mínimos Gate V2:
- LOADING;
- SUCCESS;
- EMPTY;
- PARTIAL;
- UNAVAILABLE;
- VALIDATION_ERROR;
- CONFLICT;
- ERROR;
- 403;
- 404.

Família visual:
- Administration / Master Data;
- composition do `@delpi/plugin-ui`;
- PagePath/PageHero/UnderlineNav;
- desktop/mobile;
- mesma árvore light/dark;
- keyboard/focus;
- Help sincronizada.

## RQ / AC / test matrix

Authority:
- [28-administracao.md](./28-administracao.md);
- [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md).

P6 deve preservar:
- DRAFT != PUBLISH;
- snapshot imutável;
- prospective effective dating;
- no hard delete;
- Core owns identities;
- Core owns effective permissions;
- notification delivery failure não muda business state;
- sem permission proliferation.

## Scripts e artefatos auxiliares PLANNED

Authority principal:
- validators listados em [28-administracao.md](./28-administracao.md).

Adicionar ao futuro brief:

```text
validate-p6-notification-adapter
- usa Core /integrations/notifications
- service-token only
- sourceApp/action target tipados
- failure não muda business state

validate-p6-core-people-boundary
- references resolvidas no Core
- no user/RBAC writes

validate-p6-catalog-contracts
- catalog registry tipado
- no unknown/free-form schema
```

Não criar esses scripts durante a FASE A.

## Inventários técnicos remanescentes

- ADM01 — persistence física;
- E01 — bank/account seed/source;
- E05 — attachment roles seed/obrigatoriedade;
- E06 — rejection reasons seed;
- ADM06 — Core people adapter/eligibility;
- ADM07 — optimistic concurrency binding;
- notification adapter físico do produto — category/template/payload/deep-link.

T02 deixa de ser “capability inexistente”: **a capability de notification do Core é PROVEN no HEAD atual**. O que resta é binding/configuração do adapter do produto.

## Gate documental V2

```text
OBJECTIVE_BOUNDARY_DEFINED  = PASS
OWNERS_DEFINED              = PASS
VISUAL_SPEC_DEFINED         = PASS via 28
CONTRACT_DEFINED            = PASS
AUTHZ_DEFINED               = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS via 28
STATES_DEFINED              = PASS via 28
DEEP_LINK_F5_DEFINED        = PASS via 28
RESPONSIVE_DEFINED          = PASS via 28
LIGHT_DARK_DEFINED          = PASS via 28
A11Y_DEFINED                = PASS via 28
HELP_SYNC_DEFINED           = PASS via 28
RQ_AC_DEFINED               = PASS via 28/23
TEST_MATRIX_DEFINED         = PASS via 28
SCRIPTS_ARTIFACTS_PLANNED   = PASS
IMPLEMENTATION_AUTHORIZED   = NO
```

Resultado:

```text
A13 P6 ADMINISTRAÇÃO / CONFIGURAÇÃO
= READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
!= IMPLEMENTED
```


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

1. **DECISION_REQUIRED:** quem é a autoridade operacional de confirmação de rejeição terminal; como é designada e substituída, e se a confirmação pode ser negada (e qual estado fica então). Não equiparar automaticamente a `manage`.
2. **DECISION_REQUIRED:** procedimento excepcional de correção de aceite P5 fora da UI V1 (owner, autorização, efeitos na conclusão mensal e revalidação), se for implementado nesta versão; na ausência de decisão, **capability não existe na V1**.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **CONTRACT_PENDING:** mapa versionado tipo de pacote → áreas obrigatórias em P6; regras de publicação/vigência/snapshot, defaults inválidos, configuração ausente e concorrência; não inventar tabelas/migrations.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.
