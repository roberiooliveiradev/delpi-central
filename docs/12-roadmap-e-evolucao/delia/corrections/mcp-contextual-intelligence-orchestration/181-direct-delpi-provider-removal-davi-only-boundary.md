# 181 — DÉLIA · Direct DELPI Provider Removal & DAVI-Only Boundary Validation

**TASK_ID:** `DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-AND-DEPLOY-01`
**Executor:** Cursor / Devin
**Base HEAD:** `1784260ebfd4aabd382a14dedf0eb1538a9f3149`
**Decisão de produto:** explícita do usuário — DÉLIA não acessa a API DELPI diretamente; a integração empresarial ocorre exclusivamente via DAVI/MCP. Capabilities que o DAVI não expõe são **legitimamente indisponíveis** — sem fallback, sem caminho direto alternativo.
**Status:** implementado localmente; deploy **bloqueado** pelo gate de segurança (ver §9).

---

## 1. Reancoragem

HEAD/origin `1784260ebf` (contém docs 179–180 + revisões); worktree limpa antes do diff. Autoridades 16→50→17→49→51→52→21→20→25; docs 175–180; ledger. Fase C3 — CP/RQ não avançado.

## 2. WP0 — Inventário da boundary (estado pré-remoção)

| Elemento | Localização |
|---|---|
| Source direto | `root_composer._wire_openapi_provider` → `build_openapi_source(source_id="delpi")` → `OpenApiCapabilityProvider` |
| Declarações | `delia-api/config/openapi_declarations.delpi.json` — 2 caps remanescentes (`get_product_summary`, `search_customers`) |
| Settings | `openapi_delpi_enabled`, `openapi_delpi_base_url`, `openapi_delpi_declarations_path` + `openapi_timeout_seconds` (consumidor único) |
| Env | `infra/docker-compose.yml`, `infra/docker-compose.dev.yml`, `delia-api/env.example` — blocos `DELIA_OPENAPI_DELPI_*` + `DELIA_OPENAPI_TIMEOUT_SECONDS` |
| Fallback | nenhum — providers são fail-closed por construção; verificado |
| Consumidores compartilhados | `HttpOpenApiInvoker`, `OpenApiCapabilityProvider`, `source_loader`, `capability_catalog_adapter` — preservados (evals/tests usam a classe diretamente) |

## 3. WP1 — RED

5 testes RED confirmados no estado pré-remoção:

- `test_no_direct_delpi_declarations_file` — arquivo existia.
- `test_no_governed_declarations_expose_direct_delpi_capabilities` — 2 ids `delpi.*` presentes.
- `test_composer_has_no_direct_delpi_source` — `_wire_openapi_provider` + `source_id="delpi"` presentes.
- `test_infra_and_env_carry_no_direct_delpi_wiring` — 3 arquivos com `DELIA_OPENAPI_DELPI`.
- `test_no_direct_delpi_openapi_settings` (test_config.py) — attrs existiam em `Settings`.

## 4. WP2 — Remoção aplicada

| Arquivo | Ação |
|---|---|
| `delia-api/config/openapi_declarations.delpi.json` | **removido** (binding integral; sem consumidor não-relacionado) |
| `root_composer.py` | `_wire_openapi_provider` removida; call site removido; import `OpenApiCapabilityProvider` removido; comentário §6.130 atualizado — MCP é a família wired; indisponibilidade legítima para caps fora do DAVI |
| `settings.py` | `openapi_delpi_*` removidos; `openapi_timeout_seconds` removido (único consumidor era o wiring removido — dead config) |
| `infra/docker-compose.yml` / `.dev.yml` | bloco §6.130 + 4 env vars removidos (YAML validado) |
| `delia-api/env.example` | bloco substituído por nota de boundary |
| `scripts/governed_davi_migration_eval.py` | matriz de cobertura atualizada: caps não-DAVI = `UNAVAILABLE` |

**Preservados:** `HttpOpenApiInvoker`, `OpenApiCapabilityProvider`, `source_loader`, `capability_catalog_adapter` (shared, usados por evals/tests), `McpCapabilityProvider`, `SpecialistInterop`, EvidenceFacts, Outcome, CRI, governed recovery, candidato-token discover→execute.

## 5. WP3 — DAVI como único caminho

Inalterado: `McpCapabilityProvider` → `SpecialistInterop` → `davi` (`discover_delpi_information`/`execute_delpi_information`). Nenhuma capability/allowlist/mensagem DAVI tocada. Seleção permanece semântica provider-neutral — nenhuma regra por palavra-chave; o código DÉLIA não conhece a mecânica interna DAVI→DELPI.

