# 95 — DÉLIA | ConversationStopResponse — Aparência, funcionalidade e limites de interrupção

**Data:** 2026-10-16  
**Natureza:** especificação documental de produto/UX e integração futura; **não altera runtime nem autoriza implementação nesta task**.  
**Produto:** DÉLIA standalone — Continuous Operational Intelligence. Não reutilizar runtime, services, migrations ou frontend de Minha DELPI Chat.  
**Owner visual:** `plugins/plugin-ui`; **consumer e dono da requisição de interação:** `plugins/delia`.  
**Estado:** `PRODUCT_UX_SPEC_DOCUMENTED / IMPLEMENTATION_NOT_STARTED / RUNTIME_UNCHANGED / CANCEL_OUTCOME_NOT_PROVEN`.  
**Autoridade:** reancorar HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs de conversation/activity → ledger. Esta spec não promove CP, fase ou autorização.  
**HEAD observado na elaboração:** `88edaf9f7244e15c3f9b52873631ae3a52715920`; revalidar na futura execução.

## 1. Objetivo e princípio de produto

Introduzir controle **Interromper resposta** na área do `MessageComposer` enquanto uma requisição conversacional cancelável estiver em andamento. Permitir interromper a espera/recepção de conteúdo e recuperar o compositor para uma nova interação, preservando a honestidade sobre o que foi — ou não foi — interrompido.

**Três conceitos diferentes:**

1. `STOP_UI`: intenção explícita do usuário de parar de aguardar a resposta na interface.
2. `ABORT_TRANSPORT`: cancelamento local da conexão/request, quando houver `AbortController` aplicável.
3. `CANCEL_BACKEND_EXECUTION`: término efetivo do processamento/ação no servidor ou provedor, **não comprovado por abort HTTP**; exige contrato e postcondition autoritativos.

Nunca exibir "operação cancelada" ou "execução interrompida" só porque `AbortController.abort()` retornou. `PREPARE != ACT`, cancelamento de leitura != rollback de escrita.

## 2. Inventário factual mínimo (main observado)

- `plugins/plugin-ui/src/components/composer/MessageComposer.tsx`: componente render-only com textarea controlada, `onSubmit`, `loading`, `disabled`, `secondaryActions`, `ComposerSendButton`, contagem e helper; impede submit duplicado enquanto `loading`. Não faz fetch.
- `plugins/plugin-ui/src/components/composer/ComposerSendButton.tsx`: usa `ActionButton`, ícones Lucide `SendHorizontal`/`Loader2`, `type="submit"`, spinner indeterminado e disabled durante loading.
- `plugins/delia/src/ui/DeliaComposer.tsx`: wrapper fino de `MessageComposer`; recebe `loading` e repassa draft/callback; não deve receber subcomponentes primitivos novos.
- `plugins/delia/src/App.tsx`: possui `abortRef`, `AbortController` em `sendTurn`, `signal` passado a `submitInteractionTurn`, detecção de `AbortError` e cleanup ao desmontar. Também possui fluxo de demonstração assíncrono distinto; **abortRef não prova cancelamento do demo mode**.
- A presença de `abortRef` **não prova** que a requisição inteira, streams, especialistas, PREPARE/ACT ou infraestrutura backend sejam canceláveis.

**Reuse gate:** `EXISTING_EQUIVALENT = YES` para `MessageComposer`/`ComposerSendButton` e abort local; `REUSE_DECISION = EXTEND` para a apresentação de stop e ligação ao transporte atual. `EXISTING_EQUIVALENT = TO_INVENTORY` apenas para um comando backend de cancelamento com confirmação — não inferir que exista, nem criá-lo por conveniência.

## 3. Aparência completa — direção vinculada a UX, não implementação

### 3.1 Anatomia

