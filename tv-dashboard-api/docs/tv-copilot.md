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
| `GET` | `/data/copilot/capabilities` | `TV_WRITE` | `{ catalogVersion, capabilities[] }` — fonte de verdade para a AI |
| `POST` | `/data/copilot/suggest-ops` | `TV_WRITE` | NL + hostContext → `ops[]` (payloads ricos no BFF) |
| `POST` | `/data/copilot/preview-patch` | `TV_WRITE` | Dry-run + diff + `sideEffectHints`; valida schema; **não** persiste |
| `POST` | `/data/copilot/apply-patch` | `TV_WRITE` | Persiste + `notify_presentation_changed` |
| `GET` | `/data/copilot/telemetry` | `TV_MANAGE` | Contadores |
| `POST` | `/data/builder/sessions/{id}/to-copilot-ops` | `TV_WRITE` | Materialize → mesmas ops do catálogo |

### Shape de `capabilities[]`

Cada item (declarativo em `tv_copilot_content.json`):

| Campo | Papel |
|-------|--------|
| `key` | Id estável da capability |
| `op` | Nome da op no envelope |
| `whenToUse` | Texto prescritivo (injetado no prompt addon da AI) |
| `contentMarkers` / `excludeMarkers` | Matching NL genérico |
| `actionTermSet` | `create` \| `mutation` \| `any` |
| `payloadTemplate` | Template JSON com placeholders (`{{quoted}}`, `{{selectedBlockId}}`) |
| `inputSchema` | JSON Schema dos campos da op |
| `sideEffectHints` | Hints genéricos para o MFE (`refreshFilmstrip`, `replaceNativeConfig`, …) |
| `requiresSlide` / `requiresPlaylist` | Target mínimo |

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
| Fonte + transform tipado | sim | `upsert_data_source`, `set_data_transform` |
| Bind visual (+ projections default) | sim | `bind_visual` |
| Fundo / dataFilters / speakerNotes | sim | `patch_native_config` (whitelist) |
| Mídia via `assetId` | sim | `upsert_block` com `assetId` (sem `url` solto / M) |
| Zoom / snap / régua / Exibir | **Fora** | Preferência de sessão UI |
| Undo / redo local | **Fora** | Histórico de editor, não modelo remoto |
| Export PPTX | **Fora** | Canal aparte |
| QR / editores / admin playlist | **Fora** | Governança |
| Script M / DAX / SQL livre | **Fora** | Intencional (`mForbidden`) |

## Chat base (consumer)

- Skill genérica: `tv-dashboard-copilot` (sem listar ops no markdown)
- Tool: `tv_dashboard_copilot` (`mode=preview|apply`) — ops vindas do catálogo / suggest-ops
- Apply exige confirmação explícita (`ChatWriteConfirmationService`)
- Env: `TV_DASHBOARD_API_BASE_URL`

## Embed (A1)

- Remote MF: `minha-delpi-chat` → `./EmbeddedChat`
- Host envia `hostContext`: `surface`, `playlistId`, `slideId`, `selectedBlockIds`, resumo do foco
- Preview → draft local via `sideEffectHints` (genérico); confirm → persist

## Escopo negativo

- Sem `resolved` no `native_config`
- Sem segundo pipeline de enrich
- Sem M / DAX / SQL livre
- Slide ≠ `renderPlan` do chat
- Sem cópia do catálogo na `minha-delpi-ai-api`

## Relação com Data Builder

Materialize → `to-copilot-ops` usa o **mesmo** catálogo. Turn NL legado do Builder: **deprecated** — preferir Copilot + suggest-ops / skill.

Ver também: [data-builder-chat.md](./data-builder-chat.md), regra `.cursor/rules/tv-dashboard-presentation-parity.mdc`.
