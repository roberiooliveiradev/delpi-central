# External Data API — X0 Contract Freeze (2026-10-22)

> **FROZEN / TARGET — contrato técnico congelado para X1.** Documento de contrato,
> não implementação. Nenhum código de serviço foi criado, nenhum deploy autorizado.
> Autoridades: decisão PO (`EXTERNAL-DATA-API-MVP-ARCHITECTURE.md`, `c4cad18724`),
> instruções GPT Arquiteto, regras `.cursor` globais + especializadas
> (boundaries, api-contracts, security, persistence, reliability, delivery,
> quality, plan-construction/execution, test-and-commit), HEAD `85805eb7d5`+.

## 1. EXTERNAL_DATA_OWNERSHIP_MATRIX

| Serviço | Responsabilidade atual | Contratos existentes | Consumidores | Limitações | Compat. nova capacidade | Decisão |
|---|---|---|---|---|---|---|
| `core-api` | Identidade contextual, permissões efetivas, apps/políticas | AuthN/AuthZ Core, capability catalog | Todos os BFFs | Não é camada de dados externos | Indireta (AuthZ do consumidor) | **Não owner** — permanece autoridade de permissões |
| `api-delpi` | SQL TOTVS/Protheus, contratos canônicos ERP, escritas, proveniência; **precedente CEP**: `/addresses/postal-codes/{cep}` via ViaCEP (INT-CEP-01) | OpenAPI route registry, S2S allowlist por rota | supplies-api e outros BFFs | Mandato canônico é TOTVS; CEP é exceção legada documentada, não template | Estender para CNPJ genérico inflaria responsabilidade não-TOTVS no owner ERP | **Não owner do novo conceito** — CEP permanece; migração futura seria decisão separada |
| `supplies-api` | BFF Suprimentos: AuthZ usuário/recurso, leitura canônica, S1 comparação, S2 revisões/decisões, adapter BrasilAPI local (S3.1) | `ENRICHMENT_*` HTTP, S2S caller `supplies-api` | MFE supplies | Owner de negócio, não de fontes externas | Será **primeiro consumidor** | **Consumer, não owner** do transporte externo |
| `minha-delpi-ai-api` | Chat/LLM, tools OpenAPI, actions | Action Catalog, executores | Portal/chat | Tools IA ≠ consulta cadastral S2S | Outra finalidade | **Não owner** |
| `shared/` | Biblioteca (`delpi_auth`, `delpi_api_client`, envelope) | pacote pip interno | serviços Python | Não é serviço | Infra reutilizável | **Biblioteca, não serviço** |
| `gateway` (nginx) | Proxy `/apps/{svc}/` → `{svc}:8000` | nginx.conf | navegador | Sem lógica de negócio | external-data-api não precisa de upstream público | **Sem rota pública no MVP** |
| *(novo)* `external-data-api` | **Ausente** — nenhum serviço DELPI é owner de consultas cadastrais externas reutilizáveis | — | — | — | Preenche lacuna sem inflar api-delpi/Core | **OWNER PROPOSTO** |

**Conclusão de ownership:** não existe serviço/contexto autorizado para dados
externos reutilizáveis. O precedente ViaCEP na `api-delpi` é exceção de
conveniência (INT-CEP-01), não ownership genérico — estendê-lo criaria
duplicidade conceitual (dados TOTVS + dados públicos no mesmo boundary).
Novo serviço mínimo é a decisão compatível com a direção do PO; sem
`EXECUTION_DRIFT` — nenhuma regra superior proíbe o serviço e o S2S existente
suporta o novo callee sem mudança arquitetural.

## 2. SERVICE_IDENTITY_CONTRACT — `external-data-api` (CONFIRMADO)

| Item | Valor congelado | Evidência |
|---|---|---|
| Nome técnico / pasta | `external-data-api` | Convenção `*-api` do monorepo; grep: zero conflito |
| Container | `delpi-external-data-api` | Padrão `delpi-<service>` |
| Compose service | `external-data-api` | Aditivo ao `infra/docker-compose.yml` |
| DNS interno / porta | `external-data-api:8000` | Padrão Flask/gunicorn |
| Gateway público | **NENHUM** — serviço interno S2S-only; sem `location` em `nginx.conf` no MVP | Evita exposição desnecessária |
| Env prefix | `EXTERNAL_DATA_*` (+ `BRASILAPI_*`, `REDIS_URL`, `KEYCLOAK_*`, `S2S_*` compartilhados) | Convenção de env por serviço |
| Docs namespace | `external-data-api/docs/`, `docs/12-roadmap-e-evolucao/shared-integrations/` | Existente |
| Identidade S2S (callee) | valida tokens; allowlist inicial `("supplies-api",)` | Mesmo padrão `postal_codes_router` |

