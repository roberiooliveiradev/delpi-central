# 01 — Current State Inventory (VISTA / TV Dashboard)

HEAD de inspeção: `28943d4d9b` · 2026-10-30 · Owner: `tv-dashboard-api`

## 1. Arquitetura canônica vigente

Fonte: `tv-dashboard-api/docs/architecture/adr-vista-specialist-capability-surfaces.md`
(DECIDED, 2026-09-22 + amendments) e
`tv-dashboard-api/docs/integrations/vista-capability-matrix.md` (CURRENT).

```text
TV Dashboard domain (PresentationMutation / TvPresentationPatchV1)
  → TvPresentationWriteService (canonical write boundary)
    → GptActionsDispatchService (transport-neutral, shared)
      → capability_surface.py (canonical neutral model, uma só fonte)
        → transport="actions": projeção via parity_map⁻¹ + envelope
          mechanics (commit_now) — nunca aparece no MCP
        → transport="mcp": projeção canônica sem artefatos Actions
    → HTTP domain API (editor/preview/TV)
    → GPT Actions adapter (/gpt-actions/v1 — 12 ops)
    → MCP adapter (/mcp — 12 tools, mesmo dispatch)
    → DÉLIA capability adapter (TARGET — sem código neste HEAD)
```

Decisões ativas do ADR que a fase 2 deve respeitar ou revisar
**explicitamente**:
- item 8: *"Do not adopt TÉO entity surface (`search_records` /
  `prepare_record_change`) — VISTA is playlist/presentation workflow,
  not multi-entity CRUD."* — a superfície atual de 12 tools é **decisão
  arquitetural registrada**, não acidente. Convergir para 6 verbos
  exige supersession documentada deste item.
- item 4: *"New typed presentation op ≠ new GPT Action"* — o catálogo
  de 32 typed ops já é separado da superfície de transporte.
- item 6: proibido proxy genérico / SQL / HTTP arbitrário / RBAC local.

## 2. MCP tools (12) — `tv_app/interface/mcp/server.py` + `tool_bridge.py`

| Tool | Classe | Bridge → dispatch | Evidência |
|---|---|---|---|
| `list_playlists` | READ | `tool_list_playlists` → `_dispatch.list_playlists` | `tool_bridge.py:240` |
| `get_playlist_context` | READ | → `_dispatch.get_playlist_context` | `tool_bridge.py:248` |
| `get_playlist_history` | READ | → `_dispatch.get_playlist_history` | `tool_bridge.py:274` |
| `get_catalog` | DISCOVERY | → `_dispatch.get_catalog(transport="mcp")` | `tool_bridge.py:295` |
| `search_data_routes` | READ | → `_dispatch.search_data_routes` | `tool_bridge.py:303` |
| `inspect_data_model` | READ | → `_dispatch.inspect_data_model` | `tool_bridge.py:323` |
| `preview_data_model` | ANALYSIS | → `_dispatch.preview_data_model` | `tool_bridge.py:345` |
| `preview_data_block` | ANALYSIS | → `_dispatch.preview_data_block` | `tool_bridge.py:376` |
| `get_product_guide` | READ | → `_dispatch.get_product_guide` | `tool_bridge.py:412` |
| `suggest_change` | ANALYSIS | → `_dispatch.suggest_change` (NL→typed ops, determinístico) | `tool_bridge.py:430` |
| `prepare_change` | ACT (PREPARE) | → `_dispatch.preview_change(commit_now=False)` | `tool_bridge.py:480` |
| `commit_proposal` | ACT (COMMIT) | → `_dispatch.commit_change` | `tool_bridge.py:513` |

Todas as 12 delegam ao **mesmo** `GptActionsDispatchService`
(`tool_bridge.py:51`) — a diferença MCP↔Actions é só de projeção do
catálogo, não de execução.

## 3. GPT Actions (12) — `/gpt-actions/v1` + OpenAPI gerado

`GPT_ACTIONS_OPERATION_IDS` (`application/gpt_actions/__init__.py:10`):
`gpt_get_catalog`, `gpt_list_playlists`, `gpt_get_playlist_context`,
`gpt_search_data_routes`, `gpt_preview_data_block`,
`gpt_preview_data_model`, `gpt_inspect_data_model`,
`gpt_get_playlist_history`, `gpt_get_product_guide`,
`gpt_suggest_change`, `gpt_preview_change`, `gpt_commit_change`.

Paridade 1:1 com MCP via `surface_parity.parity_map`
(`vista_agent_intelligence.json`); OpenAPI gerado por
`openapi_builder.py` → `docs/gpt-actions/openapi-gpt-actions.json`
(12 paths, `/gpt-actions/v1/{catalog,playlists,data-routes,
data-preview,data-model-preview,data-models/inspect,playlists/{id}/history,
product-guides,changes/suggest,changes/preview,changes/commit}`).

Rotas HTTP do adapter: `interface/http/routes/gpt_actions_routes.py`
(15 decorators: 12 ops + `GET /slide-previews/{token}` + rota técnica).
Envelope `{success, message, data}`; `Idempotency-Key` header ou body.

## 4. PresentationMutation — boundary e catálogo

- **Catalog**: `tv_app/content/presentation_ops_content.json`,
  `catalogVersion=2026.10.05.presentation-authority.datamodel-patch.lossless`
  — **32 typed ops** (dict em `operations`; verificado:
  `delete_block`, `delete_slide`, `delete_section` =
  `confirmationPolicy=confirm`; `delete_data_model` = `direct` —
  ver gap G-02).
- **PlanCompiler**
  (`application/services/data/presentation_mutation/plan_compiler.py`):
  topo-sort por `produces`/`consumes` + aliases `as`/`*Ref`;
  preview com IDs sintéticos; ACT binda IDs reais;
  `DEPENDENCY_UNSATISFIABLE` em planos insatisfatórios.
  Todos os 32 ops declaram produces/consumes.
