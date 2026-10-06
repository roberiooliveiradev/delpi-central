# 28 — Administração

## Estado

**TARGET / DOCUMENTATION_GATE PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

A fase atual é exclusivamente documental:

```text
PORTAL_REVIEW_PHASE       = ACTIVE
IMPLEMENTATION_AUTHORIZED = NO
```

Este documento fecha o **Item 6 — Administração** no nível de experiência, arquitetura de informação, lifecycle administrativo, catálogos, AuthZ, contratos lógicos, auditoria, Help e testes futuros.

Fontes funcionais:
- [13-p6-administracao-e-configuracao.md](./13-p6-administracao-e-configuracao.md);
- [16-configuracoes-catalogos-e-notificacoes.md](./16-configuracoes-catalogos-e-notificacoes.md);
- [17-backlog-de-confirmacoes-e-inventarios.md](./17-backlog-de-confirmacoes-e-inventarios.md).

---

## Objetivo

**Administração** é a superfície governada para manter configurações próprias do Portal que precisam evoluir sem hardcode e sem alterar retroativamente o histórico operacional.

Ela responde:

> Quais configurações estão vigentes, quais mudanças estão em preparação e quando uma nova versão passa a valer?

Princípio:

```text
CONFIGURE
→ REVIEW
→ PUBLISH
→ BECOME EFFECTIVE
→ PRESERVE HISTORY
```

Administração **não** é:
- gestão de usuários da plataforma;
- RBAC editor;
- permission editor;
- CRUD genérico de qualquer dado;
- escrita direta em TOTVS;
- evidência operacional;
- validação de evidência;
- sacramentação de estoque;
- envio de pacote.

---

## Permission model

A única permission administrativa do Portal é:

```text
controllership-finance.manage
```

Regra:

```text
authenticated
AND effective_permission(controllership-finance.manage)
```

`MANAGE` é suficiente para a superfície administrativa.

`MANAGE` não implica `ACCESS` às páginas operacionais.

Não criar permission por:
- catálogo;
- template;
- CRUD;
- publish;
- inactivate;
- aba;
- botão;
- unidade/filial.

```text
ACCESS != MANAGE
MANAGE_APPROVAL != EVIDENCE_VALIDATION
```

---

## Rota e navegação

Rota raiz:

```text
/apps/controllership-finance/administration
```

Subáreas TARGET:

```text
Painel
Templates
Catálogos
Histórico
```

Rotas lógicas:

```text
/apps/controllership-finance/administration
/apps/controllership-finance/administration/templates
/apps/controllership-finance/administration/catalogs
/apps/controllership-finance/administration/history
```

Não criar uma rota principal para cada catálogo.

Catálogo selecionado:

```text
/administration/catalogs?catalog={catalogKey}
```

Filtros adicionais podem entrar na URL quando forem shareable e não sensíveis.

A navegação interna usa underline/subnav comum.

---

## Arquitetura de informação

### 1. Painel

Resumo governado da Administração.

Deve mostrar:
- versão/template vigente;
- draft/review existente quando aplicável;
- alterações com vigência futura;
- alertas de configuração;
- atalhos para Templates, Catálogos e Histórico.

O Painel **não** precisa inventar KPIs administrativos.

Se um número não tiver semântica de gestão real, usar status/atalho em vez de métrica decorativa.

### 2. Templates

Gerencia versões do template mestre de fechamento.

Cobrir:
- versão vigente;
- drafts;
- estado de review;
- publicação;
- `effectiveFrom`;
- histórico de versões;
- comparação de versão quando disponível;
- snapshot impact.

### 3. Catálogos

Uma única superfície com selector/lista de catálogo.

Catálogos V1:

#### Fechamento
- bancos/contas;
- checklist items;
- requirement types;
- origins.

#### Pessoas e destinos
- operational responsible;
- validators;
- recipients;
- notification targets.

#### Regras e evidências
- satisfaction rules;
- validation scopes;
- attachment roles;
- extensões de motivos de rejeição.

`vigência` é propriedade governada dos registros/versões, não um catálogo isolado.

