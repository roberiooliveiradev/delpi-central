# Catálogo de ops tipadas — PresentationMutation

> **Status:** catálogo canônico em `presentation_ops_content.json` + serviços `presentation_*`.
> Mutation: **PresentationMutation** (`presentation_mutation/`) → `TvPresentationWriteService`.
> Consumidor IA: **VISTA** `/gpt-actions/v1` (preview/commit).
> Superfície HTTP legada `/data/copilot/*` → **410 Gone** (stubs de compatibilidade).

---

## Objetivo

Patches tipados no modelo de slide/playlist via VISTA / PresentationMutation. **Não** gera Power Query M. Present permanece viewer puro (`SlideDataResolutionService`).

**Ownership:** o catálogo de capabilities vive **somente** em `tv-dashboard-api` (`PresentationOpsContentService`). Feature nova de TV = mudança neste pacote (+ UI MFE se houver). VISTA projeta o catálogo via `gpt_get_catalog` — sem lista de ops embutida no Chat.

## Envelope

```json
{
  "target": { "playlistId": "…", "slideId": "…", "selectedBlockIds": [] },
  "ops": [
    { "op": "upsert_data_source", "operationId": "…", "params": {}, "blockId": "…" },
    { "op": "set_data_transform", "blockId": "…", "steps": [] },
    { "op": "upsert_block", "block": { } },
    { "op": "delete_block", "blockId": "…" },
    { "op": "bind_visual", "visualId": "…", "dataSourceId": "…" },
    { "op": "patch_native_config", "patch": { "background": {} } },
    { "op": "add_slide_from_preset", "presetKey": "…", "branch": "01" },
    { "op": "add_blank_slide", "title": "…" },
    { "op": "update_slide", "title": "…", "durationSec": 20, "isActive": true },
    { "op": "reorder_slides", "items": [{ "id": "…", "sortOrder": 0 }] },
    { "op": "delete_slide" },
    { "op": "upsert_section", "name": "…", "sectionId": "…" },
    { "op": "delete_section", "sectionId": "…" },
    { "op": "move_slide_to_section", "sectionId": "…" },
    { "op": "create_playlist", "name": "…", "seedPresetKeys": ["…"] }
  ],
  "catalogVersion": "…"
}
```

## Discovery (contrato)

| Método | Path | Status | Notas |
|--------|------|--------|-------|
| `*` | `/data/copilot/*` | **410 Gone** | Legado; use VISTA `/gpt-actions/v1` |
| `GET` | `/gpt-actions/v1/catalog` | canônico | Capabilities + `agent_directives` |
| `POST` | `/data/builder/sessions/{id}/to-presentation-ops` | `TV_WRITE` | Materialize → mesmas ops do catálogo |

### `operations`: contrato executável

Cada op tem uma única spec em `operations`: `requiresPlaylist`, `requiresSlide`,
`inputSchema`, `risk`, `confirmationPolicy` e `sideEffectHints`. O planner e o
patch service consomem a mesma spec; capability nova não pode repetir esses campos.

- `direct`: criação/alteração inequívoca é aplicada no mesmo turno.
- `confirm`: somente `delete_block`, `delete_slide` e `delete_section`.
- `add_blank_slide` requer playlist, mas não slide aberto.
- mutações de canvas requerem playlist + slide; sem contexto, o planner devolve
  `status=clarification` e zero ops.

O planner de ops (PresentationMutation / VISTA `gpt_suggest_change`) retorna `status: ready | clarification | unsupported | error`,
`confirmationPolicy`, `risk`, requisitos agregados e os hints. Uma composição
herda a política mais restritiva entre suas ops.

### Shape de `capabilities[]`

Cada item (declarativo em `presentation_ops_content.json`):

| Campo | Papel |
|-------|--------|
| `key` | Id estável da capability |
| `op` | Nome da op no envelope |
| `whenToUse` | Texto prescritivo (injetado no prompt addon da AI) |
| `contentMarkers` / `excludeMarkers` | Matching NL genérico |
| `actionTermSet` | `create` \| `mutation` \| `any` |
| `payloadTemplate` / `payloadTemplates` | Template(s) JSON com placeholders; composites usam array |
| `requiresFilledPlaceholders` | Ex.: `["backgroundColor"]` — não emite op se vazio |
| `isComposite` | Capability que expande em várias ops (ex.: KPI = fonte + view + bind) |

Schema, target, risco e efeitos pertencem a `operations`, não às capabilities.

### Placeholders do planner de ops

| Placeholder | Origem |
|-------------|--------|
| `quoted` | Texto entre aspas na mensagem |
| `selectedBlockId` / `slideId` / `playlistId` / … | `hostContext` |
| `operationId` / `routeLabel` | `nlRouteHints` / score no catálogo → fallback host |
| `dataSourceId` / `selectedVisualId` | host (`selectedDataSourceId`, lista `dataSources`, foco) |
| `backgroundColor` | `colorVocabulary` (PT→hex) ou `#rrggbb` na mensagem |
| `paramsJson` / `branch` | `paramHints` (ex.: filial 01/02) — sem inventar |
| `transformStepsJson` | `transformStepHints` (ex.: top 10) — tipado; sem M/SQL |
| `fieldLabelsJson` | duas aspas na mensagem (campo → rótulo) |
| `newDataSourceId` / `newVisualId` | Gerados no BFF para create/composites |

Fundo canônico: `{ "type": "color", "value": "#…" }` (mesmo shape do enrich / ribbon). Sem cor resolvida → `ops: []` + `suggestNeedColor`.

Composites rota → visual + bind:

