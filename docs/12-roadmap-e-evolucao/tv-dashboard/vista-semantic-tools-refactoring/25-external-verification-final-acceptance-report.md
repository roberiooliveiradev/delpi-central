# 25 — VISTA/TV PROGRAM B EXTERNAL VERIFICATION & FINAL ACCEPTANCE REPORT

**Data:** 2026-10-31
**HEAD:** `16764ae9a4` (= origin/main)
**Escopo:** homologação externa final — A5 human channel, GPT Builder
sync, drift documental. Sem novas features/tools/Actions.

## Gate A — Consentimento humano A5

**Backend: `PASS`** (`BACKEND_CONSENT_PASS`)

Endpoints revalidados no HEAD (não presunção de histórico):

- `GET /vista/consent/proposals/{proposal_id}` — view da proposta
  selada (router `vista_consent_routes`, registrado em `main.py:154`).
- `POST /vista/consent/challenges/{challenge_id}/approve` — aprovação
  humana autenticada com **step-up claims** (`assert_step_up_token`).

Máquina `VistaConsentService` (coberta por
`test_vista_consent_foundation.py`):

- challenge bind → `proposal_id + actor_sub + plan_hash + target_ref`.
- `verify_for_commit`: artifact obrigatório; desconhecido→404;
  mismatch ator/plano/proposta→403; PENDING→400; reutilizado/expirado→409.
- `consume_for_commit`: single-use APPROVED→CONSUMED (anti-replay).
- `target_echo` valida identidade do alvo (não consentimento).
- `CONFIRMATION_UNAVAILABLE` fail-closed sem canal (testado).

**Canal humano externo: `EXTERNAL_HUMAN_CHANNEL_PENDING`**

O endpoint existe e está certificado em backend; a experiência humana
de aprovação no Portal/GPT Builder não pode ser exercitada a partir
desta sessão CLI (sem acesso à UI autenticada com Keycloak). **Sem
evidência humana real, não se declara `EXTERNAL_HUMAN_CHANNEL_PASS`.**

### Handoff para o operador — homologação do canal humano A5

1. Em ambiente homologado (ou prod com playlist de teste criada por
   fixture autorizada), autenticar usuário com `tv-dashboard.write`.
2. Via VISTA (MCP ou GPT Actions), chamar `delete` `phase=prepare` com
   `entity=playlist` + `target.playlistId` da fixture → obter
   `proposal_handle` + `consentChallenge.challengeId`.
3. No canal confiável (Portal autenticado ou chamada OAuth direta),
   abrir `GET /apps/tv-dashboard-api/vista/consent/proposals/{handle_id}`
   — conferir alvo/impacto.
4. Aprovar: `POST /vista/consent/challenges/{challengeId}/approve`
   com JWT step-up → artifact = `challenge_id`.
5. Chamar `delete` `phase=commit` com `proposal_handle` +
   `consent_artifact={challenge_id}` + `target_echo=playlistId` →
   esperado `status=VERIFIED` + fixture deletada.
6. Evidência a devolver: timestamps dos passos, `challengeId`
   (não o valor do artifact), resultado do commit, screenshot opcional.

## Gate B — GPT Builder / Actions sync

**`GPT_BUILDER_SYNC_PENDING_OPERATOR`** — sem acesso ao GPT Builder a
partir desta sessão. Evidência atual:

- OpenAPI público em produção contém **exatamente 6** operationIds
  `vista_*` (verificado em `srv-api` após cada onda, última imagem
  `sha256:778924bca211`).
- Consumidor MCP real ativo em prod (`POST /mcp/ 200 OK` em logs).

### Handoff para o operador — sync do GPT Builder

1. Abrir o GPT Custom VISTA no ChatGPT Builder (owner do produto).
2. Em **Actions**, substituir o schema pelo OpenAPI atual:
   `https://<host>/apps/tv-dashboard-api/gpt-actions/v1/openapi.json`
   (fonte canônica: `docs/gpt-actions/openapi-gpt-actions.json`,
   regenerado a cada wave — mesmas 6 Actions).
3. Confirmar: exatamente 6 operations (`vista_get_context`,
   `vista_read`, `vista_analyze`, `vista_knowledge`, `vista_execute`,
   `vista_delete`) — zero `gpt_*` legadas.
4. Preservar: identidade, instruções, OAuth/Auth configuration.
5. Salvar e testar: `vista_get_context`, `vista_read` (list playlists),
   `vista_knowledge` — operações read-only seguras.
6. Evidência a devolver: versão do schema importado, print das 6
   Actions, resultado dos smokes.

## Gate C — Drift documental

`DOCUMENTATION_DRIFT_RESOLVED`: doc 24 contagem corrigida
`8/10 → 9/10 gates PASS` (G1–G4 + G6–G10 = 9; G5 PENDING).

## Matriz G1–G10 (estado final)

| Gate | Veredito |
|---|---|
| G1 HEAD | PASS |
| G2 Six-tools | PASS |
| G3 Capabilities | PASS |
| G4 AuthZ | PASS |
| G5 Consentimento | `BACKEND_CONSENT_PASS` + `EXTERNAL_HUMAN_CHANNEL_PENDING` |
| G6 Shares/invites | PASS |
| G7 MDD | PASS (SINGLE_INSTANCE_CONSTRAINT documentada) |
| G8 Paridade | PASS |
| G9 Regressão | PASS (2357/2357) |
| G10 Runtime | PASS |

**Contagem: 9 PASS / 1 PENDING**

## Preservações registradas (não corrigidas nesta homologação)

- `_PreviewStore` in-memory + `SINGLE_INSTANCE_CONSTRAINT` +
  TTL 900s + token não actor-bound (contrato vigente — reavaliar
  antes de escalar réplicas; `NO_PATCH_REQUIRED`).
- Canal humano/Builder: sem patch especulativo — são verificações
  operacionais, não defeitos de engenharia.

## Veredito

**`PROGRAM_B_FINAL_ACCEPTANCE = PENDING_EXTERNAL_VERIFICATION`**

Critério de encerramento: quando o operador executar os dois handoffs
acima e devolver evidência (aprovação humana real + 6 Actions
reconhecidas no GPT externo), o veredito converte para
`PASS` sem nova intervenção de engenharia — os sistemas
já estão certificados do lado backend/runtime.
