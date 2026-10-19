# DÉLIA — Audio Recorder Remove Extra Permission & Production Fix 01 — Execution Evidence

**DATA:** 2026-10-19
**TASK:** `DELIA-UX-AUDIO-RECORDER-REMOVE-EXTRA-PERMISSION-AND-PRODUCTION-FIX-01`
**SPEC:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md)
**BASE:** `cc18410cc675` (= origin/main na reancoragem)
**COMMIT:** `a3df0d4be64516e5845f812585173a8a12a0e788` (main)
**STATUS:** `EVIDENCE_READY_FOR_REVIEW` — correção implementada e validada live no dev stack (bundle paridade-produção); **deploy em produção PENDENTE** (runbook abaixo).

## 1. Decisão do Product Master (correção da decisão anterior)

`delia.audio-capture.test` foi introduzida sem solicitação do PM e **deixou de ser requisito**. Gravação local fica disponível a todo usuário legitimamente admitido à DÉLIA — o acesso já é controlado por `delia.access` (Core RBAC, enforced upstream pelo Portal antes do MFE montar). Escopo: gravação local apenas — sem upload, transcrição, envio ou AuthZ por voz.

## 2. Mudanças (menor diff)

| Arquivo | Mudança |
|---|---|
| `plugins/delia/src/audio/audioCaptureTestAdmission.ts` | Resolver por permissão **removido** — arquivo passa a declarar apenas os limites bounded de teste (`60s/256KB`) e o aviso honesto. Sem consumo de permissions/JWT/URL/flag. |
| `plugins/delia/src/App.tsx` | `audioAdmission = audioQaAdmission ?? DELIA_AUDIO_TEST_LIMITS` — mic para todo usuário admitido. `permissions` volta a ser presentation hint não consumido. Banner: QA→banner QA, demais→banner de teste. |
| `plugins/delia/delpi.manifest.json` | `delia.audio-capture.test` removida; `version` 0.0.2→0.0.3 (contrato `plugin.permission_change_not_allowed` exige nova versão p/ mudança de permissões). |
| `manifest.contract.test.ts`, `audioCaptureTestAdmission.test.ts`, `demoMode.test.tsx`, `s2.shell.test.tsx` | Contrato atualizado (1 permissão); teste s2 passa a exigir o trigger do mic na toolbar. |

Suporte de browser/contexto seguro permanece fail-closed **dentro** de `AudioRecorderControl` (`isLocalAudioCaptureSupported`: `isSecureContext` + `mediaDevices.getUserMedia`). `canSendAudio=false` mantido.

## 3. Mecanismo preservado

`AudioRecorderControl`, `useLocalAudioRecorder`, `MessageComposer`, `DeliaComposer`, `audioCaptureQaAdmission` (harness dev/QA — apenas banner QA em bundle DEV/flag; param inerte em produção, provado). Sem segundo composer, sem novo sistema de autorização.

## 4. Validação live (dev stack, bundle paridade-produção)

Imagem `infra-delia` rebuildada do SHA da task **sem** `VITE_DELIA_AUDIO_QA` (bundle compilado `VITE_DELIA_AUDIO_QA:""`). Bundle servido `App-C6g8yXfJ.js`: `delia.audio-capture.test` → 0 ocorrências; banner de teste presente.

**RBAC:** role `delia-audio-test` removida de e2e-delia → `/me` = `['delia.access']` apenas. Manifest v0.0.3 registrado via `register-manifest.sh` → `{"ok": true}`.

**Playwright (Chrome real, fake media device, e2e-delia com SOMENTE `delia.access`): 13/13 PASS**
- mic visível **sem param** + banner de teste, sem banner QA;
- `?delia-audio-qa=1` permanece inerte;
- gravação `00:02`, preview, play, descartar → idle, sem botão "enviar áudio";
- Companion Dock: mic (exatamente 1), gravação, descarte.

## 5. Legado no Core

`delia.audio-capture.test` permanece registrada no registry local do Core (registrada em v0.0.2) e a role `delia-audio-test` existe, mas **sem consumidores** — o código não a consulta. Remoção destrutiva de registros RBAC não executada (requer decisão operacional específica). Grants legados tornam-se inertes.

## 6. Gates

```text
VITEST_DELIA=PASS 240/240 (21 files)
TYPECHECK_DELIA=PASS
BUILD_DELIA=PASS (docker build; verify-federation-react-patch OK)
VITEST_PLUGIN_UI / TYPECHECK_PLUGIN_UI / BUILD_PLUGIN_UI=PASS (sem diff)
FEDERATION=PASS (remote __federation_expose_App-pSIF9iog servido; App-C6g8yXfJ sem a permissão)
PLAYWRIGHT=PASS 13/13
```

## 7. Deploy em produção — runbook (PENDENTE — executor sem SSH ao srv-api)

```bash
# 1. srv-api: pull + rebuild da imagem delia (sem build-arg)
git pull && ./infra/scripts/up-prod-sequential.sh   # ou compose build+up delia

# 2. Registrar manifest v0.0.3 no Core de produção
BASE_URL=https://minhadelpi.com.br TOKEN=<admin-jwt> \
  bash plugins/delia/scripts/register-manifest.sh

# 3. Validar: https://minhadelpi.com.br/apps/delia com usuário que tenha
#    apenas delia.access → mic visível sem param. Companion Dock idem.
# Opcional (ops): remover grants/role legados de delia.audio-capture.test
# — inertes; não executar sem decisão específica.
```

## 8. Residuais

- Deploy prod depende de operador srv-api (fora do alcance do executor).
- `HUMAN_SPEECH_PLAYBACK=TEST_NOT_RUN`.
- Firefox/Edge/Safari `TEST_NOT_RUN`.
- Permissão/role legadas no Core de prod ficam inertes (consumo removido); limpeza é decisão ops.
- Fase inalterada: `C3_EXECUTED=NO`, `C4/C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`.
