# VD-F04 — Voice Dictation Composer Visual Refinement — Relatório de evidência

**TASK_ID:** `DELIA-UX-VOICE-DICTATION-VISUAL-REFINEMENT-AND-PRODUCTION-DEPLOY-01`
**DATA:** 2026-10-20
**SPEC primária:** [120 — especificação visual](../../120-voice-dictation-composer-visual-refinement-ux-specification.md)
**Referência funcional:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md)
**BASE_HEAD:** `dec58d9abb4783eef47278e3a0b47ebf1ec863c1`
**Escopo:** refinamento visual/UX do composer de ditado existente; zero alteração de backend, contrato `dictation.transcription.v1`, provider, RBAC ou STT.

## 1. Reuse gate

| Conceito | Equivalente existente | Decisão |
|---|---|---|
| Composer | `MessageComposer` (`plugin-ui/src/components/composer/MessageComposer.tsx`) | REUSE |
| Gravador | `AudioRecorderControl` + `useLocalAudioRecorder` | EXTEND (tooltips/copy via `helpCopy`, sem novo gravador) |
| Botões | `IconButton`, `ActionButton`, `ComposerClearDraftButton`, `ComposerSendButton` | REUSE/EXTEND (forward de `aria-describedby`) |
| Help | `HelpTooltip` (`plugin-ui/src/components/help/HelpTooltip.tsx`, modo `wrap`) | REUSE — nenhum sistema novo de tooltip |
| STT | `dictation.transcription.v1`, `dictationClient`, `delia-api` | PRESERVE — diff backend = 0 |

## 2. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `plugins/plugin-ui/src/components/actions/IconButton.tsx` | forward de `aria-describedby` |
| `plugins/plugin-ui/src/components/actions/ActionButton.tsx` | forward de `aria-describedby` |
| `plugins/plugin-ui/src/components/composer/audioRecorderTypes.ts` | `helpCopy` tipado |
| `plugins/plugin-ui/src/components/composer/AudioRecorderControl.tsx` | `HelpTooltip(wrap)` em todos os controles icon-only; conteúdo dinâmico por estado |
| `plugins/plugin-ui/src/components/composer/ComposerClearDraftButton.tsx` | copy “Limpar texto” + tooltip |
| `plugins/plugin-ui/src/components/composer/ComposerSendButton.tsx` | tooltip padronizado |
| `plugins/plugin-ui/src/components/composer/MessageComposer.test.tsx` | cobertura atualizada |
| `plugins/plugin-ui/src/styles/audio-recorder.css` | superfície única arredondada, controles circulares, waveform refinada, motion + reduced-motion, responsivo |
| `plugins/delia/src/App.tsx` | remoção da faixa amarela de ditado do header; banner demo preservado |
| `plugins/delia/src/audio/audioCaptureQaAdmission.ts` | remoção da constante de banner QA (faixa global) |
| `plugins/delia/src/audio/audioCaptureTestAdmission.ts` + `.test.ts` | disclosure contextual no composer substitui banner; limites preservados |
| `plugins/delia/src/ui/DeliaComposer.tsx` | `helpCopy`, disclosure STT contextual, superfície de transcrição em estado único, cancel-transcription tooltip, aviso pós-transcrição |
| `plugins/delia/src/ui/DeliaComposer.test.tsx` | cobertura VD-F04 (tooltips, disclosure, transcribing, draft, sem auto-submit, preview local) |
| `plugins/delia/src/index.css` | estilos locais do composer (disclosure, notice, estados), tokens existentes |

Backend (`*-api`), contrato, provider, RBAC e `DELIA_STT_*`: **nenhum diff**.

## 3. Verificação automatizada (SHA testado = working tree pós-implementação)

| Gate | Resultado |
|---|---|
| Vitest `plugin-ui` (suíte completa) | PASS — 377 arquivos / 2250 testes (uma falha transitória em `AudioRecorderControl.test.tsx` não reproduzida no re-run) |
| Vitest `delia` (suíte completa) | PASS — 21 arquivos / 257 testes |
| Typecheck `plugin-ui` | PASS (exit 0) |
| Typecheck `delia` | PASS (exit 0) |
| Build `plugin-ui` + `verify-host-exports` | PASS |
| Build `delia` (Vite) | PASS |
| Federation | PASS (host exports verificados) |

## 4. Browser QA (Playwright, Chrome headless, localhost autenticado `e2e-delia`)

Script: `C:\temp\delia-qa\qa-vdf04.mjs` — **40/40 PASS**.
Captura de áudio sintética via `--use-file-for-fake-audio-capture` com fala pt-BR real → **transcrição real** via provider configurado localmente.