```text
Estado idle / pronto
+--------------------------------------------------------+
| Pergunte à DÉLIA...                                    |
|                                                        |
| [ações secundárias quando contratadas]     [Enviar ↗] |
+--------------------------------------------------------+

Estado responding / cancelável
  [DÉLIA] Preparando resposta... (ActivityViewer existente)
+--------------------------------------------------------+
| [rascunho preservado; bloqueio do envio durante request]|
|                                                        |
| [ações secundárias]                [■ Interromper]     |
+--------------------------------------------------------+

Estado stopping / pedido local de interrupção
+--------------------------------------------------------+
| [rascunho preservado]                                  |
|                                     [Interrompendo…]   |
+--------------------------------------------------------+

Estado após abort local confirmado no cliente
+--------------------------------------------------------+
| [rascunho preservado / editável]                [Enviar]|
+--------------------------------------------------------+
  [Aviso neutro opcional: "Você parou de aguardar a resposta."]
```

Representação ilustrativa. O controle primário ocupa **o mesmo slot de ação do ComposerSendButton**; não empilhar botão Stop ao lado de Enviar ativo.

### 3.2 Especificação visual

- Ícone Lucide `Square` preenchido ou quadrado central inerte, visualmente reconhecível; o label textual **Interromper resposta** deve permanecer disponível a leitores de tela. Em largura estreita, label pode colapsar para icon-only mantendo `aria-label`/tooltip.
- Preservar a forma, radius, escala, tokens, altura e alinhamento vertical do botão primário já existente; não alterar o tamanho do compositor ao alternar estados.
- Fundo/contraste coerentes com `ActionButton` e tokens `--delpi-ui-*`, com estado de interrupção claramente distinto do envio; não utilizar cor de erro/danger para sugerir falha de operação.
- Hover discreto, `focus-visible` contrastante, pressed, disabled e stopping legíveis. Alvo de toque adequado (preferir >= 40–44px conforme kit/host).
- Spinner de stop somente enquanto houver transição local real; não representar progresso numérico, cancelamento remoto ou sucesso não confirmado.
- Sem layout shift, overlays globais, modal de confirmação para simples read abort ou barra de progresso fictícia.
- Integração na toolbar inferior do `MessageComposer`, alinhada ao mesmo lugar do botão Enviar. O compositor permanece junto ao footer fixo do `ConversationWorkspace`.
- Igual em full-page e Companion Dock; CSS no `plugin-ui` com container queries, 320/420px, zoom 200%, light/dark, fontes grandes e `prefers-reduced-motion`.

## 4. Máquina de estados funcional (target, contrato futuro)

| Estado | Botão | Submit | Intenção e transição |
|---|---|---|---|
| `idle` | Enviar (habilitado apenas com draft válido) | Permitido pelo contrato atual | onSubmit por clique/Enter explícito |
| `responding_cancelable` | Interromper resposta | Desabilitado | onStop explícito → stopping |
| `responding_not_cancelable` | Estado de espera sem falsa affordance de stop | Desabilitado | Somente monitorar; não oferecer cancelamento sem contrato |
| `stopping` | Interrompendo… (inativo) | Desabilitado | Uma única intenção, aguardar resolução/fechamento local |
| `stopped_local` | Enviar | Permitido após reconciliação do cliente | Sem alegar cancelamento do servidor |
| `completed` | Enviar | Permitido | Resultado recebido e reconciliado |
| `failed` | Enviar conforme guardas | Conforme estado de erro | Exibir erro honesto, preservando draft |

Um `loading` genérico não significa necessariamente `cancelable`. O modo de stop deve vir de estado controlado pelo consumer e política/capability legítima. Evitar que `stopping` fique preso indefinidamente: o fechamento local e limpeza de recursos devem ser determinísticos; status backend permanece desconhecido quando não há confirmação.

## 5. Comportamento e UX

### 5.1 Interrupção por intenção explícita

