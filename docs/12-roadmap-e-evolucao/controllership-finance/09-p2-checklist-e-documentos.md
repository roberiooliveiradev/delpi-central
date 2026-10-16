# 09 — P2 — Checklist e Documentos

## Estado

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

## Job

> Quero saber quais entregáveis são esperados, quais estão satisfeitos, quais dependem de terceiros/validação e o que falta para liberar o pacote.

P2 é a superfície operacional de checklist, evidências, validação e histórico da competência.


## Responsabilidade, owners e non-goals

| Capability/dado | Owner |
|---|---|
| MonthlyChecklistItem / snapshot da competência | produto / `controllership-finance-api` |
| template mestre e catálogos | P6/Administração do produto |
| evidence metadata/versioning | produto, com storage adapter futuro |
| validação/rejeição/reversão/N.A./cancelamento | P2 business rules |
| sources internas derivadas | owner canônico da source, integrado via BFF |
| identities/validator/responsible | Core |
| notifications delivery | Minha DELPI |
| chrome visual/attachments UI | `@delpi/plugin-ui` |

Não pertence a P2:
- editar RBAC/usuário;
- manter template mestre diretamente fora do fluxo P6;
- escrever regra TOTVS;
- considerar upload como validação;
- hard delete de evidence/histórico;
- SMTP próprio;
- SLA/overdue transversal;
- promoção retroativa do snapshot;
- browser chamar owner externo diretamente.


---

## Objetivo visual

O usuário deve conseguir:

```text
LOCALIZAR ITEM
→ ENTENDER REGRA E ESTADO
→ ANEXAR / REVISAR EVIDÊNCIA
→ VALIDAR QUANDO AUTORIZADO
→ ENTENDER HISTÓRICO
→ IDENTIFICAR O QUE AINDA BLOQUEIA
```

A página não deve virar uma tabela única com todas as informações expostas ao mesmo tempo.

---

## Estrutura visual canônica — desktop

```text
┌──────────────────────────────────────────────────────────────────────┐
│ TOPBAR                                                               │
├──────────────────────────────────────────────────────────────────────┤
│ Início > Central de Fechamento > Checklist e Documentos              │
├──────────────────────────────────────────────────────────────────────┤
│ CHECKLIST E DOCUMENTOS                                               │
│ Competência [MM/AAAA] • contexto • freshness • Help                  │
├──────────────────────────────────────────────────────────────────────┤
│ RESUMO: Required | Pendentes | Em validação | Aceitos | N/A          │
├──────────────────────────────────────────────────────────────────────┤
│ filtros / busca / grupo / origem / recipient / requirement / estado  │
├───────────────────────────────┬──────────────────────────────────────┤
│ LISTA DE ITENS                │ DETALHE DO ITEM                      │
│                               │                                      │
│ [estado] Item A               │ Identificação e regra               │
│ REQUIRED • Financeiro         │ Requirement / origem / responsável  │
│                               │                                      │
│ [estado] Item B               │ Evidências                           │
│ CONDITIONAL • Terceiro        │ [upload] [arquivos / preview]        │
│                               │                                      │
│ [estado] Item C               │ Validação                            │
│ OPTIONAL • Interno            │ status / validator / ações           │
│                               │                                      │
│ paginação                     │ Histórico e notificações             │
└───────────────────────────────┴──────────────────────────────────────┘
```

Desktop usa **master-detail**. O detalhe principal não deve abrir em modal.

---

## Estrutura visual — mobile

No mobile a experiência vira lista → detalhe em largura total.

```text
Topbar
→ PagePath
→ contexto
→ resumo
→ filtros/busca
→ lista de itens
→ selecionar item
→ detalhe full-width
   → regra
   → evidências
   → validação
   → histórico
   → ações
```

Regras:
- preservar item selecionado em deep link quando o router permitir;
- preservar filtros relevantes ao voltar;
- usar `BackLink`/PagePath para retorno;
- não usar modal como substituto do detalhe principal;
- upload, validação e histórico continuam acessíveis por teclado;
- nenhuma ação crítica depende apenas de swipe/hover.

---

## Cabeçalho e resumo

Exibir:
- competência;
- contexto de empresa/unidade quando aplicável como dado, não permission;
- freshness;
- acesso ao Help.

