# PROC-0076.R5 — MetalCharts Free API: implementação e evidência

- **Execução:** PROC-0076.R5-METALCHARTS
- **Data:** 2026-10-27
- **Owner técnico:** `external-data-api`
- **Estado do feed:** OFF por padrão (kill switch duplo) — nenhum dado real entra sem a homologação S1 com chave válida.

## 1. Escopo entregue

| Camada | Artefato | Função |
|---|---|---|
| Migration | `external-data-api/migrations/V007__r5_metalcharts_adapter_readiness.sql` | Fonte `metalcharts` (inativa, `store_cache_only`, `ttl_cache`), `metal_instrument_sources` (bindings inativos, só cobre `HG` verificado), `metal_quote_cache` (TTL obrigatório), `source_api_call_ledger` (contabilização de franquia) |
| Domínio | `app/domain/market_data.py`, `app/domain/usage_policy.py` | Retenção por fonte (`permanent`/`ttl_cache`), escopo `store_cache_only`, binding de instrumento |
| Infra | `app/infrastructure/providers/metalcharts_provider.py` | Adapter REST (Bearer, TLS, host allowlist, timeout finito, retry com backoff + `Retry-After`, erros tipados, observações `Decimal`) |
| Infra | `app/infrastructure/persistence/market_data_repository.py` | Bindings, upsert de cache TTL, ledger de chamadas, feed status |
| Aplicação | `app/application/metalcharts_budget.py` | Budget servidor-side: 160 weight/mês e 8 weight/minuto (headroom sob 200/10) |
| Aplicação | `app/application/market_data_ingestion.py` | Feed `metals-daily` (OFF): guarda de direitos (`collect`+`store_cache_only`), só bindings ativos+verificados, cache TTL upsert, ledger, lock/idemportência preservados |
| Aplicação | `app/application/market_data_queries.py` | Resolução de binding efetivo: binding ativo com display decide família de tabela; fallback preserva Pink Sheet/`source_use_pending` |
| Job | `app/jobs/ingest_market_data.py` | Wiring do feed `metals-daily` |
| Config | `settings.py` + `infra/docker-compose.yml` | Envs MetalCharts; feed e chave default vazios/OFF |

## 2. Decisões de direitos (fail-closed)

- `store` (permanente) **ausente** do escopo registrado — a retenção permanente não está autorizada pelos termos verificados. Em seu lugar `store_cache_only`: cache operacional TTL.
- `metal_quote_cache.expires_at NOT NULL` — a ausência de retenção permanente é estrutural.
- `observation_retention='ttl_cache'` direciona a leitura ao cache; fontes `permanent` seguem em `metal_observations`.
- Bindings nascem `active=false` e, exceto cobre (`HG`, USD/lb — verificado na doc oficial), com `source_series_key=NULL`: nenhum símbolo foi adivinhado; ingestão falha fechado com `NoApprovedSeriesError`.
- `license_reviewed_at=NULL` + `active=false`: a fonte exige revisão institucional antes de qualquer ativação.

## 3. Proteção da franquia gratuita

- Budgets: `METALCHARTS_MONTHLY_WEIGHT_BUDGET=160`, `METALCHARTS_MINUTE_WEIGHT_BUDGET=8` — reserva ~20% da franquia mensal e 20% do limite por minuto para homologação/recuperação/ops.
- `source_api_call_ledger` deduplica por `(source_id, endpoint, params_hash, called_minute)` — retry/corrida nunca gasta dobrado.
- Refresh de página **não** chama upstream: leitura serve o cache TTL; coleta ocorre só pelo job `metals-daily`, serializado pelo advisory lock de ingestão existente.
- Sem loop ilimitado: retry com backoff finito, `Retry-After` honrado em 429.

## 4. Configuração (envs)

