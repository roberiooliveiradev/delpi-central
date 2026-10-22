# DÉLIA — F03-B Evidence: fila conversacional efêmera funcional

`TASK_ID=DELIA-UX-F03B-EPHEMERAL-CONVERSATION-QUEUE-IMPLEMENTATION-01`
Base auditada: `d2670b870b7deadc21e2705ca6c6eca2536fd5b6` (origin/main na reancoragem)
Autoridade primária: doc 122 §11 (direção do Product Master — fila efêmera em memória por conversa ativa)

## 1. Reuse Gate (confirmado contra HEAD)

- `EXISTING_EQUIVALENT=YES_PARTIAL` — envio de turno (`sendTurn`/`submitInteractionTurn`), estado local (`loading`, `requestMode`, `requestEpochRef`, `AbortController`) e superfície visual (`ConversationQueue`) já existiam; nenhum estado de fila, dispatcher ou affordance de enfileiramento existia.
- `REUSE_DECISION=EXTEND_EXISTING` — extensão do consumer DÉLIA + props aditivas no `MessageComposer`; zero novo endpoint, engine, scheduler ou storage.
- `QUEUE_VISUAL=REUSE` (`ConversationQueue` intacto), `TURN_TRANSPORT=REUSE` (`sendTurn`), `BACKEND_CHANGE=NO`, `PERSISTENCE=NONE`.

## 2. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `plugins/plugin-ui/src/components/composer/ComposerEnqueueButton.tsx` | novo — affordance "Adicionar à fila" (ListPlus, ActionButton type=button, HelpTooltip; emite intenção, nunca submit/API) |
| `plugins/plugin-ui/src/components/composer/MessageComposer.tsx` | props aditivas `onEnqueue`/`enqueueLabel`; textarea editável durante in-flight somente quando `onEnqueue` existe; Enter/form-submit enfileiram durante in-flight; hint honesto "Enter adiciona à fila"; enqueue renderizado antes de Stop/Send (Stop preservado) |
| `plugins/plugin-ui/src/components/composer/index.ts` | export `ComposerEnqueueButton` |
| `plugins/plugin-ui/src/components/composer/MessageComposer.test.tsx` | +5 testes de enqueue |
| `plugins/plugin-ui/src/styles/message-composer.css` | `.delpi-ui-message-composer__enqueue` + colapso do label <480px |
| `plugins/delia/src/queue/conversationQueue.ts` | novo — `useConversationQueue`: estado em memória, `takeNext` atômico contra ref (consumo antes do POST, anti-duplicação determinística) |
| `plugins/delia/src/queue/conversationQueue.test.ts` | novo — 6 testes unitários |
| `plugins/delia/src/App.tsx` | wiring: `turnsRef` (contexto fresco), `queuePaused`, `hasPendingConfirmation`, efeito de dispatch (idle && !paused && !pendingConfirmation → `takeNext` → `sendTurn`), `handleSubmit`/`handleEnqueue`, pausa em erro/stop, controle "Retomar fila", `ConversationQueue` alimentada por pendências reais |
| `plugins/delia/src/ui/DeliaComposer.tsx` | prop `onEnqueue` repassada; dictation liberado durante in-flight quando enqueue admitido (`busy=dictating || (inFlight && !onEnqueue)`) |
| `plugins/delia/src/index.css` | `.delia-queue-resume` (aviso + ação explícita de retomada) |
| `plugins/delia/src/conversationQueue.integration.test.tsx` | novo — 13 testes de integração contando POSTs reais |

Bug encontrado no QA real e corrigido: `setInput("")` na conclusão apagava texto digitado durante um turno enfileirado — o envio agora limpa o draft na admissão e restaura somente se o draft continuou vazio (§11 do doc 122, DraftRecovery).

## 3. Contrato de estado local

```ts
type PendingConversationRequest = { id: string; text: string; createdAt: number };
```

- IDs `local-queue-N` — manipulação visual, nunca autoridade backend.
- Texto congelado na admissão; nenhum token/credencial/AuthZ na estrutura.
- Zero `localStorage`/`sessionStorage`/IndexedDB/cookies/URL params (verificado no teste de unmount).
- Ciclo de vida: `SUBMITTED → QUEUED → (takeNext) DISPATCHING → concluído`; falha/abort/stop → `PAUSED_AFTER_ERROR` até retomada explícita; confirmação governada pendente → avanço bloqueado por derivação de `turns`.

## 4. Testes executados

