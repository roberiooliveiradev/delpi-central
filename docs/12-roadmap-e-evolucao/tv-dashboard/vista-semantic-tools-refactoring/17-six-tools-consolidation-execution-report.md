# 17 — VISTA SIX-TOOLS CONSOLIDATION — Execution Report

**Data:** 2026-10-31
**Mandato:** consolidação final da superfície VISTA em exatamente seis
ferramentas semânticas (`get_context`, `read`, `analyze`, `knowledge`,
`execute`, `delete`) — refatoração + migração de consumidores + remoção
das 12 tools/opIds legadas + commit/push `main` + deploy produção.
**Autorização:** solicitante/owner `roberiooliveiradev`, diretiva
explícita "FINAL CONSOLIDATION — SIX TOOLS ONLY"
(`REQUESTER_AUTHORIZATION = RECORDED`, ADR §11).

## Git

| Campo | Valor |
|---|---|
| Base HEAD | `9c1db83865` (`origin/main` na reancoragem) |
| Upstream no push | `44cac120ea` (engineering-api EVA + docs SURI — zero tv-dashboard-api) |
| Commit publicado | `06103630cf` — `feat(tv-dashboard): VISTA six-tools consolidation` |
| Push | `git push HEAD:main` — FF-only, sem force, detached worktree `/tmp/a6-integ` |
| Arquivos alterados | 47 arquivos sob `tv-dashboard-api/` (+5.053 / −10.269 linhas) |
| Conflitos | Nenhum (upstream concorrente não tocou tv-dashboard-api) |
| WIP preservado | Worktree compartilhado `/home/analistaptd/projetos/delpi-central` intocado (WIP de outros agentes preservado; consolidação executada em árvore isolada destacada autorizada pelo brief) |

## Arquitetura

- **ADR:** `docs/architecture/adr-vista-semantic-verbs-surface.md` —
  §11 registra `TARGET_MCP_TOOL_COUNT=6`, `TARGET_GPT_ACTION_COUNT=6`,
  `LEGACY_*=REMOVE_AFTER_CONSUMER_MIGRATION` (executado),
  `DOMAIN_CAPABILITIES=PRESERVE`, `BACKEND_AUTHORITY=UNCHANGED`.
- **Decisão de remoção:** superfície redundante removida; handlers de
  domínio retidos como implementação interna dos verbos.
- **Capability surface:** verbos em `capability_surface.py`
  (read_operations/write_operations/prepare_act_policy projetados em
  nomes neutros; `_neutral_to_actions` mapeia para `vista_*` no
  transporte Actions).
- **Owners:** Keycloak=identidade, Core=RBAC, tv-dashboard-api=domínio,
  VISTA=interface semântica. Sem RBAC/executor/registry paralelos.
- **Existing equivalent:** `PARTIAL` → `COMPLETE` (`semantic_delete`
  adicionado sobre o pipeline canônico).
- **Reuse decision:** `EXTEND` — verbos são adapters puros sobre
  `GptActionsDispatchService` (`semantic_get_context`, `semantic_read`,
  `semantic_analyze`, `semantic_knowledge`, `semantic_execute`,
  `semantic_delete` → preview_change/commit_change/catalog etc.).
- **Contratos:** MCP `tools/list` = 6; OpenAPI = 6 opIds `vista_*`;
  `surface_parity.parity_map` = 6 mapeamentos `vista_* → verbo`;
  exceção documentada `gpt_get_slide_preview_png` (auxiliar Actions,
  read-only, não-parity).
- **Drift resolvido:** idempotência em PREPARE documentada no envelope
  canônico; `confirmation=true` eliminado da superfície pública;
  `tv_data_routes.json` re-sincronizado com o baseline api-delpi
  (drift upstream absorvido no mesmo commit).
- **Drift pendente:** nenhum conhecido.

## Migração

| Legacy tool | Destino semântico | Consumidores migrados |
|---|---|---|
| `list_playlists` | `read` entity=playlist action=list | tests + directives |
| `get_playlist_context` | `read` entity=playlist action=context (+image projection preservada) | tests + directives + wire |
| `get_playlist_history` | `read` entity=playlist_history action=history | tests |
| `get_catalog` | `get_context` action=catalog | tests + directives + branding |
| `search_data_routes` | `read` entity=data_route action=search | tests |
| `inspect_data_model` | `read` entity=data_model action=inspect | tests |
| `preview_data_model` | `analyze` analysis=data_model_preview | tests |
| `preview_data_block` | `analyze` analysis=data_block_preview | tests |
| `get_product_guide` | `knowledge` action=get/search (+read entity=product_guide) | tests + refs |
| `suggest_change` | `analyze` analysis=intent_materialization | tests + directives |
| `prepare_change` | `execute`/`delete` phase=prepare | tests + directives |
| `commit_proposal` | `execute`/`delete` phase=commit | tests + directives |

