# VISTA/TV EXECUTION REPORT — A6 (`execute` semantic tool)

| Campo | Valor |
|---|---|
| BASE HEAD | `2ff4193b8c` (`feat(vista): SEMANTIC_TOOLS_V1 A5`, local) |
| origin/main na baseline | `7086824a1d` (upstream +11 commits; contém A5 como `18b2c192e6`) |
| FINAL HEAD (local) | `31ebb1d27e` — `feat(vista): SEMANTIC_TOOLS_V2 A6` |
| Branch | `main` (sem branch auxiliar; commit direto) |
| Veredito | `PASS` implementação / `BLOCKED_WITH_EVIDENCE` push |

## Root cause validada

O sistema já possuía: pipeline PREPARE/COMMIT governado
(`preview_change`/`commit_change`), PlanCompiler + typed ops, proposal
store HMAC actor-bound, consent foundation A5 (`VistaConsentService` +
challenge persistido + `consent_required`), capability surface neutra.
Gap real: ausência da fachada semântica única `execute` no contrato
canônico (`entity`/`action`/`phase`/`operations`). Hipótese confirmada.

| Campo | Valor |
|---|---|
| EXISTING_EQUIVALENT | `PARTIAL` — fachada não commitada existia no working tree, mas com CONTRACT_DRIFT (sem `entity`/`action`/`phase`; discriminava fase por presença de `proposal_handle`) e scope bleed (incluía `delete` = A7) |
| REUSE_DECISION | `EXTEND` — esqueleto `_semantic_commit` reaproveitado; contrato corrigido para o canônico (doc 10 §5 + ADR D-3); delete preservado no worktree fora do commit (gate A7) |

## Drifts classificados

- `CONTRACT_DRIFT`: implementação anterior usava `ops`/`target` sem os
  Literals fechados `entity="presentation" action="apply_mutation"` e
  sem `phase`. Corrigido no commit.
- `EXECUTION_DRIFT` (baseline): local `main` divergia de `origin/main`
  (A5 duplicado `2ff4193b8c` vs `18b2c192e6`, mesmo conteúdo).
- Working tree concorrente: ~68 arquivos staged + ~200 modificados por
  outros agentes (api-delpi products, commercial, cf plugins,
  engineering, supplies-api SURI, infra) — preservados integralmente.

## Contrato implementado

`execute` — fachada fechada, fases explícitas:

- `phase=prepare` (default): `entity="presentation"` +
  `action="apply_mutation"` + `operations[]` (`{op,args?,as?}` — args
  flattened) + `target?` → `preview_change` canônico. Resposta preserva
  `proposal_handle`, `canCommit`, `risk`, `confirmationPolicy`, `diff`,
  `baseRevision`, `fingerprint`, `consentChallenge`,
  `requiredConfirmation`, `confirmationUnavailable`.
- `phase=commit`: `proposal_handle` + `idempotency_key` +
  `consent_artifact`/`target_echo` → `commit_change`
  (`consent_required=True`). Sem booleano `confirmation` nesta
  superfície — só artifact prova consentimento humano.
- Guards: unknown entity/action → `UNKNOWN_ENTITY`/`UNKNOWN_ACTION`;
  fase inválida → `VALIDATION_ERROR`; `operations[]` em commit →
  `PLAN_MISMATCH` (409); campos de commit em prepare e vice-versa →
  `VALIDATION_ERROR`; `commit_now` só em transporte Actions (MCP →
  `VALIDATION_ERROR`).

## MCP e GPT Actions

- MCP: tool `execute` (ACT) registrada — 17 tools; adapter só traduz
  contrato de transporte; `commit_now` não exposto.
- GPT Actions: `vista_execute` → `POST /gpt-actions/v1/semantic/execute`
  + `Idempotency-Key` header; `x-openai-isConsequential`; descrição ≤300
  chars (budget); OpenAPI artifact regenerado (17 opIds);
  `parity_map += vista_execute→execute`.
- Legadas `prepare_change`/`commit_proposal` intactas (coexistência).

## Segurança e autorização

- `_governed_write_user` (principal humano + fresh RBAC Core + TV_WRITE)
  herdado — zero bypass; VISTA capability ≤ user capability.
- A5: artifact verificado por `(actor, proposal_handle, plan_hash,
  target_ref)`, single-use CONSUMED, `target_echo` byte-igual →
  `CONFIRMATION_MISMATCH`; artifact de outro plano → `CONSENT_MISMATCH`;
  actor diferente → `AUTHZ_DENIED` (403); sem artifact em plano
  `confirm` → `CONFIRMATION_REQUIRED`.

## Testes (377 verdes na superfície afetada)

- `tests/test_vista_execute.py` — 35 novos: contrato (prepare/commit/
  fase inválida/entity/action/campos não autorizados/PLAN_MISMATCH/
  `{op,args,as}` flatten), segurança (sem permissão, principal não-user,
  artifact ausente/de outro plano/echo errado, actor estrangeiro),
  concorrência (CAS `REVISION_CONFLICT`, replay idempotency, proposta
  consumida), equivalência (prepare/commit vs legado), composto
  (create_playlist+slides+block com `as`/`*Ref` preservando ordem),
  single-shot (commit_now direct aplica; confirm ignora).
- Atualizadas expectativas congeladas 16→17 (tools, opIds, parity_map,
  get_context execute.status=implemented).
- MCP conformance + facade + catalog budget + consent foundation +
  unified boundary: verdes.

## Evidência de operações compostas e read-back

- Plano composto selado com `as`/`playlistRef`/`slideRef` intactos na
  `exact_change.ops` da proposta (compilador canônico ordena).
- Commit retorna `status=VERIFIED` via `_verify_postcondition` —
  read-back autoritativo; falha → `OUTCOME_NOT_VERIFIED`.

## Rollback

Superfície 100% aditiva: remover `execute`/`vista_execute` devolve 16
tools/opIds sem tocar legados. Propostas anteriores intactas.

## Residual / pendências

- `semantic_delete`/`tool_delete`/`delete` MCP + `DELETE_VERB_STATUS` +
  `test_vista_execute_delete.py` permanecem **não commitados** no
  worktree (semente A7 — seu contrato também precisará de revisão vs
  doc 10 §6). Suite local com resíduo mostra delta honesto de superfície
  (18 vs 17).
- ADR/doc-10 declaram `idempotency_key` exigido em prepare; o pipeline
  canônico só o consome em commit/commit_now — exigência mantida no
  commit (e em prepare quando `commit_now=true`), desvio documentado.
- Docs `vista-semantic-tools-refactoring/` pré-modificados por sessão
  anterior não foram incluídos neste commit.

## Push — BLOCKED_WITH_EVIDENCE

`git merge origin/main` recusou: 20 arquivos upstream-changed
coincidem com WIP de outros agentes (supplies-api SURI, plugins
cf/engineering, docs cf/commercial, infra/docker-compose.yml). Não
commito nem sobrescrevo trabalho alheio; `stash` exige autorização.
**Ação do usuário necessária**: commitar o WIP alheio ou autorizar
stash → então `merge`/`rebase` + push de `31ebb1d27e` (+ este doc).

## Próximo bounded step

A7 — `delete` semântica: revisar contrato do resíduo vs doc 10 §6
(`entity`/`action:"delete"`/`ref`/`playlist_ref`/`phase`), adaptar ao
`_semantic_commit` já canônico, gate de consent idem, testes próprios.
