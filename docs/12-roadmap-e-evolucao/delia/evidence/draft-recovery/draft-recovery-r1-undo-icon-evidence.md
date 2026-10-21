# Draft Recovery R1 — Undo2 na toolbar do composer (evidência)

**TASK_ID:** `DELIA-UX-DRAFT-RECOVERY-R1-UNDO-ICON-TOOLBAR-01`
**Data:** 2026-10-21
**Spec:** `docs/12-roadmap-e-evolucao/delia/102-conversation-draft-recovery-future-product-ux-specification.md` §9
**Base de execução (reanchor):** `origin/main` = `ddc6dccaf9454d9f138985a943d8e2b9afc07e34`

## Escopo

Substituir a barra horizontal "Rascunho limpo — Desfazer" (`EditorChromeNotice` abaixo do
composer) por um único ícone temporário `Undo2` dentro da toolbar existente do composer.
Apresentação apenas — `useDraftRecovery` e todas as proteções permanecem intactos.

## Reuse gate

- `EXISTING_EQUIVALENT=YES` — `IconButton` + `HelpTooltip` (ambos já exportados pelo
  remoteEntry do plugin-ui e já consumidos pelo próprio `DeliaComposer`).
- `REUSE_DECISION=EXTEND_EXISTING` — nova prop `draftRecoveryAction?: ReactNode` no
  `DeliaComposer`, injetada no slot `secondaryActions` do `MessageComposer`.
- `NEW_COMPONENT=NO`, `NEW_TOOLBAR=NO`, `NEW_NOTIFICATION_SYSTEM=NO`, `NEW_BACKEND=NO`.
- `EditorChromeNotice` (componente, export federado, estilos) preservado para outros
  consumidores; apenas a renderização dedicada ao DraftRecovery saiu do App.

## Decisão de implementação relevante

O ícone é renderizado **antes** do gatilho de ditado no `secondaryActions`
(`{draftRecoveryAction}{trigger}`). Motivo: o botão Limpar ocupa o último slot antes do
envio; após o clear, o cursor permanece estático sobre aquela posição. Se o `Undo2` montasse
naquele slot, o `mouseover` sintético do Chromium (boundary event por mutação de DOM sob o
cursor) dispararia `pause()` no nascimento do candidato — o timer de 8s nunca chegaria a
correr e o ícone persistiria indefinidamente. Comprovado por instrumentação de
`setTimeout`/`clearTimeout` no probe: `timers=[{ms:8000,id:11}]` + `cleared:[11]` logo após
o clear, sem `resume` posterior. Montando o ícone à esquerda do microfone, o cursor repousa
sobre o mic (inócuo) e a expiração funciona — `expiry:icon-gone` PASS.

## Propriedades verificadas

- `aria-label="Desfazer limpeza do rascunho"`, `type="button"`, Lucide `Undo2` 18px.
- Tooltip `HelpTooltip` com o mesmo texto (screenshot `r1-dock-undo-icon.png`).
- Wrapper `span.delia-draft-undo` com `role="status"` — anúncio educado ao aparecer.
- Pausa/retomada via `onMouseEnter`/`onMouseLeave`/`onFocusCapture`/`onBlurCapture` no wrapper.
- Ghost: fundo e borda transparentes em repouso (light e dark — override escopado em
  `plugins/delia/src/index.css`, com seletor `[data-theme="dark"]` de especificidade
  suficiente para vencer a regra dark do `icon-btn`), hover tonal 10% accent, foco via
  `box-shadow`/`:focus-visible` herdado de `.delpi-ui-icon-btn`, alvo 36×36px.
- Toolbar permanece em uma linha, sem crescimento de altura (36px→36px medido) e sem
  deslocar Enviar/Limpar/mic.

## Testes

| Camada | Resultado |
|---|---|
| `draftRecovery.test.tsx` (hook) | 10/10 |
| `draftRecoveryApp.test.tsx` (integração App) | 5/5 (assertions migrados para o ícone na toolbar) |
| Suite `plugins/delia` | 291/291 |
| Typecheck delia | PASS |
| Build delia | PASS |
| Federation `verify-host-exports` (plugin-ui) | PASS |

## Browser QA — Playwright (Chrome headless, usuário local `e2e-delia`)

`44/44 PASS` — script `qa-draft-recovery-r1.mjs`:

- Dock 420×900: ciclo completo digitar → Limpar → `Undo2` aparece → tooltip/hover →
  clique → restauração exata Unicode/multiline → ícone some → foco volta ao textarea →
  **0 POST** `/interaction/turns`.
- Ícone dentro de `.delpi-ui-message-composer__toolbar`, adjacente ao mic, sem barra
  `EditorChromeNotice`/`.delia-draft-recovery` em lugar algum.
- Expiração 8s sem interação; pausa em hover (~10s) e em foco, expirando após retomada.
- Invalidação por texto novo, por envio (send-gate) e substituição por segundo clear;
  duplo clique restaura uma única vez.
- Teclado: Enter e Space restauram.
- Full page `/apps/delia`, Dock curto 360×450, viewport 320px, zoom 200%: ícone visível,
  linha única, sem overflow horizontal.
- Dark: ícone visível com fundo transparente.
- Regressões: starters R2/R3 = 4 cards no Dock alto; mic VD-F05, Enviar e Limpar intactos.

Screenshots: `shots-draft-recovery-r1/r1-*.png` (locais ao executor).

## Deploy

`PRODUCTION_DEPLOYMENT`/`DEPLOYED_SHA`/`PRODUCTION_BUNDLE_VERIFIED` — ver seção final do
relatório de execução e entrada §6.364 do ledger (preenchidos após o deploy).

`PRODUCTION_BROWSER_QA=PENDING_USER_VERIFICATION` — sem sessão autenticada de teste.

## Resíduos

- Verificação visual/funcional autenticada em `https://minhadelpi.com.br/apps/delia`
  pendente de sessão real.
- `EXECUTION_DRIFT=NONE` — nenhum conflito com autoridades; a ordem do ícone à esquerda do
  microfone continua "ao lado do ditado" conforme §9.
