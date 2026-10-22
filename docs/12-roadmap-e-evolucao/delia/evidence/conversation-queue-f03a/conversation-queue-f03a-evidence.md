# F03-A — ConversationQueue: implementação visual, integração e evidência

`TASK_ID=DELIA-UX-F03A-CONVERSATION-QUEUE-FRONTEND-IMPLEMENTATION-01`
`Spec:` doc 71 §§3–6, 11, 13 (CQ-V01–CQ-V10)
`Data:` 2026-10-22

## Escopo executado

Componente compartilhado **`ConversationQueue`** em `plugins/plugin-ui` — superfície compacta, recolhida por default, posicionada imediatamente acima do composer, render-only. Integração na DÉLIA preparada para um contrato real de fila; hoje produção passa `items=[]` e a superfície não renderiza (CQ-V01). **Nenhum** scheduler, storage, fila React, execução sequencial ou autorização foi criado.

## Reuse gate

| Decisão | Valor |
|---|---|
| EXISTING_EQUIVALENT | YES (primitivas existentes cobrem header/linha/ícone/tooltip/controles) |
| REUSE_DECISION | EXTEND — composição de primitivas do kit, zero duplicação |
| Reuso efetivo | `IconButton`, `HelpTooltip`, tokens `--delpi-ui-*`/surface, padrão `ConversationScrollNavigator` (render-only consumer) |
| Descartado | `AlertQueue` (fila de avisos transientes, semântica distinta); `TaskItemsTable`/`TaskWorklistSection` (worklist densa, outro contexto); drag-and-drop (não requerido) |

## Contrato adotado

`ConversationQueueItem`: `id` opaco, `label` (consumer), `ordinal`, `status` `"queued"|"blocked"`, `reason?`, `canMoveUp/canMoveDown/canRemove`.
`ConversationQueueProps`: `items`, `expanded?`, `loading?`, `unavailable?`, `error?`, `onExpandedChange?`, `onMoveUp?/onMoveDown?/onRemove?`, `className?`.

Callbacks = intenções apenas; elegibilidade vem por props; controles desabilitados quando não admitidos; nenhuma transição é afirmada pelo clique.

## Arquivos

- `plugins/plugin-ui/src/components/conversation/ConversationQueue.tsx` (novo)
- `plugins/plugin-ui/src/styles/conversation-queue.css` (novo; tokens, caps 180/110px, reduced-motion)
- `plugins/plugin-ui/src/styles.css` (+@import), `src/index.ts` (+export + tipos)
- `plugins/plugin-ui/scripts/verify-host-exports.mjs` (+`ConversationQueue` requerido)
- `plugins/plugin-ui/src/components/conversation/ConversationQueue.test.tsx` (novo, 11 testes)
- `plugins/delia/src/demo/queueDemo.ts` (novo — fixture QA isolada atrás de `isDemoAllowed()` + `?delia-demo-queue=`)
- `plugins/delia/src/demo/queueDemo.test.tsx` (novo, 10 testes: resolver + integração App)
- `plugins/delia/src/App.tsx` (composição acima do composer; callbacks somente quando fixture admitida)
- `plugins/delia/src/index.css` (margem + cap Dock `.global-delia-dock` = 100px)
- `plugins/delia/src/ui/DeliaComposer.test.tsx` (fix pré-existente upstream: `resolveFn` narrowing → `undefined` em vez de `null`; sem alteração semântica — desbloqueia typecheck quebrado no HEAD de base)

## Gate da fixture

`?delia-demo-queue=pending|one|blocked|loading|error|unavailable` só resolve quando `import.meta.env.DEV` **ou** `VITE_DELIA_DEMO=1` (build arg canônico). Bundle de produção tem o gate fechado — provado na rodada de paridade: param presente → `queue.count===0`, sem banner demo.

## Testes

| Gate | Resultado |
|---|---|
| Vitest plugin-ui | 2281/2281 PASS (incl. 11 novos) |
| Vitest delia | 301/301 PASS (incl. 10 novos; 3 flakes de contenção no 1º run paralelo, rerun isolado limpo) |
| Typecheck | PASS delia + PASS plugin-ui (tsc --noEmit) |
| Build | PASS plugin-ui + delia |
| Module Federation | PASS — `verify-host-exports` lista `ConversationQueue` no expose Index |
| Playwright/browser | 77/77 PASS (60 fixture + 7 Dock real + 10 paridade) |

## Browser QA (Chrome headless, usuário e2e local)

