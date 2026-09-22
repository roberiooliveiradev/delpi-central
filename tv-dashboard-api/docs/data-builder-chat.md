# Catálogo de fontes (TV Dashboard)

> **Nome de arquivo legado** (`data-builder-chat`): a superfície é o modal **Fontes de dados** (catálogo/actions), não um chat NL no editor.

## Objetivo

Permitir escolher rotas allowlistadas, ajustar filtros e materializar blocos
`data_source` no slide — **sem** chat NL no editor. Mutações tipadas de
programação/slides ficam no especialista **VISTA** (`/gpt-actions/v1`).

## Fluxo

```text
MFE (Fontes de dados)
  → POST /data/builder/sessions
  → POST /data/builder/sessions/{id}/turn   (somente action: add_source, set_params, …)
  → POST …/preview | materialize
  → createDataSourceBlock no slide

Turno com message NL → 422 NL_TURN_RETIRED
Suggest de rotas NL no catálogo → POST /data/routes/suggest (discovery owner-local)
Materialize com merge → steps tipados (`op: merge`); remap de `sourceId` no MFE ao inserir.
Transform SoT do slide = `{ steps }` (não script M).
```

## APIs

| Método | Path | Notas |
|--------|------|-------|
| POST | `/data/builder/sessions` | Cria rascunho |
| POST | `/data/builder/sessions/{id}/turn` | **Somente `action`** |
| POST | `/data/builder/sessions/{id}/preview` | Prévia tabular |
| POST | `/data/builder/sessions/{id}/materialize` | Blocos para o slide |
| POST | `/data/builder/sessions/{id}/to-presentation-ops` | Draft → ops PresentationMutation |
| POST | `/data/routes/suggest` | Discovery owner-local (sem Chat AI) |

## Fora deste módulo

- Especialista VISTA / gpt-actions
- Chat interno: handoff para VISTA (`tv_dashboard_handoff`), sem tool de mutação
- `/data/copilot/*` → 410 Gone
