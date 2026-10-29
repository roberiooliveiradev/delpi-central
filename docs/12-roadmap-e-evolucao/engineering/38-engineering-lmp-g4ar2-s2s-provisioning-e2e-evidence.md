# ENGINEERING.LMP.G4.A.R2 — S2S Provisioning & E2E Evidence

**Status:** CONCLUÍDO (dev local) — integração S2S real comprovada ponta a ponta.
**Missão:** `ENGINEERING.LMP.G4.A.R2` — S2S Provisioning & End-to-End Authentication.
**Baseline inicial:** `45118d642506e05c0e4c6fa679b3ffdcf2dbc37e` (reancorado; HEAD final `7a75a7d3` + commit R2).
**Referências:** docs 32–37; contrato S2S oficial `shared/delpi_auth`; precedente `controllership-finance-api`.

---

## 1. Objetivo

Provisionar a identidade técnica `engineering-api` no Keycloak e comprovar a cadeia real:

```
Usuário (engineering.access, autorizado pela Core na Engineering API)
  → Engineering API (BFF)
  → X-Delpi-Service-Authorization (client_credentials: engineering-api,
     scope=engineering-facts.read, aud=api-delpi)
  → API DELPI Facts (F-LMP-01..04)
  → TOTVS
```

Autorização funcional permanece na Engineering API/Core; API DELPI valida apenas o contrato técnico.

## 2. Estado inicial (PREPARE)

Provisioner `infra/scripts/keycloak_s2s_engineering_facts_scope.py` executado em `--check` sobre o realm real `delpi`:

| Recurso | Estado inicial |
|---|---|
| Client `engineering-api` | **inexistente** |
| Client scope `engineering-facts.read` | **inexistente** |
| Audience mapper `api-delpi` | **inexistente** |
| `S2S_ALLOWED_CLIENTS` (api-delpi) | `supplies-api` |
| `ENG_S2S_*` em `infra/.env` | ausente (secret len=0 → fail-closed) |

Plano PREPARE (atual → desejado → risco → rollback → owner) aprovado explicitamente pelo owner para **ambiente de desenvolvimento local** antes de qualquer `--apply`.

## 3. Autorização operacional

- Aprovação explícita do owner para ACT em **dev local** (realm `delpi`, Keycloak local HTTP).
- `--apply` exige HTTPS por padrão; liberado para HTTP **somente** com `KC_ALLOW_HTTP_APPLY=1` (opt-in explícito, documentado no script).
- Nenhuma alteração em produção/homologação; nenhum outro client tocado.

## 4. Provisionamento executado (ACT)

`keycloak_s2s_engineering_facts_scope.py --apply` (com extensão implementada nesta missão — o script original só fazia check; agora cria client/scope/mapper e persiste env sem logar secret):

```
client engineering-api — criado (confidencial, SA, sem grants interativos)
client engineering-api — service account habilitada
client scope engineering-facts.read — criado
default scope engineering-facts.read — atribuído
audience mapper api-delpi — criado
infra/.env — ENG_S2S_CLIENT_ID/SECRET gravados; engineering-api em S2S_ALLOWED_CLIENTS
```

Verificação pós-apply (`--check`): **zero DRIFT** — client, scope, default assignment e audience mapper todos `OK`.

### Contrato efetivo (após ACT)

| Campo | Valor |
|---|---|
| Realm | `delpi` |
| Client técnico | `engineering-api` (confidencial, service account) |
| Grant | `client_credentials` apenas |
| Scope | `engineering-facts.read` (default scope do client) |
| Audience | `api-delpi` (audience mapper dedicado) |
| Allowlist api-delpi | `supplies-api,engineering-api` |
| Header | `X-Delpi-Service-Authorization` |
| Secret storage | `infra/.env` (`ENG_S2S_CLIENT_ID/SECRET`, gitignored; nunca logado/commitado) |

### Correção de issuer (runtime)

Token real mintado tinha `iss=http://localhost/auth/realms/delpi` (Keycloak atrás do gateway), mas `S2S_TOKEN_URL` apontava o endpoint interno direto — primeira chamada BFF→facts retornou 401. Correção: `ENG_S2S_TOKEN_URL=http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token` em `infra/.env`; compose passa a aceitar `ENG_S2S_TOKEN_URL` com fallback para `S2S_TOKEN_URL` (mesma URL em prod; em dev precisa sair pelo gateway para o `iss` casar com `KEYCLOAK_ISSUER`).

Containers recriados: **somente** `delpi-engineering-api` e `delpi-api-delpi`.

## 5. Evidência de runtime (dev local)

### Positivos — E2E real

| Fluxo | Resultado |
|---|---|
| `GET /v1/lmps` (usuário com `engineering.access`) | 200 — `available`, total=245 |
| `GET /v1/lmps/summary` | 200 — `available`, 217 LMPs, 97.7%, 2.76d, PI `available` |
| F-LMP-01 `GET /engineering/lmps/facts` | 200 (BFF interno + gateway humano+S2S) |
| F-LMP-02 `GET /facts/003696` | 200 |
| F-LMP-03 `GET /facts/003696/history/events` + `/flow` | 200 |
| F-LMP-04 `POST /facts/pi-counts` | 200 |