## 3. EXTERNAL_DATA_CONTEXT_BOUNDARY

**external-data-api possui:** HTTP client a providers externos, normalização
técnica, validação de schema, verificação de identidade consultada (CNPJ
solicitado = CNPJ retornado), minimização de payload, classificação de fonte,
rate limiting (consumer/cnpj/global), erros tipados, correlation ID,
observabilidade sem PII, configuração de providers autorizados.

**Permanecem fora:** AuthZ de usuário/recurso, leitura canônica, comparação SA2,
elegibilidade, revisões, decisões, idempotência de workflow, `prepare-update`
→ `supplies-api`. SQL/ERP/proveniência/escrita → `api-delpi`. Identidade e
permissões efetivas → `core-api`. SSO → Keycloak.

**Invariantes congelados:** sem acesso a banco de outro contexto; sem import de
`domain/application` alheio (reuso apenas via `shared/delpi_auth` —
biblioteca, não regra de negócio); sem lógica SA2 nem decisão de fornecedor;
sem permission por endpoint; sem exposição direta de BrasilAPI a frontend;
sem escrita ERP; sem estado próprio no MVP (**stateless**, sem PostgreSQL).

## 4. EXTERNAL_DATA_CNPJ_API_CONTRACT (FROZEN para X1)

```
GET /v1/cnpj/{cnpj}          Host: external-data-api:8000 (rede interna apenas)
```

**Por que não `/internal/external-data/v1/...`:** o serviço não é exposto pelo
gateway — o prefixo `/internal/` é cosmético aqui e diverge do padrão real
(api-delpi usa paths de domínio planos, ex. `/addresses/postal-codes/{cep}`;
`internal` aparece apenas como segmento em `/ppm/internal/*`). Contrato
versionado plano é consistente e mínimo. Se um dia houver exposição via
gateway, a decisão de prefixo é revista sob `GATE-CONTRACT`.

**Request:**

| Campo | Regra |
|---|---|
| Path `cnpj` | 14 dígitos numéricos; formato alfanumérico BrasilAPI **rejeitado** (paridade S1 — identidade S1 exige numérico) |
| `X-Delpi-Service-Authorization` | JWT client-credentials Keycloak — obrigatório, validado por signature+issuer+audience |
| `X-Request-Id` / `X-Correlation-Id` | Propagado quando presente; gerado se ausente |
| Identidade de usuário | **NÃO aceita** — serviço não recebe nem confia em identidade de usuário final |

**Response 200 (DTO versionado `v1`, allowlist estrita):**

```json
{
  "tax_id": "19131243000197",
  "legal_name": "...",
  "trade_name": null,
  "address": {
    "street": "...", "number": "...", "complement": null,
    "district": "...", "postal_code": "...", "city": "...",
    "state": "...", "ibge_city_code": null
  },
  "contact": {"area_code": null, "phone": null, "email": null},
  "registration": {
    "status": null, "main_cnae": null,
    "legal_nature": null, "opening_date": null
  },
  "source": {
    "provider_id": "brasilapi-cnpj-v1",
    "source_type": "THIRD_PARTY_API",
    "retrieved_at": "<RFC3339 UTC>",
    "correlation_id": "...",
    "schema_version": "v1"
  }
}
```

Nunca: `qsa`, CPF, sócios, raw payload BrasilAPI, campos SA2 (`A2_*`),
`source_type=GOVERNMENT_API`. `contact` é dado cadastral de empresa (não
pessoal), retornado; classificação LGPD/ROPA permanece gate operacional.

**Erros — envelope `{"detail": str, "code": str}` (mesmo padrão supplies-api):**

| HTTP | code | Condição |
|---|---|---|
| 400 | `EXTERNAL_DATA_INVALID_TAX_ID` | Formato CNPJ inválido/alfanumérico |
| 401 | `unauthorized` | Token ausente/inválido |
| 403 | `forbidden` | Cliente S2S fora da allowlist |
| 404 | `EXTERNAL_DATA_TAX_ID_NOT_FOUND` | CNPJ inexistente no provider |
| 429 | `EXTERNAL_DATA_RATE_LIMITED` + `Retry-After` | Cap consumer/cnpj/global excedido |
| 502 | `EXTERNAL_DATA_INVALID_RESPONSE` | Schema inesperado / CNPJ divergente |
| 503 | `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` | Provider 5xx/403/erro de transporte |
| 503 | `EXTERNAL_DATA_LIMITER_UNAVAILABLE` | Backend de rate limit indisponível |
| 504 | `EXTERNAL_DATA_PROVIDER_TIMEOUT` | Timeout upstream (default 6s) |

