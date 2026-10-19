# DÉLIA — Audio Recorder Live QA Integration 01 (AU-F05) — Execution Evidence

**DATA:** 2026-10-19
**TASK:** `DELIA-UX-AUDIO-RECORDER-DELIA-LIVE-QA-INTEGRATION-01`
**SPEC:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md) — AU-F05
**BASE_HEAD / TESTED_SHA:** `b69d2359f7dd552226b150e6d1f46d1647d1583c` + working tree da task
**STATUS:** `EVIDENCE_READY_FOR_REVIEW` — gate QA implementado; produção permanece OFF.

## 1. Objetivo

Permitir testar `AudioRecorderControl` na DÉLIA real — página completa `/apps/delia` e Companion Dock no Portal — **sem** ativar captura em produção e **sem** backend/upload/transcrição.

## 2. Reuse Gate

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=REUSE_OR_EXTEND
```

- `AudioRecorderControl` / `useLocalAudioRecorder` / `DeliaComposer` / `submitDisabled`: reutilizados integralmente, **zero** novo componente/composer/state machine.
- Mecanismo de admissão espelha o gate canônico já existente `demoMode.isDemoAllowed()` (`import.meta.env.DEV || VITE_DELIA_DEMO=1` + query param explícito) — mesmo padrão, nenhum segundo sistema de feature flags.
- Nenhum provider, store global, proxy de áudio ou endpoint criado.

## 3. Implementação (menor diferença legítima)

| Arquivo | Mudança |
|---|---|
| `plugins/delia/src/audio/audioCaptureQaAdmission.ts` | Gate QA: `isAudioQaBundleAllowed` = `DEV \|\| VITE_DELIA_AUDIO_QA="1"`; `resolveAudioQaAdmission(search)` exige `?delia-audio-qa=1` **e** bundle admitido; constantes `DELIA_AUDIO_QA_MAX_DURATION_MS=60_000` / `MAX_BYTES=256_000` marcadas como **fixtures de QA, não política de produção** |
| `plugins/delia/src/audio/audioCaptureQaAdmission.test.ts` | 9 testes: prod+param→null, dev sem param→null, param ≠"1"→null, dev+param→limites, build-flag+param→limites |
| `plugins/delia/src/App.tsx` | `resolveAudioQaAdmission(window.location.search)` uma vez no mount → `audioCaptureEnabled/maxDurationMs/maxBytes` no `DeliaComposer`; banner honesto "Captura de áudio em modo QA — gravação local apenas, sem envio." |
| `plugins/delia/Dockerfile` | `ARG VITE_DELIA_AUDIO_QA=""` + `ENV` antes do `vite build` — **default OFF**; imagens de produção nunca admitem o param |

Por que URL param sozinho não autoriza em produção: `VITE_DELIA_AUDIO_QA` é build-time; bundle de produção tem `""` → `isAudioQaBundleAllowed=false` → `?delia-audio-qa=1` inerte (provado em `fullpage-noparam:no-mic` e `dock-noparam:no-mic`).

## 4. Deploy QA executado (stack dev local autorizado)

- `docker build -f plugins/plugin-ui/Dockerfile -t infra-plugin-ui:latest plugins/` — remote plugin-ui com exports da fundação AU-F02.
- `docker build -f plugins/delia/Dockerfile --build-arg VITE_DELIA_AUDIO_QA=1 -t infra-delia:latest plugins/` — bundle delia com flag QA **somente nesta imagem local**.
- `docker compose up -d plugin-ui delia` — containers recriados no stack dev.
- Verificado no bundle servido: `VITE_DELIA_AUDIO_QA:"1"` + `delia-audio-qa` em `App-CGRiKyQB.js`; `AudioRecorderControl` em `__federation_expose_Index-Bzru-gee.js` do remote plugin-ui. **Componente presente no bundle efetivamente servido pelo host, não só no build local.**
- `delpi-keycloak` estava parado há ~6h (502 em silent-SSO) — reiniciado para auth real (`e2e-delia`).

## 5. Testes automatizados

```text
VITEST_DELIA=PASS 237/237 (20 files; +9 admission, gate prod-off/dev-on/param)
TYPECHECK_DELIA=PASS (tsc --noEmit)
BUILD_DELIA=PASS (vite build 5.67s, sem flag — default OFF)
FEDERATION=PASS (verify-federation-react-patch OK)
VITEST_PLUGIN_UI=PASS (inalterado nesta task — 2246/2246 registrado em AU-F02 no mesmo SHA base)
TYPECHECK/BUILD_PLUGIN_UI=PASS (sem diff plugin-ui)
```

## 6. Browser QA integrado (Playwright, Chrome real, Portal autenticado)

Chrome headless real, `--use-fake-device-for-media-stream` (pipeline getUserMedia/MediaRecorder real, áudio sintético), origem `http://localhost` promovida a secure context. Login real Keycloak `e2e-delia`.