### 4. Histórico

Auditoria administrativa read-only.

Cobrir:
- actor;
- timestamp;
- entity/catalog;
- action;
- before/after quando aplicável;
- reason;
- effective date;
- correlation;
- version.

Histórico não pode ser apagado pela UI.

---

## Família visual

```text
VISUAL_FAMILY = ADMINISTRATION / MASTER DATA
FULL_PAGE      = NONE
PLUGIN_UI      = COMPOSITION
```

Não existe `AdministrationPage` full-page canônica no kit.

A página deve compor primitives públicas do `@delpi/plugin-ui`.

---

## Reuso obrigatório de @delpi/plugin-ui

Import preferencial:

```ts
import {
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionRouteCard,
  createDashboardUnderlineNav,
  DataTableSection,
  createDashboardFiltersKit,
  FormGrid,
  FormActions,
  NativeTextField,
  NativeSelectField,
  NativeTextAreaField,
  EditableSectionCard,
  ReadOnlyField,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  StatusBadge,
  StateBanner,
  EmptyState,
  LoadingState,
  Timeline,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

Todos os exports acima estão públicos no HEAD atual.

### DO NOT RECREATE

- PageHero;
- PagePath;
- UnderlineNav;
- SectionRouteCard;
- DataTableSection;
- filtros;
- form grid/actions;
- native fields;
- editable/read-only cards;
- modal shell;
- confirm panel;
- notice stack;
- status badge;
- timeline;
- loading/empty/state chrome.

Não criar design-system administrativo dentro do MFE.

---

## Wireframe — Painel / desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda       │
│                                      Buscar | Favoritos | [avatar] Usuário │
└──────────────────────────────────────────────────────────────────────────────┘

← Portal Controladoria & Finanças / Administração

[ Painel ] [ Templates ] [ Catálogos ] [ Histórico ]

┌──────────────────────────────────────────────────────────────────────────────┐
│ ADMINISTRAÇÃO                                                [Atualizar]     │
│ Configurações versionadas do Portal Controladoria & Finanças.               │
└──────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────┐ ┌───────────────────────────────┐
│ TEMPLATES                     │ │ CATÁLOGOS                     │
│ Vigente: v12                  │ │ Configurações operacionais    │
│ Efetiva desde: 01/10/2026     │ │ versionadas e auditáveis.    │
│ Draft: v13                    │ │                               │
│ [Abrir templates]             │ │ [Abrir catálogos]            │
└───────────────────────────────┘ └───────────────────────────────┘

┌───────────────────────────────┐ ┌───────────────────────────────┐
│ ALTERAÇÕES FUTURAS            │ │ HISTÓRICO                     │
│ 2 alterações agendadas        │ │ Última publicação: ...        │
│ [Revisar vigências]           │ │ [Abrir histórico]            │
└───────────────────────────────┘ └───────────────────────────────┘

[!] alertas materiais de configuração, se houver contract real
```

Se não houver contagem confiável, o card usa label/status sem número.

---

## Wireframe — Templates