## 5. EXTERNAL_DATA_S2S_SECURITY_CONTRACT

Máquina existente, zero invenção:

- **Callee:** `delpi_auth` — `ServiceTokenValidator.from_env()` +
  `@require_s2s_service(allowed_clients=("supplies-api",))` por rota;
  valida signature (JWKS), issuer, audience (`S2S_AUDIENCE_ENV`),
  extrai `client_id` dos claims. Padrão idêntico ao `postal_codes_router`.
- **Caller (supplies-api):** `ClientCredentialsTokenProvider.from_env()`
  singleton process-wide, header `X-Delpi-Service-Authorization`.
- **Env callee:** `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`,
  `KEYCLOAK_ISSUER_INTERNAL`, `S2S_AUDIENCE`/`KEYCLOAK_AUDIENCE` — mesmas
  vars já usadas por core/api-delpi.
- **Não** aceita JWT de usuário como autoridade; **não** cria permission
  por rota; **não** concede acesso irrestrito a capacidades futuras —
  allowlist é por rota/capacidade.
- Fail-closed: token inválido, audience divergente, cliente fora da
  allowlist ou validator indisponível → 401/403, nunca consulta upstream.

## 6. EXTERNAL_DATA_BRASILAPI_PROVIDER_CONTRACT

| Item | Valor |
|---|---|
| Upstream | `GET https://brasilapi.com.br/api/cnpj/v1/{cnpj}` (público, sem auth, fonte Minha Receita — intermediária comunitária) |
| `provider_id` / `source_type` | `brasilapi-cnpj-v1` / `THIRD_PARTY_API` (nunca `GOVERNMENT_API`) |
| Timeout | `BRASILAPI_TIMEOUT_SECONDS`, default 6s, zero retries agressivos |
| 429 upstream | Honrar `Retry-After`; nunca contornar anti-abuso |
| Normalização | Allowlist → campos do DTO §4; `logradouro` já embute número (dedup preservado da evidência S3.1); `ddd_telefone_1` → `area_code`+`phone` |
| Validações | CNPJ resposta = CNPJ solicitado; schema mínimo presente; JSON válido; rejeita resposta incompatível → 502 |
| Exclusões | `qsa`, `ddd_telefone_2`, `porte`, CPF/pessoais fora do DTO — nunca lidos, logados ou persistidos |
| Logs | Sem CNPJ cru, sem payload; `source_reference` mascarado |
| Migração de código | `brasilapi_registry_provider.py` da supplies-api é **referência de adaptação**, não import — reimplementar no novo contexto sob testes de paridade |

## 7. RATE LIMIT CONTRACT

- Backend: reimplementação do design `registry_rate_limits.py` (adaptação
  autorizada — Ports & Adapters, não import cross-context): script Lua
  atômico único (check-todas-dimensões→incrementa, sem consumo parcial,
  TTL em toda chave).
- **Dimensões no owner externo:** `consumer` (S2S `client_id`, substitui
  `actor` — o serviço não vê usuário final), `cnpj` (SHA-256[:20], nunca
  cru), `global`. Limites conservadores internos (default 10/10/30 por
  min) — não são quota BrasilAPI.
- **Dimensão `actor` (usuário):** permanece na `supplies-api` — política
  por `EffectiveUser.id` é responsabilidade do BFF, já implementada.
- Estratégia `process_local|distributed` + gate
  `EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED` (mesma semântica S3.3:
  `process_local` só com opt-in explícito; desconhecida → fail-closed).
- Redis indisponível → `EXTERNAL_DATA_LIMITER_UNAVAILABLE` 503; nunca
  consulta externa; consumidor não é derrubado (erro isolado na rota).
- **REDIS DEPENDENCY:** idêntica à S3.3 — nenhum Redis DELPI autorizado
  hoje; `evolution-redis` proibido; provisionamento é `GATE-INFRA`/X3.

## 8. EXTERNAL_DATA_MINIMAL_RUNTIME_CONTRACT

