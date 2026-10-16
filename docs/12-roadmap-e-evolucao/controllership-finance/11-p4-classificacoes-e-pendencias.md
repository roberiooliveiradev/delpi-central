# 11 — P4 — Classificações e Pendências

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED      = PASS
CONTRACT_DEFINED         = PASS
AUTHZ_DEFINED            = PASS
PLUGIN_UI_REUSE_DEFINED  = PASS
STATES_DEFINED           = PASS
TEST_MATRIX_DEFINED      = PASS
```

> Este documento fecha P4 no nível de produto, experiência, arquitetura de informação, estados, AuthZ visual, reuso do `@delpi/plugin-ui`, Help e aceite visual. Não autoriza runtime. Bindings físicos permanecem T01/T05.

## Objetivo da página

Assistir a classificação/CC necessária ao fechamento e operar filas de pendências sem automatizar decisão humana, sem transferir ownership de regra upstream e sem gravar correção no ERP na V1.

A página deve responder, em ordem:

1. qual competência/contexto está sendo operado;
2. quais pendências exigem atuação;
3. qual é o estado, source e owner/responsável de cada pendência;
4. quais evidências explicam a pendência;
5. quando houver classificação, qual sugestão existe e quem precisa confirmar;
6. quais ações o backend autoriza para o usuário corrente;
7. qual histórico de ownership/decisão existe.

## Invariantes

```text
AI_SUGGESTION != HUMAN_DECISION
PENDING != OVERDUE
PENDING_SINCE != SLA
DISMISSED != NOT_APPLICABLE
P4_PORTAL_DECISION != ERP_WRITE
UI_VISIBILITY != AUTHORIZATION
```

- V1 não grava correção no ERP.
- Sugestão de IA nunca muda estado, owner ou classificação por si só.
- O conjunto de estados é fechado; não criar estado livre.
- Severidade só aparece quando uma regra owner/source realmente a fornecer.
- `pending_since` é dado factual; não derivar atraso, SLA ou prazo.
- P4 do fechamento não absorve despesas por centro de custo do Portal Financeiro P0.
- A página não cria permission code, user, role ou RBAC local.


## Responsabilidade, owners e non-goals

| Capability/dado | Owner |
|---|---|
| pendência/state machine do fechamento | P4 / `controllership-finance-api` |
| classificação confirmada no contexto P4 | P4, com decisão humana autorizada |
| regra upstream/CC/fatos canônicos | owner da source/regra correspondente |
| identity/effective permissions | Core / PermissionResolver |
| people references / assignee | Core Directory + references do produto |
| sugestão explicativa de IA | adapter governado, nunca authority |
| write ERP | **fora do Portal V1** |
| chrome visual | `@delpi/plugin-ui` |

Não pertence a P4:
- redefinir regra de centro de custo;
- absorver o Portal Financeiro P0;
- criar permission por fila/unidade;
- calcular SLA/overdue;
- confirmar classificação por IA;
- gravar correção no ERP;
- transformar `DISMISSED` em `NOT_APPLICABLE`;
- conceder acesso via claim/reassign.


## Classificação / CC

```text
dados/evidências
→ regra determinística + IA explicativa
→ sugestão
→ humano confirma
→ decisão auditada no Portal
```

Owner da autoridade de CC permanece gestor/solicitante quando aplicável.

O Portal registra a decisão de P4 necessária ao fechamento, mas não se torna owner da regra upstream.

## IA

Pode:
- explicar;
- sugerir;
- apontar evidência;
- comparar padrões;
- resumir recorrências.

Não pode:
- gravar ERP;
- resolver ambiguidade sozinha;
- alterar owner;
- validar documento;
- confirmar classificação;
- resolver/dismissar pendência.

A sugestão deve ser visualmente apresentada como recomendação, nunca como estado concluído.

## Ownership

Pendências pertencem a fila/papel configurado.

Usuário autorizado pode assumir quando o backend indicar a capability aplicável.

Histórico preserva:
- fila;
- responsável anterior;
- responsável atual;
- timestamps.

Claim/reassign não altera a authority da regra que originou a pendência.

## Estados

Estados canônicos:

- `OPEN`
- `IN_ANALYSIS`
- `WAITING_EXTERNAL`
- `RESOLVED`
- `DISMISSED`

Não criar estados livres.

A UI não define sozinha o transition graph. As ações disponíveis devem vir do contrato/backend e ser revalidadas server-side.

## Resolução

Responsável atual ou papel autorizado pode resolver conforme business rule.

Justificativa/evidência quando aplicável deve ser tratada pelo contrato de ação.

## DISMISSED

Usado quando a pendência é não procedente/dispensada por regra autorizada.

Não usar para esconder blocker ou substituir `NOT_APPLICABLE`.

Justificativa obrigatória.

## Arquitetura de informação

```text
PagePath
→ PageHero / contexto da competência
→ filtros + cobertura/source status
→ fila de pendências
→ detalhe da pendência selecionada
   → resumo de estado/owner/source
   → evidências
   → classificação/sugestão quando aplicável
   → ações autorizadas
   → histórico de ownership/decisão
