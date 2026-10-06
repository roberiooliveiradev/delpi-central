# 12 — P5 — Pacote, Finalização e Envio

**TARGET / VISUAL_SPEC_DEFINED / DOCUMENTATION_GATE PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

> Este documento fecha P5 no nível de produto, experiência, arquitetura de informação, estados, AuthZ visual, reuso do `@delpi/plugin-ui`, Help e aceite visual. Não autoriza runtime. O slice de envio real permanece bloqueado por E04/T04.

## Objetivo da página

Versionar o pacote do fechamento, permitir finalização controlada, acompanhar pacotes por destinatário, tratar esclarecimentos e preservar histórico sem confundir:

```text
READY_TO_FINALIZE
!= PACKAGE_FINALIZED
!= PACKAGE_SENT
!= MONTHLY_CLOSING_COMPLETED
```

A página deve responder, em ordem:

1. qual competência/contexto está sendo operado;
2. quais destinatários possuem pacote aplicável;
3. quais blockers impedem finalização;
4. qual versão está em trabalho/finalizada;
5. quais pacotes já foram enviados por capability comprovada;
6. quais esclarecimentos permanecem abertos;
7. qual histórico de versão/entrega existe.

## Invariantes

```text
FINALIZE != SEND
PACKAGE_FINALIZED != PACKAGE_SENT
PACKAGE_SENT = IMMUTABLE
RECIPIENT_PACKAGE_A != RECIPIENT_PACKAGE_B
SEND_CAPABILITY_UNKNOWN != SEND_AVAILABLE
NO_OPEN_CLARIFICATION is required for monthly completion
UI_VISIBILITY != AUTHORIZATION
```

- Finalizar cria snapshot/versão; não envia.
- Um destinatário avança independentemente dos demais.
- Pacote enviado é histórico imutável.
- Correção pós-envio cria complemento/nova versão ligada à anterior.
- Não existe botão de force completion.
- Read/ack do destinatário não bloqueia a V1.
- Canal de envio não pode ser assumido.
- Se envio real não estiver implementado, a UI não apresenta ação/canal fictício.

## Lifecycle do pacote

### Preparação e finalização

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED_V1
```

Finalizar exige que os requisitos aplicáveis permitam avanço.

### Reabertura antes do envio

```text
FINALIZED_V1
→ REOPEN_WITH_REASON
→ WORKING_COPY
→ FINALIZED_V2
```

A versão anterior permanece histórica.

### Envio

Somente quando E04/T04 provarem capability corporativa real:

```text
PACKAGE_FINALIZED
→ SEND THROUGH PROVEN CORPORATE CAPABILITY
→ PACKAGE_SENT
```

O nome do canal, payload, proof of delivery e retry pertencem ao inventário técnico.

### Esclarecimentos

Por destinatário:

```text
PACKAGE_SENT
→ WAITING_FOR_CLARIFICATION
→ CLARIFICATION_RESOLVED
```

### Correção pós-envio

```text
PACKAGE_SENT_V1
→ COMPLEMENT_OR_NEW_VERSION
→ LINK_TO_V1
→ NEW_DELIVERY
```

Motivo obrigatório; V1 permanece imutável.

### Conclusão mensal

```text
ALL_APPLICABLE_RECIPIENT_PACKAGES_SENT
AND
NO_OPEN_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

Sem ação independente para “forçar conclusão”.

## Arquitetura de informação

```text
PagePath
→ PageHero / competência
→ blockers / readiness de pacote
→ pacotes por destinatário
→ detalhe do pacote selecionado
   → resumo/status
   → itens/versão
   → finalização/reabertura quando autorizadas
   → delivery status somente quando capability existir
   → esclarecimentos
   → histórico de versões/entregas
→ Help contextual
```

A unidade principal é o **recipient package** dentro da competência.

A página não deve representar o estado mensal inteiro como um único percentual.

## Jornada principal — package/finalization

```text
Abrir P5
→ carregar competência e recipient packages
→ selecionar destinatário
→ revisar blockers e itens
→ atingir READY_TO_FINALIZE
→ usuário autorizado finaliza
→ backend valida business rules
→ snapshot/version criado
→ PACKAGE_FINALIZED
→ histórico atualizado
```

Se houver reabertura antes do envio:

```text
PACKAGE_FINALIZED
→ reabrir com motivo
→ working copy
→ corrigir
→ finalizar nova versão
```

## Jornada de envio — somente quando liberada

```text
PACKAGE_FINALIZED
→ capability corporativa comprovada
→ usuário autorizado aciona envio
→ backend revalida AuthZ/business rule
→ delivery result/proof
→ PACKAGE_SENT
```