| Item | Decisão |
|---|---|
| Stack | Python 3.12-slim + Flask + gunicorn (padrão comprovado, sem troca de framework) |
| Lib compartilhada | `COPY shared /shared` + `pip install -e "/shared[flask]"` (mesmo Dockerfile pattern) |
| Workers | `--workers 2 --threads 4` — exige `distributed` para rate limit correto |
| Estado | **Stateless** — sem PostgreSQL no MVP |
| Health | `GET /health` (padrão container healthy) |
| Env | `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable|brasilapi` (default `unavailable` fail-closed), `EXTERNAL_DATA_RATE_LIMIT_STRATEGY`, `EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED`, `EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE`, `EXTERNAL_DATA_GLOBAL_MAX_QUERIES_PER_MINUTE`, `BRASILAPI_BASE_URL`, `BRASILAPI_TIMEOUT_SECONDS`, `REDIS_URL`, `KEYCLOAK_*`, `S2S_*` |
| Deploy | `up-prod-sequential.sh` fase `api`; **NOT RUN** até GATE-INFRA/RUNTIME |

## 9. SUPPLIES_EXTERNAL_DATA_CONSUMER_CONTRACT

```
supplies-api
  └─ CompanyRegistryProvider (port estável — sem mudança)
       └─ ExternalDataApiCompanyRegistryProvider (adapter HTTP+S2S — X2)
            └─ GET external-data-api:8000/v1/cnpj/{cnpj}
```

- `EXTERNAL_DATA_*` erros mapeados 1:1 para `ENRICHMENT_*` existentes
  (invalid→422, not-found→404, 429→429+Retry-After, unavailable→503,
  invalid-response→502, limiter→503) — **zero mudança de envelope ao MFE**.
- Feature flag provisória: `COMPANY_REGISTRY_PROVIDER=unavailable|brasilapi|
  external-data-api` — `brasilapi` (local) mantido até paridade comprovada;
  remoção do adapter local só após runtime saudável.
- **Paridade obrigatória (X2):** mesmo CNPJ → snapshot equivalente em todos
  os `source_field`s S1; CNPJ divergente rejeitado; QSA excluído;
  `provider_id`/`source_reference`/`retrieved_at` equivalentes; erros e
  envelopes idênticos; zero escrita Protheus; AuthZ usuário/recurso
  permanece no BFF; comparação S1, persistência S2, idempotência e
  `prepare-update` inalterados.

## 10. EXTERNAL_DATA_IMPLEMENTATION_PLAN

| Etapa | Entrega | Gate |
|---|---|---|
| **X1** Foundation + CNPJ | Serviço mínimo (Flask/gunicorn/delpi_auth), health, S2S+allowlist, `GET /v1/cnpj/{cnpj}`, adapter BrasilAPI reimplementado, normalização, rate limiter (3 dims, Lua), erros tipados, testes + Redis/PG efêmeros | GATE-OWNER ✓, GATE-CONTRACT ✓, GATE-SECURITY |
| **X2** Consumer parity | `ExternalDataApiCompanyRegistryProvider` na supplies-api, flag `external-data-api`, paridade de projeção/erros, regressão S1/S2 integral | GATE-CONSUMER-PARITY |
| **X3** Runtime & deploy | Redis DELPI autorizado (pendência herdada de S3.3), migrations V002/V003 sob backup, build/deploy restrito, smokes autenticados, SHA/digest, rollback | GATE-INFRA, GATE-RUNTIME |
| **X4** UX Suprimentos | Comparação assistida no MFE — somente com autorização específica de página | GATE-FEATURE |

X1 **não** inicia automaticamente. Serpro fora de escopo até contratação.

## 11. Status de gates X0

- `GATE-OWNER` = **PASS** — nenhum serviço existente é owner; CEP/api-delpi
  é exceção documentada, não conflito.
- `GATE-CONTRACT` = **FROZEN** — §4–§6.
- `GATE-SECURITY` = **FROZEN** com residual — DPO/ROPA p/ consulta externa
  segue pendência operacional herdada (não bloqueia X1 código).
- `GATE-INFRA` = **INCONCLUSIVE** — Redis DELPI inexistente (mesma
  pendência de S3.3); bloqueia X3, não X1/X2 (process_local+opt-in cobre
  dev/test; produção exige distributed).
- `GATE-CONSUMER-PARITY` / `GATE-RUNTIME` = `TARGET` para X2/X3.