→ Help contextual
```

A fila é a superfície primária. O detalhe é contextual ao item selecionado.

A página não deve usar percentual único como representação principal do trabalho.

## Jornada principal

```text
Abrir P4
→ recuperar competência/contexto
→ carregar fila
→ selecionar pendência
→ compreender source + motivo + owner
→ revisar evidências
→ se houver classificação: revisar sugestão e contexto
→ executar somente ação autorizada
→ backend revalida AuthZ/business rule
→ atualizar detalhe + histórico
```

Deep link vindo de P1, Home, Minhas tarefas ou histórico deve abrir o mesmo contexto sem bypass de AuthZ.

## Wireframe — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ PagePath                                                                     │
│ Classificações e Pendências                                                  │
│ Competência / contexto / freshness / Help                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ Filtros: estado | source | unidade quando aplicável | busca                  │
│ Coverage/source banner somente quando necessário                             │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ FILA                          │ DETALHE                                      │
│                               │                                              │
│ [status] Pendência A          │ Pendência A                                  │
│ source • responsável          │ Status • fila/responsável • pending_since    │
│ pending_since                 │ Source • unidade • evidência                  │
│                               │                                              │
│ [status] Pendência B          │ Evidências / contexto                         │
│ ...                           │                                              │
│                               │ Classificação                                │
│ paginação/busca               │ sugestão explicável quando aplicável          │
│                               │ confirmação humana quando autorizada          │
│                               │                                              │
│                               │ Ações autorizadas                            │
│                               │                                              │
│                               │ Histórico de ownership/decisão               │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

Desktop usa master-detail com `ResizableColumns`.

A fila pode usar `DataTableSection` quando a densidade de dados justificar tabela. O detalhe não deve ser espremido para preservar uma tabela larga.

## Wireframe — mobile

```text
PagePath
→ PageHero compacto
→ filtros
→ lista de DataRecordCard
→ selecionar item
→ detalhe full-width
   → BackLink
   → estado/owner/source
   → evidências
   → classificação/sugestão
   → ações
   → histórico
```

No mobile:

- não manter split comprimido;
- fila e detalhe são passos progressivos;
- retornar para a fila preserva filtros/contexto;
- ações materiais permanecem alcançáveis sem scroll horizontal;
- status, owner/source e evidência aparecem antes de ações secundárias.

## Conteúdo da fila

Cada item deve expor apenas campos semanticamente disponíveis no contrato:

- estado;
- título/motivo;
- source;
- unidade/contexto quando aplicável;
- fila/responsável;
- `pending_since`;
- severidade somente quando owner fornecer;
- indicador de ação disponível quando útil.

Não exibir:
- `overdue` derivado;
- SLA inventado;
- prioridade derivada de idade;
- owner/team scope não provado.

## Detalhe da pendência

O detalhe organiza:

### Resumo

- status;
- source;
- contexto/unidade;
- fila;
- responsável atual;
- `pending_since`;
- severidade quando contratualmente disponível.

### Evidências

Exibir facts/proveniência disponíveis sem reinterpretar ausência como sucesso.

Source indisponível deve produzir estado explícito, não payload vazio convertido em “sem pendências”.

### Classificação

Quando o item exigir classificação:

```text
evidência
→ sugestão determinística/IA
→ humano autorizado confirma
```

A sugestão deve mostrar, quando disponível:
- valor sugerido;
- racional/evidências;
- source/proveniência;
- aviso explícito de que a confirmação é humana.

A UI não cria regra de classificação e não assume threshold/modelo não homologado.

### Ações

A UI pode apresentar ações como claim, reassign, iniciar análise, aguardar externo, resolver, dismissar ou confirmar classificação somente quando o backend/contract indicar que a ação é válida para o ator, estado e recurso.

A lista de ações visíveis não é authority. Toda mutação é reautorizada server-side.

`DISMISSED` exige justificativa.

Ações corretivas/destrutivas usam confirmação quando material.

### Histórico

Usar timeline auditável para eventos relevantes:

- `PENDENCY_CREATED`
- `PENDENCY_CLAIMED`
- `PENDENCY_REASSIGNED`
- `PENDENCY_ANALYSIS_STARTED`
- `PENDENCY_WAITING_EXTERNAL`
- `PENDENCY_RESOLVED`
- `PENDENCY_DISMISSED`
- `CLASSIFICATION_SUGGESTED`
- `CLASSIFICATION_CONFIRMED`

Histórico preserva actor/timestamp e contexto disponível. Não apagar evento anterior ao reassignment/resolução.

## Contratos TARGET — MFE → BFF → owners

```text
plugins/controllership-finance
→ controllership-finance-api
   → Core effective permissions / Directory
   → source/owner adapters autorizados
   → IA governada quando aplicável
