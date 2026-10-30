# 10 — Semantic Contracts (proposta — nada implementado)

Contratos-alvo das 6 tools. Todos os `entity`/`action` são
**Literals fechados** — dispatch por allowlist, nunca por URL,
método, nome de função, SQL ou código.

## Convenções comuns

- Erros estruturados: `{success:false, error:{code, message, details?}}`
  — `code` ∈ {`VALIDATION_ERROR`, `UNKNOWN_ENTITY`, `UNKNOWN_ACTION`,
  `AUTH_REQUIRED` (401), `FORBIDDEN` (403), `PROPOSAL_NOT_FOUND`,
  `PLAN_MISMATCH`, `CONFIRMATION_REQUIRED`, `CONFIRMATION_MISMATCH`,
  `CONFIRMATION_UNAVAILABLE` (transporte/host sem mecanismo de
  consentimento — bloqueio explícito), `CONSENT_MISMATCH` (artifact
  não vincula actor/proposta/alvo), `DEPENDENCY_UNRESOLVED`,
  `REVISION_CONFLICT` (409), `NOT_IMPLEMENTED` (501, status
  honesto), `INTERNAL`}.
- `VISTA capability ≤ user capability` — catálogo informa, backend
  autoriza; nenhum campo do schema é autoridade.
- Paginação: `pagination: {limit ≤ 100, cursor?}`; respostas paginadas
  levam `nextCursor`.
- `idempotency_key` em toda operação de escrita.
- `status` por capability: `proven | planned | not_implemented`.

## 1. `get_context`

```json
{ "action": "context" | "catalog" }
```

- `context` → `{assistant:{id, displayName, avatarReference?},
  principal:{type:"user"}, effectiveCapabilities:[...ops permitidas
  pós-AuthZ...], confirmationModel:{destructive:
  "consent_artifact_required", targetCheck:"target_echo",
  elicitation:"host_dependent", fallback:"CONFIRMATION_UNAVAILABLE"},
  catalogVersion}`
- `catalog` → capability surface completa (entidades, ações, status
  honesto, typed_ops disponíveis, `agent_directives`).

## 2. `read`

```json
{ "entity": "playlist"|"playlist_history"|"data_route"|"data_model"
            |"product_guide"|"slide_preset"|"media_asset",
  "action": "list"|"get"|"context"|"history"|"search"|"inspect"
            |"guide",
  "ref": "<id>?",
  "filters": { "..." : "campos declarados por ação" },
  "pagination": {...}, "projection": ["campo",...]? }
```

Mapeamento (capability → handler existente):
| entity.action | handler atual |
|---|---|
| playlist.list | `list_playlists` |
| playlist.get / playlist.context | `get_playlist_context` |
| playlist_history.history | `get_playlist_history` |
| data_route.search | `search_data_routes` |
| data_model.inspect | `inspect_data_model` |
| product_guide.guide | `get_product_guide` |
| slide_preset.list *(novo, D-6)* | `GET /slide-presets` |
| media_asset.list *(novo, D-6)* | `GET /media` |

`filters` rejeita chaves não declaradas (padrão CAIO `_filters`).

## 3. `analyze`

```json
{ "analysis": "data_block_preview"|"data_model_preview"
              |"intent_materialization",
  "subjectRefs": {"playlistId": "...", "blockId": "...", "...": "..."},
  "parameters": { "...": "por análise" } }
```

| analysis | handler atual |
|---|---|
| data_block_preview | `preview_data_block` (rota real) |
| data_model_preview | `preview_data_model` |
| intent_materialization | `suggest_change` (NL→typed ops) |

Saída inclui `evidenceClass` (`fact|calculation|preview`) quando
aplicável — alinhamento ao rótulo honesto do padrão SURI.

## 4. `knowledge`

```json
{ "action": "search"|"get", "topic": "<guide topic>?", "query": "?",
  "knowledgeId": "?", "limit": 20 }
```

Mapeia para `get_product_guide` + conteúdo estático do domínio.
**Evolução necessária**: entradas do guia ganham `source`/`locator`/
`evidence_class` (padrão SURI `suri_knowledge.json`) — corpus citável,
não texto solto.

## 5. `execute` (contrato revisado — fidelidade à proposal)

### `phase=prepare` — campos exigidos

```json
{ "entity": "presentation",
  "action": "apply_mutation",
  "operations": [ {"op":"<typed_op>","args":{...},"as":"<alias>?"}, ...],
  "idempotency_key": "<key>" }
```