```text
← Administração / Templates

[ Painel ] [ Templates ] [ Catálogos ] [ Histórico ]

┌──────────────────────────────────────────────────────────────────────────────┐
│ TEMPLATES                                                    [Novo draft]*  │
│ Controle de versões do template mestre do fechamento.                      │
│ * quando lifecycle permitir                                                 │
└──────────────────────────────────────────────────────────────────────────────┘

[Todos] [Draft] [Review] [Publicados]

Versão | Estado | Effective from | Criado por | Atualizado | Ações
v13    | DRAFT  | —              | ...        | ...        | [Abrir]
v12    | EFFECTIVE | 01/10/2026  | ...        | ...        | [Abrir]
v11    | SUPERSEDED| 01/09/2026  | ...        | ...        | [Abrir]

DETALHE
┌──────────────────────────────────────────────────────────────────────────────┐
│ Versão v13 — DRAFT                                                        │
│ Conteúdo/configuração do template                                         │
│                                                                            │
│ [Editar draft] [Enviar para review]                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

A disponibilidade de `Novo draft` deve respeitar o lifecycle físico futuro; não criar duplicação concorrente sem regra.

---

## Lifecycle de template

Regra canônica:

```text
DRAFT
→ REVIEW
→ PUBLISH
→ EFFECTIVE_FROM
```

Semântica:

### DRAFT
- mutável;
- save não publica;
- pode ser revisado;
- ainda não afeta competência.

### REVIEW
- conteúdo congelado para revisão/publicação;
- um usuário com MANAGE pode publicar;
- segundo MANAGE não é obrigatório no TARGET atual.

### PUBLISH
Ação material:
- cria versão publicada imutável;
- registra actor/timestamp;
- exige `effectiveFrom` válido;
- não altera snapshot existente.

### EFFECTIVE_FROM
Quando a data chega:
- nova competência aberta após a vigência usa a versão aplicável;
- competência já aberta mantém snapshot anterior.

Apresentação pode derivar estados como:
- PUBLISHED_SCHEDULED;
- EFFECTIVE;
- SUPERSEDED.

Esses labels de UX não substituem o lifecycle canônico.

---

## Regra de snapshot

```text
COMPETENCE OPEN
→ SNAPSHOT(template version + effective config)
```

Depois disso:

```text
NEW PUBLISH
!= MUTATE OPEN COMPETENCE
```

Não alterar retroativamente:
- competência aberta;
- checklist snapshot;
- histórico;
- package;
- evidence metadata histórica.

Se uma correção estrutural precisa atingir competência aberta:
- usar o mecanismo operacional específico já documentado em P2/P6;
- não reescrever o mestre silenciosamente.

---

## Wireframe — Catálogos

```text
← Administração / Catálogos

[ Painel ] [ Templates ] [ Catálogos ] [ Histórico ]

┌──────────────────────────────────────────────────────────────────────────────┐
│ CATÁLOGOS                                                      [Atualizar]   │
│ Opções versionadas usadas pelas páginas operacionais.                      │
└──────────────────────────────────────────────────────────────────────────────┘

Catálogo
[ Bancos e contas ▼ ]

Status [Todos]   Vigência [Atual/Futura/Inativa]   [Buscar...]

Item                  Estado     Vigência       Contexto        Ações
Banco A / Conta 001   ACTIVE     01/01/2026     Unidade 01      [Abrir]
Banco B / Conta 002   ACTIVE     01/01/2026     Unidade 03      [Abrir]
...

[Adicionar item]

