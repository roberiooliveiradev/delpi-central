# PROC-0076 R11 — Cotações diárias (/v1/prices) e persistência histórica

Data: 2026-10-30. Escopo executado: feed diário barato de refresh
(`metals-prices-daily`), precedência de semântica spot/close, roteamento
de retenção fail-closed, superfície de leitura e deploy. Persistência
permanente: **BLOCKED_BY_SOURCE_RIGHTS** (gate documentado em
`PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md` §7).

## Decisões

- `PRODUCT_OWNER_AUTHORIZATION = APPROVED` (INTERNAL_MARKET_INTELLIGENCE,
  REDISTRIBUTION=FORBIDDEN, TARGET_RETENTION=PERMANENT, DAILY).
- `PROVIDER_PERMANENT_STORAGE_RIGHT = PENDING` — nenhuma linha
  MetalCharts vai para `metal_quote_observations` enquanto o catálogo
  mantiver `observation_retention=ttl_cache` + escopo sem `store`.
- Implementadas e testadas as partes independentes: contrato do
  endpoint, orçamento, roteamento de destino, precedência de basis,
  agendamento, leitura e rótulos de UI.

## Contrato do endpoint (re-verificado no adapter — S1/R5)

`GET /v1/prices/` (barra final obrigatória — sem ela → 401): uma
requisição, 1 weight, retorna `data[symbol]` para todos os símbolos;
campos preservados `price, bid, ask, timestamp, exchange, marketType,
stale, currency, unit`. Cobertura: bindings ativos HG/ALI/NI/ZN/PB
(S1 §5.3). Custo: ~31 weight/mês — dentro do budget 160/mês.

## Semântica do preço (AC-04)

- `/v1/prices` reporta **último negócio intradiário**, não fechamento.
- `spot_last_quote_basis(exchange, marketType)` em `domain/market_data.py`
  gera o rótulo honesto: `comex_futures_last`, `lme_spot_last`,
  `spot_last`, fallback determinístico `…_last` — nunca `*_daily_close`.
- `AUTHORITATIVE_QUOTE_BASES` = closes diários + média mensal. Os
  upserts (`upsert_metal_cache`, `upsert_metal_observation`) aplicam a
  precedência atomicamente no `ON CONFLICT`: um `*_last` **nunca**
  sobrescreve uma linha close/average da mesma identidade; um close
  pode substituir um `*_last`; basis desconhecido/NULL existente fica
  protegido.
- BFF: pontos diários e `summary.latest`/`last_quote` carregam
  `quote_basis` + `observation_timestamp` (campos aditivos, só quando
  presentes — compatibilidade preservada).

## Feed `metals-prices-daily`

- `FEED_METALS_PRICES_DAILY`; lock advisory `76007606`;
  `provider_id_for_feed → metalcharts`; flag
  `EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED` (default off).
- `_ingest_metals_prices_daily`: gate de direitos por retenção
  (`_quote_source`) → bindings ativos com símbolo verificado →
  `budget.acquire(1)` → `fetch_spot()` → `budget.record("prices",1)` →
  por binding: símbolo ausente / `stale` / timestamp ausente / preço
  nulo → `skipped` (nunca fabrica data nem preço).
- `observation_date` vem do `timestamp` do provedor (UTC), não do
  relógio da execução (AC-10). `source_record_key` =
  `metalcharts:prices:{symbol}:{date}` — idempotente por dia.
- Destino por retenção: `ttl_cache` → `metal_quote_cache` (expires_at
  obrigatório); `permanent` → `metal_quote_observations` — alcançável
  só com `store` no escopo.
- Retry: sem hot-retry — uma falha (429/rede/egress) fecha o run
  `failed` e o scheduler tenta no dia seguinte (política R10).

## Scheduler (S3)

- Reutiliza `app/jobs/ingest_scheduler.py`; intervalo por env
  `EXTERNAL_DATA_SCHEDULER_METALS_PRICES_DAILY_INTERVAL_DAYS` (default 1).
- Produção: `EXTERNAL_DATA_SCHEDULER_FEEDS=metals-daily,metals-prices-daily`,
  RUN_AT 20:30 (provisório — horário de publicação upstream pendente de
  evidência, mesmo TO_INVENTORY do R10).

## Leitura / Frontend (S4/S5)

- `feed_statuses` reporta `metals-prices-daily` com freshness do cache.
- `_feed_for_instrument` no BFF escolhe o feed por granularidade do
  instrumento (day → prices feed).
- MFE: `quoteBasis` ganha rótulos `Último negócio COMEX/LME/spot` e o
  KPI de último valor exibe a basis do ponto mais recente — spot nunca
  apresentado como fechamento.

## Evidência de produção (read-only, pré-deploy)

- Último run `metals-daily` 29/10 12:52 → `failed`
  (`EXTERNAL_DATA_PROVIDER_UNAVAILABLE`) — egress Sophos ainda bloqueado.
- `metal_quote_cache` ao vivo: 0 linhas (TTL expirado);
  `metal_quote_observations`: 198 linhas (Pink Sheet mensal, max 2026-09).
- Catálogo `metalcharts`: active, `ttl_cache`, escopo sem `store`.

## Testes

- `external-data-api/tests/test_metalcharts_prices_feed.py` — 16 casos:
  gates (disabled, scope, permanente sem `store`, sem chave, sem
  bindings), happy path (1 chamada, weight 1, data do provedor,
  `comex_futures_last`), epoch/basis, stale/ausente/sem timestamp →
  skipped, 429 sem hot-retry, provider indisponível, roteamento
  permanente, paramétrico de `spot_last_quote_basis`.
- `supplies-api` r5s1 BFF: propagação `quote_basis`/`observation_timestamp`
  em ponto diário e `summary.latest`.
- Suítes completas: external-data-api e supplies-api verdes; MFE build ok.

## Pendências

- `PROVIDER_PERMANENT_STORAGE_RIGHT` PENDING → permanente bloqueado.
- Sophos/TechMaster: liberação de egress para `api.metalcharts.org`
  pendente — feed rodará `failed` até desbloqueio.
- Horário real de publicação upstream: sem evidência; RUN_AT provisório.

## Deploy e runtime (2026-10-30)

- Commit `9b02b6eda9` em `main` (+ branch `fix/f43-post-put-tracking`).
- `delpi-external-data-api` e `delpi-external-data-scheduler`
  rebuildados no srv-api (192.168.1.237) via git pull + compose build.
- Scheduler ativo: `feeds=metals-daily,metals-prices-daily`,
  RUN_AT 20:30, intervalo 1 dia para o novo feed.
- `.env` produção: `EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED=true`,
  `EXTERNAL_DATA_SCHEDULER_FEEDS=metals-daily,metals-prices-daily`,
  `EXTERNAL_DATA_SCHEDULER_METALS_PRICES_DAILY_INTERVAL_DAYS=1`.
- Run manual `metals-prices-daily`: `failed`
  `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` (egress Sophos ainda bloqueado),
  0 fetched / 0 weight cobrado — run registrado no ledger. Estado
  correto e honesto até a liberação pela TechMaster.
- `POSTCONDITION = PENDING` (permanent ingestion blocked by source
  rights + egress pendente para coleta real).