Logs api-delpi: `operation_id=list_lmp_facts` / `get_lmp_pi_counts` → 200. Logs eng-api: `operation_id=list_lmps` / `get_lmp_summary` → 200 com `request_id` correlacionado.

### Negativos — runtime real

| Cenário | Resultado |
|---|---|
| Sem `Authorization` nos facts | 401 |
| S2S válido **sem** Bearer humano | 401 (ator humano exigido — service-only não basta) |
| Human + `X-Delpi-Service-Authorization` inválido | 401 `S2S_TOKEN_INVALID` |
| Human + token S2S de **outro serviço** (supplies-api, JWT válido real) | 403 `S2S_CLIENT_DENIED` |
| `/v1/lmps` sem token | 401 |
| `engineering.access` sozinho nos facts (sem S2S) | 401 (rota exige credencial técnica — boundary test) |

Unit tests cobrem adicionalmente: `engineering.manage`-only → 403; permissão legada → 403; Core indisponível → fail-closed; `caller_app` não autoriza; scope ausente → `S2S_SCOPE_DENIED`; zero chamada downstream quando AuthZ funcional falha.

## 6. Testes (SHA final)

| Suíte | Resultado |
|---|---|
| `engineering-api` completa (venv) | **293 passed** |
| `api-delpi` `-k lmp` | **182 passed** (6120 deselected) |
| audit_architecture_phase3 (pytest) | 37 passed + 4 subtests |
| audit_platform_guardrails (pytest) | incluído acima |
| audit_openapi_contracts | 0 findings |
| audit_fastapi_authz | 0 findings |
| audit_backend_boundaries | 0 findings |

Residual search: zero `engineering.access|engineering.manage|ENGINEERING_*` em `api-delpi/app/`; zero secrets no diff escopado.

## 7. Configuração alterada (diff)

| Arquivo | Mudança |
|---|---|
| `infra/scripts/keycloak_s2s_engineering_facts_scope.py` | modo `--apply` completo (cria client/scope/mapper, persiste `ENG_S2S_*` em `.env`, nunca imprime secret, HTTPS obrigatório salvo opt-in dev `KC_ALLOW_HTTP_APPLY=1`) |
| `infra/docker-compose.yml` | `S2S_TOKEN_URL: ${ENG_S2S_TOKEN_URL:-${S2S_TOKEN_URL}}` (eng-api) |
| `infra/docker-compose.dev.yml` | idem, com comentário sobre `iss` via gateway |
| `infra/.env` | `ENG_S2S_CLIENT_ID`, `ENG_S2S_CLIENT_SECRET`, `ENG_S2S_TOKEN_URL`, allowlist ampliada — **gitignored** |

## 8. Isolamento de credenciais

- Secret exclusivo do client `engineering-api`; não há reutilização do segredo `supplies-api`.
- Compose eng-api mapeia `ENG_S2S_*` → `S2S_*` (R1) impedindo herança acidental das variáveis genéricas do `.env` compartilhado.
- **Residual transversal** (doc 37 §5, owner Platform Security): outros serviços continuam herdando credenciais S2S via `env_file` compartilhado — fora de escopo desta missão.

## 9. Rollback

1. Deletar client `engineering-api` no Keycloak (admin API/console).
2. Reverter `infra/.env` (remover `ENG_S2S_*`, allowlist volta a `supplies-api`).
3. Recriar os 2 containers → facts voltam a `unavailable` fail-closed, sem impacto em consumidores legados.

## 10. Riscos e residuais

- **Risco:** allowlist ampliada para `engineering-api` — mitigado por scope `engineering-facts.read` restrito às rotas facts e client exclusivo.
- **Residual:** nginx do gateway mantém DNS cacheado de upstreams (`api-delpi`) — após recreate do container, requests gateway→api-delpi falhavam 404/502 até `nginx -s reload`. Recorrente nesta missão; recomenda-se `resolver` no nginx ou restart pós-recreate (owner Platform Runtime).
- **Residual:** `pi-counts` teve timeout intermitente na primeira chamada pós-restart (retry → `available`) — comportamento de cold start TOTVS, observável e honesto no envelope.
- **Pendente externo:** provisioning em staging/prod exige ACT separado com HTTPS e owner do ambiente.
- **Não iniciado:** G4.B (shadow real, benchmark, E-LMP-02/04/05).

## 11. Compatibilidade

Dashboard LMPs legado, Dashboard Engenharia, Strategic Indicators, DÉLIA, EVA MCP, TV Dashboard: intocados. Allowlist facts é aditiva; nenhum contrato legado alterado; nenhuma permissão `engineering.*` em guards da API DELPI; fluxo unidirecional eng-api→api-delpi (zero dependência circular — audit 0 findings).

## 12. Veredicto proposto

**`ACCEPT`** — todos os critérios R2-01..16 com evidência objetiva em ambiente real de desenvolvimento: client técnico correto, scope/audience restritos, segredo isolado, API DELPI protegida, AuthZ funcional na Core/eng-api, smoke E2E positivo e negativo, legado preservado. G4.B **não** iniciado — retorna à Coordenação.
