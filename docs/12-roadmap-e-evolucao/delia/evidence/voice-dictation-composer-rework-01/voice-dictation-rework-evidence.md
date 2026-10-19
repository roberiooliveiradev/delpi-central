# Evidência — DELIA-UX-VOICE-DICTATION-COMPOSER-REWORK-01 (VD-F02)

**Data:** 2026-10-19
**Base:** `origin/main = 68de5577a4c8afb94cddfe7290d7f25b0ccbc6bb` (reanchor; REFERENCE_HEAD fornecido `0142c8938c` era mais antigo que o merge vigente)
**Spec:** [119](../../119-conversation-audio-recorder-composer-product-ux-specification.md) §0 (Voice Dictation Composer)
**Status:** `EVIDENCE_READY_FOR_REVIEW` — VD-F02 implementado; STT `BLOCKED_BY_CONTRACT`

## 1. Reuse Gate declarado

| Item | Resultado |
|---|---|
| `EXISTING_EQUIVALENT_COMPOSER` | `YES` |
| `REUSE_DECISION_COMPOSER` | `EXTEND` — `MessageComposer` ganhou `bodyOverride?: ReactNode` |
| `EXISTING_EQUIVALENT_AUDIO_CAPTURE` | `YES` |
| `REUSE_DECISION_AUDIO_CAPTURE` | `REUSE`/`EXTEND` — hook/estados intactos; render props estendidos com `errorReason`; `autoFocus` no Finalizar via `IconButton` |
| `EXISTING_EQUIVALENT_STT` | `NO` (inventário: sem provider/API/OpenAPI/adapter/capability STT legítimos em `delia-api`, `core-api` ou plugins; hits residuais = marcador determinístico de transcript em `handle_interactive_turn.py` e UI do Chat — não reutilizáveis) |
| `REUSE_DECISION_STT` | `PENDING_DECISION` — nenhum provider/gateway/adapter criado; integração condicionada a owner + contrato aprovado |

## 2. Implementação (menor extensão, sem segundo composer)

- `plugins/plugin-ui/src/components/composer/MessageComposer.tsx` — nova prop `bodyOverride?: ReactNode`: quando presente, a **mesma moldura** (`__surface`) renderiza o conteúdo de captura no lugar da banda de escrita + toolbar; textarea **desmontada** (nada de campo focável), ações secundárias/hint/envio fora da tela; `canSubmit` inclui `bodyOverride == null` (submit impossível, inclusive por controle `type="submit"` inserido no override).
- `plugins/plugin-ui/src/components/composer/AudioRecorderControl.tsx` — render props estendidos com `errorReason`; formatter de erro exportado como `audioRecorderErrorMessage` (barrel `composer/index.ts`); `Finalizar gravação` recebe `autoFocus` ao entrar em `recording`.
- `plugins/plugin-ui/src/components/actions/IconButton.tsx` — prop `autoFocus?: boolean` (passthrough).
- `plugins/plugin-ui/src/styles/message-composer.css` — regra `__surface > .delpi-ui-audio-recorder-shell` achata o cartão do recorder dentro da moldura (mesmo espaço visual do campo de escrita, sem card duplo).
- `plugins/delia/src/ui/DeliaComposer.tsx` — composição: painel de captura (`requesting_permission`/`recording`/`stopping`/`preview`) vira `bodyOverride`; `secondaryActions` (mic) some durante captura; `submitDisabled` ativo; status `error` permanece em modo escrita com a mensagem honesta no slot `error` do composer; efeito restaura foco ao textarea ao sair de captura → `idle`. `canSendAudio=false` preservado.
- **Não criado:** `VoiceDictationComposer` separado, segundo gravador, provider/gateway/adapter STT, permissão nova, flag nova.

## 3. Comportamento resultante (honesto, sem STT)

`writing` → clique no mic (gesto) → `requesting_permission`/`recording`/`stopping`/`preview` **substituem** a área de escrita na mesma moldura → `cancel`/`discard`/`error` retornam à escrita com o rascunho exato. `stop` → `preview` local (ouvir/descartar/regravar) — **não** existe estado `transcribing` fictício nem texto fabricado. `Enviar` nunca acionável durante captura; `onSubmit` nunca chamado pelo fluxo de áudio. Limites bounded de teste (60 s / 256 KB) e `delia.access` permanecem; `VITE_DELIA_AUDIO_QA` inerte no bundle servido.

