# PROC-0076 R12 — Persistência histórica de cotações de metais (evidência)

Data: 2026-11-03. Escopo executado: verificar e completar o caminho
**permitido** de persistência permanente em `external-data-api`
(tabela existente `metal_quote_observations`, sem nova solução de
armazenamento) e provar em PostgreSQL real descartável que uma coleta
diária autorizada insere observação por data de referência, é
idempotente, preserva o histórico e é servida ao BFF/MFE.
Persistência MetalCharts em produção: **BLOCKED_BY_SOURCE_RIGHTS**
(`PROVIDER_PERMANENT_STORAGE_RIGHT = PENDING`, §5).

## Decisões registradas

- `PRODUCT_OWNER_AUTHORIZATION = APPROVED` (INTERNAL_MARKET_INTELLIGENCE,
  REDISTRIBUTION=FORBIDDEN, TARGET_RETENTION=PERMANENT, DAILY).
- Autorização empresarial **não** substitui licença do fornecedor:
  `store` permanece ausente do `allowed_use_scope` da fonte
  `metalcharts` → nenhuma linha MetalCharts em `metal_quote_observations`.
- Nenhuma tabela nova criada: `metal_quote_observations` atende AC-01–05
  (chave natural `(instrument_id, observation_date, source_id)` +
  índice único intradiário por `observation_timestamp`; `revised_at`
  registra revisões; `native_price > 0`; FK para catálogo de fontes).

## Lacunas encontradas no S0 e corrigidas (owner: external-data-api)

O caminho permanente do R11 estava "pronto-mas-não-ativado"; três
defeitos de ativação foram corrigidos com diff mínimo:

1. **Mistura de fontes na leitura** — `list_metal_observations` não
   filtrava `source_id`. Sob `permanent`, uma segunda fonte autorizada
   escrevendo no mesmo instrumento misturaria séries (ex.: médias
   mensais Pink Sheet × barras diárias MetalCharts num mesmo gráfico).
   O parâmetro `source_id` passou a ser obrigatório e a query filtra
   pela fonte efetiva resolvida pelo binding (AC-12/AC-15).
2. **`metals-daily` (barras/fechamentos) não roteava por retenção** —
   usava sempre o gate de cache (`collect`+`store_cache_only`) e
   escrevia só em `metal_quote_cache`. Sob `permanent`, os fechamentos
   autoritativos expirariam e o feed falharia fechado se o escopo
   migrasse para `store`. Agora usa `_quote_source` (mesmo padrão do
   feed `/v1/prices`): `permanent` → `upsert_metal_observation`,
   `ttl_cache` → comportamento atual inalterado (AC-04/AC-06).
3. **`feed_statuses` media freshness só no cache** — sob `permanent`
   reportaria 0 linhas/NULL com histórico autorizado existente. Os
   feeds MetalCharts agora medem a tabela efetiva conforme
   `observation_retention` da fonte (AC-14).

## Verificação executada (ambiente controlado — disposable PostgreSQL)

`tests/test_persistent_metal_quotes_pg.py` (6 casos, todos PASS em
PostgreSQL real provisionado via `tests/provision_pg_test_db.py`,
catálogo migrado V001–V008 e fonte `metalcharts` promovida a
`permanent`+`store` **somente dentro do banco descartável**):

- coleta `/v1/prices` (1 chamada, weight 1) insere 5 observações com
  `observation_date` do timestamp do provedor (nunca do relógio),
  valor real, `source_record_key`, `observation_timestamp`, basis
  `*_last` honesta; re-execução idêntica → 0 inserções (idempotente);
  coleta do dia seguinte → +5 linhas, anteriores intactas (AC-02–04);
- leitura servida filtra pela fonte efetiva — linha Pink Sheet do mesmo
  instrumento não aparece na série MetalCharts (AC-12/AC-15);
- `metals-daily` sob `permanent` grava 10 fechamentos diários em
  `metal_quote_observations`, cache vazio (AC-04/AC-06);