**Rodada fixture** (imagem `infra-delia` com `--build-arg VITE_DELIA_DEMO=1`):

- Full-page 1440×900: header "3 solicitações aguardando" recolhido com preview "Próxima:", `aria-expanded=false`; expansão → 3 linhas, ordinais 1–3, controles por elegibilidade (↑ desabilitado no 1º, ↓ no último); reordenação local da fixture; remove → "2 solicitações aguardando"; colapso; **0 POST** `/interaction/turns`.
- Teclado: Enter expande, Space colapsa.
- Estados: `loading` ("Carregando fila…"), `error` (role=alert), `unavailable`, `blocked` (badge "Bloqueado — aguardando a solicitação anterior" + controles desabilitados), `one` (singular).
- Dock real (`.global-delia-dock`, 1280×900): fila no Dock, corpo capado em **100px** com scroll interno, composer visível, sem overflow.
- 420/360/320/375px: sem overflow horizontal, corpo ≤110px com scroll, composer visível, fila diretamente acima.
- Dark: fundo opaco `rgb(15,17,21)`; zoom ~200%: sem overflow; reduced-motion: sem transições.
- Regressões no fixture: composer, mic VD-F05, Undo2 draft-recovery, starters — intactos.

**Rodada paridade** (imagem sem `VITE_DELIA_DEMO` — paridade de produção):

- `?delia-demo-queue=pending` → inerte: sem fila, sem banner demo (10/10).
- Ciclo completo draft→clear→Undo2→restore; mic; zero auto-POST.

Screenshots: `C:/temp/delia-qa/shots-f03a/` (a1-collapsed, a2-expanded, b-*, c-*, d-*, e-dock-*, f-parity-empty).

## Veredito CQ-V01–V10

| Critério | Resultado |
|---|---|
| CQ-V01 sem pendências → sem fila/espaço | PASS (fixture sem param + paridade) |
| CQ-V02 header recolhido + contagem | PASS |
| CQ-V03 expansão/título/truncamento/controles | PASS |
| CQ-V04 keyboard + reorder elegível, sem drag | PASS |
| CQ-V05 loading/unavailable/error/blocked honestos | PASS |
| CQ-V06 altura/scroll, composer nunca encoberto | PASS (100/110/180px) |
| CQ-V07 full-page/Dock/320–420/zoom/temas/reduced-motion | PASS |
| CQ-V08 regressões DraftRecovery/Starters/ditado/envio/timeline | PASS |
| CQ-V09 nada fabricado (fila/Work/persistência/scheduler/AuthZ) | PASS — fixture só em bundle QA |
| CQ-V10 vitest/typecheck/build/federation/evidência no SHA testado | PASS |

## Limites honestos

- `BACKEND_QUEUE_CONTRACT=TO_INVENTORY` — nenhum contrato operacional de fila existe; este slice **não** implementa execução, scheduler, persistência nem "executar agora".
- Produção: fila invisível até um owner publicar pendências autorizadas — comportamento correto por CQ-V01.
- Fase/CP/RQ inalterados; entrega é frontend bounded.

## Deploy

- Commit `6efcd12915` em `main`; deploy via `up-prod-sequential.sh --cpu --build plugin-ui delia` no host `192.168.1.237` (checkout `~/projetos/delpi-central`, pull --ff-only).
- Containers `delpi-plugin-ui`/`delpi-delia` recriados saudáveis.
- RemoteEntry plugin-ui: `__federation_expose_Index-C_iDYTdG.js` exporta `ConversationQueue`; CSS `style-CJxVwzqB.css` contém `.delpi-ui-conversation-queue`.
- Bundle delia `App-F7-bkdoP.js` contém a wiring `delia-conversation-queue` + gate `delia-demo-queue`; servido via gateway `https://minhadelpi.com.br/apps/delia` (200, asset verificado).
- Bundle de produção compilado **sem** `VITE_DELIA_DEMO` → fixture inerte; superfície ausente (CQ-V01) — comportamento correto, não falha.
- QA funcional autenticado em produção: `PENDING_USER_VERIFICATION`.

```text
F03A_VISUAL=EXECUTED
PRODUCTION_QUEUE_SURFACE=ABSENT_BY_DESIGN
QA_FIXTURE=GATED(VITE_DELIA_DEMO+param)
QUEUE_EXECUTION=NOT_IMPLEMENTED
TESTS=PASS / QA=PASS_77_77
DEPLOYED_SHA=6efcd12915
```