**16/16 PASS:**

| Superfície | Cenário | Resultado |
|---|---|---|
| `/apps/delia` sem param | sem mic, composer textual ok | PASS (produção-like) |
| `/apps/delia?delia-audio-qa=1` | mic trigger + banner QA | PASS |
| full page | gravação real, duração `00:01`, indicador | PASS |
| full page | preview, play, sem botão Enviar | PASS |
| full page | descartar → idle | PASS |
| Portal `?delia-audio-qa=1` | dock abre, mic no composer dock | PASS |
| dock | gravação + preview + descartar | PASS |
| dock sem param | sem mic, textarea ok | PASS |

Screenshots: `a1-fullpage-noparam.png`, `b1-fullpage-recording.png`, `b2-fullpage-preview.png`, `c1-dock.png`, `probe.png`, `real-mic-preview.png`.

## 7. Microfone físico real

Script dedicado **sem** `--use-fake-device-for-media-stream` (Chrome usa o dispositivo físico; `--use-fake-ui` apenas auto-aceita a permissão — QA autorizado):

```text
mic trigger=1 → recording=1 (stream física obtida)
dur=00:04 previewDur=00:04 (duração real)
playing=1 (playback do áudio capturado)
discard→idle (mic liberado, trigger restaurado)
waveform activeBars=0/24 (conteúdo = silêncio ambiente — sem operador falando)
```

```text
REAL_MIC_CAPTURE=PASS (ciclo de captura em dispositivo físico)
  residual honesto: conteúdo gravado = silêncio (ninguém falou no mic);
  audibilidade de fala não verificada — requer operador humano.
```

## 8. Cobertura da matriz AU-F05

- **Grupo A (gate):** prod-like sem param→sem mic; QA bundle+param→controle; sem limites→indisponível (DeliaComposer tests); prod build→param inerte (unit + live).
- **Grupo B (captura):** gesto explícito, permissão, duração real, waveform, finalização — live QA + suite AU-F02.
- **Grupo C (prévia):** play/pause, descarte, regravação, cleanup, sem auto-send/upload — live QA + suite AU-F02.
- **Grupo D (integração):** composer funcional, sem duplicação, texto preservado, dock+full page — live QA.
- **Grupo E (compatibilidade):** Chrome PASS; Firefox/Edge/Safari `TEST_NOT_RUN`.

## 9. Segurança/privacidade mantida

Sem upload, sem transcrição, sem retenção, sem áudio em logs/prompts, sem AuthZ por voz, sem auto-gravação. Browser permission não substitui gate (duplo: bundle flag + param explícito). Limites = fixtures QA declarados, não política corporativa.

## 10. Residuais

- Imagem local `infra-delia:latest` carrega a flag QA (dev stack); Dockerfile commitado default OFF. Rebuild sem `--build-arg` restaura.
- `REAL_MIC` audibilidade de fala não verificada (silêncio ambiente).
- Firefox/Edge/Safari: `TEST_NOT_RUN`.
- Limites de produção permanecem `CONTRACT_REQUIRED` (spec 119 §5).
- Revogação do gate durante captura: comportamento `captureAdmitted→unavailable` coberto pelo hook; teste live dessa transição `TEST_NOT_RUN`.

## 11. Fase

`C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `CP-333=PLANNED`, `PRODUCTION_READINESS=NOT_PROVEN` — **inalterados**.
