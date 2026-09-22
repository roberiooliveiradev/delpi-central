# Descoberta NL de fontes (TV Dashboard)

## Objetivo

Permitir que o usuário descreva o dado em linguagem natural (modal **Fontes de dados** no MFE ou Action GPT `gpt_search_data_routes`) e receba um top-K do catálogo TV allowlist — **sem** Chat AI como autoridade de ranking e **sem** dump enciclopédico de domínio.

## Fluxo

```text
MFE (Fontes de dados / POST /data/routes/suggest) ──┐
                                                   ├→ TvDataRouteSuggestService
GPT gpt_search_data_routes ────────────────────────┘         ↓
                                                   TvDataRouteDiscoveryService
                                                             ↓
                                                   tv_data_routes.json (allowlist)
```

- Ranking lexical/category/path/label/`whenToUse` **owner-local** em `tv-dashboard-api`.
- Chat AI **não** é autoridade do suggest TV.
- Client S2S `suggest_operational_params` / `MinhaDelpiAiClient` **removidos** (builder é action-only).

## Contratos

| Camada | Endpoint | Auth |
|--------|----------|------|
| TV BFF (MFE) | `POST /data/routes/suggest` | JWT `TV_READ` / `TV_WRITE` |
| GPT Action | `GET …/gpt-actions/data-routes?query=` | OAuth user + `TV_READ` |
| MFE catálogo completo | `GET /data/routes` | JWT — **não** é superfície GPT |

Body suggest: `{ "query": string, "limit"?: 1–20, "category"?: string }`

Resposta: `{ suggestions: [rota + reason + score], query, total, searchMissDoesNotProveAbsence }`

GPT search: `query` **obrigatória** (422 se vazia); `limit` default 8 max 20; DTO compacto com `paramSchema`; envelope `searchMissDoesNotProveAbsence`.

## Regras

- Search miss ≠ ausência de dado na empresa — refine a query.
- Params (ex. `granularity=week`) vêm do `paramSchema` do hit; preview GPT preferir `{ operationId, params }`.
- Heurísticas mutáveis de discovery: `agent_directives.data_discovery` (não Instructions Builder).

## UX (MFE)

- Um campo unificado: texto curto (1 token) → só substring; frase (≥ 2 tokens ou ≥ 12 chars) → debounce 350 ms → suggest owner-local.
- Clique na sugestão = mesmo fluxo do card do catálogo.
- **Não** auto-executa preview HTTP nem insere bloco no canvas.
