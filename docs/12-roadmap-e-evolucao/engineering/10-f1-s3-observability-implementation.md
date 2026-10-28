# F1.S3 — Engineering API Observability — Registro de Execução

> **Documento:** `10-f1-s3-observability-implementation.md`
> **Fase:** F1.S3 — request observability, correlation & error handling
> **BASE_HEAD:** `1b59fdc8952bcd0e70db9a8f3793fde694e3a6a1` (`origin/main` na reancoragem;
> baseline de referência `c84f4fbd70` = F1.S2R1, ancestral ✓)
> **Autorização:** Coordenação EVA — F1.S3 ONLY (sem F1.S4/S5, F2, Portal ou MCP)
> **Estado anterior:** F1.S2R1 — `ACCEPT_WITH_RESIDUAL` (gate §10 preservado)

---

## 1. Objetivo

Camada mínima e governada de observabilidade de requisição na `engineering-api`: correlation id, operation id estável, tempo de resposta, logging estruturado e propagação de contexto — reutilizando somente contratos já existentes na plataforma, sem frameworks ou abstrações novas.

## 2. Padrão reutilizado (Abstraction Gate)

Inventário real no HEAD:

| Fonte | Contrato |
|---|---|
| `api-delpi/app/middleware/request_observability_middleware.py` | `X-Operation-Id` (rota `operation_id` via `scope["route"]`), `X-Response-Time-Ms`, log estruturado `method/path/status/operation_id/duration_ms`, contextvars + reset |
| `supplies-api/app/interfaces/http/request_context.py`, `delia-api/.../request_logging.py` | `X-Request-Id`: preserva recebido, gera `uuid4`, ecoa na resposta, propaga downstream |
| `external-data-api` | fallback `X-Correlation-Id → X-Request-Id → uuid4` |
| `observability-standards.mdc` | campos comuns, redaction, cardinalidade, preservação de correlation id |

Decisão: **implementação local pequena** — não existe middleware de observabilidade neutro em `shared/`; importar código interno de `api-delpi`/`supplies` acoplaria bounded contexts. ContextVar fica no próprio arquivo do middleware (sem `infrastructure/` prematuro).

## 3. Contrato de correlation id

- **Header oficial:** `X-Request-Id` (canônico em supplies/delia/external-data/core/tv).
- **Alias de entrada:** `X-Correlation-Id` (precedência canônica de external-data). Saída é sempre `X-Request-Id`. Quando ambos presentes, `X-Request-Id` vence.
- **Preservação:** id recebido é reutilizado somente se válido — charset `[A-Za-z0-9._~:-]`, ≤128 chars, sem espaços/controle — senão é substituído por `uuid4` (nunca refletido).
- **Geração:** `uuid.uuid4()` quando ausente/inválido.
- **Uso proibido:** request id não é identidade, autorização nem chave de recurso.

## 4. Contrato de operation id e tempo de resposta

- `X-Operation-Id`: vem de `request.scope["route"].operation_id` após o roteamento (padrão api-delpi). Ausente em paths sem rota — nunca derivado de input; o log classifica como `unmatched_route` (cardinalidade zero).
- `X-Response-Time-Ms`: `time.perf_counter()`, arredondado a 2 casas, ≥0.
- operationIds estáveis preservados: `get_engineering_health`, `get_engineering_ready`.

## 5. Logging estruturado

Logger `engineering_api.request`, `INFO` por request:

```text
engineering_api_request method=GET path=/health status=200
operation_id=get_engineering_health request_id=<uuid>
duration_ms=0.58 result=2xx
```

- `result` = classe do status (`2xx`/`4xx`/`5xx`).
- `path` sanitizado (`_safe_path`) — caracteres não-imprimíveis viram `?` (log forging via path decodificado).
- Exceção propagando do `call_next` → `logger.error` com `error_class=<tipo>` sanitizado, re-raise.
- **Redaction:** nunca loga Authorization, JWT, cookies, bodies, query string, secrets ou dados pessoais — verificado por testes dedicados.