O resumo deve usar contagens factuais, por exemplo:
- REQUIRED total e satisfeitos;
- pendentes;
- aguardando terceiros;
- em validação;
- aceitos;
- N/A aplicável.

Não usar percentual único para afirmar readiness do pacote.

---

## Lista e filtros

Filtros:
- todos;
- pendentes;
- aguardando terceiros;
- em validação;
- concluídos;
- grupo;
- origem;
- destinatário;
- requirement;
- busca.

Cada item mostra, sem excesso de detalhe:
- nome;
- requirement;
- origem;
- destinatário quando material;
- provider/responsável;
- satisfaction;
- blocking;
- estado.

A linha/card deve abrir o detalhe. Ações destrutivas não ficam espalhadas na lista.

### Estados visuais do item

O status precisa ser textual e semântico, não apenas cor.

Exemplos conforme state model real:
- PENDING;
- WAITING_EXTERNAL;
- ATTACHED;
- UNDER_REVIEW;
- ACCEPTED;
- REJECTED / REPLACEMENT_REQUIRED;
- NOT_APPLICABLE;
- CANCELLED.

Não inventar estado físico se o contrato usar nomenclatura diferente.

---

## Detalhe do item

Ordem visual canônica:

```text
Identificação e regra
→ Evidências
→ Validação
→ Histórico / notificações
→ Ações secundárias/estruturais
```

### Identificação e regra

Mostrar:
- título;
- requirement_type;
- origem;
- recipient/responsible;
- satisfaction_rule;
- validator;
- validation_scope;
- attachment roles;
- blocking;
- observação/descrição;
- estado atual.

Campos estruturais bloqueados após evento material devem aparecer como read-only, não como controle aparentemente editável.

---

## Evidências

Área de evidências deve diferenciar claramente:

```text
NO_EVIDENCE
ATTACHED
UNDER_REVIEW
ACCEPTED
REJECTED
REPLACEMENT_REQUIRED
```

Upload não significa validação.

```text
ATTACHED != VALIDATED
```

Cada arquivo deve mostrar quando disponível:
- nome;
- role/tipo;
- versão;
- uploader;
- timestamp;
- status de validação;
- comentário/motivo associado;
- preview/download conforme capability.

Versão rejeitada permanece histórica.

---

## Multi-anexo

### PER_ATTACHMENT

Cada arquivo é validado independentemente.

Visualmente:
- status por arquivo;
- ação de validar/rejeitar no arquivo aplicável;
- rejeição parcial não apaga aceites siblings.

### WHOLE_SET

O conjunto é a unidade lógica de validação.

Visualmente:
- arquivos aparecem individualmente;
- estado de validação principal pertence ao conjunto;
- substituição de um arquivo cria nova composição;
- nova composição inteira volta para validação.

A UI deve deixar evidente qual escopo está vigente.

---

## Validação

Mostrar:
- validation_scope;
- validator/responsável;
- estado;
- versão/conjunto avaliado;
- timestamp da última decisão;
- ações permitidas.

Ações como `Aceitar` e `Rejeitar` só aparecem quando o backend/capability permitir.

UI escondida não substitui AuthZ server-side.

---

## Rejeição

Rejeição usa fluxo confirmado, não ação de um clique.

Motivo estruturado obrigatório:
- Competência incorreta;
- Documento incompleto;
- Arquivo ilegível;
- Informação divergente;
- Documento incorreto;
- Outro.

`Outro` exige comentário.

```text
REJECTED → REPLACEMENT_REQUIRED
```

Visual:

```text
Rejeitar
→ Modal/Confirm panel
→ motivo estruturado
→ comentário quando necessário
→ confirmação
→ feedback
→ item permanece no detalhe com histórico atualizado
```

---

## Reversão de rejeição

O mesmo validador que rejeitou pode reverter se nenhuma nova versão foi anexada.

Justificativa obrigatória.

Resultado explícito:
- UNDER_REVIEW; ou
- ACCEPTED.

Nova versão existente bloqueia reversão da rejeição anterior.

A reversão notifica os mesmos destinatários efetivamente notificados na rejeição original.

Visualmente a reversão deve ser ação secundária e contextual no histórico/decisão rejeitada, não CTA principal da página.

