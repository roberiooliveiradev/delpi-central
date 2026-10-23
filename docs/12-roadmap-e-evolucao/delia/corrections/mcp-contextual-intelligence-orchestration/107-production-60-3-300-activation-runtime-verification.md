# 107 — Ativação produtiva 60/3/300 + verificação de runtime

**Data:** 2026-10-23. **Task:** `DELIA-C3-PRODUCTION-60-3-300-ACTIVATION-AND-VERIFICATION-01`.
**Decisão:** PO explícita registrada no brief da task — ativar timeout 60s por chamada/estágio LLM, até 3 tentativas por chamada lógica, teto global monotônico 300s; timeouts de MCP/Domain preservados; **R4 aceito como risco residual OPEN/DEFERRED_BY_PO** (não é bypass: é o aceite formal do risco pelo owner competente — a remediação técnica segue postergada, não executada).
**Host:** `srv-api`, checkout `~/projetos/delpi-central`.

## 1. Execução

| Etapa | Resultado |
|---|---|
| Mudança versionada | `infra/docker-compose.yml` defaults: LLM_TIMEOUT 30→60, MODEL_STAGE 30→60, TURN_BUDGET 30→300, LLM_CALL_MAX_ATTEMPTS 1→3, INTERACTION_TOTAL 60→300 — commit `6c5bae9568` → main |
| Override legado | `infra/.env` prod tinha `DELIA_LLM_TIMEOUT_SECONDS=30` (bloqueava o novo default) → atualizado para `60` |
| Deploy | `git pull --ff-only` → `6c5bae9568`; `up-prod-sequential.sh delia-api` (recreate env-only, imagem `eec7be0f913c` mantida — zero rebuild/zero diff de código) |
| `DELIA_MAX_GOVERNED_ATTEMPTS` | **intocado =1** — resume de turno preserva gate e contrato próprios |
| Migrations / serviços externos | zero — somente env do `delia-api` |

## 2. Runtime efetivo (lido no container ativo, não presumido)

| Setting | Antes | Agora |
|---|---|---|
| `DELIA_LLM_TIMEOUT_SECONDS` | 30 | **60** |
| `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` | 30 | **60** |
| `DELIA_TURN_BUDGET_SECONDS` | 30 | **300** |
| `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` | 60 | **300** |
| `DELIA_LLM_CALL_MAX_ATTEMPTS` | 1 | **3** (gate: decisão PO formal, R4 aceito) |
| `DELIA_MAX_GOVERNED_ATTEMPTS` | 1 | **1** (inalterado) |

## 3. Verificação pós-deploy

- `delpi-delia-api`: **Up, healthy**; boot limpo, `env=production`, CRI carregado.
- Smoke (sem credencial, zero chamadas LLM pagas): `GET /health` → 200; `POST /interaction/turns` → 401; `Accept: x-ndjson` → 401. Auth/AuthZ intactos.
- Gateway: zero 502/504 novos; `proxy_read_timeout 86400` por gap já cobre keepalive 15s.
- NDJSON + keepalive: código presente na imagem em execução (deploy do doc 106).
- `EXTERNAL_PAID_LLM_TEST_CALLS=0` — homologação de inferência fica para o PO/manual.

## 4. O que está disponível / bloqueado para o PO

**Disponível agora:** nova política de tempo completa (60s/chamada, 60s/estágio, 300s global, até 3 invocações por chamada lógica), streaming NDJSON, keepalive de transporte, cancelamento, terminal único, painel Contexto, observabilidade por turno/estágio — tudo por trás da mesma AuthZ/AuthN.

**Segue bloqueado (não é bug):** retomada governada do turno (`DELIA_MAX_GOVERNED_ATTEMPTS=1` — gate próprio); remediação técnica R4 (risco aceito, não corrigido); `EDGE_300S_VERIFICATION`/`BROWSER_QA`/`NDJSON_WIRE_PROD` = testes do PO.

## 5. Rollback

`git checkout 54ad4cfb9e` (ou reverter `6c5bae9568`) + `DELIA_LLM_TIMEOUT_SECONDS=30` no `.env` + `up-prod-sequential.sh delia-api`. Zero migrations — trivial.

## DECISION_LOG

`PO_DECISION_RECORDED=YES`; `PRODUCTION_TIME_POLICY_ACTIVE=YES(60/60/300/300)`; `PRODUCTION_RETRY_POLICY_ACTIVE=YES(3/chamada — gate satisfeito por decisão PO)`; `TURN_RESUME=1 (inalterado)`; `R4_RISK_STATUS=OPEN/DEFERRED_BY_PO`; `R4_ACTIVATION_GATE=PO_RISK_ACCEPTANCE (não bypass)`; `RUNTIME_VERIFIED=YES`; `PAID_LLM_CALLS=0`; `ROLLBACK_AVAILABLE=YES`; `READY_FOR_PO_MANUAL_TEST=YES`.
