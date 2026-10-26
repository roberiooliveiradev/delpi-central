# External Data API — Serviço de Dados Externos (X1)

Owner compartilhado de consultas a fontes cadastrais externas da Minha DELPI.
Contrato congelado: `docs/12-roadmap-e-evolucao/shared-integrations/EXTERNAL-DATA-API-CONTRACT-FREEZE-X0.md`.

## Responsabilidades

Transporte HTTP a providers externos, normalização técnica, minimização,
classificação de origem, rate limiting, erros tipados, correlation ID,
observabilidade segura. **Não possui**: AuthZ de usuário/recurso,
comparação SA2, revisões/decisões, escrita ERP.

> **Evolução de contrato (PROC-0076):** o serviço nasceu stateless (X0)
> e passa a deter também o histórico de **dados de mercado** (cotações
> de metais e câmbio) — decisão PO, evolução aditiva: o contrato X0/X1
> de CNPJ permanece intacto. O estado novo vive exclusivamente no schema
> `external_data` do `postgres-plugins`, com migrations próprias
> (`external-data-api/migrations/`), checksum sha256 e imutabilidade de
> arquivos aplicados. Sem acesso a outros schemas e sem tabela de
> fornecedores.

## Endpoints

| Rota | Auth | Descrição |
|---|---|---|
| `GET /health` | nenhuma | liveness do processo — nunca consulta provider |
| `GET /v1/cnpj/{cnpj}` | **S2S obrigatório** | consulta CNPJ numérico (14 dígitos) |
| `GET /v1/market-data/catalog` | **S2S obrigatório** | catálogo de instrumentos, séries FX e fontes licenciadas |
| `GET /v1/market-data/metals/observations` | **S2S obrigatório** | histórico persistido por `instrument_code` + janela + cursor |
| `GET /v1/market-data/fx/observations` | **S2S obrigatório** | séries FX persistidas por `pair` + `rate_kind` + janela |
| `GET /v1/market-data/ingestion-status` | **S2S obrigatório** | última run/sucesso e frescor por feed |

Rotas market-data servem **somente histórico persistido** — nenhuma
chamada à internet acontece no request; a coleta é o job
`python -m app.jobs.ingest_market_data --feed fx-daily|metals-monthly`,
opt-in por env (`EXTERNAL_DATA_FEED_*_ENABLED`) e por fonte ativa e
licenciada no catálogo. Limites: `limit` ≤ 500, janela diária FX ≤ 366
dias, janela mensal metais ≤ 3660 dias. `data_status=no_data` quando o
período é legítimo mas vazio — nunca zero fictício.

Serviço **interno** — DNS `external-data-api:8000` na `delpi-network`;
sem rota no gateway nginx e sem porta publicada no host.

## S2S

- Header: `X-Delpi-Service-Authorization` — JWT client-credentials
  Keycloak validado por `delpi_auth.ServiceTokenValidator`
  (signature/JWKS + issuer + audience + allowlist).
- Allowlist inicial por rota: `("supplies-api",)`.
- `client_id` validado vira a dimensão `consumer` do rate limiter.
- Nenhum JWT de usuário autoriza; headers de identidade arbitrários são
  ignorados. Falha do validator/config → fail-closed 503.

## DTO v1 (200)

```json
{
  "tax_id": "...", "legal_name": "...", "trade_name": null,
  "address": {"street","number","complement","district","postal_code","city","state","ibge_city_code"},
  "contact": {"area_code": null, "phone": null, "email": null},
  "registration": {"status","main_cnae","legal_nature","opening_date"},
  "source": {"provider_id": "brasilapi-cnpj-v1", "source_type": "THIRD_PARTY_API",
             "retrieved_at", "correlation_id", "schema_version": "v1"}
}
```

Nunca: `qsa`, CPF, sócios, raw payload, campos `A2_*`,
`GOVERNMENT_API`.

**LGPD — contatos:** `contact` existe no DTO mas `area_code`/`phone`/
`email` permanecem `null` até que finalidade e minimização do tratamento
de contatos empresariais potencialmente pessoais estejam autorizadas
institucionalmente (correção X1 sobre a redação do freeze X0).

## Erros — envelope `{"detail", "code"}`