DETALHE
Nome / código / contexto / regra
Effective from
Inactive from
Metadados específicos
[Salvar] [Inativar]
```

---

## Registry de catálogos

O BFF deve manter um registry explícito:

```text
catalogKey
→ schema
→ labels
→ validation rules
→ allowed fields
→ reference resolver
→ audit event mapping
```

Não aceitar um CRUD genérico arbitrário onde o frontend envia schema livre.

```text
CONFIGURABLE != FREE_FORM_EVERYWHERE
```

Cada catálogo tem contrato tipado.

---

## Catálogo — Bancos e contas

Owner:
- configuração própria do Portal;
- seed/owner inicial ainda E01.

Campos lógicos mínimos:
- bank/account identifier;
- display label;
- empresa/unidade aplicável;
- active/effective range.

Regras:
- sem hardcode;
- sem union silencioso de fontes históricas;
- não criar/alterar conta financeira real no ERP;
- mudança vale prospectivamente.

E01 permanece inventário de seed, não decisão arquitetural.

---

## Catálogo — Checklist items

Define opções do template mestre.

Campos lógicos dependem do P2:
- label;
- requirement type;
- origin;
- responsible reference;
- validator reference;
- satisfaction rule;
- validation scope;
- attachment role(s);
- notification target(s);
- effective range.

Não copiar snapshot de competência de volta para o mestre automaticamente.

Promoção de item excepcional:
- exige MANAGE;
- cria/atualiza mestre prospectivamente;
- não altera a competência que originou o item.

---

## Catálogos de pessoas

```text
operational responsible
validator
recipient
notification target
```

Esses catálogos **não** criam identidade.

A seleção de pessoa deve usar Core Directory / app access conforme contract vigente.

Administração pode armazenar referência estável autorizada, por exemplo `userId`/subject conforme contract.

Não:
- criar usuário;
- editar perfil;
- conceder ACCESS/MANAGE;
- criar role no Core;
- duplicar nome/e-mail como authority.

Se o usuário ficar indisponível/inativo:
- histórico preserva referência;
- novos selections devem respeitar eligibility atual;
- snapshot existente não é reescrito silenciosamente.

---

## Catálogo — Motivos de rejeição

Modelo:

```text
CORE REASONS
+ MANAGE EXTENSIONS
```

Regras:
- extensões auditáveis;
- inativação prospectiva;
- código usado historicamente permanece interpretável;
- sem delete físico.

E06 define cobertura/seed inicial.

---

## Catálogo — Attachment roles

Modelo reutilizável.

Regras:
- role formal pode ser obrigatória por item/template;
- anexo genérico continua permitido quando business rule permitir;
- inativação prospectiva;
- histórico preservado.

E05 define seed/obrigatoriedade real.

---

## Notification targets

Configuração define alvo lógico, não infraestrutura de envio.

Exemplos:

```text
OPERATIONAL_RESPONSIBLE
UPLOADER
CONFIGURED_ROLE_OR_RECIPIENT
```

```text
PORTAL_NOTIFICATION != EMAIL_IMPLEMENTATION
```

T02 continua owner do inventário de capability da Minha DELPI.

Não criar SMTP, preference store ou retry engine próprio em P6.

---

## Effective dating

Todo registro configurável que afete operação deve ter semântica prospectiva clara.

Modelo lógico:

```text
effectiveFrom
inactiveFrom?
```

Regras:
- `inactiveFrom > effectiveFrom`;
- inativação não apaga;
- effective date no passado só quando contract/regra permitir explicitamente;
- não alterar snapshot já aberto;
- conflito de vigência deve falhar com mensagem explícita;
- múltiplas versões não podem produzir ambiguidade no mesmo contexto/grain.

---

## Inativação

Lifecycle:

```text
ACTIVE
→ INACTIVE_FROM(date)
```

Ação exige:
- reason;
- actor;
- timestamp;
- effective date.

Não existe hard delete de referência histórica.

Se o item nunca foi usado e policy futura permitir delete físico:
- isso exige contract explícito;
- não assumir na V1.

---

## Formulários

Usar:
- `FormGrid`;
- `NativeTextField`;
- `NativeSelectField`;
- `NativeTextAreaField`;
- `ReadOnlyField`;
- `EditableSectionCard` quando fizer sentido.

Regras:
- technical identifiers em inglês;
- labels UX em PT-BR;
- validação client-side melhora UX, mas backend revalida tudo;
- required/format/range errors ficam próximos do campo;
- erro de negócio não vira tooltip silencioso.

Dirty state:
- bloquear/navegar com confirmação quando houver mudanças não salvas;
- Cancelar restaura baseline;
- Salvar draft não publica.

---

## Confirmações

Usar `ModalShell` / `ConfirmModalPanel` para ações materiais:

- publicar;
- inativar;
- descartar draft/change não salvo;
- aplicar mudança estrutural quando contract exigir confirmação.

Copy deve explicitar:
- o que muda;
- quando passa a valer;
- o que não muda retroativamente.

Evitar confirmação genérica `Tem certeza?`.

---

## Concorrência

Administração deve tratar stale version/conflito.

Modelo lógico:

```text
client reads revision N
→ another MANAGE writes N+1
→ stale write from N is rejected
```

Mecanismo físico:
- ETag;
- revision field;
- optimistic lock equivalente.

```text
CONCURRENCY_MECHANISM = TO_INVENTORY_BEFORE_IMPLEMENTATION
```

A UI:
- preserva draft local quando possível;
- informa conflito;
- permite recarregar;
- nunca sobrescreve silenciosamente.

---

## Histórico / auditoria

Rota:

```text
/apps/controllership-finance/administration/history
```

Filtros:
- período;
- actor;
- entity/catalog;
- action;
- version.

Eventos mínimos:

```text
TEMPLATE_DRAFT_CREATED
TEMPLATE_DRAFT_UPDATED
TEMPLATE_REVIEW_STARTED
TEMPLATE_VERSION_PUBLISHED
MASTER_ITEM_CREATED
MASTER_ITEM_UPDATED
MASTER_ITEM_INACTIVATED
CONFIG_CATALOG_ITEM_CREATED
CONFIG_CATALOG_ITEM_UPDATED
CONFIG_CATALOG_ITEM_INACTIVATED
```

Quando houver mudança:
- before/after;
- reason;
- effective date;
- correlation.

Histórico é read-only.

Não usar log comum de infraestrutura como única auditoria de negócio.

---

## Contract surface lógica

Os nomes físicos finais entram no OpenAPI futuro.

### Summary

```text
GET /apps/controllership-finance-api/administration/summary
```

### Templates

```text
GET  /administration/templates
POST /administration/templates/drafts
GET  /administration/templates/{versionId}
PATCH /administration/templates/{versionId}
POST /administration/templates/{versionId}/review
POST /administration/templates/{versionId}/publish
```

Todos os writes exigem MANAGE e optimistic concurrency quando aplicável.

### Catalog registry

```text
GET /administration/catalogs
```

### Catalog items

```text
GET  /administration/catalogs/{catalogKey}/items
POST /administration/catalogs/{catalogKey}/items
GET  /administration/catalogs/{catalogKey}/items/{itemId}
PATCH /administration/catalogs/{catalogKey}/items/{itemId}
POST /administration/catalogs/{catalogKey}/items/{itemId}/inactivate
```

Não expor DELETE físico na V1.

### Audit

```text
GET /administration/audit
```

Esses contracts são lógicos; não autorizam implementação agora.

---

## Estados da experiência

### LOADING
- Hero/subnav visíveis;
- body com loading do kit;
- não mostrar lista vazia como resultado.

### REFRESHING
- preservar conteúdo anterior quando seguro;
- indicar atualização.

### SUCCESS
Dados completos e revision atual.

### EMPTY
Exemplos:
- nenhum draft;
- catálogo ainda sem item;
- nenhum evento para o filtro.

Empty não é error.

### PARTIAL
Painel pode degradar por seção:
- summary disponível;
- audit unavailable;
- um catálogo auxiliar indisponível.

Writes na capability afetada ficam desabilitados/fail-closed.

### VALIDATION_ERROR
- campo/regra inválida;
- manter draft;
- focar primeira falha quando possível.

### CONFLICT
Stale revision/conflito de vigência.
Nunca auto-merge silencioso.

### ERROR
Falha da capability solicitada.

### FORBIDDEN
Sem MANAGE → 403.

### NOT_FOUND
Version/item inexistente → 404.

### SUCCESS_NOTICE
Salvar/publicar/inativar usa notice explícito.

---

## Deep link / F5

Preservar:

```text
/administration/templates?status=draft
/administration/templates/{versionId}
/administration/catalogs?catalog=attachment-roles&status=active
/administration/history?action=TEMPLATE_VERSION_PUBLISHED
```

F5 reconstrói o contexto.

Não colocar dados sensíveis, before/after ou motivo completo na URL.

---

## Mobile

Administração não tenta reproduzir desktop comprimido.

### Painel
Cards em uma coluna.

### Templates
- lista/tabela responsiva;
- detalhe full-width.

### Catálogos
- selector de catálogo;
- filtros empilhados;
- lista/table/card conforme kit;
- editor em modal/drawer/full page conforme volume de campos.

### Histórico
Tabela responsiva ou cards via `DataTableSection` quando aplicável.

Ações materiais continuam acessíveis e com confirmação.

---

## Light / dark

Mesma árvore:

```text
SAME DOM
SAME FIELDS
SAME ACTIONS
SAME STATUS
+ THEME TOKENS
```

Não criar CSS administrativo duplicado.

---

## Acessibilidade

Obrigatório:
- headings/landmarks;
- subnav por teclado;
- form labels;
- validation associada ao campo;
- foco visível;
- dirty-state dialog acessível;
- confirm modal com focus trap;
- tabela navegável;
- status não depende de cor;
- action disabled com motivo compreensível;
- notices anunciados;
- destructive/effective-date copy clara.

---

## Help

A Ajuda deve explicar, quando a feature estiver implementada:

- quem pode acessar Administração;
- ACCESS vs MANAGE;
- Painel, Templates, Catálogos e Histórico;
- draft vs review vs publish;
- `effectiveFrom`;
- snapshot;
- mudança prospectiva;
- inativação vs exclusão;
- lista bancária configurável;
- checklist master;
- responsables/validators/recipients como referências a usuários Core;
- motivos;
- attachment roles;
- notification targets;
- conflito/stale version;
- auditoria;
- por que mudanças não alteram competências abertas;
- que P6 não gerencia permission ou usuário.

Não publicar catálogo ainda não implementado.

---

## RQ / AC

### RQ-ADM-01 — acesso simples
Aceite:
- rota exige `controllership-finance.manage`;
- MANAGE não implica ACCESS operacional;
- nenhum permission code adicional.

### RQ-ADM-02 — IA administrativa enxuta
Aceite:
- subnav Painel/Templates/Catálogos/Histórico;
- nenhum catálogo vira topbar;
- nenhum catálogo vira permission.

### RQ-ADM-03 — template lifecycle
Aceite:
- DRAFT → REVIEW → PUBLISH → EFFECTIVE_FROM;
- salvar não publica;
- segundo MANAGE não obrigatório;
- published version imutável.

### RQ-ADM-04 — snapshot imutável
Aceite:
- publicação futura não altera competência aberta;
- nova competência usa versão aplicável;
- histórico preservado.

### RQ-ADM-05 — catálogos tipados
Aceite:
- registry explícito;
- schema/validation por catálogo;
- sem generic free-form CRUD.

### RQ-ADM-06 — inativação prospectiva
Aceite:
- sem delete físico;
- reason/actor/timestamp/effective date;
- referência histórica continua interpretável.

### RQ-ADM-07 — identidade permanece Core
Aceite:
- responsible/validator/recipient selecionam referências elegíveis;
- Portal não cria usuário, role ou permission;
- perfil não é duplicado.

### RQ-ADM-08 — notifications mantêm boundary
Aceite:
- target é configuração de negócio;
- delivery usa capability Minha DELPI;
- sem SMTP/preferences local.

### RQ-ADM-09 — concorrência segura
Aceite:
- stale write é rejeitado;
- nenhuma sobrescrita silenciosa;
- UI permite recovery.

### RQ-ADM-10 — auditoria
Aceite:
- eventos materiais com actor/time/entity/action/before-after/reason/effective/version;
- histórico read-only.

### RQ-ADM-11 — plugin-ui first
Aceite:
- componentes públicos do kit;
- nenhum design-system admin local;
- desktop/mobile/light/dark/a11y.

### RQ-ADM-12 — Help sync
Aceite:
- manual explica somente capabilities implementadas;
- lifecycle/snapshot/inactivation consistentes com runtime.

---

## Matriz futura de testes

### Positive
- MANAGE abre Administração;
- navegar Painel/Templates/Catálogos/Histórico;
- criar draft;
- salvar draft;
- review;
- publish com effective date;
- nova competência resolve versão aplicável;
- criar catalog item;
- editar item;
- agendar inativação;
- selecionar responsável/validator elegível;
- consultar audit;
- deep link/F5.

### Sibling
- editar catálogo A não altera B;
- publish vN não altera competência aberta;
- inativar motivo não altera histórico;
- alterar validator mestre não troca validator de snapshot aberto;
- falha T02 não altera catálogo;
- erro de audit não apaga template/catalog.

### Negative
- sem MANAGE;
- ACCESS sem MANAGE;
- permission por botão/catalog inexistente;
- hard delete;
- publish sem effective date válido;
- publish stale revision;
- vigência conflitante;
- sobrescrever published version;
- alterar snapshot via master;
- criar usuário no Portal;
- conceder ACCESS/MANAGE via P6;
- selecionar identity fora da eligibility permitida;
- SMTP próprio;
- free-form catalog schema vindo do frontend;
- open redirect/deep link inválido.

### Experiência
- loading;
- refreshing;
- empty;
- partial;
- validation error;
- conflict;
- error;
- 403;
- 404;
- success notice;
- unsaved changes;
- desktop;
- mobile;
- light;
- dark;
- keyboard/focus;
- Help.

---

## Scripts / validators planejados para futura implementação

Não criar agora.

```text
validate-admin-catalog-registry
- catalogKey registrado
- schema/labels/validation definidos
- no free-form unknown fields