- Clique/tap/ativação por teclado no botão -> `onStop` **uma vez**; nunca `onSubmit`.
- No `plugins/delia`, reaproveitar a instância correta de `AbortController` para a solicitação corrente; requisições antigas não podem parar ou alterar o estado de uma solicitação posterior.
- Guardar identidade/epoch de request para evitar **race conditions**: resposta tardia de request interrompida não adiciona turnos, atividade, confirmações nem limpa draft de request novo.
- Cancelamento do fetch/stream não implica rollback, outcome remoto ou não execução de writes. Para casos com operação material em curso, o botão não pode ser oferecido como garantia de cancelamento; contratos específicos e pós-condição autoritativa serão necessários.
- Falhas de abort local, conclusão simultânea com Stop, desmontagem e repetição do clique devem resultar em estados consistentes e sem claims falsos.
- Manter histórico de turnos **já aceitos e exibidos**; não apagar resultados anteriores. Partial stream / activity observada só pode ser preservada se houver projeção/contrato que distinga parcial de fato final; não transformar conteúdo incompleto em FACT.
- Preserve `draft != send`: manter rascunho digitado, salvo quando o usuário enviou explicitamente e o contrato de envio limpou-o com sucesso. Em interrompidos, não fabricar uma mensagem final da DÉLIA.
- Após interrupção local, permitir novo turno quando o estado cliente estiver reconciliado e as regras de backend/governança permitirem.

### 5.2 Teclado e acessibilidade

- Enquanto idle: Enter envia / Shift+Enter quebra linha / IME não envia, conforme compositor atual.
- Enquanto responding: Enter **não envia** (nem dispara stop); Stop só com foco e Enter/Space no botão, sem interceptação global de Escape.
- `aria-label="Interromper resposta"`, `type="button"` no Stop (nunca submit), `disabled` verdadeiro em stopping, estados de carregamento sem `aria-live` repetitivo.
- A mudança do botão Enviar para Stop não deve roubar foco inesperadamente; teclado/touch/dispositivos assistivos continuam operáveis.
- Se houver aviso pós-stop, deve ser neutro e não competir com `ConversationError`/`ActivityViewer`.

### 5.3 Segurança e autorização

- O `plugin-ui` é puramente presentational: não chama APIs, não armazena tokens, não implementa `AbortController` de negócio ou decisão de segurança. Pode receber `mode`, `canStop`, `onStop`, loading/labels controlados.
- A DÉLIA MFE controla transporte da sua requisição; backend/Core/Domain/Policy continuam autoridades reais.
- Nenhum `MCP result`, contexto de página, JWT, metadata ou output do modelo dá permissão de cancelamento de processo remoto.
- `read != write`; `PREPARE != ACT`; `abort_transport != cancel_backend_execution`; `technical_success != verified_business_outcome`.
- Não expor proposal handle bruto, segredo, body integral ou IDs de providers em logs/telemetria comuns.

## 6. Contrato de UI previsto (ilustrativo, não congelado)

Extensão preferida dos componentes existentes em `plugin-ui`: `MessageComposer` e, se necessário, `ComposerSendButton`/composição adjacente no mesmo kit.

```ts
type ComposerRequestMode =
  | "idle"
  | "responding_cancelable"
  | "responding_not_cancelable"
  | "stopping";

type MessageComposerStopProps = {
  requestMode?: ComposerRequestMode;
  onStop?: () => void;          // intenção controlada; não cancelamento backend
  stopLabel?: string;            // "Interromper resposta"
  stoppingLabel?: string;        // "Interrompendo…"
};
```

O shape é referência conceitual. Revalidar types/props, compatibilidade com consumers atuais, event handling e test doubles antes de implementação. Não criar `ConversationStopResponse` como uma segunda toolbar desnecessária; nomeia a **capability visual** e pode se materializar como extensão/composição de `MessageComposer` no `plugin-ui`.

**Contrato de integração futuro:** `plugins/delia/src/ui/DeliaComposer.tsx` continua wrapper fino e propaga `requestMode/onStop` recebidos da `App`; `App` reutiliza `abortRef` e controla request identity/races. `@delpi/plugin-ui/index` expõe os tipos/componentes necessários e o gate de Federation preserva exports host-only.

## 7. Casos adversariais e testes futuros