---

## N/A

Somente CONDITIONAL.

Exige justificativa e auditoria.

`REQUIRED` nunca apresenta ação `Marcar N/A`.

Pode ser revertido por ACCESS autorizado para PENDING antes de PACKAGE_SUBMITTED_FOR_REVIEW.

Fluxo visual:

```text
Marcar N/A
→ confirmação
→ justificativa
→ estado NOT_APPLICABLE
→ evento no histórico
```

---

## Item excepcional

ACCESS pode criar item apenas para a competência corrente.

Exige:
- justificativa;
- auditoria.

ACCESS seleciona somente opções existentes:
- requirement_type;
- origin_type;
- recipient/responsible;
- satisfaction_rule;
- validator;
- validation_scope;
- notification targets;
- attachment roles catalogados.

Não altera template mestre.

Visualmente `Adicionar item excepcional` é ação secundária da página/lista, não ação de destaque maior que o checklist.

---

## Edição

Antes de evidência/validação/evento material:
- ACCESS pode ajustar configuração permitida.

Depois:
- campos estruturais ficam bloqueados;
- descrição/observação operacional continuam editáveis quando permitido;
- título fica protegido.

Campos read-only devem usar apresentação de leitura; não simular input desabilitado quando o componente de leitura existir.

---

## Cancelamento

Pré-execução:
- ACCESS pode cancelar;
- justificativa obrigatória;
- estado CANCELLED;
- sem delete;
- sai da completude ativa.

Após evento material:
- cancelamento simples bloqueado.

`CANCELLED` é terminal. Se voltar a ser necessário, criar novo item.

Cancelamento deve exigir confirmação e nunca parecer `Excluir`.

---

## Correção estrutural pós-execução

```text
ACCESS REQUEST
→ MANAGE REVIEW
→ APPROVE / REJECT
→ NEW REVISION
```

Aprovação preserva revisão anterior, evidências e validações históricas.

Se a mudança afetar validade:
- evidência suficiente → UNDER_REVIEW;
- evidência insuficiente → PENDING.

MANAGE pode autoaprovar a própria solicitação, mantendo request e approval como eventos separados e auditados.

Notificações canônicas da correção estrutural:

```text
STRUCTURAL_CORRECTION_REQUESTED
→ notificar MANAGE aplicável

STRUCTURAL_CORRECTION_APPROVED
→ notificar requester

STRUCTURAL_CORRECTION_REJECTED
→ notificar requester

STRUCTURAL_CORRECTION_REVALIDATION_REQUIRED
→ notificar validator resolvido
```

Canal lógico:
- Minha DELPI;
- e-mail conforme configuração existente da plataforma.

Sem SMTP próprio, sem SLA, sem reminder periódico e sem escalonamento temporal inventado.

Visualmente:
- request aparece como evento/estado contextual;
- revisão MANAGE não substitui histórico anterior;
- nova revisão é identificável.

---

## Promoção ao mestre

Somente MANAGE:
- cria draft;
- revisa todos os campos;
- define effective_from;
- publica versão futura;
- sem retroatividade.

Em P2, `Promover ao mestre` é ação contextual/secondary. A edição do draft deve navegar ao fluxo owner de Administração, não reproduzir P6 dentro de P2.

---

## Histórico e notificações

Timeline deve cobrir eventos materiais:
- criação/snapshot;
- alteração permitida;
- upload;
- substituição;
- validação;
- rejeição;
- reversão;
- N/A/reversão;
- cancelamento;
- correction request/review;
- notificação relevante.

Notificação anterior não desaparece quando uma decisão é revertida.

Temporalidade:

```text
FORMAL_SLA = NO
DUE_DATE = NO
OVERDUE = NO
TIME_BASED_ESCALATION = NO
PENDING_SINCE = YES
```

`pending_since` é idade factual. A P2 não deriva atraso, prazo ou escalonamento apenas do tempo decorrido.

---

## Contratos TARGET — MFE → BFF → owners

```text
plugins/controllership-finance
→ controllership-finance-api
   → persistence própria do checklist/evidence state
   → Core para identity/effective permissions
   → api-delpi/outro owner somente quando uma source derivada exigir
   → Minha DELPI notifications
   → attachment storage adapter futuro
```

