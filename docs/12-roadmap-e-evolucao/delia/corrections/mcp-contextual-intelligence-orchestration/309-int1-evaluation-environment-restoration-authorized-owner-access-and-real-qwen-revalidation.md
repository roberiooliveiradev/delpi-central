# 309 — INT-1 Evaluation Environment Restoration, Authorized Owner Access and Real Qwen Revalidation

**TASK_ID:** `DELIA-C3-T2-INT1-EVAL-ENV-AUTHZ-RESTORATION-AND-REAL-QWEN-REVALIDATION-01`  
**Data:** 2026-11-12  
**EXTERNAL_LLM:** AUTHORIZED — EXECUTED (G1+P1+M1 ×1)  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**FULL_BATTERY:** NOT_RUN  
**AGENT_CHANGED:** NO  

---

## 1. Reancoragem

| Item | Value |
|---|---|
| REFERENCE_HEAD (task) | `def694b899…` |
| WORK HEAD (início) | `1a82ca9863…` → avançou para `c5bd6bc708…` (inclui remoção `.env.local`) |
| PHASE_FROM_16 | C3/T2 INT-1 BLOCKED |
| Instruction | `generalist-semantic-v2-1-object-continuity` / fp `4ebd5260b6cf9ba9` MATCH |
| Model / profile | `qwen/qwen3-14b` / `openrouter_qwen` |
| Config fp | `e4a5b706a3b3156b` |
| Pydantic AI | `2.50.0` |
| Eval ID | `or-qwen14b-be922c439302` |
| Isolation | `delpi-delia-eval-int1-or-qwen14b`; `PROD_CONTAINER_UNTOUCHED=YES` |

---

## 2. Padrão de `.env` confirmado

| Ambiente | Fonte |
|---|---|
| Templates | `infra/.env.dev.example`, `infra/.env.prod.example` |
| Desenvolvimento | `infra/.env` (gitignored) |
| Produção | `infra/.env` no host de prod (não tocado) |

`.env.local`: ABSENT. Remoção do override legado já em `c5bd6bc708` (`get-dev-token.sh`, `keycloak-dev-bootstrap.sh`). Teste pontual `infra/scripts/tests/test_get_dev_token_env_source.sh` PASS.

---

## 3. Matriz de fontes (avaliação)

| Componente | Fonte atual | Fonte esperada | Divergência |
|---|---|---|---|
| Harness INT-1 | `infra/.env` seletivo | `infra/.env` | OK |
| Token DEV | `DEV_PORTAL_*` em `.env` | idem | OK (sem `.env.local`) |
| OpenRouter (eval) | `DELIA_LLM_API_KEY` se `sk-or-`; senão `KIMI_API_KEY` (mesma conta OpenRouter) | chave OpenRouter autorizada | Host `.env` mantém `DELIA_LLM_API_KEY` local + `DELIA_LLM_BASE_URL=ollama`; harness isola OpenRouter |
| Keycloak / Core / DAVI / TÉO | compose + `.env` | idem | OK após bootstrap + cache Core |

---

## 4. Identidade

| Campo | Evidência |
|---|---|
| HISTORICAL_EVAL_SUBJECT | `rober` / `rober@dev.local` — Core `is_superadmin=true` + `api-delpi.access` / `transformometro.access` / `delia.access` (baseline 303–307) |
| CURRENT_EVAL_SUBJECT | `ti_delpi` / `ti_delpi@delpi.local` — username canônico `.env.dev.example` pós-reorg |
| SUBJECT_EQUIVALENCE | NÃO idêntico; AUTHZ de owner **restaurada** no Core para códigos documentados do portal DEV |
| SUBJECT_ID_HASH | `4903c6464e2cd62d` |
| TOKEN | VALID; issuer `http://localhost/auth/realms/delpi`; aud inclui `delpi-central`,`delia-api`; client `delpi-central`; realm `delpi` |

**Causa 308:** sujeito `ti_delpi` existia no Keycloak/Core sem overrides de permissão; cache RBAC do Core mantinha `permissions=[]` → DAVI `AUTHORIZATION_DENIED`.

