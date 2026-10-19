# DÉLIA — Audio Recorder Composer Foundation 01 — Execution Evidence

**DATA:** 2026-10-19
**TASK:** `DELIA-UX-AUDIO-RECORDER-COMPOSER-FOUNDATION-01`
**SPEC:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md) — AU-F02 + AU-F03
**TESTED_SHA:** `6e6024c952888a79f4247cf6f1aeed27d88ee0a8` + working tree da task
**STATUS:** `EVIDENCE_READY_FOR_REVIEW` — fundação local apenas; feature gate OFF em produção.

## 1. Reuse gate executado

```text
EXISTING_EQUIVALENT_COMPOSER=YES   (MessageComposer.tsx — secondaryActions legítimo)
REUSE_DECISION_COMPOSER=REUSE      (propriedade aditiva submitDisabled; sem segundo composer)

EXISTING_EQUIVALENT_RECORDER=NO    (inventário repo-wide: nenhum MediaRecorder/getUserMedia/player/hook de captura existente)
REUSE_DECISION_RECORDER=NEW        (menor componente compartilhado em plugin-ui, Abstraction Gate OK: consumer real = DeliaComposer)
```

Inventário também verificou `components/forms/`, `components/feedback/`, `styles/message-composer.css`, exports públicos e consumidores. Nenhum upload/transcription/player contract existente → `canSendAudio` permanece `false` estruturalmente.

## 2. Implementação (owner: `plugins/plugin-ui`)

| Arquivo | Papel |
|---|---|
| `src/components/composer/AudioRecorderControl.tsx` | Componente UI: trigger mic em `secondaryActions`, painel recording/preview, erros acessíveis, render-prop `{trigger, panel, blocking}` |
| `src/components/composer/useLocalAudioRecorder.ts` | Lifecycle nativo: `getUserMedia` (só após gesto), `MediaRecorder` (timeslice 250ms), `AudioContext`+`AnalyserNode` waveform real (opcional), timers, playback `HTMLAudioElement`, cleanup total |
| `src/components/composer/audioRecorderMime.ts` | Seleção MIME por `MediaRecorder.isTypeSupported` (webm/opus → webm → mp4 → ogg) + `isLocalAudioCaptureSupported` (secure context + APIs) |
| `src/components/composer/audioRecorderTypes.ts` | `LocalAudioDraft`, `AudioRecorderUiStatus`, `AudioRecorderCaptureErrorReason`, props tipadas, `formatAudioDurationMs` |
| `src/styles/audio-recorder.css` | Tokens `--delpi-ui-*` com fallback, light/dark, flex-wrap p/ dock estreito, `prefers-reduced-motion` (sem pulse), dot de captura |
| `MessageComposer.tsx` | Extensão aditiva `submitDisabled` — bloqueia Enter/send durante captura sem apagar draft |
| `components/composer/index.ts`, `styles.css` | Exports públicos + import do CSS |

Estados: `unavailable | idle | requesting_permission | recording | stopping | preview | error`; `discarded` = cleanup → `idle`. `sending`/`sent` **não implementados** por design (sem contrato de envio).

Composição DÉLIA (`plugins/delia/src/ui/DeliaComposer.tsx`): `AudioRecorderControl` envolve `MessageComposer`; gate triplo `audioCaptureEnabled && maxDurationMs>0 && maxBytes>0 && isLocalAudioCaptureSupported()`; `canSendAudio=false` sempre; `busy` deriva de `loading||requestMode`; draft textual preservado.

## 3. Testes (Vitest, jsdom)

- `plugin-ui/src/components/composer/AudioRecorderControl.test.tsx` — **20 testes PASS**: formatação mm:ss, MIME pick/unsupported, gate OFF, unavailable sem limites aprovados, trigger gated, gesto explícito→gravação, permissão negada→alert, dispositivo ausente, finalizar→preview sem send, play/pause, descartar→idle+revoke, **regravar→revoke+nova captura**, cancelar→tracks stop, submit bloqueado durante gravação com draft preservado, sem auto-submit, start duplicado ignorado, object URL revogada no unmount, `submitDisabled` no MessageComposer.
- `plugins/delia/src/ui/DeliaComposer.test.tsx` — **3 testes PASS**: gate OFF (default) sem mic, gate ON sem limites aprovados → indisponível, gate ON + limites → mic presente.

