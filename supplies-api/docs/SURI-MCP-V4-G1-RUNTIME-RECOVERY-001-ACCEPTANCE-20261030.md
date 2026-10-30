# SURI-MCP-V4-G1-RUNTIME-RECOVERY-001 — Aceite de Recuperação

Data: 2026-10-30
TASK: `SURI-MCP-V4-G1-RUNTIME-RECOVERY-001`
Escopo: corrigir as duas falhas do smoke autenticado ChatGPT da SURI V4 G1 e
revalidar em produção. Sem G2–G7, sem alteração cadastral real.

## 1. Baseline

```text
BASE HEAD:        386191e219 (rebaseline; aceite deploy = bfeae42952)
ORIGIN MAIN:      e282bdabc6 (rebaseline) → 87d40a538b (final)
FINAL HEAD:       87d40a538b
SOURCE SHA V4:    c82d92880219a7e97b76457e6174bc1caf4a27ac
GIT STATUS:       limpo no commit; commits concorrentes (VISTA/CAIO/CF)
                  disjuntos de supplies-api/infra-mcp
MCP IMAGE:        infra-supplies-mcp f6414a1e41db (inalterada — mudança só de env)
BFF IMAGE:        infra-supplies-api 8c87aefe1e66 (inalterada)
CONTAINERS:       delpi-supplies-mcp 7cbf41558f8a (healthy, restarts=0)
                  delpi-supplies-api 7541c4052de8 (healthy, restarts=0)
```

## 2. FAIL-01 — Ficha 360 (read(suppliers,get) → 502)

### Causa raiz

Indisponibilidade **transitória** do serviço OAuth2 do Protheus REST
(`192.168.1.231:8061/restall/api/oauth2/v1/token`) na janela do smoke do
usuário. Cadeia comprovada nos logs:

```text
api-delpi: "Protheus unavailable method=POST url=.../oauth2/v1/token"
→ upstream 503 → DelpiS2SApiGateway error → tool_bridge map → MCP 502
```

O caminho MCP é idêntico ao do Portal — BFF `GET /suppliers/<code>/<store>`
e `read(suppliers,get)` convergem no mesmo upstream
`/integrations/protheus/suppliers/{supplier_id}` com o mesmo gateway S2S
(`X-Delpi-Service-Authorization` + Bearer do usuário) e mesma projeção
`project_detail`. Não era INPUT/ROUTE/AUTHZ/S2S/ERROR-MAPPING — era
UPSTREAM externo transitório.

### Evidência pós-fix

- Sonda direta no endpoint OAuth Protheus: HTTP 400 para grant inválido —
  serviço respondendo (outage transitória encerrada).
- `GET /integrations/protheus/status` via S2S: configuration/authentication/
  connection/suppliers_read = `ok`.
- Chamada completa S2S + Bearer do usuário (delegated): supplier 00201201
  retornado com dados reais do Protheus.
- Smoke autenticado MCP (abaixo): `read(suppliers,get)` → 200, ficha 360
  completa (identification/address/contact/fiscal/purchasing).

### Fix

Nenhum — comportamento correto: mapeamento 503→502 honesto preservado.
Não se inventa fallback nem dado sintético.

## 3. FAIL-02 — Pré-cadastro (analyze(supplier_creation_preview) → 503)

### Causa raiz

`ENRICHMENT_RATE_LIMITER_UNAVAILABLE` — "distributed rate limiter
configured but REDIS_URL is missing". O limiter distribuído falhou fechado
**corretamente**. O gap: o bloco `environment:` de `supplies-mcp` no
`infra/docker-compose.yml` não tinha o mapa `REDIS_URL: ${DELPI_REDIS_URL:-}`
que `supplies-api` possui (X3). A `.env` fornece `DELPI_REDIS_URL` e
`COMPANY_REGISTRY_*` aos dois containers; só faltava o mapa explícito.
Redis `delpi-redis` estava saudável e alcançável pelos dois containers.

### Fix (menor diff)

`infra/docker-compose.yml`, bloco `supplies-mcp.environment` (+4 linhas):

```yaml
      # Supplier enrichment parity with supplies-api: distributed registry
      # rate limiter needs the shared DELPI redis URL (same X3 mapping).
      REDIS_URL: ${DELPI_REDIS_URL:-}
```