| Capability | Ops |
|------------|-----|
| `add_kpi_from_route` | fonte + `kpi_view` + `bind_visual` |
| `add_chart_from_route` | fonte + `chart_view` + `bind_visual` |
| `add_table_from_route` | fonte + `table_view` + `bind_visual` |
| `create_data_source` | só `data_source` (`newDataSourceId`) |
| `update_data_source` | `upsert_data_source` no `dataSourceId` do host |

`catalogVersion` muda quando o JSON de capabilities muda. A AI cacheia por versão — **proibido** materializar o catálogo no repo da AI.

## Matriz de paridade — VISTA / PresentationMutation vs Fora

| Capacidade do editor | VISTA / PresentationMutation | Notas |
|----------------------|------------------------------|--------|
| Criar playlist | sim | `create_playlist` |
| Slide a partir de preset | sim | `add_slide_from_preset` |
| Slide blank `custom_message` | sim | `add_blank_slide` |
| Renomear / duração / ativo | sim | `update_slide` |
| Reordenar slides | sim | `reorder_slides` |
| Excluir slide | sim | `delete_slide` |
| Seções CRUD / mover slide | sim | `upsert_section`, `delete_section`, `move_slide_to_section` |
| Texto / título / forma / ícone / grade / KPI / chart / table / input | sim | `upsert_block` (+ templates / planner VISTA) |
| Remover bloco | sim | `delete_block` |
| Fonte / modelo de dados | sim | `create_data_source`, `update_data_source` |
| Fonte + KPI/chart/table (composite) | sim | `add_*_from_route` |
| Transform tipado (subset) | sim | `set_data_transform` + `transformStepHints` — SoT = `{ steps }` |
| Bind visual (+ projections no MFE) | sim | `bind_visual`; sync via `useSyncViewDataLinks` |
| Fundo / dataFilters / speakerNotes | sim | `patch_native_config` (whitelist) |
| Mídia via `assetId` | sim | `upsert_block` com `assetId` (sem `url` solto / M) |
| Zoom / snap / régua / Exibir | **Fora** | Preferência de sessão UI |
| Undo / redo local | **Fora** | Histórico de editor, não modelo remoto |
| Export PPTX | **Fora** | Canal aparte |
| QR / editores / admin playlist | **Fora** | Governança |
| Script M / DAX / SQL / workbench M | **Fora** | Intencional (`mForbidden`); produto M desativado |

## Custom GPT Actions (consumer externo)

Façade OAuth em `/gpt-actions/v1` (ver `docs/gpt-actions/custom-gpt-actions.md`).

- **Não** é owner do catálogo — continua `presentation_ops_content.json` / PresentationOps services.
- PREPARE = suggest/preview; preview mints opaque ``proposal_handle``.
  Additive (``confirmationPolicy=direct``): ``commit_now=true`` + confirmation
  on the same preview → PREPARE+COMMIT (1 ChatGPT Allow). Destructive:
  preview then ``gpt_commit_change`` with the exact handle after one user OK.
  Never invent handles (``latest`` → ``PROPOSAL_NOT_FOUND``).
  Standalone ACT = ``proposal_handle`` + ``confirmation`` only, via
  ``TvPresentationWriteService`` (mesmo write boundary das rotas CRUD UI).
  Sem loopback HTTP; sem ``ops``/``planDigest`` no commit.
- Draft local do MFE permanece `unavailable_external` para o Custom GPT.

## Chat interno (consumer — handoff only)

- Skill/tool Chat TV Copilot: **removidos**.
- Pedido TV no Chat interno → handoff (`tv_dashboard_handoff` / `ChatTvDashboardHandoffService`)
  com direct answer orientando o especialista **VISTA** (`/gpt-actions/v1`). Sem tool de mutação.
- Mutação tipada: só VISTA Actions + PresentationMutation (ou editor MFE).
- `/data/copilot/*` → **410 Gone**.
- Chat interno ≠ VISTA ≠ DÉLIA (app standalone); ver playbook Chat OpenAPI-first.

## Embed (A1)

- Remote MF: `minha-delpi-chat` → `./EmbeddedChat` (hostContext ambient; dock Copilot TV **retirado**).
- Pedidos de mutação no embed → handoff VISTA (não aplica patch via tool).
- Draft local do editor: modal «Fontes de dados» (catálogo + builder actions).

## Persistência canônica

```text
VISTA gpt_preview_change → proposal_handle → gpt_commit_change
  → TvPresentationWriteService → CRUD /playlists/** → presentation_updated (WS)
```

Editor MFE e Actions GPT compartilham o mesmo write boundary.

## Escopo negativo

- Sem `resolved` no `native_config`
- Sem segundo pipeline de enrich
- Sem M / DAX / SQL livre
- Slide ≠ `renderPlan` do chat
- Sem cópia do catálogo na `minha-delpi-ai-api`
- Sem skill/tool de mutação TV no Chat interno

## Relação com Data Builder

| Caminho | Status | Uso |
|---------|--------|-----|
| VISTA `/gpt-actions/v1` (preview/commit) | **canônico** | Mutação tipada NL/ops |
| `POST /data/builder/sessions/{id}/to-presentation-ops` | **canônico** | Rascunho materializado → ops do catálogo |
| `POST /data/builder/sessions/{id}/turn` com `message` | **retired** (`422 NL_TURN_RETIRED`) | Sem S2S Chat AI |
| `POST /data/copilot/*` | **410 Gone** | Legado |

Ver também: [data-builder-chat.md](./data-builder-chat.md), regra `.cursor/rules/tv-dashboard-presentation-parity.mdc`.
