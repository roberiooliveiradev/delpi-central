# Assistente conversacional de dados (TV Dashboard)

## Objetivo

Substituir o catálogo «Fontes de dados» por um **chat de rascunho**: o usuário descreve o dado, adiciona fontes allowlistadas, ajusta filtros/colunas/joins e, ao confirmar, materializa blocos `data_source` (+ `dataTransform`) consumíveis pelos visuais existentes (KPI/gráfico/tabela).

## Embed do Minha Delpi Chat — quando é permitido

| Fase | Superfície | Regra |
|------|------------|-------|
| **A0** | Chat portal + skill `tv-dashboard-copilot` | Sem remote MF; tool chama BFF `/data/copilot/*` |
| **A1+** | Remote `./EmbeddedChat` na aba «Copiloto IA» | Permitido **somente** como host de UI; inteligência na `minha-delpi-ai-api`; mutação só via `TvCopilotPatchV1` |
| **Rascunho** | `DataBuilderChatPanel` (aba Rascunho) | Continua; S2S suggest; **não** reimplementa pipeline LLM |

**O que permanece no BFF:** allowlist de rotas, draft/session, materialize, `preview-patch` / `apply-patch`, `SlideDataResolutionService`, persistência + `notify_presentation_changed`.

**Proibido:** MFE → LLM direto; entregar `renderPlan` do chat como modelo do slide; gravar `resolved`.

Doc do copiloto: [tv-copilot.md](./tv-copilot.md).

## Fluxo (rascunho)

```text
MFE (DataBuilderChatPanel — aba Rascunho)
  → POST /data/builder/sessions
  → POST /data/builder/sessions/{id}/turn   (mensagem NL ou action)
      → S2S suggest routes / suggest-params (minha-delpi-ai-api)
      → muta DataModelDraft (add/remove/params/columns/merge)
  → POST .../preview                       (opcional, sob demanda)
  → POST .../materialize
  → createDataSourceBlock / addDataSourceBlock no slide

Opcional → POST .../to-copilot-ops → ops TvCopilotPatch (mesma fachada)
```

## Fluxo (copiloto)

```text
Chat portal / EmbeddedChat
  → tool tv_dashboard_copilot (preview|apply)
  → POST /data/copilot/preview-patch | apply-patch
  → SlideDataResolution (preview) | persist + notify + cache reset (apply)
  → Present (viewer puro)
```

## Contrato do rascunho

```json
{
  "sources": [
    {
      "localId": "src_…",
      "queryName": "OTD",
      "operationId": "…",
      "params": { "branch": "01" },
      "label": "…"
    }
  ],
  "primaryLocalId": "src_…",
  "transform": { "steps": [{ "op": "merge|select|…", "…" : "…" }] },
  "status": "draft|ready"
}
```

No materialize, a fonte âncora leva o `dataTransform` (inclui `merge` com `sourceId` = `localId` do draft). O MFE remapeia `sourceId` → id real do bloco após criar todos.

## APIs TV (`/data`)

| Método | Path | Permissão |
|--------|------|-----------|
| `POST` | `/builder/sessions` | `TV_WRITE` |
| `GET` | `/builder/sessions/{id}` | `TV_READ` |
| `POST` | `/builder/sessions/{id}/turn` | `TV_WRITE` |
| `POST` | `/builder/sessions/{id}/preview` | `TV_WRITE` |
| `POST` | `/builder/sessions/{id}/materialize` | `TV_WRITE` |
| `POST` | `/builder/sessions/{id}/to-copilot-ops` | `TV_WRITE` |
| `POST` | `/copilot/preview-patch` | `TV_WRITE` |
| `POST` | `/copilot/apply-patch` | `TV_WRITE` |

Body do turn: `{ "message"?: string, "action"?: { "type": "add_source"|"remove_source"|"set_params"|"set_columns"|"propose_join"|"mark_ready"|"suggest_sources", … } }`.

## S2S (chat base)

| Endpoint | Papel |
|----------|--------|
| `POST /chat/internal/operational-routes/suggest` | NL → candidatos de rota |
| `POST /chat/internal/operational-routes/suggest-params` | NL → params (dry-run do parameter builder) |

Auth: `API_DELPI_INTERNAL_SERVICE_TOKEN` nos dois serviços (mesmo valor). Ver também [data-route-nl-suggest.md](./data-route-nl-suggest.md).

## Conteúdo

- TV: `tv_app/content/data_builder_content.json`, `tv_copilot_content.json`
- MFE: `plugins/tv-dashboard/src/content/dataBuilderChatContent.ts`, `tvCopilotContent.ts`
- Chat: skill `tv-dashboard-copilot` + `assistant`/`skills` catalog

## Anti-padrões

- MFE → AI direto
- Duplicar ranking de rotas no TV/MFE
- Entregar `renderPlan` do chat como modelo do slide
- Join só no visual — join no `dataTransform` da âncora
- Auto-preview a cada tecla (só sob demanda)
- Segundo pipeline de enrich no copiloto


## Modos de descoberta (MFE)

| Modo | Comportamento |
|------|----------------|
| Pesquisa | Catálogo local (sem IA) |
| Assistente IA (rascunho) | Turn NL no builder + S2S |
| Copiloto IA | EmbeddedChat / skill + TvCopilotPatch |
