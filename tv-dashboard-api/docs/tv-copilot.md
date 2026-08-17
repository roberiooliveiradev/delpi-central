# Copiloto TV Dashboard (TvCopilotPatchV1)

## Objetivo

Patches tipados no modelo de slide/playlist via chat base (`tv_dashboard_copilot`) ou endpoints BFF. **Não** gera Power Query M. Present permanece viewer puro (`SlideDataResolutionService`).

**Ownership:** o catálogo de capabilities vive **somente** em `tv-dashboard-api`. Feature nova de TV = mudança neste pacote (+ UI MFE se houver). A `minha-delpi-ai-api` consome `GET /data/copilot/capabilities` — sem lista de ops embutida.

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

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/data/copilot/capabilities` | `TV_WRITE` | `{ catalogVersion, operations, capabilities[] }` — contrato executável |
| `POST` | `/data/copilot/suggest-ops` | `TV_WRITE` | NL + hostContext → plano discriminado + `ops[]` |
| `POST` | `/data/copilot/preview-patch` | `TV_WRITE` | Dry-run + diff + `httpCommands` + `baseRevision`; **não** persiste |
| `POST` | `/data/copilot/apply-patch` | `TV_WRITE` | **Depreciado como writer:** mesmo plano do preview (`persisted: false`, `executionMode: crud_http`). Persistência = CRUD `/playlists/**` |
| `GET` | `/data/copilot/telemetry` | `TV_MANAGE` | Contadores |
| `POST` | `/data/builder/sessions/{id}/to-copilot-ops` | `TV_WRITE` | Materialize → mesmas ops do catálogo |

### `operations`: contrato executável

Cada op tem uma única spec em `operations`: `requiresPlaylist`, `requiresSlide`,
`inputSchema`, `risk`, `confirmationPolicy` e `sideEffectHints`. O planner e o
patch service consomem a mesma spec; capability nova não pode repetir esses campos.

- `direct`: criação/alteração inequívoca é aplicada no mesmo turno.
- `confirm`: somente `delete_block`, `delete_slide` e `delete_section`.
- `add_blank_slide` requer playlist, mas não slide aberto.
- mutações de canvas requerem playlist + slide; sem contexto, o planner devolve
  `status=clarification` e zero ops.

O `suggest-ops` retorna `status: ready | clarification | unsupported | error`,
`confirmationPolicy`, `risk`, requisitos agregados e os hints. Uma composição
herda a política mais restritiva entre suas ops.

### Shape de `capabilities[]`

Cada item (declarativo em `tv_copilot_content.json`):

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

### Placeholders do suggest-ops

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

## Matriz de paridade — Copilot (modelo) vs Fora

| Capacidade do editor | Copilot | Notas |
|----------------------|---------|--------|
| Criar playlist | sim | `create_playlist` |
| Slide a partir de preset | sim | `add_slide_from_preset` |
| Slide blank `custom_message` | sim | `add_blank_slide` |
| Renomear / duração / ativo | sim | `update_slide` |
| Reordenar slides | sim | `reorder_slides` |
| Excluir slide | sim | `delete_slide` |
| Seções CRUD / mover slide | sim | `upsert_section`, `delete_section`, `move_slide_to_section` |
| Texto / título / forma / ícone / grade / KPI / chart / table / input | sim | `upsert_block` (+ templates / suggest-ops) |
| Remover bloco | sim | `delete_block` |
| Fonte / modelo de dados | sim | `create_data_source`, `update_data_source` |
| Fonte + KPI/chart/table (composite) | sim | `add_*_from_route` |
| Transform tipado (subset) | sim | `set_data_transform` + `transformStepHints` |
| Bind visual (+ projections no MFE) | sim | `bind_visual`; sync via `useSyncViewDataLinks` |
| Fundo / dataFilters / speakerNotes | sim | `patch_native_config` (whitelist) |
| Mídia via `assetId` | sim | `upsert_block` com `assetId` (sem `url` solto / M) |
| Zoom / snap / régua / Exibir | **Fora** | Preferência de sessão UI |
| Undo / redo local | **Fora** | Histórico de editor, não modelo remoto |
| Export PPTX | **Fora** | Canal aparte |
| QR / editores / admin playlist | **Fora** | Governança |
| Script M / DAX / SQL livre | **Fora** | Intencional (`mForbidden`) |

## Chat base (consumer)

- Skill genérica: `tv-dashboard-copilot` (sem listar ops no markdown)
- Tool: `tv_dashboard_copilot` (`mode=preview|apply`)
  - `preview` / `apply` pedem plano fresco ao BFF (`preview-patch`)
  - **Apply não grava no BFF:** a AI executa `httpCommands` nas rotas CRUD
    `/playlists/**` com o JWT do usuário, `If-Match` / revisão encadeada e allowlist
  - Mutação bem-sucedida publica `presentation_updated` (mesmo WS do editor)
- `direct` usa `apply` no mesmo turno; exclusão `confirm` usa preview e aguarda confirmação
- Env: `TV_DASHBOARD_API_BASE_URL`

## Embed (A1)

- Remote MF: `minha-delpi-chat` → `./EmbeddedChat`
- Host envia `hostContext`: `surface`, `playlistId`, `slideId`, seleção, fontes,
  `hasLocalDraft`, `presetKey` e resumo do foco.
- Antes de enviar o turno: `flushBeforeMutation` persiste drafts locais do editor.
- Draft local pendente bloqueia mutação remota com clarificação; nunca sobrescreve o editor.
- Após CRUD: o editor sincroniza só pelo WS `presentation_updated` (sem evento paralelo
  `delpi:tv-copilot:playlist-mutated`). Preview continua local (`replaceNativeConfig`).

## Persistência canônica (CRUD HTTP)

```text
Chat → AI → preview-patch (dry-run + httpCommands)
         → execute_crud_command (JWT + If-Match) → /playlists/**
         → notify_presentation_changed → editor WS
```

- BFF (`TvCopilotPatchService`): redutor + `TvCopilotHttpCommandPlannerService` — **nunca** `update_slide` no apply.
- OCC: header `If-Match` / corpo `currentRevision` em 409; resposta `X-Playlist-Revision`.
- Ops de canvas (`upsert_block`, `delete_block`, …) coalescem em **um** `PATCH` `nativeConfig`.

## Escopo negativo

- Sem `resolved` no `native_config`
- Sem segundo pipeline de enrich
- Sem M / DAX / SQL livre
- Slide ≠ `renderPlan` do chat
- Sem cópia do catálogo na `minha-delpi-ai-api`

## Relação com Data Builder

**Cutover (AP5):** o caminho canônico de mutação tipada é o **mesmo catálogo** do Copilot.

| Caminho | Status | Uso |
|---------|--------|-----|
| `POST /data/copilot/suggest-ops` | **canônico** | NL + `hostContext` → `ops[]` (BFF determinístico) |
| `POST /data/builder/sessions/{id}/to-copilot-ops` | **canônico** | Rascunho materializado → mesmas ops do catálogo |
| `POST /data/builder/sessions/{id}/turn` (NL) | **deprecated** | Não é o caminho de mutação tipada; não evoluir novos encodings aqui |

Materialize → `to-copilot-ops` usa o **mesmo** catálogo. Turn NL legado do Builder: **deprecated** — preferir Copilot + `suggest-ops` / skill.

Ver também: [data-builder-chat.md](./data-builder-chat.md), regra `.cursor/rules/tv-dashboard-presentation-parity.mdc`.