O browser não chama Core, `api-delpi`, notification provider ou storage diretamente.

Operações semânticas necessárias:

| Operação | Semântica |
|---|---|
| listChecklistItems | lista do snapshot da competência com filtros |
| getChecklistItem | regra/estado/evidências/validation/history |
| attachEvidence | criar nova evidence version/attachment metadata |
| validateEvidence | aceitar/rejeitar conforme validator/business rule |
| reverseRejection | reversão governada quando ainda válida |
| markNotApplicable / revertNotApplicable | somente CONDITIONAL e antes do bloqueio material |
| createExceptionalItem | item da competência, sem alterar master |
| updateExceptionalItem | somente campos permitidos antes de evento material |
| cancelExceptionalItem | pré-execução, com justificativa |
| requestStructuralCorrection | request explícito pós-execução |
| reviewStructuralCorrection | MANAGE review / nova revisão |
| promoteToMaster | navegação/ação administrativa governada por P6 |
| listItemHistory | timeline material |
| resolveEligiblePeople | references Core autorizadas |

Os nomes físicos/endpoints entram no OpenAPI futuro; esta lista congela a semântica, não a implementação.

### AuthZ

Base operacional:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND resource_scope / ownership
AND action_business_rule
```

Ações de governança estrutural/mestre:

```text
effective_permission(controllership-finance.manage)
AND administrative_scope/business_rule
```

Regras:
- `MANAGE` não implica `ACCESS`;
- validator/responsible não cria permission code;
- UI visibility não autoriza;
- backend revalida state/version/actor;
- filial/unidade permanece dado/contexto;
- falha da resolução Core → fail-closed.

## Reuso obrigatório de `@delpi/plugin-ui`

Import runtime canônico:

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  ResizableColumns,
  DataTableSection,
  DataRecordCard,
  createDashboardFiltersKit,
  StatusBadge,
  Timeline,
  StateBanner,
  StateBox,
  FileDropzone,
  AttachmentFileList,
  AttachmentPreviewStrip,
  SelectField,
  TextAreaField,
  ReadOnlyField,
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

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

### Mapeamento

| Necessidade | Componente canônico |
|---|---|
| breadcrumb / hero | `createDashboardPagePath` / `createDashboardPageHero` |
| master-detail desktop | `ResizableColumns` |
| lista desktop | `DataTableSection` |
| lista/card mobile | `DataRecordCard` |
| filtros | `createDashboardFiltersKit` |
| cards/seções de detalhe | `createDashboardSectionCard` |
| estado | `StatusBadge` |
| evidência upload | `FileDropzone` |
| lista de arquivos | `AttachmentFileList` |
| preview | `AttachmentPreviewStrip` |
| campo estrutural read-only | `ReadOnlyField` |
| motivo/opções | `SelectField` |
| justificativa/comentário | `TextAreaField` |
| histórico | `Timeline` |
| partial/unavailable | `StateBanner` / `StateBox` |
| rejeição/N.A./cancelamento | `ModalShell` / `ConfirmModalPanel` |
| feedback | `FloatingNoticeStack` |
| ações | `ActionButton` |
| retorno mobile | `BackLink` |
| ajuda contextual | `HelpTooltip` |
| loading/empty | `LoadingState` / `EmptyState` |

### DO NOT RECREATE

Não criar localmente:
- split/master-detail resizer;
- data table/list chrome;
- file dropzone;
- attachment file list/preview;
- form select/textarea/read-only field;
- status badge;
- timeline;
- modal/confirm shell;
- notice stack;
- generic loading/empty state.

Se faltar capability visual reutilizável, registrar `PLUGIN_UI_GAP_FOUND` antes de criar chrome local.

---

## Estados de experiência

### LOADING
Carregar lista e detalhe sem exibir dados default como reais.

### SUCCESS
Snapshot/item/evidências carregados de forma coerente para o recorte.

Estado vazio de um campo opcional só significa ausência real quando a source correspondente respondeu validamente.

### EMPTY
Somente quando não existirem itens aplicáveis após source/contract válidos.

### PARTIAL
Mostrar itens confiáveis e indicar explicitamente source/segmento indisponível.

### UNAVAILABLE / UNAVAILABLE_SOURCE
Não converter ausência de documento/source em `satisfeito` ou `zero`.

`UNAVAILABLE` é o estado da experiência/capability; `UNAVAILABLE_SOURCE` qualifica a origem afetada.

### VALIDATION_ERROR
Preservar item/draft/contexto, associar erro ao campo/ação e não produzir optimistic success.

### ERROR
Erro contextual por pane quando possível; falha do detalhe não deve necessariamente apagar a lista.

### FORBIDDEN
Sem exposição de item/evidência.

### NOT_FOUND
Item/deep link inexistente ou não mais acessível.

---

## ACCESS vs MANAGE

ACCESS opera a competência.

MANAGE administra regras futuras, templates e catálogos.

```text
ACCESS != MANAGE
```

Nenhuma permission por botão, item, documento ou CRUD.

## Light / dark, responsividade e acessibilidade

```text
SAME DOM
+ SAME MASTER_DETAIL
+ SAME ACTIONS
+ SAME STATE ORDER
+ THEME TOKENS
= LIGHT / DARK PARITY
```

- TopBar pertence ao shell;
- P2 é deep page e usa `PagePath`;
- desktop usa `ResizableColumns`;
- mobile usa lista → detalhe full-width;
- status nunca depende apenas de cor;
- file actions, validation, modals e timeline são keyboard-operable;
- focus volta ao contexto coerente após modal/action;
- nenhum CSS de componente do kit é duplicado no MFE.


---

## Critérios visuais de aceite

### VA-P2-01 — Master-detail
No desktop, lista e detalhe coexistem; o detalhe principal não depende de modal.

### VA-P2-02 — Mobile
No mobile, lista e detalhe usam fluxo progressivo full-width com retorno previsível e preservação de contexto.

### VA-P2-03 — Upload vs validação
Após upload, a UI não apresenta `ACCEPTED` automaticamente quando validação é requerida.

### VA-P2-04 — Evidência histórica
Versão rejeitada/substituída continua acessível no histórico.

### VA-P2-05 — Validation scope
`PER_ATTACHMENT` e `WHOLE_SET` possuem representação visual distinta e não ambígua.

### VA-P2-06 — Rejeição
Rejeição exige motivo estruturado; `Outro` exige comentário; nenhuma rejeição acontece em um clique acidental.

### VA-P2-07 — N/A
Ação N/A só aparece quando a regra permitir; REQUIRED nunca oferece N/A.

### VA-P2-08 — Cancelamento
Cancelamento é diferenciado de delete e exige justificativa quando permitido.

### VA-P2-09 — Structural lock
Campos estruturais bloqueados após evento material aparecem como leitura, não como inputs aparentemente editáveis.

### VA-P2-10 — Source failure
Source parcial/indisponível não vira item satisfeito nem empty silencioso.

### VA-P2-11 — Kit-first
Nenhum componente local duplica os exports públicos listados acima.

### VA-P2-12 — Acessibilidade
Lista, upload, preview, validação, modais e histórico são operáveis por teclado, com foco visível e status não dependente de cor.

### VA-P2-13 — Deep link/F5
Competência, item selecionado e contexto relevante sobrevivem a refresh conforme router/contract aprovado.

### VA-P2-14 — Help
Help contextual explica requirement, ATTACHED vs VALIDATED, rejection/replacement, N/A, validation scope, cancelamento e correção estrutural.

---

## RQ / AC / testes

Rastreabilidade canônica:
- `RQ-P2-01` — snapshot;
- `RQ-P2-02` — REQUIRED / CONDITIONAL / N/A;
- `RQ-P2-03` — ATTACHED != VALIDATED;
- `RQ-P2-04` — rejeição histórica + motivo estruturado;
- `RQ-P2-05` — replacement;
- `RQ-P2-06` — PER_ATTACHMENT / WHOLE_SET;
- `RQ-P2-07` — item excepcional por competência;
- `RQ-P2-08` — CANCELLED;
- `RQ-P2-09` — correção estrutural;
- `RQ-P2-10` — reversão;
- `RQ-P2-11` — notificações;
- `RQ-P2-12` — Help.

Authority executável: [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md).

Proveniência funcional TÉO reconciliada:
- 31.3–31.4 — validação/rejeição/multi-anexo;
- 31.5–31.6 — notificações/sem SLA;
- 31.7–31.8 — reversão e notificação da reversão;
- 31.9–31.11 — item excepcional/edição/cancelamento;
- 31.12–31.12.1 — correção estrutural/autoaprovação MANAGE;
- 31.13 — decisões residuais e notificações da correção.

A numeração histórica de RQs nos documentos TÉO é proveniência; o ledger 23 é o identificador TARGET canônico do handoff GitHub.

### Matriz futura mínima — positive
- abrir competência com snapshot;
- upload;
- validar ACCEPTED;
- rejeitar com motivo estruturado;
- replacement e nova validação;
- PER_ATTACHMENT;
- WHOLE_SET;
- N/A somente CONDITIONAL;
- reversão válida antes de replacement/PACKAGE_SUBMITTED_FOR_REVIEW;
- item excepcional;
- edição pré-execução;
- cancelamento pré-execução;
- correction request/review/new revision;
- autoaprovação MANAGE auditada;
- notificações de correction/reversal;
- F5 preservando item/contexto.

### Sibling
- nova versão mestre não altera competência aberta;
- rejeição de um anexo não altera sibling quando PER_ATTACHMENT;
- item excepcional não altera template mestre;
- correction de um item não reescreve evidência/validação histórica;
- falha de uma source preserva siblings confiáveis.

### Negative
- REQUIRED marcado N/A;
- upload tratado como ACCEPTED;
- rejeição sem motivo;
- replacement herdando aceite;
- reversão quando nova versão já existe;
- ACCESS alterando mestre;
- cancelamento após evento material;
- edição estrutural direta pós-execução;
- correção sem AuthZ;
- source indisponível tratado como empty/satisfeito;
- `pending_since` transformado em SLA/overdue;
- UI bypassando backend AuthZ.

### Experiência
- loading;
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
- deep link/F5;
- Help.

## Scripts e artefatos auxiliares PLANNED

Não criar durante a FASE A.

```text
validate-p2-state-machine
- ATTACHED != VALIDATED
- replacement/reversal/N.A./CANCELLED transitions