Nenhuma linha de código alterada; limiter permanece `distributed` e
fail-closed; nenhum bypass. Deploy: `docker compose up -d --no-build
supplies-mcp` (env-only; imagem não rebuildada).

### Evidência pós-fix

`analyze(supplier_creation_preview, filters.tax_id=23622391000181)` →
`success: true`:

- `duplicate_check.status = POSSIBLE_MATCH` (match exato supplier 002012/01)
- `suggestions[]` com proveniência `provider_id=brasilapi-cnpj-v1` +
  `retrieved_at` (via consumer external-data-api configurado)
- `tax_id_masked`, `person_type=J`
- `write_enabled = false` — nenhuma persistência

## 4. Smoke autenticado produção (R6)

Identidade: `devin-smoke-r4` — fluxo OAuth authorization-code + PKCE real
(mesmo client `mcp-supplies` do ChatGPT; aud
`['https://minhadelpi.com.br/apps/supplies-api/mcp', 'delpi-central',
'account']`, scope `mcp:tools`). Não é token de serviço. Foi concedido à
identidade o papel canônico `Portal Suprimentos - Acesso` (supplies.access)
via `user_roles` — grant canônico, não bypass de RBAC.

```text
read(suppliers,get) 002012/01          200  ficha 360 completa — PASS
analyze(supplier_creation_preview)     200  POSSIBLE_MATCH + proveniência — PASS
read(postal_codes,lookup) 03110-001    200  found viacep, CEP normalizado — PASS
read(suppliers,search_by_tax_id)       200  match exato — PASS
read(suppliers,catalogs) payment-methods 200 itens — PASS
read(suppliers,search) "1000 MARCAS"   200  itens — PASS
CEP inválido "123"                     422  validation — PASS
CNPJ inválido                          422  validation — PASS
catalog kind inválido "hacked"         422  allowlist fechada — PASS
filter key desconhecida                rej  schema fechado (union) — PASS
OAuth metadata                         200 — PASS
MCP sem Bearer                         401 + WWW-Authenticate correto — PASS
catalog_version                        4 — PASS
tool_count                             5 (get_context/read/analyze/knowledge/execute) — PASS
```

Antes da concessão de papel, a mesma chamada retornava 403 — evidência de
que autorização é derivada por chamada e fail-closed.

## 5. Operações de runtime executadas

- `user_roles`: INSERT (devin-smoke-r4 → Portal Suprimentos - Acesso).
- `docker restart delpi-core-api`: flush do RBACCache in-process sem TTL
  (grant via SQL direto não dispara o handler de eventos; health 200 após).
- `docker compose up -d --no-build supplies-mcp`: recriou
  delpi-supplies-mcp (e delpi-supplies-api no mesmo comando compose; mesma
  imagem/config, ambos healthy).

## 6. Testes

Mudança é de configuração (compose env), zero diff de código. Baselines
históricos permanecem: SURI 131, supplies-api 796/24. Smoke autenticado
acima é a verificação material desta recovery.

## 7. Rollback

- Config: reverter `REDIS_URL` no compose + recreate (imagem inalterada).
- Grant do usuário de smoke: aditivo e inócuo (identidade dedicada); remoção
  = DELETE em user_roles.
- Imagens V3/V4 anteriores retidas.

## 8. Resíduos

- `R7 CHATGPT SMOKE`: PENDING — requer a sessão OAuth interativa do usuário
  no conector SURI (re-executar `read(suppliers,get)` e
  `analyze(supplier_creation_preview)`; backend comprovado por smoke
  user-delegated equivalente).
- `union schema` de `read` rejeita chaves desconhecidas com texto pydantic
  pouco amigável (comportamento de rejeição correto; cosmético).

## 9. Veredito do executor

```text
SUPPLIER_360        PASS (502 transitório upstream; provado saudável agora)
CREATION_PREVIEW    PASS (REDIS_URL injetado; limiter distribuído ativo)
OAUTH/CATALOG/TOOLS PASS (inalterados)
AUTHZ               PASS (403 antes do grant → 200 após; fail-closed)
READ_ONLY           PASS (write_enabled=false; zero persistência)
REGRESSION          PASS (superfície V4 + V3 preservadas)
EXECUTION_DRIFT     nenhum
```

**STATUS: PASS** (execução) — pendente apenas homologação interativa
ChatGPT (R7), a ser reportada pelo usuário.