Enquanto E04/T04 não fecharem:

```text
SEND_ACTION = NOT_IMPLEMENTED
SEND_CHANNEL = NOT_ASSUMED
PACKAGE_FINALIZATION = STILL_VALID
```

A ausência de capability de envio não deve bloquear o fechamento documental da página de package/finalization.

## Wireframe — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ PagePath                                                                     │
│ Pacote, Finalização e Envio                                                  │
│ Competência / contexto / Help                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ Blockers / readiness                                                         │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ PACOTES POR DESTINATÁRIO      │ DETALHE DO PACOTE                            │
│                               │                                              │
│ [status] Contábil             │ Contábil                                     │
│ versão • estado               │ Estado • versão • finalizado em/por           │
│                               │                                              │
│ [status] Fiscal               │ Itens / resumo                               │
│ versão • estado               │                                              │
│                               │ Ações: finalizar/reabrir quando autorizadas   │
│ ...                           │                                              │
│                               │ Delivery status quando capability existir     │
│                               │                                              │
│                               │ Esclarecimentos                               │
│                               │                                              │
│                               │ Histórico de versões/entregas                 │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

Desktop usa master-detail com `ResizableColumns`.

A lista de recipient packages pode usar `DataTableSection` quando houver densidade suficiente; cards são válidos para baixa cardinalidade.

## Wireframe — mobile

```text
PagePath
→ PageHero compacto
→ blockers/readiness
→ lista de recipient packages
→ selecionar pacote
→ detalhe full-width
   → BackLink
   → status/versão
   → itens
   → ações autorizadas
   → delivery status se implementado
   → esclarecimentos
   → histórico
```

No mobile:

- não manter split comprimido;
- destinatários aparecem como cards;
- retorno preserva competência e seleção/filtros;
- finalizar/reabrir fica próximo ao contexto correspondente;
- envio não aparece enquanto não houver capability runtime comprovada;
- histórico não perde legibilidade por largura.

## Recipient package

Cada pacote deve expor, quando disponível:

- destinatário;
- estado;
- versão corrente;
- blockers;
- `finalizedAt` / ator quando aplicável;
- `sentAt` / delivery state somente quando capability real existir;
- esclarecimentos abertos;
- relação com versões anteriores/complementos.

Não derivar:
- envio concluído a partir de finalização;
- conclusão mensal a partir de um único destinatário;
- delivery success por HTTP 200 isolado;
- ack obrigatório se contract não exigir.

## Finalização

A ação `Finalizar`:

- existe somente em `READY_TO_FINALIZE`;
- cria versão/snapshot;
- não envia;
- registra ator/timestamp;
- preserva inputs/version usados;
- é revalidada no backend.

Após sucesso:

```text
PACKAGE_FINALIZED
```

A UI deve usar linguagem inequívoca: “Finalizar pacote”, nunca “Concluir fechamento” ou “Enviar”.

## Reabertura antes do envio

Quando autorizada:

- exige motivo;
- versão finalizada anterior permanece read-only;
- cria working copy ou equivalente contratual;
- nova finalização cria nova versão;
- histórico mostra relação entre versões.

A UI não edita silenciosamente uma versão finalizada.

## Envio real

### Estado atual