**Correção legítima (local):** grants Core `user_permissions` (`granted=true`) para `api-delpi.access`, `transformometro.access`, `delia.access`, `tv-dashboard.read`; restart `delpi-core-api` para invalidar cache. Não é bypass de owner nem identidade privilegiada improvisada — alinha o usuário DEV canônico aos códigos que o portal DEV precisa para READ owners. Estado em DB local (não commitado).

---

## 5. Preflight

| Check | Result |
|---|---|
| ENV_SOURCE_VERIFIED | YES |
| SUBJECT_VERIFIED | YES (`ti_delpi`) |
| TOKEN_VALID | YES |
| CORE_AUTHZ | YES (perms efetivas listadas em `/me`) |
| DAVI_READ_PREFLIGHT | PASS — HTTP 200, root `90260921`, BOM depth-1, `success=true` |
| TEO | Core `transformometro.access` presente; MCP resource exige exchange (401 sem audience) — esperado; eval usa exchange DÉLIA |
| MCP_CONNECTIONS | DAVI/TEO/VISTA habilitados no harness |
| MODEL_PROFILE | openrouter_qwen / qwen3-14b |

---

## 6. Avaliação real Qwen (`or-qwen14b-be922c439302`)

| Cenário | First tool | AUTHZ | Recovery | Objective |
|---|---|---|---|---|
| G1 | `teo.read` decomposition_tree | TEO owner error interno (não AUTHZ_DENIED) | → `davi.get_context` → `davi.read` gps SUCCESS | **SATISFIED** (GROUNDED, root+componente+qty) |
| P1 | `davi.get_context` | OK | schema → gps SUCCESS | **SATISFIED** |
| M1 | `davi.get_context` | OK | → gps SUCCESS | **SATISFIED** |

Métricas: MODEL_REQUESTS=3; TOOL_CALLS(MCP)=8; TOKEN_USAGE=UNAVAILABLE; COST=UNAVAILABLE; LATENCY≈170198 ms.

---

## 7. Comparação 307 / 308 / 309

| Cenário | Doc. 307 | Doc. 308 | Doc. 309 |
|---|---|---|---|
| G1 first | TÉO | TÉO | TÉO |
| G1 objetivo | SATISFIED | NOT_SATISFIED / AUTHZ | **SATISFIED** |
| P1 first | DAVI | DAVI | DAVI |
| P1 objetivo | SATISFIED | NOT_SATISFIED / AUTHZ | **SATISFIED** |
| M1 first | DAVI/TÉO | TÉO | **DAVI** |
| M1 objetivo | NOT_SATISFIED | NOT_SATISFIED | **SATISFIED** |

| Equivalência | Status |
|---|---|
| ENVIRONMENT | YES (isolado OpenRouter; `.env` exclusivo) |
| IDENTITY | PARCIAL (`ti_delpi` ≠ `rober`; AUTHZ owner alinhada) |
| AUTHZ | YES após restauração Core |
| MODEL_CONFIG | YES (`e4a5b706a3b3156b`) |
| INSTRUCTION | 309 = v2-1; 307 = v2 |
| TOOLSET | YES (B3 15 tools) |

Sob condições comparáveis ao 307, v2-1: P1 estável; M1 melhora first-tool (DAVI) + satisfação; G1 ainda TEO-first mas recovery + satisfação OK.

---

## 8. Residuais

| ID | Status |
|---|---|
| INT1-EVAL-SUBJECT-AUTHZ | REMEDIATED_LOCAL (Core grants + cache clear) — persistência operacional do seed DEV a documentar |
| INT1-G1-TEO-FIRST-ATTRACTOR | OPEN |
| INT1-COVERAGE-UNKNOWN-FINALIZE | OPEN |
| INT1-OPENROUTER-KEY-HOST-DRIFT | OPEN — host `.env` LLM local vs profile openrouter; harness usa `KIMI_API_KEY` |
| INT1-TEO-MCP-DIRECT-401 | EXPECTED sem token exchange |
| INT1-STAGE | BLOCKED (review) |
| INT1-CLOSED | NO |

---

## 9. Próximo passo

`COORDINATION_INT1_AUTHORIZED_REAL_EVAL_INDEPENDENT_REVIEW`  
Opcional: seed/documentação para permissões do `DEV_PORTAL_USERNAME` canônico após reorg (evitar grants manuais).