```

O browser não chama Core, `api-delpi`, IA provider ou qualquer owner externo diretamente.

Operações semânticas:

| Operação | Semântica |
|---|---|
| listPendencies | fila autorizada, filtros, coverage/source status |
| getPendency | detalhe, facts, source, owner, history |
| claimPendency | assumir responsabilidade conforme business rule |
| reassignPendency | mudar responsável preservando histórico |
| startAnalysis | OPEN → IN_ANALYSIS quando permitido |
| waitExternal | transição para WAITING_EXTERNAL quando permitida |
| resolvePendency | resolução governada |
| dismissPendency | DISMISSED com justificativa |
| getClassificationSuggestion | sugestão + rationale/provenance, sem decisão |
| confirmClassification | decisão humana auditada |
| listPendencyHistory | ownership + state + classification events |

Os paths/DTOs físicos entram no OpenAPI futuro.

### AuthZ

Authority runtime revalidada no HEAD atual:

```text
Core PermissionResolver
→ effective permissions
→ no JWT permission fallback
```

Base P4:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND resource_scope / ownership
AND business_rule
```

Claim/reassign não concedem acesso ao recurso; apenas alteram responsabilidade dentro de um contexto já autorizado.

A BFF:
- resolve effective access no Core;
- valida resource/context access;
- valida transition/action flags;
- falha fechado quando authorization estiver indisponível;
- não aceita owner/assignee arbitrário do frontend sem resolver eligibility.

## Reuso obrigatório de `@delpi/plugin-ui`

Import preferencial:

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  ResizableColumns,
  DataTableSection,
  DataRecordCard,
  createDashboardFiltersKit,
  DetailFieldGrid,
  ReadOnlyField,
  SelectField,
  TextAreaField,
  StatusBadge,
  AlertQueue,
  Timeline,
  StateBanner,
  StateBox,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  ActionButton,
  BackLink,
  HelpTooltip,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Uso esperado:

| Necessidade | Reuso |
|---|---|
| path/contexto | `createDashboardPagePath` + `createDashboardPageHero` |
| filtros | `createDashboardFiltersKit` |
| master-detail | `ResizableColumns` |
| fila desktop | `DataTableSection` |
| fila mobile | `DataRecordCard` |
| status | `StatusBadge` |
| source/coverage warning | `StateBanner` / `StateBox` |
| resumo de detalhe | `DetailFieldGrid` / `ReadOnlyField` |
| formulários de ação | `SelectField` / `TextAreaField` |
| evidência/sugestão | `SectionCard` + primitives de detalhe |
| blockers/avisos | `AlertQueue` quando semanticamente aplicável |
| histórico | `Timeline` |
| confirmação | `ModalShell` + `ConfirmModalPanel` |
| feedback | `FloatingNoticeStack` |
| loading/empty | `LoadingState` / `EmptyState` |
| retorno mobile | `BackLink` |
| ajuda curta | `HelpTooltip` |

**DO NOT RECREATE:** master-detail, tabela/card responsivo, filter chrome, badges, generic states, timeline, modal/confirm, notices, form fields ou HelpTooltip.

Se o runtime futuro provar gap real no kit, primeiro avaliar contribuição ao `plugin-ui`; não criar clone visual no MFE.

## Estados de experiência

### LOADING

Primeira leitura:
- mostrar chrome e loading do kit;
- não renderizar contagem zero fictícia;
- não inferir fila vazia antes do source responder.

### REFRESHING

Quando já houver conteúdo confiável:
- preservar conteúdo anterior;
- indicar refresh sem bloquear toda a página;
- falha no refresh não apaga dados anteriores quando o contrato permitir sua apresentação como stale/previous.

### SUCCESS