validate-p2-snapshot
- master publication não altera competence snapshot
- exceptional item não altera master

validate-p2-evidence-history
- rejected/replaced versions preservadas
- no hard delete

validate-p2-authz
- ACCESS/resource/action rules
- MANAGE apenas governance
- fail-closed

validate-p2-attachment-boundary
- roles/config
- source unavailable != satisfied
- storage adapter only through BFF

validate-p2-notifications
- events/targets coerentes
- delivery failure não muda business state

validate-p2-help
- requirement/validation/N.A./replacement/correction sincronizados

validate-p2-plugin-ui
- master-detail/attachments/forms/modal/timeline reutilizados
- no local clone
```

Tecnologia/localização seguem o padrão do HEAD da futura implementação.

## Inventários técnicos remanescentes

- `E05` — seed/obrigatoriedade dos attachment roles;
- `E06` — seed/cobertura inicial de motivos de rejeição;
- `T02` — capability física de notificações;
- `T05` — Core effective permissions/resource ownership;
- contracts físicos de attachment/storage/validator/people selectors.

As decisões de produto correspondentes estão fechadas. Seed/binding não deve ser promovido silenciosamente a nova regra.

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
TEO_DECISIONS_RECONCILED    = PASS
IMPLEMENTATION_AUTHORIZED   = NO
```

Inventários:
- E05 seed/obrigatoriedade de attachment roles;
- E06 seed/cobertura inicial de motivos;
- T02 notification binding;
- T05 effective permissions/resource scope;
- attachment storage/people/contracts físicos.

Resultado:

```text
A09 P2 CHECKLIST E DOCUMENTOS
= READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
!= IMPLEMENTED
```

## Resultado esperado

P2 deve parecer uma **estação operacional de documentos**, não um formulário extenso nem uma planilha administrativa.

```text
LISTA CLARA
+ DETALHE FOCADO
+ EVIDÊNCIA RASTREÁVEL
+ DECISÃO HUMANA EXPLÍCITA
+ HISTÓRICO PRESERVADO
```

Esse é o contrato visual de P2.
