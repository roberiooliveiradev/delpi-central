# DÉLIA — ConversationDraftRecovery · evidência de execução

**Task:** `DELIA-UX-CONVERSATION-DRAFT-RECOVERY-FULL-IMPLEMENTATION-01`
**Data:** 2026-10-21 · **Spec:** [102-conversation-draft-recovery](../../102-conversation-draft-recovery-future-product-ux-specification.md)
**BASE_HEAD:** `670fc65687423e65f8af47b89b52095dcb72c954`

## 1. Escopo entregue

Recuperação local e transitória do último rascunho explicitamente limpo: o usuário clica em **Limpar texto** (botão `ComposerClearDraftButton` existente), recebe o aviso compacto **"Rascunho limpo — Desfazer"** ancorado abaixo do composer e pode restaurar o texto exato em até ~8 s. Sem persistência, sem backend, sem recuperação de mensagens enviadas e sem restauração após reload.

## 2. Reuse Gate

```text
EXISTING_EQUIVALENT = YES_PARTIAL
REUSE_DECISION      = EXTEND_EXISTING
NEW_COMPOSER        = NO
NEW_BACKEND         = NO
NEW_STORAGE         = NO
```

- `FloatingNoticeStack` (plugin-ui) foi avaliado e **rejeitado** para este caso: é portal fixed top-right (spec quer aviso junto ao composer) e não pausa countdown em hover/focus (exigência de acessibilidade do §4.2).
- `EditorChromeNotice` (plugin-ui, inline, `role="status"`, action tipada) foi adotado como padrão compartilhado — único acréscimo no remote: export explícito + proteção em `verify-host-exports.mjs` (host-only export contra tree-shake da federation).
- `ComposerClearDraftButton`/`MessageComposer` inalterados; seam nova apenas em `DeliaComposer` (`onClearDraft(clearedValue)`).

## 3. Owners e contrato

| Camada | Owner | Responsabilidade |
|---|---|---|
| Apresentação, a11y, action "Desfazer" | `plugin-ui` (`EditorChromeNotice`) | render-only; zero acesso a estado da DÉLIA |
| Snapshot, epoch, timer, invalidação, gate de restore | `plugins/delia` (`useDraftRecovery` + `App`) | estado transitório em memória |

Contrato efetivo (reconciliado com o componente existente): `EditorChromeNoticeProps` (`tone`, `actionLabel="Desfazer"`, `onAction`, `actionProps`) + handle do hook `{visible, capture, undo, invalidate, pause, resume}` — equivalente ao `DraftRecoveryNoticeProps` ilustrativo da spec.

## 4. Arquivos alterados

```text
plugins/plugin-ui/src/index.ts                          (+8  export explícito)
plugins/plugin-ui/scripts/verify-host-exports.mjs       (+1  proteção host-export)
plugins/plugin-ui/src/styles/editor-chrome.css          (+8  :focus-visible no action)
plugins/delia/src/draft/draftRecovery.ts                (novo hook — estado/timers/epoch)
plugins/delia/src/ui/DeliaComposer.tsx                  (prop onClearDraft(clearedValue))
plugins/delia/src/App.tsx                               (wiring + notice no footer + invalidações)
plugins/delia/src/index.css                             (+12 .delia-draft-recovery)
plugins/delia/src/draft/draftRecovery.test.tsx          (10 testes de hook)
plugins/delia/src/draft/draftRecoveryApp.test.tsx       (5 testes de integração App)
docs/.../102-…specification.md                          (autorização + §8 resultado)
docs/.../evidence/execution-ledger.md                   (§6.360)
```

## 5. Comportamento verificado

| Regra | Resultado |
|---|---|
| Snapshot só na limpeza explícita (nunca por digitação) | PASS — `capture()` só chamado via `onClearDraft` |
| Rascunho vazio não gera candidato | PASS — botão não renderiza com `value=""` + `capture("")` no-op |
| Restauração exata (espaços, quebras, Unicode, longo) | PASS — string integral, `setInput` direto, caret no fim |
| Um candidato por vez; novo clear substitui | PASS — teste `replace` hook + App |
| Timeout ~8 s descarta | PASS — `DRAFT_RECOVERY_DISMISS_MS=8000` |
| Hover/focus pausa contagem | PASS — `pause()`/`resume()` com tempo restante real |
| Texto novo após limpar invalida (nunca sobrescreve/mescla) | PASS — efeito sobre `input !== ""` |
| Envio / epoch / request-mode não-idle invalida | PASS — `requestEpochRef` + efeito sobre `loading/requestMode` |
| Unmount/reload limpa timers e snapshot | PASS — cleanup no hook; zero persistência |
| Clique duplo restaura no máx. 1× | PASS — consume-atômico antes de `onRestore` |
| Foco retorna ao composer | PASS — `focus()` + caret ao fim via rAF |
| Zero `POST /interaction/turns` no ciclo | PASS — contagem de requests no QA |
| Sem storage/telemetria de conteúdo | PASS — nenhum `localStorage`/`IndexedDB`/fetch no diff |

