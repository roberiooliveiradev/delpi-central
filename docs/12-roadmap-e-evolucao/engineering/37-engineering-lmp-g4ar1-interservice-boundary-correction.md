# ENGINEERING.LMP.G4.A.R1 — Interservice Boundary Correction & Auth Evidence

> Documento 37 da série EVA / Portal Engenharia DELPI.
> Execução: SECURITY & ARCHITECTURE REWORK autorizado (bloqueante G4.B).
> Baseline: `c99cd37f913b769b0e78dbbdda7953b8adc782a4` (`origin/main`).

## 1. Causa-raiz

A G4.A (commit `8a8ee4ec`) adicionou `engineering.access` à allowlist
humana do contrato facts na api-delpi para destravar a delegação. Isso
replicou RBAC funcional de Engenharia dentro do bounded context de dados —
violação de fronteira: **a api-delpi valida o consumidor técnico, não
conhece permissões funcionais de outra aplicação**.

A causa estrutural: a Engineering API delegava o Bearer humano para os
facts, então a api-delpi precisava autorizar o usuário — criando a
dependência de RBAC. A correção é usar a **autenticação interserviços
oficial** (já existente e aprovada em produção), na qual a credencial
técnica autoriza a operação e o Bearer humano permanece apenas como ator
delegado para auditoria.

## 2. Mecanismo interno inventariado

| Mecanismo | Contrato | Status |
|---|---|---|
| `X-Delpi-Service-Token` (legado, segredo compartilhado) | `delpi_auth/service_token.py` | **Signal de composição apenas** — mint `principal_type=service`/`is_superadmin`; explicitamente NEGADO (`LEGACY_SERVICE_TOKEN`) em superfícies S2S; nunca promovido a autoridade |
| `X-Delpi-Service-Authorization: Bearer <JWT>` | `delpi_auth/service_contract.py` + `service_token_provider.py` + `service_token_validator.py` | **Mecanismo oficial S2S individual** — Keycloak client-credentials, audience dedicada, allowlist de `azp`, scopes por operação, fail-closed |
| `require_s2s_or_any_permission` | `api-delpi/app/interface/http/s2s_service_access.py` | Guard composto: S2S presente → validação técnica estrita; ausente → permissão humana legada; legado → deny |

**Precedente comprovado em produção**: `controllership-finance-api`
(`api_delpi_gateway.py`) e `supplies-api` consomem a api-delpi exatamente
por esse contrato — `Authorization` = Bearer humano delegado,
`X-Delpi-Service-Authorization` = credencial técnica própria, falha de
token/config → fail closed.

**Limites impostos ao consumidor** (api-delpi, por rota facts):
`required_scopes=("engineering-facts.read",)`,
`allowed_clients=("engineering-api",)`, `S2S_AUDIENCE=api-delpi`.
Client errado → `S2S_CLIENT_DENIED` (403); scope ausente →
`S2S_SCOPE_DENIED` (403); token/audience inválida → `S2S_TOKEN_INVALID`
(401); ausente → `S2S_TOKEN_MISSING` (401); config/JWKS down → 503.

## 3. Correção aplicada — antes/depois

### api-delpi (boundary restaurado)

| Antes (G4.A) | Depois (R1) |
|---|---|
| `ENGINEERING_LMP_FACTS_ACCESS = legado + engineering.access` | Constante removida; guard volta a `ENGINEERING_LMP_ACCESS` (apenas legado) |
| `ENGINEERING_ACCESS`/`ENGINEERING_MANAGE` definidos em `api_delpi_permissions.py` | Removidos — api-delpi não conhece `engineering.*` |
| Humano com só `engineering.access` → facts 200 | Humano com só `engineering.*` → **403** (testado); legado preservado 200 |

### engineering-api (autenticação interserviços oficial)

| Antes (G4.A) | Depois (R1) |
|---|---|
| Facts adapter enviava só Bearer humano | Adapter injeta `X-Delpi-Service-Authorization` via `ClientCredentialsTokenProvider` (mesmo padrão controllership-finance-api) |
| `DownstreamClient` sem credencial técnica | `service_token` opt-in por chamada → header canônico `build_service_authorization`; Bearer humano preservado para auditoria/ator delegado |
| Falha S2S → comportamento ambiguo | `ServiceAuthError` → `DownstreamError(service_auth_unavailable)` → estado `unavailable`, **nenhum HTTP emitido sem credencial** |
| Compose sem envs S2S | `S2S_TOKEN_URL/CLIENT_ID/CLIENT_SECRET/SCOPE/TIMEOUT` mapeadas (`ENG_S2S_*`), secret vazio até provisioning |

