# Descoberta NL de fontes (TV Dashboard)

## Objetivo

Permitir que o usuário descreva o dado em linguagem natural no modal **Fontes de dados** e receba 3–5 rotas do catálogo TV, com motivo legível — sem duplicar a inteligência de seleção do chat e sem executar a api-delpi automaticamente.

## Fluxo

```text
MFE (DataRoutesSidePanel)
  → POST /apps/tv-dashboard-api/data/routes/suggest
    → S2S POST minha-delpi-ai-api /chat/internal/operational-routes/suggest
      → OperationalRouteSuggestionService (dry-run / ExternalActionSelection)
    → intersect allowlist TvDataRouteCatalogService + enrich labels
  → faixa «Sugestões» no DataRouteCatalogPanel → pickRoute atual
```

## Contratos

| Camada | Endpoint | Auth |
|--------|----------|------|
| Chat base | `POST /chat/internal/operational-routes/suggest` | Internal service token |
| TV BFF | `POST /data/routes/suggest` | JWT `TV_READ` / `TV_WRITE` |

Body TV: `{ "query": string, "limit"?: 1–20 }`  
Resposta: `{ suggestions: [rota catálogo + reason + score], query, total, degraded? }`

Se a AI estiver indisponível, o BFF devolve `suggestions: []` com `degraded: true` (HTTP 200). O MFE mantém busca substring local.

## Env

| Variável | Default |
|----------|---------|
| `MINHA_DELPI_AI_API_URL` | `http://delpi-minha-delpi-ai-api:8000` |
| `MINHA_DELPI_AI_API_TIMEOUT_SECONDS` | `20` |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | (mesmo token S2S das demais integrações) |

Em dev, o serviço `minha-delpi-ai-api` exige profile Compose `chat` (ou `vision`).

## UX (v1)

- Um campo unificado: texto curto → só substring; frase (≥ 3 tokens ou ≥ 16 chars) → debounce 350 ms → suggest.
- Clique na sugestão = mesmo fluxo do card do catálogo (detalhe → Usar esta fonte).
- **Não** auto-executa preview HTTP nem insere bloco no canvas.

## Fora do v1

Pré-preencher params, auto-preview no detalhe, «montar no slide» com confirmação — ver plano IA Fontes TV Dashboard.
