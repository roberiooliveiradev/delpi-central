# Assistente conversacional de dados (TV Dashboard)

## Objetivo

Substituir o catálogo «Fontes de dados» por um **chat de rascunho**: o usuário descreve o dado, adiciona fontes allowlistadas, ajusta filtros/colunas/joins e, ao confirmar, materializa blocos `data_source` (+ `dataTransform`) consumíveis pelos visuais existentes (KPI/gráfico/tabela).

Não embute o stream do Minha Delpi Chat no editor. Inteligência de rotas/params fica no chat base via S2S; allowlist, draft, preview e persistência no slide ficam no TV BFF/MFE.

## Fluxo

```text
MFE (DataBuilderChatPanel)
  → POST /data/builder/sessions
  → POST /data/builder/sessions/{id}/turn   (mensagem NL ou action)
      → S2S suggest routes / suggest-params (minha-delpi-ai-api)
      → muta DataModelDraft (add/remove/params/columns/merge)
  → POST .../preview                       (opcional, sob demanda)
  → POST .../materialize
  → createDataSourceBlock / addDataSourceBlock no slide
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

Body do turn: `{ "message"?: string, "action"?: { "type": "add_source"|"remove_source"|"set_params"|"set_columns"|"propose_join"|"mark_ready"|"suggest_sources", … } }`.

## S2S (chat base)

| Endpoint | Papel |
|----------|--------|
| `POST /chat/internal/operational-routes/suggest` | NL → candidatos de rota |
| `POST /chat/internal/operational-routes/suggest-params` | NL → params (dry-run do parameter builder) |

Auth: `API_DELPI_INTERNAL_SERVICE_TOKEN` nos dois serviços (mesmo valor). Ver também [data-route-nl-suggest.md](./data-route-nl-suggest.md).

## Conteúdo

- TV: `tv_app/content/data_builder_content.json` (+ `TvDataBuilderContentService`)
- MFE: `plugins/tv-dashboard/src/content/dataBuilderChatContent.ts`

## Anti-padrões

- MFE → AI direto
- Duplicar ranking de rotas no TV/MFE
- Entregar `renderPlan` do chat como modelo do slide
- Join só no visual — join no `dataTransform` da âncora
- Auto-preview a cada tecla (só sob demanda)


## Modos de descoberta (MFE)

| Modo | Comportamento |
|------|----------------|
| **Pesquisa** | Busca local no catálogo TV por label/path/`operationId` (sem IA). |
| **Assistente IA** | Mensagem NL → `turn` → suggest S2S. |

«mostre uma prévia» (ou botão **Prévia**) dispara preview do rascunho; a tabela usa `resolved.preview` / `resolved.table` / `resolved.query`.