## 4. Contrato de confiança resultante

```
Usuário (JWT humano)
  → Engineering API
      delpi_auth valida JWT + Core resolve `engineering.access`  [AuthZ funcional]
      → api-delpi
          Authorization: Bearer <humano>          [ator delegado — auditoria]
          X-Delpi-Service-Authorization: Bearer <client-credentials engineering-api>
          X-Delpi-Caller-App: engineering-api     [telemetria, nunca authz]
          api-delpi valida: assinatura/issuer/audience=api-delpi,
                            azp∈{engineering-api}, scope=engineering-facts.read
```

- Sem bypass: header S2S ausente/malformado/inválido → deny explícita.
- Sem elevação: credencial técnica nunca vira principal humano; o ator
  delegado permanece o usuário.
- Sem replay indiscriminado: token de vida curta (client-credentials) +
  audience dedicada + allowlist por rota.
- `caller_app` continua metadado — nunca autorização.
- Token legado compartilhado nunca é emitido nem aceito nos facts.

## 5. Achado de segurança adicional (documentado)

`env_file: .env` injeta `S2S_CLIENT_ID=supplies-api` + secret em **todo**
container. Sem override, o engineering-api teria se autenticado como
`supplies-api` (identidade cruzada). O bloco `environment:` novo força
`S2S_CLIENT_ID=engineering-api` + `ENG_S2S_CLIENT_SECRET` (vazio até
provisioning) — falha fechado por configuração. Residual transversal para
platform-security-identity-authorization: credenciais S2S ambientes por
`env_file` compartilhado são uma superfície de confusão de identidade em
outros serviços.

## 6. Provisioning pendente (externo, não improvisado)

Checklist exato (script pronto, check-mode verificado → DRIFT correto):
1. Client confidencial Keycloak `engineering-api` com service account.
2. Client scope `engineering-facts.read` como **default** do client.
3. Audience mapper `api-delpi` no client.
4. `S2S_ALLOWED_CLIENTS += engineering-api` na api-delpi.
5. `ENG_S2S_CLIENT_SECRET` (e `ENG_S2S_CLIENT_ID` se divergir) no `.env`.

`infra/scripts/keycloak_s2s_engineering_facts_scope.py` — `--check` por
default; `--apply` exige https e autorização administrativa.

## 7. Matriz de testes (positivos + negativos)

| Cenário | Esperado | Resultado |
|---|---|---|
| `engineering.access` na Core | eng-api autoriza | PASS (routes, real) |
| Sem `engineering.access` | 403 sem chamar downstream | PASS |
| `engineering.manage` isolado | sem acesso operacional | PASS 403 (route + facts) |
| Permissão legada isolada | não autoriza novo endpoint | PASS 403 |
| `engineering.*` nos facts api-delpi | negado | PASS 403 (2 testes) |
| JWT ausente | 401 | PASS real (route + facts) |
| JWT inválido | negado | PASS real 401 |
| Core indisponível | fail-closed | PASS 503/403 |
| Token interno ausente/inválido | api-delpi nega | PASS 401 real + testes |
| Consumidor técnico não autorizado | api-delpi nega | PASS `S2S_CLIENT_DENIED` |
| Scope não permitido | api-delpi nega | PASS `S2S_SCOPE_DENIED` |
| Audience incorreta | nega | PASS `S2S_TOKEN_INVALID` |
| S2S não configurado (eng-api) | fail-closed, sem HTTP | PASS — `unavailable/service_auth_unavailable`, zero chamadas (teste + real) |
| Token legado compartilhado | nunca emitido/aceito | PASS — header ausente em teste; `LEGACY_SERVICE_TOKEN` no guard |
| Header caller autodeclarado | não autoriza | PASS — `caller_app` é telemetria |
| Falha api-delpi | erro honesto | PASS forbidden/unavailable |
| Consumidores antigos | sem regressão | PASS — humano legado facts 200 real; suites verdes |

## 8. Smoke real executado

Ambiente compose local (dev) autorizado:

