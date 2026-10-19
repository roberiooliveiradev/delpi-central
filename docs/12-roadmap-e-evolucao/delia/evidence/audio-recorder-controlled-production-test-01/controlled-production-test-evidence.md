# DÉLIA — Audio Recorder Controlled Production Test 01 — Execution Evidence

**DATA:** 2026-10-19
**TASK:** `DELIA-UX-AUDIO-RECORDER-CONTROLLED-PRODUCTION-TEST-01`
**SPEC:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md)
**BASE:** `f104b802eb` (= origin/main na reancoragem)
**COMMIT:** `5df2f3c5174ce6859bd762323f93e2f130f2945f` (main)
**STATUS:** `EVIDENCE_READY_FOR_REVIEW` — admissão RBAC implementada e validada live; **deployment em produção PENDENTE de execução operacional** (runbook abaixo).

## 1. Decisão

Product Master autorizou teste controlado do gravador **em produção** para usuários admitidos. Não autoriza ampliação de permissões, AuthZ por voz, captura automática, upload ou transcrição.

## 2. Reuse Gate

```text
EXISTING_EQUIVALENT_AUDIO_COMPONENT=YES → REUSE (zero diff em plugin-ui)
EXISTING_EQUIVALENT_FEATURE_GATE=YES → REUSE_OR_EXTEND
```

Contrato legítimo reutilizado: **`MeResponse.permissions` → `AppProps.permissions`** — projeção de RBAC resolvida pelo Core (backend-first), já entregue pelo Portal host às duas superfícies (página completa e Companion Dock). Nenhum novo provider/store/flag-system.

## 3. Implementação (menor diff)

| Arquivo | Mudança |
|---|---|
| `plugins/delia/delpi.manifest.json` | `version` 0.0.1→0.0.2 (contrato exige nova versão para mudar permissões — `update_plugin_manifest_use_case` bloqueia em `plugin.permission_change_not_allowed`); nova permissão `delia.audio-capture.test` com descrição bounded |
| `plugins/delia/src/audio/audioCaptureTestAdmission.ts` | `resolveAudioTestAdmission(permissions)` — fail-closed, match exato; limites `60s/256KB` declarados como **bounded test values autorizados pelo PM para esta task**; banner honesto de teste |
| `plugins/delia/src/App.tsx` | `audioTestAdmission` via `useMemo(permissions)` (reativo — revogação do grant flipa `enabled`→false e o hook faz `hardCleanup` mid-capture, contrato já coberto em plugin-ui); banner compõe QA/teste |
| `manifest.contract.test.ts` + `audioCaptureTestAdmission.test.ts` | +5 testes de admissão; contrato do manifest atualizado |

`canSendAudio=false`, upload e transcrição permanecem estruturalmente OFF.

## 4. Pipeline de autorização validado live (stack dev)

```text
manifest v0.0.2 → POST /core-api/admin/apps/register → permission registrada
role "delia-audio-test" + permission → assign a e2e-delia (Core RBAC)
/me de e2e-delia: ['delia.access', 'delia.audio-capture.test'] ✓ backend-resolved
```

Nota operacional: o endpoint `POST /admin/rbac/roles/{id}/permissions` recebe `{"id": "<permission.code>"}` (por código, não UUID).

## 5. Validação live — bundle paridade-produção

Imagem `infra-delia` rebuildada do SHA da task **sem** `VITE_DELIA_AUDIO_QA` (bundle compilado `VITE_DELIA_AUDIO_QA:""` — paridade exata com produção). Playwright Chrome real, fake media device:

**13/13 PASS:**
- usuário admitido **sem param** → mic visível + banner de teste ("Gravação de áudio em teste. O áudio fica neste navegador e ainda não pode ser enviado à DÉLIA.")
- `?delia-audio-qa=1` **inerte** (sem flag no bundle → banner QA não aparece)
- gravação real `00:02`, indicador, preview, play, descartar → idle, sem botão "enviar áudio"
- Companion Dock: mic + gravação + descarte

**Fail-closed / revogação (sem redeploy):**
- role removida do usuário → `/me` volta a `[delia.access]` → reload: **mic ausente com e sem param**, textarea intacta → `REVOCATION_PASS`
- revogação mid-capture: garantida pelo contrato (`useMemo` reativo + `hardCleanup` do hook quando `enabled`→false; coberto por unit test plugin-ui); prova live em remount: PASS

Não-autorizado (default state): fail-closed, provado (e2e-delia sem grant = mic ausente; outros e2e users sem `delia.access` não alcançam a página).

## 6. Gates

```text
VITEST_DELIA=PASS 242/242 (21 files; +5 admission)
TYPECHECK_DELIA=PASS
BUILD_DELIA=PASS (docker build; verify-federation-react-patch OK)
VITEST_PLUGIN_UI=PASS (sem diff; 2246/2246 baseline vigente)
FEDERATION=PASS (bundle servido contém delia.audio-capture.test + banner)
PLAYWRIGHT=PASS 13/13 + revogação PASS
```

## 7. Deployment em produção — runbook (PENDENTE)

Executor **não possui acesso SSH ao srv-api** (não configurado nesta máquina). Deploy canônico = operador no servidor (`local-first-deploy.mdc`):

```bash
# 1. srv-api: pull + rebuild da imagem delia (SEM build-arg — flag QA fica OFF)
git pull
./infra/scripts/up-prod-sequential.sh   # ou compose build+up delia

# 2. Registrar manifest v0.0.2 no Core de produção (admin token)
BASE_URL=https://minhadelpi.com.br TOKEN=<admin-jwt> \
  bash plugins/delia/scripts/register-manifest.sh

# 3. RBAC: criar/atribuir permissão aos usuários admitidos
#    Portal admin → RBAC → role (ex.: "delia-audio-test") +
#    permission delia.audio-capture.test → usuários do teste

# Rollback/revogação sem redeploy: remover a permissão/role no RBAC admin.
```

Após o passo 1, usuários **não admitidos** continuam sem mic (fail-closed). O mic aparece somente após o passo 3 para usuários admitidos — produção permanece segura em cada etapa intermediária.

## 8. Segurança

Consentimento por gesto, indicador ativo, sem persistência/upload/transcrição, sem áudio em logs, sem AuthZ por voz, cleanup de tracks/URLs, revogação via RBAC sem código novo, param de URL não concede acesso (provado), permissão backend-resolved (não JWT-claim lida pelo client como autoridade — é a projeção autoritativa do Core via `/me`).

## 9. Residuais

- Deploy em produção depende de operador com acesso ao srv-api + grant RBAC aos usuários do teste.
- `HUMAN_SPEECH_PLAYBACK=TEST_NOT_RUN` (sem operador falando).
- Cache de permissões do resolver pode adiar revogação até TTL/refresh do `/me` — remount/reload resolve; documentado.
- Firefox/Edge/Safari `TEST_NOT_RUN`.
- Fase inalterada: `C3_EXECUTED=NO`, `C4/C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`.