## 4. Gates executados nesta task

| Gate | Resultado |
|---|---|
| plugin-ui vitest | `PASS` 2250/2250 (377 arquivos) — inclui 3 novos testes `bodyOverride` |
| delia vitest | `PASS` 246/246 (21 arquivos) — inclui 6 novos testes do ciclo de ditado |
| tsc delia (`tsconfig.app.json`) | `PASS` |
| tsc plugin-ui (`tsconfig.json`) | `PASS` |
| build plugin-ui | `PASS` (`verify-host-exports OK`) |
| build delia (vite + docker) | `PASS` (`verify-federation-react-patch OK`) |
| Playwright (Chrome real, fake media device) | `PASS` 20/20 — ver §5 |
| `REAL_MIC_CAPTURE` físico | `TEST_NOT_RUN` (fake device apenas) |
| `REAL_TRANSCRIPTION` | `TEST_NOT_RUN` — sem STT |

## 5. Playwright — stack local (`http://localhost`, e2e-delia só `delia.access`)

Bundle servido por imagem reconstruída a partir do worktree (`App-QhdGmp3-.js` + `__federation_expose_App-QhdGmp3-.js`; container `delpi-plugin-ui` reconstruído para expor `audioRecorderErrorMessage` ao remote — correção de mismatch de remote resolvida antes do PASS).

```
PASS full:mic-visible              PASS full:preview-modal
PASS full:single-surface           PASS full:no-textarea-in-preview
PASS full:recording-region         PASS full:no-send-in-preview
PASS full:no-textarea-while-recording  PASS full:no-audio-send
PASS full:no-send-while-recording  PASS full:no-fake-transcribing
PASS full:cancel-finish-controls   PASS full:idle-restored
PASS full:draft-preserved          PASS cancel:draft-preserved
PASS cancel:mic-back               PASS dock:mic-visible (count=1)
PASS dock:recording-region         PASS dock:no-textarea-while-recording
PASS dock:no-send-while-recording  PASS dock:restored
20/20 PASS
```

Screenshots: `shots-voice-dictation/p1-full-recording.png` (superfície única: `● Gravando 00:02` + waveform + Cancelar/Finalizar, **sem textarea**), `p2-full-preview.png`, `p3-full-restored.png`, `p4-dock-recording.png`, `p5-dock.png`.

## 6. STT — bloqueio específico (VD-F01/VD-F03)

Inventário dirigido executado: nenhum owner, provider, API, OpenAPI, adapter ou capability de Speech-to-Text legítimo na plataforma. Requisitos de contrato pendentes (spec §0.3): owner/consumer, request/response tipados, `pt-BR`, MIME/limites, AuthN/AuthZ, consentimento/finalidade, timeout/cancel, erros, idempotência, retenção/logs/observabilidade, postcondition de transcrição. **Nenhum transporte criado.** Quando um contrato for aprovado: `stop` → upload ao STT admitido → `transcribing` real → `review` com texto editável. Regra de **merge** entre transcrição e rascunho pré-existente também requer decisão de UX (`ARCHITECTURE_DECISION_REQUIRED` — VD-07); nenhum merge silencioso foi implementado.

## 7. Deploy produção

`PENDING` — executor sem SSH ao `srv-api`. Procedimento do operador:

1. `git pull` no checkout de produção (HEAD com este rework);
2. rebuild das imagens **plugin-ui** e **delia** sem `VITE_DELIA_AUDIO_QA` (paridade prod);
3. `docker compose up -d plugin-ui delia`;
4. validar `https://minhadelpi.com.br/apps/delia`: mic visível para usuário `delia.access`; gravação substitui textarea; finalizar → prévia local; descartar → rascunho intacto. **Nenhuma** indicação de transcrição deve aparecer.

## 8. Fase/CP-RQ

`C3_EXECUTED=NO; C4_AUTHORIZED=NO; C5_AUTHORIZED=NO; PRODUCTION_READINESS=NOT_PROVEN; CP-333=PLANNED` — inalterados. Nenhum avanço de fase, RBAC, contrato ou flag.