- `entity`/`action`/`operations`/`idempotency_key` — obrigatórios.
- `operations[]` ≤ 20 entradas (limite proposto, alinhado PlanCompiler).
- Resposta: `proposal_handle` (opaco, HMAC, actor-bound, TTL,
  single-use) + `plan_fingerprint` + diff/preview + `base_revision`
  + `required_confirmation` (lista de ops `confirm` do plano e seus
  alvos — sem expor internals) + `consent_challenge` (quando houver
  op `confirm` — ver D-5).

### `phase=commit` — campos exigidos

```json
{ "entity": "presentation",
  "action": "apply_mutation",
  "phase": "commit",
  "proposal_handle": "<opaque>",
  "idempotency_key": "<key>",
  "target_echo": "<id do alvo confirm>?",   // identidade do alvo
  "consent_artifact": "<token|challenge_ack>?" }  // prova humana
```

- `proposal_handle` **vincula o plano preparado** — o commit executa
  o plano selado no prepare, não um plano reenviado.
- **`operations[]` NÃO é reenviado no commit** — o handle é a
  referência imutável do plano; reenviar permitiria substituição de
  plano. Se enviado por robustez, o backend **deve** rejeitar
  divergência de fingerprint (`PLAN_MISMATCH`).
- `target_echo`: verificação de identidade do alvo (anti wrong-object)
  — obrigatório quando o plano contém ops `confirm`; **não é prova
  de consentimento** (ver D-5).
- `consent_artifact`: prova de ação humana emitida por canal
  verificável (ack de `ctx.elicit` em host capaz, ou token do
  consent challenge backend-mediado). **Obrigatório para ops
  `confirm`.** Ausência → `CONFIRMATION_REQUIRED`; ausência de
  mecanismo no transporte → `CONFIRMATION_UNAVAILABLE` (bloqueio,
  sem downgrade).

### Semânticas

- **Idempotência**: `idempotency_key` + handle single-use — retry
  seguro; replay de handle → `PROPOSAL_NOT_FOUND`.
- **CAS**: `assert_expected_revision` chain por op; conflito →
  `REVISION_CONFLICT` 409 com `currentRevision`/`revisionBefore`/
  `revisionAfter`.
- **Parcial**: falha em op i → `PARTIAL_COMMIT` + estado real dos
  aplicados; sem rollback compensatório (limitação documentada).
- **Single-shot** (`commit_now`, Actions-only): permitido **somente
  quando** (a) política de todas as ops é `direct`, (b) nenhuma op
  `confirm` no plano, (c) AuthZ passa. Com op `confirm` →
  `CONFIRMATION_REQUIRED` (o host deve usar two-phase).
- **Confirmação humana interrompe o fluxo**: entre prepare e commit
  o humano age fora-banda (elicit ou Portal challenge); o modelo
  não avança o plano sozinho — commit sem artifact válido bloqueia.
- **Resultado desconhecido**: `OUTCOME_NOT_VERIFIED` — nunca
  sucesso afirmado sem read-back.

## 6. `delete`

```json
{ "entity": "block"|"section"|"slide",
  "action": "delete",
  "ref": "<id do alvo>",
  "playlist_ref": "<playlist>",
  "phase": "prepare"|"commit",
  "proposal_handle": "?", "idempotency_key": "<key>",
  "target_echo": "<ref exato>",
  "consent_artifact": "<token|challenge_ack>" }
```

- `entity` mapeia 1:1 para os 3 typed ops `confirm`
  (`delete_block|delete_section|delete_slide`).
- `phase=prepare` devolve impacto + `consent_challenge` para o
  humano decidir.
- `phase=commit` exige **dois artefatos distintos**:
  - `target_echo` byte-igual ao `ref` — verificação de identidade
    do alvo (anti wrong-object); mismatch → `CONFIRMATION_MISMATCH`;
  - `consent_artifact` — prova de ação humana (ack de elicit em
    host MCP capaz, ou token do consent challenge backend-mediado).
    Sem artifact válido → `CONFIRMATION_REQUIRED`; transporte sem
    mecanismo → `CONFIRMATION_UNAVAILABLE` (bloqueio explícito,
    **nunca** fallback silencioso para echo-como-prova).
- Delega integralmente ao envelope PREPARE/COMMIT — nenhum executor
  paralelo.

## Compatibilidade

- MCP: 6 novas tools com estes schemas; 12 legadas marcadas
  `deprecated` (descrição + `x-deprecated`).
- Actions: 6 opIds `vista_*`; 12 `gpt_*` com `deprecated: true` no
  OpenAPI gerado.
- `agent_directives`/`specialist-instructions`: reescritos para o
  vocabulário novo — apontam para o catálogo, não re-declaram ops.