## 6. WP4 — Regressão e segurança

- GREEN: 69 testes nos arquivos tocados.
- Suite completa delia-api: única falha = `PRE_EXISTING_CRI_CONTRACT_DRIFT` (residual do owner da instrução, inalterado).
- Architecture gate `audit_architecture_phase3 --base HEAD --check`: **OK**.
- Garantias preservadas: `IDENTITY → LIVE CORE AUTHZ → DOMAIN AUTHORITY`, `DISCOVERY != APPROVAL`, `TOOL METADATA != PERMISSION`, `READ != WRITE`, `PREPARE != ACT`, `TECHNICAL SUCCESS != BUSINESS OUTCOME`.

## 7. WP5 — Residual search

`grep -rn 'OPENAPI_DELPI|openapi_delpi|openapi_declarations.delpi' delia-api infra` → apenas testes do contrato de remoção e comentários. `DIRECT_DELPI_PROVIDER=0`, `DIRECT_DELPI_CAPABILITIES=0`, `DIRECT_DELPI_PROVIDER_REGISTRATIONS=0`, `DIRECT_DELPI_PROVIDER_ENV_SETTINGS=0`, `DIRECT_DELPI_RUNTIME_FALLBACKS=0`. Referências `api-delpi` remanescentes: nome do resource DAVI (`mcp-api-delpi`), metadado de owner em `rules.py` e docs históricas — legítimas.

## 8. WP6 — E2E local (paired eval, zero rede)

`governed_davi_migration_eval.py` reexecutado: declared recoverable SUCCESS (2wire B0-adapter / 4wire B1), undeclared/non-recoverable/transient terminais, AUTHZ_DENIED nos dois caminhos, repeated rejection bounded, `VALIDATION_ERROR` legado terminal, `AUTHORIZATION_DENIED`→AUTHZ_DENIED, `CAPABILITY_NOT_ALLOWED`/`OWNER_EXECUTION_ERROR` terminais. Capability coverage: `search_products`/`get_product_stock` MIGRATED; `get_product_summary`/`search_customers` → `UNAVAILABLE` (sem binding direto). Classificado como **teste de contrato local** — não é prova de produção. Runtime real: **INCONCLUSIVE**.

## 9. WP8 — Gates de deploy

`CODE_REVIEW=diff minimal` · `CONTRACT_TESTS=PASS` · `FULL_REGRESSION=PASS(1 pre-existing CRI drift)` · `ARCHITECTURE_GATE=OK` · `DIRECT_DELPI_REMOVAL_VERIFIED=YES` · `DAVI_MCP_INTEGRATION_VERIFIED=local-contract` · **`SECURITY_OWNER_RELEASE_DECISION=PENDING`** — exposição de credencial doc 174 sem ratificação formal do security owner → **`RELEASE_GATE=BLOCKED → DEPLOY_NOT_EXECUTED`**. Nenhuma mutação de runtime produtivo; zero queries produtivas.

## 10. Residuais

1. `SECURITY_OWNER_RELEASE_DECISION` (doc 174) bloqueia qualquer release produtiva desta mudança.
2. `get_product_summary`/`search_customers` indisponíveis por decisão de produto — exposição DAVI continua `OWNER_DECISION_REQUIRED` para restauração futura legítima.
3. `PRE_EXISTING_CRI_CONTRACT_DRIFT` (owner da instrução).
4. Filtros `product_type|sort|direction` de `search_products` — `OWNER_DECISION_REQUIRED` DAVI.

## 11. Rollback

`git revert` do commit desta task restaura arquivo de declarações, wiring do composer, settings e envs — reversão completa em um commit. Runtime produtivo intocado.

## 12. Veredito

`LOCAL_PASS_WITH_RESIDUAL` — boundary direto eliminado e provado por residual search + RED/GREEN + regressão. Deploy `BLOCKED` pelo gate de segurança (não por falha técnica). A arquitetura DÉLIA→DAVI-only está completa no código: DELPI domain data só chega via `mcp-api-delpi`; ausência de capability = indisponibilidade legítima.

`DEPLOY_EXECUTED=NO` · `PRODUCTION_QUERIES=0` · `MODEL_CHANGED=NO` · `KEYCLOAK_MODIFIED=NO` · `API_DELPI_CODE_UNCHANGED=YES` · `DAVI_CAPABILITIES_UNCHANGED=YES` · `INDEPENDENT_REVIEW=PENDING` · fase não avançada.