| HTTP | code |
|---|---|
| 400 | `EXTERNAL_DATA_INVALID_TAX_ID` |
| 400 | `EXTERNAL_DATA_INVALID_QUERY` (market data) |
| 401 | `unauthorized` |
| 403 | `forbidden` (S2S negado) |
| 404 | `EXTERNAL_DATA_UNKNOWN_INSTRUMENT` / `EXTERNAL_DATA_UNKNOWN_SERIES` |
| 429 | `EXTERNAL_DATA_RATE_LIMITED` (+ `Retry-After`) |
| 502 | `EXTERNAL_DATA_INVALID_RESPONSE` (ingestão/provider) |
| 503 | `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` / `EXTERNAL_DATA_STORAGE_UNAVAILABLE` / `EXTERNAL_DATA_SOURCE_NOT_LICENSED` / `EXTERNAL_DATA_FEED_DISABLED` / `EXTERNAL_DATA_INGESTION_LOCKED` |
| 504 | `EXTERNAL_DATA_PROVIDER_TIMEOUT` |
| 403 | `forbidden` |
| 404 | `EXTERNAL_DATA_TAX_ID_NOT_FOUND` |
| 429 | `EXTERNAL_DATA_RATE_LIMITED` + `Retry-After` |
| 502 | `EXTERNAL_DATA_INVALID_RESPONSE` |
| 503 | `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` |
| 503 | `EXTERNAL_DATA_LIMITER_UNAVAILABLE` |
| 503 | `service_unavailable` (validator/config S2S) |
| 504 | `EXTERNAL_DATA_PROVIDER_TIMEOUT` |

## Provider — BrasilAPI CNPJ v1

`GET {BRASILAPI_BASE_URL}/cnpj/v1/{cnpj}` — público, comunidade (fonte
Minha Receita via intermediário). Timeout 6s default, zero retry, 429
honrado. CNPJ retornado deve igualar o consultado; payload não-objeto ou
CNPJ divergente → 502. Normalização em
`app/infrastructure/normalization/brasilapi_cnpj_normalizer.py` (pura,
allowlist).

## Rate limit

Dimensões `consumer` (client_id), `cnpj` (SHA-256[:20]), `global` —
aquisição atômica única (sem consumo parcial). `process_local` exige
`EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED=true` quando o provider é
`brasilapi`; `distributed` usa Redis (`REDIS_URL`) com script Lua +
TTL + namespace `external-data:rate-limit:`; Redis indisponível →
fail-closed 503. Estratégia desconhecida → fail-closed.

## Configuração

```
EXTERNAL_DATA_CNPJ_PROVIDER=unavailable|brasilapi   (default unavailable)
EXTERNAL_DATA_RATE_LIMIT_STRATEGY=process_local|distributed
EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED=false
EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE=10
EXTERNAL_DATA_GLOBAL_MAX_QUERIES_PER_MINUTE=30
EXTERNAL_DATA_RATE_LIMIT_PREFIX=external-data:rate-limit:
EXTERNAL_DATA_REDIS_TIMEOUT_SECONDS=1.5
BRASILAPI_BASE_URL=https://brasilapi.com.br/api
BRASILAPI_TIMEOUT_SECONDS=6
REDIS_URL=
S2S_AUDIENCE=external-data-api
S2S_ALLOWED_CLIENTS=supplies-api
KEYCLOAK_URL/KEYCLOAK_REALM/KEYCLOAK_JWKS_URL/KEYCLOAK_ISSUER/KEYCLOAK_AUDIENCE

# Market data (PROC-0076) — sem PLUGINS_DB_* o serviço permanece
# stateless e as rotas market-data respondem STORAGE_UNAVAILABLE.
PLUGINS_DB_HOST/PLUGINS_DB_PORT/PLUGINS_DB_NAME/PLUGINS_DB_USER/PLUGINS_DB_PASSWORD
PLUGINS_DB_CONNECT_TIMEOUT=5
PLUGINS_DB_SSLMODE=prefer
# EXTERNAL_DATA_SCHEMA é constante canônica fixa ("external_data") —
# não configurável por env: migrations V001+ criam o schema literal e
# isolar por nome quebraria o ledger schema_migrations vs DDL real.
# Isolamento entre ambientes é por PLUGINS_DB_* (host/database).
EXTERNAL_DATA_RUN_MIGRATIONS_ON_STARTUP=true
EXTERNAL_DATA_FEED_FX_DAILY_ENABLED=false
EXTERNAL_DATA_FEED_METALS_MONTHLY_ENABLED=false
PTAX_BASE_URL=https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1
PTAX_TIMEOUT_SECONDS=15
WORLDBANK_PINKSHEET_MONTHLY_URL=https://thedocs.worldbank.org/…/CMO-Historical-Data-Monthly.xlsx
WORLDBANK_PINKSHEET_TIMEOUT_SECONDS=30
```

## Fontes licenciadas (PROC-0076)

- **PTAX — Banco Central do Brasil** (ODbL, boletim de fechamento,
  compra e venda). Attribution exigida e trafegada no DTO.
