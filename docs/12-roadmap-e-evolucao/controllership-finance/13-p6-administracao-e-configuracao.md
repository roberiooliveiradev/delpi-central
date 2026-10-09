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
- recipients;
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
RESPONSIBLE / VALIDATOR / RECIPIENT
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