| Camada | Resultado |
|---|---|
| `delia` vitest (suíte completa) | **320/320** — inclui 6 unitários do hook (FIFO, move bounds, remove, takeNext atômico, clear) + 13 integração (admissão sem POST extra, Enter enfileira, dispatch sequencial A→C→B após reorder, remoção do meio impede envio, contexto B contém resposta A, erro→pausa→Retomar, stop→pausa→Retomar, confirmação governada bloqueia, zero chamadas de gestão de fila, unmount descarta sem storage) |
| `plugin-ui` vitest | **2286/2286** — inclui 5 novos (lock sem `onEnqueue` preservado, textarea editável+enqueue com Stop primário, intenção sem submit, Enter enfileira, empty-draft desabilita) |
| Typecheck | PASS (delia `tsc --noEmit`, plugin-ui `tsc --noEmit`) |
| Build | PASS (plugin-ui ~32s, delia ~4s) |
| Federation | PASS (`verify-host-exports` OK) |

## 5. Browser QA — backend real (localhost, dev compose)

`page.route` adiciona 1.5s de delay ao **request** (resposta NDJSON real inalterada) para janela de observação determinística; POSTs contados via network listener com `input` capturado.

**Full-page (19/19):**
- Enqueue affordance visível durante resposta; draft fica editável
- B,C enfileirados → "2 solicitações aguardando", exatamente 1 POST
- Draft limpo após enqueue; reorder C acima de B
- Fila some quando vazia; POSTs = `[A, C, B]` (reordenação efetiva, sequencial)
- Remoção do item do meio → nunca despachado; demais em ordem `[D, E, G]`
- Stop → "Retomar fila" aparece, fila preservada, zero auto-dispatch, resume despacha pendente

**Companion Dock real (8/8):**
- Enqueue durante resposta, "2 aguardando", corpo expandido capado a 89px ≤ 100px
- 3 POSTs FIFO `[a, b, c]`, fila some
- Paridade: `?delia-demo-queue=pending` inerte no bundle de produção

**Mobile 360px (4/4):** fila visível, zero overflow horizontal, enqueue visível com label colapsado a ícone.

## 5b. QA autenticado de produção (2026-10-22)

Sessão real autenticada (`user`) em `https://minhadelpi.com.br/apps/delia`, headless Chrome, request-delay de 1.5–2.5s apenas como janela de observação (backend e payload reais):

**Drain + reordenação (11/11):** affordance de enqueue durante resposta, "2 solicitações aguardando", exatamente 1 POST durante in-flight, draft limpo após enqueue, controle de reordenação, fila some quando vazia, 3 POSTs na ordem **A → C → B** após reordenação.

**Stop → pausa → retomada (9/9):** enqueue visível, fila com pendente, Stop local → "Retomar fila" aparece, pendência preservada, zero auto-dispatch após stop, retomada despacha a pendência, fila esvazia e oculta, **zero chaves de fila em local/session storage**.

**Pausa por erro observada ao vivo:** uma resposta inválida do backend de produção (latência de modelo — residual já documentado no relatório 87) pausou a fila com pendências preservadas e zero auto-avanço — comportamento especificado, não defeito da fila.

`PRODUCTION_BROWSER_QA=PASS` (cenários determinísticos 20/20 + pausa-por-erro observada ao vivo em condição real de backend).

## 6. Limites documentados (intencionais do slice)

- Fila morre no unmount/reload/troca full-page↔Dock (mounts separados — `GlobalDeliaDock.tsx` `hostRef`); sem promessa de recuperação, multiaba ou continuidade entre dispositivos.
- `AbortController`/stop local ≠ cancelamento backend (documentado no código).
- Enfileirar ≠ autorizar: cada item despachado passa pelo mesmo `POST /interaction/turns` com AuthZ live e gates existentes; somente `MESSAGE` — confirmações/comandos governados nunca são enfileirados.
- `queued → running` é client-driven (efeito de dispatch); não existe drenagem backend — decisão consistente com doc 122 §11.

## 7. Estado final

```text
F03B_IMPLEMENTATION=EXECUTED
QUEUE_STORAGE=MEMORY_ONLY
QUEUE_SCOPE=ACTIVE_CONVERSATION_MOUNT
BACKEND_CHANGED=NO
PERSISTENCE_ADDED=NO
TESTS=PASS
PLAYWRIGHT=31/31 local (19 fullpage + 8 dock + 4 mobile) + 20/20 prod autenticado
PRODUCTION_DEPLOYMENT=EXECUTED (cff65bb63b; plugin-ui+delia via up-prod-sequential.sh --cpu)
PRODUCTION_BUNDLE_VERIFIED=YES (remoteEntry novo; local-queue/Retomar fila no chunk App-Bzh-kyGF.js)
PRODUCTION_BROWSER_QA=PASS (20/20 determinísticos + pausa-por-erro ao vivo)
PHASE_PROGRESSION=NONE
```