## 6. Testes executados

```text
Vitest delia     = 291/291 (24 files) — incl. draftRecovery 10/10 + App integration 5/5
Vitest plugin-ui = 335/335 dirigido (layout + composer)
Typecheck        = PASS delia + plugin-ui
Build            = PASS plugin-ui (33s) + delia (4s)
Federation       = verify:host-exports OK — EditorChromeNotice no remoteEntry
```

## 7. Browser QA (stack local, Chrome headless, usuário e2e)

```text
BROWSER_QA = 33/33 PASS
```

- **Dock 420×900:** clear → aviso → Desfazer → restauração exata (Unicode + multiline), foco no composer, 0 turnos.
- **Expiração:** aviso some ~8,7 s; Desfazer indisponível depois.
- **Pausa por hover:** aviso sobrevive a 10 s com hover; expira ~3 s após saída do pointer (tempo restante).
- **Texto novo:** digitar após limpar remove o aviso e preserva o novo texto; Desfazer ausente.
- **Substituição:** segundo clear → Desfazer restaura o segundo rascunho.
- **Overlap:** o aviso não cobre nenhum botão do composer (Enviar, ditado, Limpar); Enviar permanece visível.
- **Página completa** `/apps/delia`: ciclo completo idêntico.
- **Dock baixo (360×450):** sem overflow horizontal; composer utilizável.
- **Zoom 200% equivalente** (viewport 840×450 na página — `body.zoom` sintético colapsa o dock, artefato já conhecido do F02-A-R3): aviso legível, Desfazer funcional, sem overflow.
- **Dark theme** (`colorScheme: dark`): aviso renderiza com tokens escuros.
- **Teclado:** focus em Desfazer pausa contagem; Enter restaura.
- **Regressões:** 4 starter suggestions no Dock alto (F02-A-R2/R3 preservado); VD-F05 "Ditar mensagem" presente; composer/lifecycle intactos.

Screenshots: `C:/temp/delia-qa/shots-draft-recovery/` (dock-notice.png, dock-notice-420.png, fullpage.png, dock-dark-notice.png, dock-zoom200eq-notice.png).

## 8. Limites confirmados

Sem mudanças em backend/Core/Keycloak/MCP; sem controle permanente na toolbar; sem atalho de teclado; sem `AbortController` novo; sem auto-snapshot por digitação/navegação; sem sessão cross-tab/device. `PRODUCTION_BROWSER_QA` depende de sessão autenticada real em produção.

```text
STATUS = IMPLEMENTED_TESTED_LOCAL_QA_PASS
PHASE_PROGRESSION = NONE
```

## 9. Deploy em produção (2026-10-21)

```text
PROD_HOST              = operador@srv-api (192.168.1.237)
PROD_CHECKOUT          = ~/projetos/delpi-central (main, pull --ff-only até 54d2b47fb0)
PROD_SCRIPT            = infra/scripts/up-prod-sequential.sh --cpu --build plugin-ui delia
DEPLOYED_SHA           = 54d2b47fb0d27ed1932059a56f7edf510551272e
CONTAINERS             = delpi-delia + delpi-plugin-ui recriados; delia-api/backend não tocados
BUNDLE_CHAIN           = /apps/delia/assets/remoteEntry.js (200)
                         -> __federation_expose_App-D-Qnq36X.js
                         -> App-Dj41tMIx.js contém "Rascunho limpo"/"Desfazer limpeza do rascunho"
PLUGIN_UI_EXPOSE       = __federation_expose_Index-BVz5t-Qo.js contém EditorChromeNotice
PRODUCTION_BROWSER_QA  = PENDING_USER_VERIFICATION (sem sessão autenticada de teste em produção)
```