GPT Actions: `gpt_get_catalog`, `gpt_list_playlists`,
`gpt_get_playlist_context`, `gpt_get_playlist_history`,
`gpt_search_data_routes`, `gpt_inspect_data_model`,
`gpt_preview_data_model`, `gpt_preview_data_block`,
`gpt_get_product_guide`, `gpt_suggest_change`, `gpt_preview_change`,
`gpt_commit_change` → removidos do OpenAPI e de
`GPT_ACTIONS_OPERATION_IDS` (→ `vista_*` ×6).

- **Consumidores internos:** todos migrados e verificados por testes
  (call-sites reescritos para os verbos; assertions de superfície
  atualizadas para contratos semânticos).
- **Consumidores externos:** Custom GPT requer re-import manual do
  OpenAPI consolidado no GPT Builder — quebra deliberada aprovada
  (mandato + ADR §11); sem acesso ao Builder nesta sessão
  (follow-up operacional registrado).
- **Handers internos preservados:** `list_playlists`,
  `get_playlist_context`, `get_playlist_history`, `get_catalog`,
  `search_data_routes`, `inspect_data_model`, `preview_data_model`,
  `preview_data_block`, `get_product_guide`, `suggest_change`,
  `preview_change`, `commit_change` — reutilizados pelos verbos.

## Segurança

- **AuthN:** user-bound (401 sem OAuth em produção; testes de
  identidade verdes).
- **AuthZ:** backend canônico inalterado (RBAC fresco + permissões
  tv-dashboard.* no dispatch).
- **Consentimento:** `confirmation=true` removido de toda a superfície
  pública; planos `confirm` exigem `consent_artifact` + `target_echo`
  (A5); `execute` não aceita ops destrutivas fora do catálogo e
  `delete` restringe-se a block/section/slide.
- **Replay/CAS/idempotência:** serviço canônico de commit reutilizado;
  snapshot replay e conflito de revisão testados.
- **Read-back:** VERIFIED só com leitura autoritativa pós-commit.
- **Bypass search:** rotas `/changes/preview`, `/changes/commit`,
  `/suggest`, `/context`, `/catalog`, `/playlists/**` removidas do
  OpenAPI e dos routers — não resta caminho alternativo de escrita.

## Testes

- **Total:** 2.290 testes na árvore consolidada — **2290/2290 PASS**
  (0 falhas), executados após rebase limpo.
- **Paridade:** `parity_map` (6) == `MCP_TOOL_NAMES` (6) ==
  `GPT_ACTIONS_OPERATION_IDS` (6); gates de drift verdes.
- **Negativos:** sem permissão, ator diverso, artifact
  ausente/expirado/reuso, plano divergente (`PLAN_MISMATCH`),
  operations-no-commit, alvos inválidos, idempotência replay, CAS —
  todos verdes.
- **Outcome semantics:** VERIFIED/UNKNOWN_OUTCOME/partial honestos
  preservados (envelope canônico).
- **E2E/wire:** streamable HTTP + image projection (editor_live)
  migrados e verdes.

## Produção

| Campo | Valor |
|---|---|
| Host | `srv-api` (`operador@192.168.1.237`) |
| Pipeline | `./infra/scripts/up-prod-sequential.sh --build tv-dashboard-api` |
| SHA base prod | `9184127737` → merge `e4ca2801a5` (contém `06103630cf`) |
| Imagem | `infra-tv-dashboard-api` sha256:`44f12ff61c1a875377d2c4dded2caf0d7e599675cca5d401dae5638031fc3dbb` |
| Container | `delpi-tv-dashboard-api` Up — startup limpo, sync catálogo 590 rotas, MCP session manager ativo |
| Migrations | Nenhuma (sem mudança de schema) |
| Gateway | `/apps/tv-dashboard-api` roteando (OpenAPI 200) |
| OpenAPI público | **exatamente 6 operações**: `vista_get_context`, `vista_read`, `vista_analyze`, `vista_knowledge`, `vista_execute`, `vista_delete` |
| MCP discovery | POST `/mcp` → **401** sem OAuth (esperado — user-bound; conformidade certificada pelos testes de descoberta) |
| ChatGPT sync | **NOT VERIFIED** — re-import do OpenAPI no GPT Builder requer acesso operacional externo |
| Rollback | Imagem anterior `sha256:6a6503aaf0bc…` (17 tools, A6) — `git revert 06103630cf` + rebuild redeploy; sem migrations aditivas neste commit; handles pendentes continuam consumíveis pelo serviço canônico de commit preservado. Rollback reintroduz superfície com `confirmation=true` — usar somente como contenção temporária, não como prova de consentimento |

## Veredito

- `INTEGRATION_PASS`
- `CONSUMER_MIGRATION_PASS` — interno; re-import externo do Custom GPT
  é follow-up operacional com breaking change deliberada aprovada
- `CERTIFICATION_PASS` — 2290/2290 na árvore consolidada
- `DEPLOY_VERIFIED`
- `SIX_TOOLS_VERIFIED` — OpenAPI público com exatamente 6 `vista_*`;
  descoberta MCP autenticada pendente do canal OAuth humano
  (registro de seis tools provado por conformance tests)