- `feed_statuses` reporta `latest_observation_date`/`observation_count`
  da tabela permanente (AC-14);
- falha de provider após coleta bem-sucedida → run `failed`, histórico
  intacto (AC-14);
- advisory lock rejeita run concorrente; 4 upserts concorrentes da
  mesma identidade → 1 linha, 1×`inserted`+3×`unchanged` (AC-03).

Suítes verdes: `test_persistent_metal_quotes_pg` 6/6, repository_pg
15/15, r5 44/44, prices_feed 16/16, queries 8/8, r2_pg — 1 falha
**PREEXISTENTE_CONFIRMADA** (`test_legacy_tables_unaffected`: asserção
da era R2 esperando `display_allowed=false` em metais, superada pela
ativação V008 — falha também no HEAD sem o diff, verificado por
stash). Gates `audit_architecture_phase3` e `audit_platform_guardrails`:
0 findings.

## Evidência de produção (read-only, 2026-11-03)

- `metalcharts`: `active=t`, `observation_retention=ttl_cache`, escopo
  `collect;derive;internal_display;store_cache_only;no_redistribute`
  — direitos inalterados, sem `store`.
- `metal_quote_observations` = 198 linhas (Pink Sheet até 2026-09),
  0 linhas metalcharts — correto; `metal_quote_cache` 110 linhas,
  0 não expiradas (TTL estrutural).
- Scheduler ativo (`feeds=metals-daily,metals-prices-daily`,
  RUN_AT 20:30, intervalos 3d/1d); últimos runs 2026-11-01/02 →
  `failed` `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` — egress Sophos segue
  bloqueado; ledger do mês = 0 weight (nenhuma chamada upstream).
- Estado coerente e fail-closed: feeds agendados, falha honesta
  registrada, nenhum dado retido sem direito.

## R12.S5 — Rights gate MetalCharts

`PROVIDER_PERMANENT_STORAGE_RIGHT = PENDING` — nenhuma evidência nova
de licença foi localizada no repositório ou fornecida. Permanece
proibido: alterar `store_cache_only`→`store` sem evidência, copiar
cache→observations, desativar o guard ou contornar o Sophos.

`R12_METALCHARTS_PERSISTENCE = BLOCKED_BY_SOURCE_RIGHTS`

### Checklist de ativação (quando o direito for comprovado)

1. Documento de aprovação (licença/escrita do fornecedor) registrado
   em `PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md` §5.
2. Migration aditiva: `observation_retention='permanent'` +
   `allowed_use_scope` com `store` na linha `metalcharts` (imutável
   histórico, sem `down`).
3. Deploy normal (local → push → pull → rebuild) — o código de
   roteamento/testes já está pronto neste commit.
4. Run real `metals-daily`/`metals-prices-daily` após liberação de
   egress `api.metalcharts.org` (Sophos, pendência TechMaster).
5. Verificar SELECT na tabela, BFF e gráficos; smoke federado.

## Pendências (inalteradas do R10/R11)

- Egress `api.metalcharts.org` bloqueado pelo Sophos — TI/TechMaster.
- Horário real de publicação upstream: RUN_AT 20:30 provisório.
- Substituição de fonte ou licença LME/MetalCharts para histórico
  permanente produtivo.

## Arquivos alterados

- `external-data-api/app/infrastructure/persistence/market_data_repository.py`
  — `list_metal_observations(source_id=…)` obrigatório; `feed_statuses`
  com freshness pela tabela efetiva da retenção.
- `external-data-api/app/application/market_data_queries.py` — passa
  `effective_source_id` ao repositório.
- `external-data-api/app/application/market_data_ingestion.py` —
  `metals-daily` roteia por `observation_retention` via `_quote_source`.
- `external-data-api/tests/test_persistent_metal_quotes_pg.py` — novo;
  `test_metalcharts_r5.py`, `test_market_data_repository_pg.py` —
  cobertura do roteamento permanente e do filtro de fonte.