- **World Bank "Pink Sheet"** — preços mensais de commodities
  (CC BY 4.0). Cobre, alumínio, zinco, níquel, chumbo e estanho,
  USD/tonelada métrica, base `monthly_average`. **Proveniência de
  terceiros:** as descrições das séries do workbook identificam as
  cotações subjacentes como LME; a CC BY 4.0 do Banco Mundial não
  cobre dados de terceiros. V003 registra essa proveniência; **V004
  (R1.1)** refina o escopo para
  `collect;store;derive;internal_display_pending_lme_review;
  no_redistribution_pending_lme_review` — os ToU oficiais de datasets
  do WB delegam dados de terceiros aos termos do provedor, e a LME
  licencia exibição separadamente do uso interno limitado. Coleta,
  armazenamento e derivação da publicação WB estão cobertos; exibição
  interna e redistribuição aguardam decisão institucional formal.
  Matriz de evidências:
  `docs/12-roadmap-e-evolucao/shared-integrations/PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md`.
- Fontes sem licença documental (LME direto, Shockmetais etc.)
  **não existem** no catálogo — ingestão recusa fonte inativa/não
  licenciada (`SOURCE_NOT_LICENSED`), sem fallback para sites
  alternativos.
- **Quarentena fail-closed (R1.2):** a política de uso é por operação
  (`collect`, `store`, `derive`, `internal_display`) em
  `app/domain/usage_policy.py`. O valor `*_pending_*` no
  `allowed_use_scope` **não** é concessão — as seis séries LME-backed
  do Pink Sheet permanecem armazenadas (nada é apagado), mas as rotas
  de observação/catálogo recusam `internal_display` com
  `EXTERNAL_DATA_USE_NOT_APPROVED` e expõem `display_allowed=false`
  no catálogo. Ingestão exige `collect`+`store` concedidos
  explicitamente; flag de feed ativada indevidamente não basta. A
  liberação futura exige migration aditiva após decisão institucional
  documentada — não existe bypass por configuração.

## Migrations de market data

`external-data-api/migrations/` — V001 (schema `external_data` +
tabelas), V002 (catálogo licenciado), V003 (proveniência LME do
Pink Sheet), V004 (escopo de exibição interna pendente de revisão LME). Arquivos aplicados são imutáveis e verificados por
checksum sha256; divergência aborta o boot do módulo. O runner usa
advisory lock PostgreSQL entre workers e, em falha, o serviço sobe
**degradado** — CNPJ continua respondendo e market-data responde
`STORAGE_UNAVAILABLE`, nunca derruba o processo.

## Testes

`pytest tests/` — unitários (normalizer, provider, limiter, factory),
HTTP (S2S, envelope, correlação), segurança (spoofing, fail-closed,
zero upstream pré-auth). Integração Redis real:
`EXTERNAL_DATA_TEST_REDIS_URL=redis://... pytest` — cobre dois clientes,
dois processos, concorrência, TTL, fail-closed, isolamento de namespace.

**PostgreSQL real (descartável, fail-closed — R1.2):** os testes
`test_market_data_repository_pg.py` e `test_startup_migrations.py` rodam
contra um banco isolado quando `EXTERNAL_DATA_TEST_PG_HOST` está definido
(+ `_PORT`/`_NAME`/`_USER`/`_PASSWORD`); sem a env, são `TEST_NOT_RUN`.
Antes de qualquer migration ou `DROP`, `tests/pg_disposable_guard.py`
exige: (1) `EXTERNAL_DATA_TEST_PG_DISPOSABLE=1` explícito; (2) host
loopback (ou `EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE=1`); (3) dbname com
`test` no nome e fora da lista reservada; (4) **prova independente de
provisionamento** — `EXTERNAL_DATA_TEST_PG_TOKEN` emitido por
`tests/provision_pg_test_db.py` deve casar com a linha
`provisioned_by='pg_provision'` gravada pelo provisionador em
`public.delpi_disposable_db_guard`, no mesmo banco conectado. A guarda
**nunca** cria nem escreve a sentinela; flag, nome `*_test`, host
loopback, schema vazio ou sentinela pré-existente/estrangeira não são
prova suficiente. Falha de qualquer camada aborta antes de SQL mutante
(`UnsafeTestDatabaseError`). Verificação manual:
`python -m tests.pg_check_env`. Prova cobre migrations V001–V004,
checksum/imutabilidade, advisory lock, constraints `NUMERIC`,
unicidade/FK, idempotência e boot degradado. Isolamento é por database
de teste — o schema é sempre o canônico `external_data`.

## Operação local

```bash
pip install -r requirements.txt && pip install -e "../shared[flask]"
python -m app.main        # :8000 — /health ok, /v1/cnpj exige S2S
```

## Preparação X2

`supplies-api` consumirá via `CnpjDataSource` HTTP+S2S atrás do port
`CompanyRegistryProvider` existente — paridade de projeção/erros
obrigatória antes de remover o adapter local `brasilapi`.
