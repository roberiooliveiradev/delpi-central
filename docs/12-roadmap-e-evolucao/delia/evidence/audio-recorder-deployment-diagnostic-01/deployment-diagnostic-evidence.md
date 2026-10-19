# DÉLIA — Audio Recorder Deployment Diagnostic & QA 01 — Execution Evidence

**DATA:** 2026-10-19
**TASK:** `DELIA-UX-AUDIO-RECORDER-DEPLOYMENT-DIAGNOSTIC-AND-QA-01`
**SPEC:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md)
**BASE_HEAD:** `1ab2707546` (local; divergente de `origin/main=eca913e4f8` por commits concorrentes — plugins/delia intacto desde `1a95344d54`)
**STATUS:** `EVIDENCE_READY_FOR_REVIEW` — diagnóstico concluído; **nenhuma correção de código necessária**; produção corretamente OFF.

## 1. Pergunta

Por que o botão de microfone não aparece em `https://minhadelpi.com.br/apps/delia`?

## 2. Causa-raiz comprovada

```text
ROOT_CAUSE=WORKING_AS_DESIGNED — PRODUCTION_QA_FLAG_OFF
```

O bundle de produção da DÉLIA contém o código completo da feature, mas foi compilado **sem** `VITE_DELIA_AUDIO_QA` (baked `""`) e com `DEV:false`. Logo `isAudioQaBundleAllowed()=false`, o parâmetro `?delia-audio-qa=1` é inerte, `audioCaptureEnabled` nunca é propagado e o `AudioRecorderControl` não renderiza. **É o comportamento de segurança projetado em AU-F05**, não um defeito.

## 3. Evidência do que está servido (não só HTTP 200)

Fetch direto dos assets públicos de `https://minhadelpi.com.br` (Cloudflare, `cf-cache-status: BYPASS`, `no-store` — sem cache/CDN/service worker interferindo):

| Item | Valor provado |
|---|---|
| Portal/MFE host | `minhadelpi.com.br` via Cloudflare → gateway `/apps/delia/assets/*` |
| remoteEntry DÉLIA | 1621B, expõe `__federation_expose_App-C0W0ZD32.js?v=14` |
| App chunk servido | `App-CXTCxdME.js` (34 789 B) |
| Código de admissão no bundle | `delia-audio-qa`, `resolveAudioQaAdmission`, banner `"Captura de áudio em modo QA…"`, limites `6e4/256e3` — **presente** |
| Flag compilada | `{DEV:!1, MODE:"production", PROD:!0, VITE_DELIA_AUDIO_QA:""}` — **OFF** |
| Remote plugin-ui | `__federation_expose_Index-Bzru-gee.js` (429 802 B) — **mesmo hash do build local AU-F05** |
| `AudioRecorderControl` no remote | presente (1 ref + `useLocalAudioRecorder` + `audio-recorder` CSS ×24) |
| `audioCaptureEnabled`/`canSendAudio`/`maxDurationMs` | presentes no App chunk (wiring DeliaComposer intacto) |

## 4. Deployed vs. código-fonte

Diff tokenizado entre `App-CXTCxdME.js` (produção) e build local de produção do HEAD (`App-BwDQzmXr.js`, sem flag):

```text
token-identity = 0.9899
único delta semântico: prod tem VITE_DELIA_AUDIO_QA:"" explícito no env object
demais deltas: renomeação de identificadores do minifier (I↔R, At↔vt…) — ruído de build
```

```text
GITHUB_HEAD=1ab2707546 (local) / eca913e4f8 (origin)
DEPLOYED_SHA≥1a95344d54 (admission code existe no bundle servido; plugins/delia
  não tem commit posterior a 1a95344d54 → código funcionalmente idêntico ao HEAD)
DEPLOYED_IMAGE=produção cloud (cloudflare front); build com VITE_DELIA_AUDIO_QA=""
BROWSER_LOADED_ASSET=App-CXTCxdME.js + expose Index-Bzru-gee.js (fresh, no-store)
```

## 5. Cenários do gate no runtime servido

| Cenário | Resultado comprovado |
|---|---|
| A — prod `/apps/delia` | mic OFF ✓ (flag compilada `""` → admission null) |
| B — prod `?delia-audio-qa=1` | **inerte** ✓ (`isAudioQaBundleAllowed=false` independente do param) |
| C — QA autorizado | local dev stack: imagem `infra-delia` com `--build-arg VITE_DELIA_AUDIO_QA=1` → `?delia-audio-qa=1` ativa mic + banner |
| D — Companion Dock | propagação verificada live (AU-F05, revalidado nesta task): `hostProps.search` carrega o param do host Portal para o MFE no dock |

## 6. Ambiente QA autorizado para o Product Master

Não existe domínio QA/staging na infra (`infra/` não contém host QA/homolog). O ambiente autorizado vigente é o **stack dev local** desta máquina:

```text
http://localhost/apps/delia?delia-audio-qa=1
  imagem infra-delia (dev) com VITE_DELIA_AUDIO_QA=1 baked
  verify: bundle servido = App-CGRiKyQB.js com VITE_DELIA_AUDIO_QA:"1"
Companion Dock: abrir http://localhost/?delia-audio-qa=1 → dock DÉLIA
```

Para PM testar fora desta máquina é necessária **decisão de deployment** (imagem QA dedicada em host QA). `local-first-deploy.mdc` proíbe promover flag a produção via conveniência; nenhum domínio QA existe — registrar como pedido de infraestrutura.

## 7. Revalidação live (Chrome real, fake media device, stack local)

Reexecutada a suíte AU-F05 no stack atual: **16/16 PASS** — full page + dock, gate ON/OFF, gravação, duração, preview, play, sem-send, discard.

Microfone físico (evidência AU-F05 §7 mantém-se válida — mesmo código/imagem):
ciclo de captura real provado; residual — conteúdo foi silêncio ambiente, audibilidade de fala humana não verificada (`HUMAN_SPEECH_PLAYBACK=TEST_NOT_RUN`).

## 8. Segurança

Gate duplo mantido: bundle flag (build-time, não contornável por URL) + param explícito + limites QA (60s/256KB, fixtures) + gesto + browser support. Sem upload, transcrição, AuthZ por voz ou retenção. Produção continua OFF conforme autoridades.

## 9. Residuais

- Nenhum host QA público existe — PM precisa do stack local ou de decisão de infra para um ambiente QA hospedado.
- `HUMAN_SPEECH_PLAYBACK=TEST_NOT_RUN` (sem operador falando no mic físico).
- Deployed SHA exato não assinado no bundle (nenhum build-metadata exposto); prova por conteúdo ≥`1a95344d54` e identidade token 0.99.
- Fase inalterada: `C3_EXECUTED=NO`, `C4/C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`.