Fila e detalhe refletem contrato atual, com source/freshness disponíveis quando aplicável.

### EMPTY

Só usar quando a consulta válida e completa provar que não existem pendências para o recorte.

`EMPTY != SOURCE_UNAVAILABLE`.

### PARTIAL

Quando uma source falhar e outras permanecerem válidas:
- preservar dados confiáveis;
- mostrar coverage/source failure;
- não apresentar count parcial como total definitivo;
- ações dependentes da source indisponível ficam indisponíveis pelo contract, não por inferência local.

### UNAVAILABLE / UNAVAILABLE_SOURCE

Source obrigatório indisponível:
- não converter em empty;
- não converter em zero;
- explicar indisponibilidade e permitir retry quando o contract suportar.

### VALIDATION_ERROR

Payload/action inválido:
- preservar contexto;
- associar mensagem ao campo/ação;
- não aplicar optimistic success.

### ERROR

Falha geral sem conteúdo utilizável:
- estado de erro explícito;
- retry local quando seguro;
- sem vazamento de stack/SQL/segredo.

### FORBIDDEN — 403

Sem ACCESS ou sem resource ownership/context access:
- não renderizar dados protegidos;
- UI não usa MANAGE como bypass de ACCESS.

### NOT_FOUND — 404

Item inexistente ou sem vínculo válido conforme política canônica do contract.

A decisão física 403/404 de enumeração deve seguir a API/owner; a página não inventa regra local.

## AuthZ

Base:

```text
authenticated identity
AND effective_permission(controllership-finance.access)
AND resource_scope / ownership
AND business_rule
```

Quando uma ação administrativa/mestre for necessária fora do escopo operacional, `controllership-finance.manage` permanece a capability administrativa única.

Regras:
- `MANAGE` não implica `ACCESS`;
- UI esconder/desabilitar não autoriza;
- backend autoriza fail-closed;
- filial/unidade é contexto/dado, não permission code;
- IA usa somente contexto autorizado;
- claim/reassign/resolve/confirm classification são revalidados no backend.

## URL / deep link / F5

O contrato semântico deve preservar quando aplicável:

- competência;
- unidade/contexto;
- filtros;
- pendência selecionada;
- origem/return context seguro.

Os nomes físicos de path/query params entram no router/OpenAPI futuro; este documento não os congela.

F5 deve reconstruir o recorte sem depender de state transitório do frontend.

Nunca aceitar open redirect.

## Light / dark

A mesma árvore conceitual é usada nos dois temas.

- tokens vêm do Portal/`plugin-ui`;
- status não depende apenas de cor;
- source warnings e sugestão de IA mantêm contraste e semântica;
- zero CSS de componente do kit no MFE.

## Acessibilidade

Obrigatório:
- headings semânticos;
- labels associados;
- fila e ações operáveis por teclado;
- foco visível;
- seleção da pendência anunciada;
- modal com focus trap;
- erro de validação associado ao controle;
- status com texto/ícone, não apenas cor;
- histórico navegável;
- mudança de contexto não perde foco de forma imprevisível.

## Help

Help contextual deve explicar:

- sugestão vs decisão humana;
- owner/responsável;
- claim/reassign;
- estados;
- `WAITING_EXTERNAL`;
- `RESOLVED`;
- `DISMISSED`;
- dismiss exige justificativa;
- `pending_since` sem SLA/overdue;
- V1 sem write ERP;
- source indisponível != fila vazia.

Usar o manual canônico em `/help#manual-closing`, conforme [29-ajuda.md](./29-ajuda.md).

Mudança user-facing material em P4 exige Help sync no mesmo gate.

## RQ / aceite visual

### RQ-P4-01 — sugestão não decide

Aceite:
- sugestão aparece como sugestão;
- não altera estado;
- confirmação humana é ação separada quando autorizada.

### RQ-P4-02 — confirmação humana autorizada

Aceite:
- ação de confirmar só aparece conforme capability do contract;
- backend reautoriza;
- ator/evidência aparecem no histórico após sucesso.

### RQ-P4-03 — state machine fechada

Aceite:
- somente estados canônicos são apresentados;
- UI não oferece free-form status.

### RQ-P4-04 — claim/reassign preserva histórico

Aceite:
- responsável anterior/atual e timestamps permanecem auditáveis;
- reassign não apaga evento anterior.

### RQ-P4-05 — DISMISSED

Aceite:
- exige justificativa;
- não usa copy/visual de `NOT_APPLICABLE`;
- blocker não desaparece por fallback visual.

### RQ-P4-06 — sem SLA/overdue

