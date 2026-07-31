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
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | **Obrigatório** — mesmo valor em `tv-dashboard-api` e `minha-delpi-ai-api` (header `X-Delpi-Service-Token`) |

Em prod, o compose injeta o token nos dois serviços a partir de `infra/.env`. Conferência rápida:

```bash
docker exec delpi-tv-dashboard-api sh -c 'echo TV_TOKEN_LEN=${#API_DELPI_INTERNAL_SERVICE_TOKEN}'
docker exec delpi-minha-delpi-ai-api sh -c 'echo AI_TOKEN_LEN=${#API_DELPI_INTERNAL_SERVICE_TOKEN}'
# Ambos > 0 e iguais. Depois:
docker exec delpi-tv-dashboard-api python -c "
from tv_app.infrastructure.gateways.minha_delpi_ai_client import MinhaDelpiAiClient
print(MinhaDelpiAiClient().suggest_operational_routes(query='ops em atraso', limit=3))
"
```

Em Compose dev, o serviço `minha-delpi-ai-api` exige profile `chat` (ou `vision`).

## UX (v1)

- Um campo unificado: texto curto → só substring; frase (≥ 3 tokens ou ≥ 16 chars) → debounce 350 ms → suggest.
- Clique na sugestão = mesmo fluxo do card do catálogo (detalhe → Usar esta fonte).
- **Não** auto-executa preview HTTP nem insere bloco no canvas.

## Fora do v1

Pré-preencher params, auto-preview no detalhe, «montar no slide» com confirmação — ver plano IA Fontes TV Dashboard.
