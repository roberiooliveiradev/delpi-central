# Smoke — roteamento api-delpi por domínio (mock)

Script: `scripts/smoke_api_delpi_domain_routing.py`

## Objetivo

Garantir que o **chat base** seleciona a action correta por domínio da [auditoria api-delpi](../roadmap/api-delpi-chat-intelligence-audit.md), **sem** depender de SQL Server / api-delpi online.

## Camadas

| Camada | O que valida |
|--------|----------------|
| **Mock** | `ExternalActionSelectionService` com catálogo mínimo por caso (`tests/fixtures/api_delpi_domain_routing_cases.py`) |
| **Chat sample** (opcional) | `intentRoute` + `toolCalls` com login real (`SMOKE_CHAT_SAMPLE=1`, padrão) |

## Domínios cobertos

- `products`, `engineering`, `supplies`, `sales`, `commercial`, `financial`, `production`, `quality`, `system`

## Execução

```bash
cd minha-delpi-ai-api
PYTHONPATH=. .venv/bin/python scripts/smoke_api_delpi_domain_routing.py
```

Variáveis: `SMOKE_BASE_URL`, `SMOKE_USER`, `SMOKE_PASSWORD`, `SMOKE_CHAT_PREFIX`.

Desligar amostra HTTP do chat:

```bash
SMOKE_CHAT_SAMPLE=0 PYTHONPATH=. .venv/bin/python scripts/smoke_api_delpi_domain_routing.py
```

## Falhas comuns

- Caso ausente em `SELECTION_CASES` → `KeyError` ao montar `DOMAIN_ROUTING_CASES`
- Agente sem actions importadas → WARN no chat sample (roteamento unitário ainda passa)