## 6. Ordem dos middlewares

```text
request
→ request_observability_middleware   (outer — registra após o JWT, roda antes)
→ jwt_middleware (wrapper allowlist estrita F1.S2R1 → base delpi_auth)
→ ExceptionMiddleware → router
```

Convenção api-delpi: último `app.middleware("http")` registrado executa primeiro. Observability envolve o JWT → 401/403/503 de auth também recebem `X-Request-Id` + `X-Response-Time-Ms` e são logados com status real. A instrumentação não altera o fluxo de autenticação.

`get_request_id()` expõe o contexto via ContextVar (`engineering_request_id`) — usado pelo `unhandled_exception_handler` no log de erro interno e disponível para futura propagação downstream (padrão `delpi_api_gateway`).

## 7. Erros e respostas

- Envelope `fail()` preservado; `delpi_auth` continua devolvendo `{"detail": ...}` nos 401/403/503 canônicos — sem normalização local.
- Status reais sempre registrados (401, 403, 404, 422, 500, 503 — nenhum re-mapeado pela instrumentação).
- `unhandled_exception` loga `request_id` — a resposta ao cliente permanece `"Erro interno do servidor."` sem internals.

## 8. Testes — 113 passing

`python -m pytest` (Python 3.12, pins + `shared[fastapi]`): **81 anteriores + 32 novos**.

| Área | Cobertura (`test_observability.py`) |
|---|---|
| Correlation | geração uuid4; preservação válida; alias X-Correlation-Id; precedência X-Request-Id; 10 ids inválidos (controle, >128, injection, aspas, backslash) → uuid; header em 401; isolamento entre requests; id não deriva de identidade |
| Operation id | estável em /health e /ready; ausente em path sem rota (sem arbitrariedade) |
| Tempo | `X-Response-Time-Ms` presente, numérico, ≥0, em 200 e 401 |
| Logging | método/path/status/operation/request_id/duration/result no evento; `unmatched_route` em 401; sem token/Authorization/Bearer nos logs; query não vaza; path sanitizado contra forging |
| Composição S2 | auth não enfraquecido; **gate F1.S2R1: log registra o path real, nunca o mascarado**; probe autorizado com headers completos; contextos isolados |

## 9. Build smoke

`uvicorn engineering_app.main:app` real:

- `GET /health` → 200 + `x-request-id` uuid + `x-operation-id: get_engineering_health` + `x-response-time-ms`.
- `GET /v1/x` → 401 + `x-request-id` (auth dentro do envelope de observability).
- `X-Request-Id: smoke-99` → eco preservado.
- Log `engineering_api.request` com todos os campos.

## 10. Residual F1.S2R1 — gate verificado

O mascaramento temporário de `scope["path"]` no auth middleware (restrição à política pública ampla do `delpi_auth`) **não** afeta a observabilidade: a mutação ocorre dentro do JWT e é restaurada antes de `call_next`/resposta — o log sempre vê o path real (prova: `test_observability_sees_real_path_not_masked` em `/x/api-delpi/health` → 401, log com path real). Nenhum comportamento inseguro revelado — residual permanece registrado, sem workaround adicional.

## 11. Limitações e pendências

- Sem exportador de métricas/tracing — Prometheus/OTel **TO_INVENTORY** (não autorizado introduzir plataforma nesta fase); duração/status via middleware+logs conforme §5.
- Propagação downstream de `X-Request-Id` prevista para os futuros gateways da Engenharia (`get_request_id()` disponível).
- Docker build: `TEST_NOT_RUN` (sem daemon); serviço não integrado a gateway/Compose — F1.S5.

## 12. Próximo bounded step

F1.S4/S5 conforme roadmap — infra wiring canônico (gateway, Compose, `FASE_API`) ou próxima etapa autorizada pela Coordenação. Não iniciado automaticamente.
