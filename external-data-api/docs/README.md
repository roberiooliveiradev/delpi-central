# External Data API — Serviço de Dados Externos (X1)

Owner compartilhado de consultas a fontes cadastrais externas da Minha DELPI.
Contrato congelado: `docs/12-roadmap-e-evolucao/shared-integrations/EXTERNAL-DATA-API-CONTRACT-FREEZE-X0.md`.

## Responsabilidades

Transporte HTTP a providers externos, normalização técnica, minimização,
classificação de origem, rate limiting, erros tipados, correlation ID,
observabilidade segura. **Não possui**: AuthZ de usuário/recurso,
comparação SA2, revisões/decisões, escrita ERP, estado próprio (stateless,
sem PostgreSQL).

## Endpoints

| Rota | Auth | Descrição |
|---|---|---|
| `GET /health` | nenhuma | liveness do processo — nunca consulta provider |
| `GET /v1/cnpj/{cnpj}` | **S2S obrigatório** | consulta CNPJ numérico (14 dígitos) |

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
| 401 | `unauthorized` |
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
```

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