| Check | Evidência |
|---|---|
| A — escrita: mic visível/circular, tooltip hover+focus, sem faixa amarela | PASS ×5 |
| B — gravação: superfície única, sem textarea/send, controles circulares, waveform real, `mm:ss`, disclosure STT, tooltips cancel/finish | PASS ×11 |
| C — transcrição: superfície única, indicador, cancelar+tooltip, texto editável, merge no cursor (`len=71`), aviso “Revise antes de enviar.”, **zero `POST /interaction/turns`** (sem auto-submit), clear+tooltip | PASS ×10 |
| D — cancelar preserva draft + mic retorna | PASS ×2 |
| E — Dock: mic, tooltip dentro do viewport, gravação, sem overflow, restauração | PASS ×7 |
| F — reduced-motion: estado correto, sem animação ornamental | PASS ×2 |
| G — 360px: gravação sem scroll horizontal | PASS ×2 |

Screenshots: `C:\temp\delia-qa\shots-vdf04\` (01–13). A faixa amarela de ditado no header **não** aparece em nenhum estado; o banner de demo permanece condicionado ao modo demo.

Estado de erro honesto também observado: tom sintético (sem fala) → “Não foi possível reconhecer fala no áudio…” com draft preservado — caminho de erro contextual, sem modal global.

## 5. Matriz VD-V

| ID | Resultado | Base |
|---|---|---|
| VD-V01 superfície única | PASS | QA B/C (`single-surface`, `no-inner-card`) |
| VD-V02 controles circulares | PASS | `border-radius:999px` mic/cancel/finish/clear |
| VD-V03 waveform real proporcional | PASS | barras >10 alimentadas por amplitude do hook; silêncio tom → resposta proporcional |
| VD-V04 cronômetro `mm:ss` estável | PASS | timer real, `tabular-nums`, sem anúncio por segundo |
| VD-V05 transição/layout + motion | PASS | transição de superfície sem shift; reduced-motion PASS |
| VD-V06 processamento limpo | PASS | transcribing na mesma superfície, sem borda dupla nem percentual |
| VD-V07 retorno editável/foco/feedback | PASS | merge real + notice contextual |
| VD-V08 erros/cancel/timeout preservam draft | PASS | QA D + caminho de erro honesto |
| VD-V09 aviso contextual substitui faixa global | PASS | `A:no-audio-banner` + disclosure no composer |
| VD-V10 320/360/420 + zoom 200% | PASS parcial* | 360px validado sem overflow; 320/420 cobertos por wrap flexível; zoom 200% = residual de QA visual |
| VD-V11 a11y (teclado/labels/focus/contraste) | PASS | labels pt-BR, `aria-describedby`, focus-visible, tooltips por foco |
| VD-V12 zero diff backend/RBAC/contrato | PASS | `git diff` confirma escopo frontend |
| VD-V13 gates automatizados + evidência | PASS | seção 3 + este doc |
| VD-V14 produção mic físico pt-BR | PENDING_USER_VERIFICATION | requer sessão `delia.access` em prod |
| VD-V15 tooltips hover/foco em todos os controles | PASS | A/B/C/E |
| VD-V16 conteúdo dinâmico correto por estado | PASS | copy por estado validada nos testes + QA |
| VD-V17 `HelpTooltip` reutilizado (wrap) | PASS | diff — nenhum tooltip novo |
| VD-V18 sem clipping no Dock/teclado/disabled/reduced-motion | PASS | `E:dock-tooltip-in-viewport`, focus, wrap em disabled |
| VD-V19 copy honesta (sem auto-submit/multimodal) | PASS | revisão de copy + `no-auto-submit` |

\* VD-V10 PASS parcial justificado: superfície usa wrap + larguras fluidas; 360px medido sem overflow. 320/420/200% listados como residual visual, não bloqueio funcional.

## 6. Deploy de produção

**Deploy executado em 2026-10-20 em `srv-api` (`operador@192.168.1.237`)**

- `git pull --ff-only` → `a82dab16268b92e0c054d4da6d6638b600c1d413` (worktree limpo).
- `infra/scripts/up-prod-sequential.sh --cpu --build plugin-ui delia` — `infra-plugin-ui` e `infra-delia` reconstruídas, `verify-host-exports OK` (expose `__federation_expose_Index-CH5qqPYa.js`, idêntico ao build local testado), containers recriados e `Started`; `delia-api` **não** rebuildado (backend sem diff).
- Verificado: `GET /apps/plugin-ui/assets/remoteEntry.js` → 200; `GET /apps/delia/assets/remoteEntry.js` → 200; bundle `App-YHMoA3Zc.js` contém `Ditar mensagem` + `Texto transcrito` (código VD-F04 servido); `GET /apps/delia-api/dictation/status` sem token → `401` (AuthZ hardened preservada, log metadata-only); `delpi-delia-api` healthy.
- **PRODUCTION_BROWSER_QA = PENDING_USER_VERIFICATION** — mic físico + fluxo completo exige sessão `delia.access` (sem conta QA no realm de produção — mesmo gate da §6.311).

## 7. Residuals

- VD-V14: QA de produção com microfone físico = `PENDING_USER_VERIFICATION`.
- VD-V10: zoom 200% e 320/420px — residual de screenshot visual; sem overflow aos 360px medidos.
- Mic físico local não exercitado (headless usa dispositivo sintético com fala real).
