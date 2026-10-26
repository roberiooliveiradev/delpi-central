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
EXTERNAL_DATA_SCHEMA=external_data
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
  USD/tonelada métrica, base `monthly_average`.
- Fontes sem licença documental (LME, Shockmetais etc.) **não existem**
  no catálogo — ingestão recusa fonte inativa/não licenciada
  (`SOURCE_NOT_LICENSED`), sem fallback para sites alternativos.

## Testes

`pytest tests/` — unitários (normalizer, provider, limiter, factory),
HTTP (S2S, envelope, correlação), segurança (spoofing, fail-closed,
zero upstream pré-auth). Integração Redis real:
`EXTERNAL_DATA_TEST_REDIS_URL=redis://... pytest` — cobre dois clientes,
dois processos, concorrência, TTL, fail-closed, isolamento de namespace.

## Operação local

```bash
pip install -r requirements.txt && pip install -e "../shared[flask]"
python -m app.main        # :8000 — /health ok, /v1/cnpj exige S2S
```

## Preparação X2

`supplies-api` consumirá via `CnpjDataSource` HTTP+S2S atrás do port
`CompanyRegistryProvider` existente — paridade de projeção/erros
obrigatória antes de remover o adapter local `brasilapi`.
