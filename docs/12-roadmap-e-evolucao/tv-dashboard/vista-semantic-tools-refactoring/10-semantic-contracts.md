# 10 — Semantic Contracts (proposta — nada implementado)

Contratos-alvo das 6 tools. Todos os `entity`/`action` são
**Literals fechados** — dispatch por allowlist, nunca por URL,
método, nome de função, SQL ou código.

## Convenções comuns

- Erros estruturados: `{success:false, error:{code, message, details?}}`
  — `code` ∈ {`VALIDATION_ERROR`, `UNKNOWN_ENTITY`, `UNKNOWN_ACTION`,
  `AUTH_REQUIRED` (401), `FORBIDDEN` (403), `PROPOSAL_NOT_FOUND`,
  `CONFIRMATION_REQUIRED`, `CONFIRMATION_MISMATCH`, `REVISION_CONFLICT`
  (409), `NOT_IMPLEMENTED` (501, status honesto), `INTERNAL`}.
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
  pós-AuthZ...], confirmationModel:{destructive:"target_echo",
  elicitation:"host_dependent"}, catalogVersion}`
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

## 5. `execute`

```json
{ "entity": "presentation",
  "action": "apply_mutation",
  "phase": "prepare"|"commit",
  "operations": [ {"op":"<typed_op>","args":{...},"as":"<alias>?"}, ...],
  "proposal_handle": "<opaque>?",      // phase=commit
  "idempotency_key": "<key>",          // ambas as phases
  "target_echo": "<id do alvo>?",      // ops confirm (D-5)
  "commit_now": false }                // Actions-only mecânica
```

- `phase=prepare` → `preview_change(commit_now=false)`: valida ops,
  compila plano (topo-sort produces/consumes), minta proposal
  opaco (HMAC, actor-bound, TTL, single-use), devolve diff+preview+
  `requiredConfirmation`.
- `phase=commit` → `commit_change`: revalida ator/TTL/single-use/
  `target_echo`, executa ops em sequência com CAS por op
  (`assert_expected_revision` chain), read-back → `VERIFIED |
  OUTCOME_NOT_VERIFIED | PARTIAL_COMMIT`.
- `commit_now` (Actions, política `direct`, confirmação cumprida):
  single-shot prepare+commit — mecânica já existente.
- Comportamentos explícitos: validação → `VALIDATION_ERROR`; op fora
  do catálogo → `UNKNOWN_ACTION`; CAS → `REVISION_CONFLICT` (409 c/
  `currentRevision`); parcial → `PARTIAL_COMMIT` + estado real;
  retry → mesmo `idempotency_key` + single-use handle = seguro;
  resultado desconhecido → `OUTCOME_NOT_VERIFIED` honesto, nunca
  sucesso falso.

## 6. `delete`

```json
{ "entity": "block"|"section"|"slide",
  "action": "delete",
  "ref": "<id do alvo>",
  "playlist_ref": "<playlist>",
  "phase": "prepare"|"commit",
  "proposal_handle": "?", "idempotency_key": "<key>",
  "target_echo": "<ref exato>" }
```

- `entity` mapeia 1:1 para os 3 typed ops `confirm`
  (`delete_block|delete_section|delete_slide`).
- `target_echo` **obrigatório** em `phase=commit` — deve ser
  byte-igual ao `ref`; mismatch → `CONFIRMATION_MISMATCH`.
- `ctx.elicit` (MCP, quando o host suporta) como prova adicional;
  ausência não bloqueia se `target_echo` correto (echo é a prova
  transport-neutral).
- Delega integralmente ao envelope PREPARE/COMMIT — nenhum executor
  paralelo.

## Compatibilidade

- MCP: 6 novas tools com estes schemas; 12 legadas marcadas
  `deprecated` (descrição + `x-deprecated`).
- Actions: 6 opIds `vista_*`; 12 `gpt_*` com `deprecated: true` no
  OpenAPI gerado.
- `agent_directives`/`specialist-instructions`: reescritos para o
  vocabulário novo — apontam para o catálogo, não re-declaram ops.
