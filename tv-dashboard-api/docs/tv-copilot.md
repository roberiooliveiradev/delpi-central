# Copiloto TV Dashboard (TvCopilotPatchV1)

## Objetivo

Patches tipados no modelo de slide/playlist via chat base (`tv_dashboard_copilot`) ou endpoints BFF. **Não** gera Power Query M. Present permanece viewer puro (`SlideDataResolutionService`).

## Envelope

```json
{
  "target": { "playlistId": "…", "slideId": "…" },
  "ops": [
    { "op": "upsert_data_source", "operationId": "…", "params": {}, "blockId": "…" },
    { "op": "set_data_transform", "blockId": "…", "steps": [] },
    { "op": "upsert_block", "block": { } },
    { "op": "bind_visual", "visualId": "…", "dataSourceId": "…" },
    { "op": "add_slide_from_preset", "presetKey": "…", "branch": "01" },
    { "op": "create_playlist", "name": "…", "seedPresetKeys": ["…"] }
  ]
}
```

## APIs

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `POST` | `/data/copilot/preview-patch` | `TV_WRITE` | Dry-run + diff; fingerprint opcional; **não** persiste |
| `POST` | `/data/copilot/apply-patch` | `TV_WRITE` | Persiste + `notify_presentation_changed` (cache + WS) |
| `GET` | `/data/copilot/telemetry` | `TV_MANAGE` | Contadores preview/apply |
| `POST` | `/data/builder/sessions/{id}/to-copilot-ops` | `TV_WRITE` | Fachada: materialize builder → ops |

## Chat base

- Skill: `tv-dashboard-copilot` (`catalog.json` + policy `tv-dashboard-copilot-skill.md`)
- Tool: `tv_dashboard_copilot` (`mode=preview|apply`)
- Apply exige `ChatWriteConfirmationService` (confirmação explícita)
- Env: `TV_DASHBOARD_API_BASE_URL` (default `http://delpi-tv-dashboard-api:8000`)

## Embed (A1)

- Remote MF: `minha-delpi-chat` → `./EmbeddedChat`
- Host: aba «Copiloto IA» no `DataCatalogModalHost` (`TvCopilotSidePanel`)
- Carrega `minha-delpi-chat/assets/remoteEntry.js` em **runtime** (`container.get("./EmbeddedChat")`) — **não** declara o chat como remote no `vite.config` do TV (evita quebrar `@delpi/plugin-ui`)
- `hostCallbacks.onPreviewPatch` → `applySlideTemplate` (draft local)
- Se o remote estiver indisponível, fallback com contexto playlist/slide para o chat portal

## Escopo negativo

- Sem `resolved` no `native_config`
- Sem segundo pipeline de enrich
- Sem M / DAX / SQL livre
- Slide ≠ `renderPlan` do chat

## Relação com Data Builder

O Assistente de dados (aba Rascunho) permanece; `to-copilot-ops` e materialize compartilham a mesma fachada. Cutover NL: preferir skill/tool do chat; deprecar `turn` NL no TV quando cobertura = 100%.

Ver também: [data-builder-chat.md](./data-builder-chat.md), regra `.cursor/rules/tv-dashboard-presentation-parity.mdc`.
