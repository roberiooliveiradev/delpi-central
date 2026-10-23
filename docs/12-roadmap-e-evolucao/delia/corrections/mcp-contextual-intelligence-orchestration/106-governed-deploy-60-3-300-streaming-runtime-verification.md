# 106 — Deploy governado + verificação de runtime (produção)

**Data:** 2026-10-23. **Task:** `DELIA-C3-DEPLOY-60-3-300-STREAMING-CONTEXT-AND-RUNTIME-VERIFICATION-01`.
**Escopo autorizado:** `delia-api` + `delia` (MFE) — somente. **Host:** `srv-api` (`operador@192.168.1.237`), checkout `~/projetos/delpi-central`.
**Veredicto:** `DEPLOY_SUCCESS=YES (escopo delia-api + delia)`; `POSTCONDITION_VERIFIED=YES`; `RELEASE_DO_REGIME_60_3_300=NOT_AUTHORIZED` (flags produtivas congeladas).

## 1. Baseline

| Item | Valor |
|---|---|
| Prod checkout antes | `54ad4cfb9e` (limpo) |
| Prod checkout depois | `a77b6b763` (`git pull --ff-only`) |
| Avaliado pela revisão | `24d230eb15` + parecer `54989bda6f` |
| Drift no escopo DÉLIA | **zero** — `54989bda6f..a77b6b763` não toca `delia-api`, `plugins/delia`, compose, gateway |
| Migrations no range | **zero** |
| Imagens rollback | api `b05a0f35b52c` → `eec7be0f913c`; MFE `d327a8bcba3c` → `820d01e5ab97` (antigas preservadas no host) |
| Procedimento | `up-prod-sequential.sh --build delia-api`, idem `delia` (canônico, local-first) |

## 2. Configuração efetiva pós-deploy (verificada no container, não presumida)

| Setting | Valor efetivo | Estado |
|---|---|---|
| `DELIA_LLM_TIMEOUT_SECONDS` | 30 | congelado |
| `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` | 30 | congelado |
| `DELIA_TURN_BUDGET_SECONDS` | 30 | congelado |
| `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` | 60 | congelado |
| `DELIA_LLM_CALL_MAX_ATTEMPTS` | **1** | OFF explícito (novo pin) |
| `DELIA_MAX_GOVERNED_ATTEMPTS` | **1** | resume OFF |
| `DELIA_LLM_PROVIDER` | openai_compatible (OpenRouter, kimi-k3) | inalterado — provider externo autorizado em prod |

`infra/.env` prod sobrescreve apenas `DELIA_LLM_TIMEOUT_SECONDS=30`. O regime 60/3/300 **existe no código mas NÃO está ativo** em produção — exigência cumprida: sem gate aprovado, sem ativação.

## 3. Verificação de runtime

- `delpi-delia-api`: imagem `eec7be0f913c`, `env=production`, **healthy**; gunicorn limpo; marcadores de código novos presentes (`keepalive` no routes, `llm_call_max_attempts` em settings); zero ERROR/exception nos logs pós-deploy.
- `delpi-delia` (MFE): imagem `820d01e5ab97`, `Up`; `remoteEntry.js` novo servido pelo gateway em `/apps/delia/assets/remoteEntry.js` — md5 `b34a7cb2…` (imagem antiga) → `7d742045…` (running) — **o Portal recebe o build novo**; chunks federados com hash novo (`__federation_expose_App-DC-frWC-.js`).
- Gateway prod `/apps/delia-api/`: `proxy_read_timeout 86400` (por gap; ainda mais permissivo que o dev 120s — keepalive 15s satisfeito); `X-Accel-Buffering: no` segue no contrato upstream.
- Smoke gateway (sem credencial, zero chamadas LLM): `GET /health` → **200**; `POST /interaction/turns` → **401**; com `Accept: application/x-ndjson` → **401** (rota alcançável, auth enforced pre-stream). Zero 502/504 no gateway pós-deploy.

## 4. Não executado (honesto)

- `AUTHENTICATED_TURN=TEST_NOT_RUN` — sem identidade de teste prod autorizada; chamada real consumiria OpenRouter pago. Reservado ao PO.
- `NDJSON_WIRE_PROD=TEST_NOT_RUN` — mesma razão; evidência local do doc 105 permanece a referência.
- `EDGE_300S_VERIFICATION=TEST_NOT_RUN` — sessão de 5 min via Cloudflare não exercida; não declarar compatibilidade.
- `BROWSER_QA=TEST_NOT_RUN` — testes do painel Contexto/seleção/Activity-Evidence-Outcome ficam para a sessão manual do PO.
- `PRODUCTION_PAID_TEST_CALLS=0`; `EXTERNAL_LLM_TEST_CALLS=0`.

## 5. Postconditions

Backend atualizado e saudável ✓; MFE novo servido pelo Portal ✓ (remoteEntry md5 comprovado); SHA efetivo identificado (`a77b6b763` checkout; imagens acima); contratos compatíveis (keepalive é forward-compatible, parser ignora); **retry produtivo NÃO ativado** (env=1 provado); streaming NDJSON compatível (código deployado + gateway generoso); sem degradação (zero erros); rollback disponível (imagens antigas no host + `git checkout 54ad4cfb9e` + `up-prod-sequential.sh --build`).

## 6. Rollback

Se necessário: `git checkout 54ad4cfb9e` no srv-api + `./infra/scripts/up-prod-sequential.sh --build delia-api delia` — ou retag das imagens `b05a0f35b52c`/`d327a8bcba3c` e `up -d`. Nenhuma migration, nenhuma mudança de schema: rollback trivial.

## DECISION_LOG

`DEPLOY_SUCCESS=YES`; `POSTCONDITION_VERIFIED=YES`; `PRODUCTION_RETRY=OFF_PROVEN_AT_RUNTIME`; `REGIME_60_3_300=CODE_DEPLOYED_NOT_ACTIVATED`; `EDGE_300S_VERIFICATION=TEST_NOT_RUN`; `BROWSER_QA=TEST_NOT_RUN`; `PAID_LLM_CALLS=0`; `REVOCATION_RISK=OPEN/DEFERRED_BY_PO`; `ROLLBACK_EXECUTED=NO`; `PHASE_ADVANCE=NO`.