Aceite:
- `pending_since` é factual;
- nenhuma badge “atrasada”, due date ou bucket temporal é derivado localmente.

### RQ-P4-07 — boundary P0 preservado

Aceite:
- UI de P4 usa somente contexto de fechamento;
- não reutiliza despesas por CC do Portal Financeiro P0 como authority automática;
- expansão corporativa exige novo gate.

### RQ-P4-08 — Help

Aceite:
- Help contextual leva à seção canônica;
- conteúdo explica IA/owner/states/dismiss/no-SLA;
- feature não publicada não aparece como capability runtime.

## Testes futuros mínimos

### Positive
- carregar fila completa;
- abrir detalhe;
- confirmar classificação autorizada;
- claim/reassign autorizado;
- resolver;
- dismissar com justificativa;
- histórico atualizado;
- F5 preservando contexto.

### Sibling
- alterar uma pendência não muda sibling;
- reassign de um item não muda responsável de outro;
- source parcial não apaga itens válidos de outra source.

### Negative
- sem ACCESS;
- MANAGE sem ACCESS;
- resource fora do ownership/context access;
- confirmação não autorizada;
- dismiss sem justificativa;
- estado livre/inválido;
- IA tentando mudar estado;
- source unavailable tratado como empty;
- `pending_since` convertido em overdue;
- tentativa de usar P0 como authority automática;
- open redirect.

### Experiência
- loading;
- refreshing;
- empty;
- partial;
- unavailable source;
- validation error;
- error;
- 403;
- 404;
- desktop/mobile;
- light/dark;
- keyboard/focus;
- Help.

## Scripts e artefatos auxiliares PLANNED

Não criar durante a FASE A.

```text
validate-p4-state-machine
- apenas OPEN / IN_ANALYSIS / WAITING_EXTERNAL / RESOLVED / DISMISSED
- transition inválida rejeitada

validate-p4-human-decision
- AI suggestion != confirmation
- actor/evidence/provenance auditados

validate-p4-ownership
- claim/reassign preserva history
- assignee não concede resource access

validate-p4-source-boundary
- P0 não vira authority automática
- unavailable != empty
- no ERP write

validate-p4-authz
- ACCESS + scope/ownership + business rule
- Core fail-closed
- no permission proliferation

validate-p4-deep-links
- competence/filters/selected item/F5
- safe return context

validate-p4-help
- states/AI/dismiss/no-SLA/source semantics sincronizados

validate-p4-plugin-ui
- master-detail/table/cards/forms/timeline/modal reused
- no local clone
```

Tecnologia/localização seguem o padrão do HEAD da futura implementação.

## Inventários técnicos remanescentes

### T01 — source/bindings

`TO_INVENTORY_BEFORE_IMPLEMENTATION`

Provar endpoints, campos, source, freshness, errors, scope e owner.

### T05 — effective permissions / ownership

`TO_INVENTORY_BEFORE_IMPLEMENTATION`

Provar bindings reais de Core effective permissions, resource scope/ownership e fail-closed.

### Contract físico

`TO_INVENTORY_BEFORE_IMPLEMENTATION`

Nomes físicos de endpoints, DTOs, action flags, filtros, paginação, ordenação e deep-link params entram no OpenAPI/router futuro.

Esses inventories não reabrem produto quando apenas materializam o contrato lógico já fechado. Se a evidence provar owner/comportamento incompatível, parar como `EXECUTION_DRIFT`.

## Gate documental V2

```text
OBJECTIVE_BOUNDARY_DEFINED  = PASS
OWNERS_DEFINED              = PASS
VISUAL_SPEC_DEFINED         = PASS
CONTRACT_DEFINED            = PASS
AUTHZ_DEFINED               = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
STATES_DEFINED              = PASS
DEEP_LINK_F5_DEFINED        = PASS
RESPONSIVE_DEFINED          = PASS
LIGHT_DARK_DEFINED          = PASS
A11Y_DEFINED                = PASS
HELP_SYNC_DEFINED           = PASS
RQ_AC_DEFINED               = PASS
TEST_MATRIX_DEFINED         = PASS
SCRIPTS_ARTIFACTS_PLANNED   = PASS
IMPLEMENTATION_AUTHORIZED   = NO
```

Inventários:
- T01 source/bindings;
- T05 resource scope/ownership bindings;
- DTOs/action flags/paginação/deep-link params físicos.

Resultado:

```text
A11 P4 CLASSIFICAÇÕES E PENDÊNCIAS
= READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
!= IMPLEMENTED
```