```text
Q22 = PENDING_IMPLEMENTATION
E04 = PENDING_IMPLEMENTATION_CONFIRMATION
T04 = TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Antes de capability comprovada:

- não renderizar botão “Enviar” operacional;
- não escolher e-mail/Teams/pasta/download manual como fallback;
- não inventar proof of delivery;
- não inventar retry;
- Help não ensina ação inexistente.

Quando a capability existir, o slice de envio deve ser gated separadamente por contract físico + AuthZ + testes.

## Esclarecimentos

Após `PACKAGE_SENT`, um recipient package pode entrar em `WAITING_FOR_CLARIFICATION`.

A UI deve exibir:

- destinatário;
- status;
- questão/assunto quando contract fornecer;
- ator/timestamp;
- resolution state;
- histórico.

Resolver esclarecimento não reabre automaticamente pacote enviado.

Se uma correção de conteúdo for necessária, aplicar o fluxo de complemento/nova versão.

## Histórico

Eventos mínimos:

- `PACKAGE_VERSION_CREATED`
- `PACKAGE_FINALIZED`
- `PACKAGE_REOPENED`
- `PACKAGE_SENT`
- `CLARIFICATION_OPENED`
- `CLARIFICATION_RESOLVED`
- `PACKAGE_COMPLEMENT_CREATED`
- `MONTHLY_CLOSING_COMPLETED`

Usar timeline auditável.

Pacote enviado e versões antigas permanecem read-only.

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
  DetailFieldGrid,
  ReadOnlyField,
  ProgressTracker,
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
| readiness/blockers | `AlertQueue` / `StateBanner` |
| lifecycle visual | `ProgressTracker` quando ajuda a explicar state progression |
| master-detail | `ResizableColumns` |
| recipient list desktop | `DataTableSection` |
| recipient list mobile | `DataRecordCard` |
| status | `StatusBadge` |
| resumo do pacote | `DetailFieldGrid` / `ReadOnlyField` |
| seções | `SectionCard` |
| histórico | `Timeline` |
| confirmação | `ModalShell` + `ConfirmModalPanel` |
| feedback | `FloatingNoticeStack` |
| loading/empty | `LoadingState` / `EmptyState` |
| retorno mobile | `BackLink` |
| ajuda curta | `HelpTooltip` |

**DO NOT RECREATE:** master-detail, recipient table/cards, state chrome, lifecycle chrome, detail fields, timeline, modal/confirm, notices ou HelpTooltip.

Nenhum componente de “delivery/send” específico deve ser criado antes de T04 provar a necessidade real. Se o capability precisar de chrome reutilizável inexistente, avaliar contribuição ao `plugin-ui` após o contract físico.

## Estados de experiência

### LOADING

- primeira leitura usa loading do kit;
- não assumir zero recipient packages;
- não mostrar conclusão falsa.

### REFRESHING

- preservar conteúdo anterior quando seguro;
- indicar refresh;
- falha de refresh não apaga version/history previamente válida quando contract permitir.

### SUCCESS

- lista e detalhe refletem estado atual;
- cada recipient package mantém estado independente.

### EMPTY

Usar somente se o contrato provar ausência de pacotes aplicáveis.

`EMPTY != SOURCE_UNAVAILABLE`.

### PARTIAL

Quando uma source/recipient falhar:

- preservar siblings válidos;
- exibir coverage/source failure;
- não elevar competência para completa;
- não converter pacote desconhecido em “não aplicável”.

### UNAVAILABLE_SOURCE

- não transformar source indisponível em blocker resolvido;
- não produzir READY_TO_FINALIZE por ausência de dados;
- retry somente quando contract suportar.

### VALIDATION_ERROR

- preservar contexto;
- mostrar motivo da ação inválida;
- nenhuma transição otimista permanece se backend rejeitar.

### ERROR

- erro explícito;
- retry local quando seguro;
- sem vazamento técnico.

### FORBIDDEN — 403

Sem ACCESS ou sem resource ownership/context access:
- não renderizar dados protegidos;
- MANAGE não bypassa ACCESS.

### NOT_FOUND — 404

Pacote/competência inexistente ou inacessível conforme política do contract.

A página não decide enumeração localmente.

## AuthZ

Base:

```text
authenticated identity
AND effective_permission(controllership-finance.access)
AND resource_scope / ownership
AND business_rule
```

Para toda ação:

- backend reautoriza;
- UI não é authority;
- MANAGE não implica ACCESS;
- nenhum permission code por destinatário, finalização, envio ou esclarecimento;
- filial/unidade permanece dimensão de dado/contexto.

## URL / deep link / F5

Preservar semanticamente quando aplicável:

- competência;
- destinatário selecionado;
- versão;
- filtro/status;
- origem/return context seguro.

Nomes físicos de path/query params ficam para router/OpenAPI futuro.

F5 reconstrói contexto sem depender apenas de state frontend.

Nunca aceitar open redirect.

## Light / dark

Mesma árvore conceitual.

- tokens do Portal/`plugin-ui`;
- status não depende apenas de cor;
- PACKAGE_FINALIZED e PACKAGE_SENT precisam de labels inequívocos;
- nenhum CSS de componente do kit no MFE.

## Acessibilidade

Obrigatório:

- headings semânticos;
- status textual;
- lista/detalhe navegáveis por teclado;
- foco visível;
- modal com focus trap;
- confirmação com texto inequívoco;
- mudança de recipient package preserva lógica de foco;
- eventos de histórico legíveis por leitor de tela;
- ação bloqueada por ausência de capability não é exposta como botão enganoso.

## Help

Help contextual deve explicar:

- finalizar != enviar;
- versionamento;
- recipient packages independentes;
- reabertura antes do envio;
- PACKAGE_SENT imutável;
- complemento/correção pós-envio;
- esclarecimentos;
- regra de conclusão mensal;
- envio real somente quando capability estiver implementada.

Fonte canônica: [29-ajuda.md](./29-ajuda.md), seção da Central de Fechamento.

Se envio real continuar bloqueado, o manual não instrui canal/botão inexistente.

## RQ / aceite visual

### RQ-P5-01 — blockers impedem finalização

Aceite:
- READY_TO_FINALIZE só aparece quando rules aplicáveis permitem;
- blocker/source failure permanece visível;
- botão de finalizar não mascara blocker.

### RQ-P5-02 — finalizar cria versão, não envia

Aceite:
- ação rotulada “Finalizar pacote”;
- sucesso resulta em PACKAGE_FINALIZED;
- nenhuma delivery confirmation é mostrada como efeito da finalização.

### RQ-P5-03 — reabertura preserva versão

Aceite:
- motivo obrigatório;
- versão anterior read-only;
- working copy/nova versão distinta.

### RQ-P5-04 — pacotes independentes por destinatário

Aceite:
- ação/status de um destinatário não altera sibling;
- cada package possui versão/estado próprios.

### RQ-P5-05 — envio só com capability comprovada

Aceite:
- sem E04/T04 fechados não existe ação operacional de envio;
- nenhum canal é assumido;
- implementação futura exige contract/integration test.

### RQ-P5-06 — PACKAGE_SENT imutável

Aceite:
- edição direta rejeitada/indisponível;
- correção navega para complemento/nova versão.

### RQ-P5-07 — correção pós-envio preserva histórico

Aceite:
- nova entrega referencia a anterior;
- V1 permanece visível/read-only.

### RQ-P5-08 — conclusão mensal derivada

Aceite:
- todos recipient packages aplicáveis enviados;
- nenhum esclarecimento aberto;
- sem force completion.

### RQ-P5-09 — ack não bloqueia V1

Aceite:
- ausência de read/ack não impede conclusão quando demais regras passam;
- UI não inventa requisito de aceite.

### RQ-P5-10 — Help

Aceite:
- manual explica os invariantes;
- capacidade bloqueada não aparece como ação disponível.

## Testes futuros mínimos

### Positive
- pacote READY_TO_FINALIZE;
- finalizar e criar versão;
- reabrir com motivo antes do envio;
- novo finalize cria V2;
- siblings por destinatário independentes;
- esclarecer após envio quando capability estiver implementada;
- conclusão derivada somente com condições completas;
- F5 preserva recipient/version context.

### Sibling
- finalizar Fiscal não finaliza Contábil;
- enviar um destinatário não envia outro;
- esclarecimento de um pacote não muda sibling;
- reabrir um pacote não altera versão de outro.

### Negative
- sem ACCESS;
- MANAGE sem ACCESS;
- resource fora do scope;
- finalizar com blocker;
- editar versão finalizada sem reabertura;
- reabrir sem motivo;
- editar PACKAGE_SENT;
- force completion;
- source unavailable interpretada como pronta;
- enviar sem capability E04/T04;
- canal fictício/fallback manual;
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

## Inventários técnicos remanescentes

### Owners/sources de package

`TO_INVENTORY_BEFORE_IMPLEMENTATION`

Provar producer/consumer e source de cada dado material do package.

### E04 — canal real

`PENDING_IMPLEMENTATION_CONFIRMATION`

Confirmar canal, formato, comprovante, aceite, segurança e capability disponível.

### T04 — capability corporativa de envio

`TO_INVENTORY_BEFORE_IMPLEMENTATION`

Inventariar serviço de documentos/e-mail/tracking/retry/proof of delivery.

### Contract físico

`TO_INVENTORY_BEFORE_IMPLEMENTATION`

Endpoints, DTOs, version identifiers, recipient ids, delivery result, clarification contract e deep-link params entram no OpenAPI/router futuro.

Se evidence futura provar ausência/incompatibilidade de capability de envio, manter slice bloqueado e classificar conforme stop condition; não contornar com canal ad hoc.

## Gate documental P5

```text
PRODUCT_RULES_DEFINED       = PASS
INFORMATION_ARCH_DEFINED    = PASS
DESKTOP_DEFINED             = PASS
MOBILE_DEFINED              = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
UX_STATES_DEFINED           = PASS
AUTHZ_MODEL_DEFINED         = PASS
LIGHT_DARK_DEFINED          = PASS
A11Y_DEFINED                = PASS
DEEP_LINK_SEMANTICS_DEFINED = PASS
HELP_CONTRACT_DEFINED       = PASS
RQ_ACCEPTANCE_DEFINED       = PASS
PACKAGE_FINALIZATION_DESIGN = PASS
SEND_RUNTIME_CAPABILITY     = BLOCKED_WITH_EVIDENCE
PHYSICAL_BINDINGS           = TO_INVENTORY
IMPLEMENTATION_AUTHORIZED   = NO
```

P5 package/finalization está documentalmente pronto para brief técnico futuro com inventário. O slice de envio real continua bloqueado até E04/T04.