validate-admin-template-lifecycle
- transitions válidas
- save != publish
- published immutable
- effectiveFrom required

validate-admin-snapshot-immutability
- master changes não alteram competence snapshot
- promotion is prospective

validate-admin-effective-dates
- ranges válidos
- no ambiguous overlap
- inactivation prospective

validate-admin-authz
- MANAGE required
- ACCESS alone denied
- no extra permission codes

validate-admin-identity-boundary
- user refs vêm do Core
- no profile/RBAC writes

validate-admin-audit
- material writes emit required audit metadata

validate-admin-help
- only implemented catalogs/capabilities documented
```

Tecnologia/localização seguem padrão do HEAD futuro.

---

## Inventários técnicos restantes

### ADM01 — persistência física
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Definir schema/migrations/repositories apenas quando o slice for autorizado.

### ADM02 — E01 bancos/contas
```text
PENDING_IMPLEMENTATION_CONFIRMATION
```
Seed, source inicial e owner.

### ADM03 — E05 attachment roles
```text
PENDING_IMPLEMENTATION_CONFIRMATION
```
Seed e obrigatoriedade.

### ADM04 — E06 rejection reasons
```text
PENDING_IMPLEMENTATION_CONFIRMATION
```
Cobertura do catálogo inicial.

### ADM05 — T02 notifications
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Capability Minha DELPI, templates, recipients, delivery status.

### ADM06 — Core people selector
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Lookup/eligibility para responsible/validator/recipient.

### ADM07 — optimistic concurrency
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
ETag/revision/version mechanism conforme padrões atuais.

Nenhum desses inventários reabre as decisões de produto deste documento.

---

## Gate

```text
VISUAL_FAMILY_DEFINED       = PASS
INFORMATION_ARCHITECTURE    = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
PERMISSION_MODEL_DEFINED    = PASS
TEMPLATE_LIFECYCLE_DEFINED  = PASS
SNAPSHOT_RULE_DEFINED       = PASS
CATALOG_MODEL_DEFINED       = PASS
IDENTITY_BOUNDARY_DEFINED   = PASS
NOTIFICATION_BOUNDARY       = PASS
EFFECTIVE_DATE_DEFINED      = PASS
INACTIVATION_DEFINED        = PASS
CONCURRENCY_BEHAVIOR        = PASS
AUDIT_DEFINED               = PASS
DEEP_LINK_DEFINED           = PASS
LIGHT_DARK_DEFINED          = PASS
MOBILE_DEFINED              = PASS
A11Y_DEFINED                = PASS
RQ_AC_TEST_MATRIX_DEFINED   = PASS
HELP_CONTRACT_DEFINED       = PASS
IMPLEMENTATION              = NOT_AUTHORIZED
```

Estado:

```text
ITEM 6 = READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
```

---

## Resultado esperado

```text
MANAGE
→ PREPARE CONFIG
→ REVIEW
→ PUBLISH WITH EFFECTIVE DATE
→ NEW WORK USES NEW VERSION
→ OLD/OPEN WORK KEEPS SNAPSHOT
→ AUDIT EVERYTHING MATERIAL
```

Sem permission proliferation, sem hard delete e sem retroatividade silenciosa.