```
GET /v1/lmps (humano com engineering.access via Core)
  → 200 envelope, data.status="unavailable",
    reason="service_auth_unavailable"
  → Engineering API autorizou via Core, credencial técnica ausente →
    fail-closed ANTES do downstream. Prova o modelo: AuthZ funcional na
    eng-api, autenticação técnica na api-delpi, nenhum RBAC duplicado.
In-container: _s2s_service_token() → ServiceAuthConfigError
    code=S2S_CONFIG_MISSING
GET facts direto (humano legado)        → 200 (preservado)
GET facts sem token                      → 401
GET facts X-Delpi-Service-Authorization: Bearer bad → 401 S2S_TOKEN_INVALID
GET /v1/lmps sem token                   → 401
```

`REAL_INTEGRATION_SMOKE`: o caminho técnico fica **PENDING** de
provisioning S2S (item 6) — o smoke end-to-end com credencial real será
reexecutado quando o client `engineering-api` existir. Nenhum PASS foi
declarado sobre rota permissiva ou mock; o bloqueio é externo e exato.

## 9. Compatibilidade transversal

Preservados e verificados: Dashboard LMPs legado (humano legado → facts
200 real), Dashboard Engenharia, SI, Portal Engenharia MFE, DÉLIA, EVA
MCP, TV Dashboard. Contratos F-LMP-01..04 intocados no wire. Zero novos
consumidores habilitados.

## 10. Ciclos, boundaries e duplicação

- `audit_backend_boundaries`: 0 findings; fluxo eng-api→api-delpi
  unidirecional.
- Sem `engineering.*` em guards da api-delpi (scan + teste de boundary).
- Sem novo mecanismo de auth — `service_contract`,
  `ClientCredentialsTokenProvider`, `ServiceTokenValidator`,
  `require_s2s_or_any_permission` reutilizados do `shared/delpi_auth`
  e do `s2s_service_access` (Abstraction Gate passou).
- Sem secrets no repositório — envs mapeiam `${ENG_S2S_*}` vazios.

## 11. Observabilidade

- `X-Request-Id` propagado; `X-Delpi-Caller-App` para caller-stats.
- Log `lmp_facts_s2s_token_unavailable code=...` (código, nunca token).
- Denials S2S logados por código (`S2S_CLIENT_DENIED` etc.) na api-delpi.
- Estados honestos: `available|empty|unavailable|forbidden|contract_error`.
- Residual menor mantido do doc 36: api-delpi não ecoa request_id em log.

## 12. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `api-delpi/.../api_delpi_permissions.py` | remove `ENGINEERING_*` do G4.A |
| `api-delpi/.../lmp_facts_router.py` | guard volta a `ENGINEERING_LMP_ACCESS` |
| `api-delpi/tests/test_lmp_facts_contracts.py` | -3 testes do acoplamento; +2 negativos boundary + guarda de constante; S2S negatives mantidos |
| `engineering-api/.../downstream_client.py` | `service_token` opt-in → header S2S canônico |
| `engineering-api/.../api_delpi_facts.py` | credencial S2S injetada; ServiceAuthError→unavailable |
| `engineering-api/.../lmp_composer.py` | provider lazy process-wide + reset hook |
| `engineering-api/tests/test_lmp_facts_adapter.py` | novo — 6 testes S2S/boundary |
| `infra/docker-compose.yml` + `.dev.yml` | envs `S2S_*` engineering-api |
| este documento | evidência R1 |

## 13. Testes no SHA final

```
engineering-api: 293 passed (287 + 6 adapter S2S)
api-delpi LMP:   182 passed (facts 29/29 após ajuste de escopo)
audits: phase3, platform_guardrails, openapi_contracts,
        fastapi_authz, backend_boundaries — 0 findings
secrets scan: limpo
```

## 14. Riscos, residuais e gate seguinte

1. Provisioning S2S (§6) — externo; sem ele `/v1/lmps*` permanece
   `unavailable` por desenho. Script pronto.
2. Credenciais S2S ambientes via `env_file` compartilhado — residual
   transversal (§5) para platform-security.
3. Smoke end-to-end com credencial real — PENDING do item 1.
4. Shadow real 200×12 + benchmark — G4.B, após item 1.

**Veredicto proposto: `ACCEPT_WITH_RESIDUAL`** — boundary corrigido e
provado por teste e runtime; residuais exclusivamente externos
(provisioning S2S) e transversais já rastreados.