| Env | Default | Função |
|---|---|---|
| `EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED` | `false` | Kill switch do feed (job) |
| `METALCHARTS_API_KEY` | vazio | Bearer `mc_live_*` — somente backend; nunca logada nem retornada |
| `METALCHARTS_BASE_URL` | `https://api.metalcharts.org` | Base da API |
| `METALCHARTS_ALLOWED_HOSTS` | `api.metalcharts.org` | Allowlist de egress (anti-SSRF) |
| `METALCHARTS_TIMEOUT_SECONDS` | `15` | Timeout finito |
| `METALCHARTS_MONTHLY_WEIGHT_BUDGET` | `160` | Budget mensal (Free=200) |
| `METALCHARTS_MINUTE_WEIGHT_BUDGET` | `8` | Budget/minuto (Free=10) |
| `METALCHARTS_CACHE_TTL_HOURS` | `48` | TTL do cache operacional |

## 5. Runbook de ativação (pós-S1)

1. Provisionar `METALCHARTS_API_KEY` no mecanismo de secrets do ambiente (nunca no repo).
2. Homologar S1 com a chave real: `/v1/instruments` (símbolos/unidades dos 6 metais), `/v1/prices`, `/v1/history/{symbol}` (30d), 401/403/429.
3. Preencher `metal_instrument_sources.source_series_key`/`unit_code` verificados e marcar `active=true` via migration aditiva; registrar `license_reviewed_at` na fonte.
4. Ativar `market_data_sources.active=true` e `EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED=true` após decisão documentada.
5. Observar `source_api_call_ledger` (consumo de franquia) e `feed_statuses`.

## 6. Evidência de testes

| Suíte | Resultado |
|---|---|
| `tests/test_metalcharts_r5.py` (28 casos: adapter, budget, direitos, ingestão, bindings, queries, cache TTL, ledger, idempotência, lock) | **PASS** |
| `tests/test_market_data_migrations.py` (+V007, aditiva/fail-closed) | **PASS** |
| `tests/test_market_data_repository_pg.py` (PG descartável, V001–V007) | **PASS** |
| `tests/test_contract_readiness_pg.py` | **PASS** |
| `tests/test_market_r2_pg.py` | **PASS** |
| Suíte unitária completa (`-k "not pg"`) | **PASS** (0 falhas) |

Integração externa real (chave válida, cobertura Free dos 6 metais, 401/403/429 ao vivo): **TEST_NOT_RUN** — `METALCHARTS_API_KEY` não provisionada nesta execução.

## 7. Classificação dos critérios R5

| AC | Estado |
|---|---|
| R5-01 autenticação segura | PASS (código: Bearer backend-only, allowlist, TLS, timeout) / TEST_NOT_RUN ao vivo |
| R5-02 catálogo seis metais | TEST_NOT_RUN (bindings inativos, `source_series_key` NULL exceto `HG`) |
| R5-03 cobertura Free | TEST_NOT_RUN |
| R5-04 preços/unidades | PASS (adapter preserva preço/unidade/basis; cobre USD/lb) — validação real TEST_NOT_RUN |
| R5-05 histórico 30d | PASS (adapter `/v1/history`) — validação real TEST_NOT_RUN |
| R5-06 cache/retenção | PASS (TTL estrutural, sem permanente) |
| R5-07 franquia mensal | PASS (budget + ledger + dedup) |
| R5-08 rate limits/retries | PASS (429+Retry-After, backoff finito) |
| R5-09 external-data-api | PASS |
| R5-10 supplies-api | PASS (contratos R4 inalterados — leitura via binding efetivo) |
| R5-11 dashboard R4.1 | PASS (sem alteração de frontend) |
| R5-12 séries com dados reais | PENDING (aguarda S1 + direitos) |
| R5-13 comparação compatível | PENDING (idem) |
| R5-14 Core AuthZ/S2S | PASS (inalterado) |
| R5-15 quarentena LME | PASS (bindings separados, fallback preserva `source_use_pending`) |
| R5-16 regressão IBGE/Comex/PTAX | PASS (suíte completa + PG verdes) |
| R5-17 testes/documentação | PASS |
| R5-18 deploy/smoke | deploy técnico com feed OFF — smoke revalida estados honestos |

## 8. Pendências

1. Chave `METALCHARTS_API_KEY` e homologação S1 real (símbolos, unidades, cobertura Free, 401/403/429).
2. Revisão institucional da licença (`license_reviewed_at`, ativação da fonte).
3. Decisão sobre exibição pública/redistribuição (crédito visível; restrições upstream COMEX/LME).