1. Idle: Enviar só com texto válido; Enter/Shift+Enter/IME atuais preservados.
2. Responding cancelável: Enviar não acionável, Stop acessível e único.
3. Responding não cancelável: sem botão Stop enganoso; loading honesto.
4. Stop durante request: AbortController da request corrente chamado, sem submit extra.
5. Clique duplo/triplo Stop: exatamente uma intenção, nenhuma nova request.
6. Resultado chega após Stop: resposta tardia não repopula turnos, ActivityViewer, error ou draft.
7. Stop concorre com conclusão e início de novo turno: request anterior não cancela a nova.
8. Fetch/stream abortado, backend não confirmado: copy neutral, sem claim de operação remota cancelada.
9. Fallback sem suporte a cancelamento, erro de abort, desmontagem e modo demo: estados estáveis; demo exige cancelamento explícito próprio se houver timers pendentes.
10. Full-page + dock: mesmo composer e controle, sem mudança de altura relevante, overflow, scroll jump, keyboard traps.
11. Tema claro/escuro, 320/420px, zoom 200%, reduced-motion, screen reader.
12. Regressões de `MessageComposer`, `ComposerSendButton`, `DeliaComposer`, build/federation e testes integração DÉLIA.
13. Segurança: nenhum efeito material/ACT, idempotência ou postcondition de backend presumidos do abort local.

**Evidência requerida quando executar:** testes red/green no SHA, typecheck, build plugin-ui + DÉLIA, `verify-host-exports`, `verify:federation`, browser QA real e report. `TEST_NOT_RUN` até execução factual; implementação não se autoaceita.

## 8. Fora de escopo e regras de ativação

**Esta task documental não cria código, CSS, testes, deploy, endpoints, scheduler ou mudanças no ledger/fase.** Não acrescentar hotkey global Escape ou botão "Cancelar operação" para writes.

O botão poderá ser integrado para interromper apenas **recepção/espera local de uma resposta cancelável**, e nunca ser reutilizado como cancelamento governado de PREPARE/ACT ou confirmação do owner. Qualquer interrupção remota controlada exige owner, contrato idempotente/seguro, errors, audit e authoritative postcondition.

**Próxima task, somente mediante autorização:** bounded frontend `REANCHOR → REUSE/EXTEND → RED TESTS → IMPLEMENT PLUGIN-UI → IMPORT DELIA → TEST → BUILD/FEDERATION → BROWSER QA → DOC/LEDGER FACTUAL → COMMIT/PUSH → INDEPENDENT REVIEW`.

```text
SPEC_STATUS = DOCUMENTED
EXISTING_EQUIVALENT = YES (COMPOSER + ABORT_LOCAL)
REUSE_DECISION = EXTEND
BACKEND_CANCEL_EQUIVALENT = TO_INVENTORY
RUNTIME_IMPLEMENTATION = NOT_STARTED
BACKEND_CANCEL_OUTCOME = NOT_PROVEN
TESTS = TEST_NOT_RUN
DEPLOY = NOT_AUTHORIZED
PHASE_PROGRESSION = NONE
NEXT = BOUNDED_FRONTEND_IMPLEMENTATION_IF_AUTHORIZED
```

## 9. Registro de implementação frontend candidata (2026-10-16)

**Task:** `DELIA-UX-CONVERSATION-STOP-RESPONSE-PLUGIN-UI-01`.
O Product Master autorizou a implementação frontend nesta conversa. Composição visual implementada em `plugin-ui` por extensão de `MessageComposer`, reutilizando `ComposerSendButton` e adicionando `ComposerStopButton` no mesmo slot da toolbar. `DeliaComposer` apenas repassa props, e `App` gerencia AbortController com epoch por request. Stop é oferecido exclusivamente para MESSAGE sem confirmação/ACT, não para decisões governadas. Requisições tardias/atividade depois do abort não devem alterar estado. O stop local não confirma cancelamento remoto.

**Evidência:** arquivos de código e testes comprometidos no GitHub. Sem ambiente de build/runner conectado, testes, typecheck, build, federação e QA de navegador seguem `TEST_NOT_RUN`; aceite independente `PENDING`. Nenhuma fase/CP foi promovida. **A entrega ainda depende de validação real**, inclusive concorrência entre requests, demo e browser dock/full-page.