```text
VITEST_PLUGIN_UI=PASS 2246/2246 (377 files)   TESTED_SHA=worktree sobre 6e6024c952
VITEST_DELIA=PASS 228/228 (19 files)
TYPECHECK_PLUGIN_UI=PASS (tsc --noEmit limpo — erros tsc históricos resolvidos upstream)
TYPECHECK_DELIA=PASS
BUILD_PLUGIN_UI=PASS (vite build 25.26s)
BUILD_DELIA=PASS (vite build 3.38s)
FEDERATION=PASS (verify-host-exports OK; AudioRecorderControl presente em __federation_expose_Index-*.js)
```

## 4. Browser QA (Playwright, Chrome real headless)

Chrome 141+ `headless` com `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream` → pipeline **real** `getUserMedia`+`MediaRecorder` sobre dispositivo sintético. Origem `http://172.23.107.128:5199` promovida a secure context via flag. Harness temporário (vite.qa.config + qa-audio.html + src/qa/audioHarness.tsx, **não commitado**) montava `DeliaComposer` real com gate ON + limites QA (60s/256KB) e um segundo composer gate OFF como controle.

**28/28 PASS:**

| Cenário | Resultado |
|---|---|
| gate OFF sem mic, textarea ok | PASS |
| gate ON mic trigger presente | PASS |
| gesto → indicador `Gravando` + duração real (`00:01`) + barras de wave | PASS |
| draft textual preservado durante gravação | PASS |
| Enter não submete durante gravação (submit=0) | PASS |
| finalizar → preview, sem botão Enviar | PASS |
| play/pause preview | PASS |
| zero auto-submit | PASS |
| descartar → idle | PASS |
| regravar → nova captura | PASS |
| cancelar durante gravação → idle, painel removido | PASS |
| teclado: mic focável, Enter inicia | PASS |
| dock 320px sem overflow horizontal | PASS |
| tema dark (bg `rgb(27,32,48)`) | PASS |
| zoom 200% renderiza | PASS |
| reduced-motion: `animation: none`, label `Gravando` presente | PASS |
| permissão negada (browser sem fake flags): `role=alert` legível + texto utilizável | PASS |

Screenshots: `02-recording.png`, `03-preview.png`, `07-dock-320.png`, `08-dark.png`, `09-zoom200.png`, `11-denied.png`.

```text
PLAYWRIGHT=PASS 28/28 (fake device — NÃO é microfone físico)
REAL_MIC_CAPTURE=TEST_NOT_RUN (ambiente headless; requer sessão com mic autorizado)
```

## 5. Privacidade/segurança verificada

- Permissão somente após clique explícito; nenhum getUserMedia em mount.
- Indicador visível (`Gravando` + dot) durante track ativa; não só cor.
- Zero upload/request de áudio: `canSendAudio=false`, `onConfirmSend` só renderizado se `canSendAudio` (nunca na DÉLIA atual).
- Tracks `stop()` em cancel/discard/unmount/stop; `URL.revokeObjectURL` em discard/rerecord/unmount; `AudioContext.close()`; `audioEl.pause()`+src removido.
- Nenhum byte/URL/permissão em logs; `LocalAudioDraft` transitório in-memory.
- Erros mapeados: `NotAllowedError→permission_denied`, `NotFoundError→device_not_found`, `NotReadableError→device_not_readable`, `SecurityError→secure_context_required`, `mime_unsupported`, `recorder_failed`, `limit_duration`, `limit_bytes`.
- Limites: enforced por `maxDurationMs`/`maxBytes` injetados pelo consumer — **nenhum valor de produção aprovado existe**; gate exige os dois → captura não abre em produção sem decisão de produto.

## 6. Residuais honestos

- `REAL_MIC_CAPTURE=TEST_NOT_RUN`: fake device prova pipeline real do browser, não hardware.
- `sending`/`sent`/upload/transcrição: fora de escopo, exigem AU-F04 (contrato owner-approved).
- Limites de mídia de produção: `CONTRACT_REQUIRED` — sem valores aprovados, produção permanece `audioCaptureEnabled=false`.
- Harness de QA não versionado (temporário); screenshots versionados neste diretório.
- Storybook: não existe no repositório; cobertura via Vitest + harness.

## 7. Fase

`C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`, `CP-333=PLANNED` — **inalterados**. Frontend UX slice; nenhuma promoção.