- **Mutation engine**: `presentation_mutation.PresentationPatchService`
  — deep-merge nested (`style`/`frame`/`dataBinding`/`background`),
  `null` explícito limpa (task 029: ausente = manter).
- **Write boundary**: `TvPresentationWriteService` — mesma fronteira
  do editor UI.
- **NL materializer**: `PresentationSuggestOpsService` — NL→typed ops
  determinístico, catálogo-driven, **sem LLM no BFF**
  (`presentation_suggest_ops_service.py:1`).

## 5. Ciclo de write governado — GOVERNED_PREPARE_COMMIT_V2

`commit_service.py` (~1700 linhas):
- `suggest_change` (opcional) → `prepare_change`/`gpt_preview_change`
  minta `proposal_handle` opaco, HMAC-signed, actor-bound, single-use,
  TTL'd (`proposal_store.py`, **in-process — ACCEPT_WITH_RESIDUAL**).
- Actions-only: `commit_now=true` + confirmation + política `direct`
  → PREPARE+COMMIT no mesmo request (`commit_now_applied`,
  `capability_surface._project_for_actions:271`).
- `commit_proposal`/`gpt_commit_change`: handle exato +
  `idempotency_key` + `confirmation` boolean **declarado pelo modelo**
  quando `confirmationPolicy=confirm`.
- Pós-commit: read-back autoritativo → `VERIFIED` /
  `OUTCOME_NOT_VERIFIED` / `PARTIAL_COMMIT` (`commit_service.py:1193+`,
  `_verify_postcondition:1253`).
- Handles inventados → `PROPOSAL_NOT_FOUND`; replay de handle → negado
  (single-use).

## 6. Capability surface canônica

`capability_surface.py`: um único modelo neutral → duas projeções.
Entidades: `playlist` (ENTITY, read-only na superfície).
Workflows: `presentation_change` (WORKFLOW — suggest/prepare/commit,
`typed_ops_count=32`, `destructive_typed_ops` derivado do catálogo).
Analyses: `data_route_search`, `data_block_preview`,
`domain_intent_materialization`, `product_guide` (MCP-primary),
`playlist_history` (MCP-primary), `data_model_lifecycle`
(5 write ops declaradas dentro do analysis entry — ver gap G-07).
`agent_directives` vem de `vista_agent_intelligence.json`
(MCP-primary `character`, orçamento Actions ≤100 KiB com
`test_gpt_actions_catalog_budget.py`).

## 7. Inteligência e instruções

`vista_agent_intelligence.json` v`2026.10.16.4` — 40 seções
top-level (persona/narrative/story + heurísticas mutáveis). Projetado
como `agent_directives` no catálogo; Builder Instructions
(`specialist-instructions.md`) = stable-only, gate de budget +
leak-gate (`test_vista_builder_instructions_budget.py`).

## 8. Backend REST — superfície total (~90 endpoints, 14 routers)

`interface/http/routes/`: characters, content (presets/templates
import/export, product-guides, branch-scope, health), data_api
(`/m/*`, builder sessions, routes, openapi sync, display-format,
preview-block/model, validate-config, copilot/*), data_routes,
gpt_actions, media (CRUD + uploads + optimize + poster),
native_screen, playlist_history (list/get/**restore**), playlist
(CRUD completo + edit-invites + import + activate/deactivate +
preview-payload + public-url + qr + duplicate + export +
regenerate-token + shares), presentation_realtime (WS), public
(`/present/{token}` + media), section (CRUD + ensure-main + reorder),
slide (CRUD + from-preset + reorder + rendered-preview +
preview-data-block + presentation-mutations + duplicate), template
(CRUD + from-slide + import + publish/unpublish/archive/clone/export).

## 9. Superfícies retired (não reativar)

- `POST /data/copilot/*` → **410 Gone** (ADR 7c).
- Chat skill/tool `tv_dashboard_copilot` removido; MFE Copilot dock
  retired; Chat → `tv_dashboard_handoff` (direct answer → VISTA).
- Aliases `tv_copilot_*` / `TvCopilotPatch*` removidos (ADR 7d/7e).

## 10. Runtime/deploy

- Container `delpi-tv-dashboard-api` (Docker `infra` compose),
  health `/apps/tv-dashboard-api/health` 200; catalog sem auth 401
  fail-closed; OAuth discovery 200 — verificado local e em
  `operador@192.168.1.237` (prod) neste HEAD.
- MCP mount: `interface/mcp/asgi.py` + `routes.py` (metadata router
  shared `delpi_mcp.resource_contract`).
- Avatar oficial: rota pública `GET /characters/{id}/avatar/{filename}`
  (`characters_routes.py:38`, `get_public_character_avatar`) +
  `agent_directives.character.avatar_reference` (repo path) —
  asset `tv_app/content/characters/vista/avatar-v2.jpg`.

## 11. Testes (superfícies relevantes)

175 arquivos de teste; 28 arquivos `test_*{mcp,vista,gpt}*`. Principais:
`test_mcp_platform_conformance.py`, `test_mcp_streamable_http_wire.py`,
`test_vista_mcp_{read,write}_surface.py`, `test_vista_mcp_client_migration.py`,
`test_gpt_actions_{catalog_budget,facade,response_compact}.py`,
`test_gpt_*` (data routes, datamodel, preview, route field exposure),
`test_vista_*` (intelligence, unified boundary, playlist history,
knowledge orchestration, design intelligence, display format bridge,
avatar discovery projection, character avatar public route, persona
integration, builder instructions budget, ready-slide corpus gate,
eval telemetry).
