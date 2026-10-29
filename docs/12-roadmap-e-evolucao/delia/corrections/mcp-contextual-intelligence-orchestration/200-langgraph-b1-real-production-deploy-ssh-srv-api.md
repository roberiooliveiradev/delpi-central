# 200 — LangGraph B1 real production deployment (SSH, srv-api)

TASK_ID: `DELIA-C3-LANGGRAPH-B1-REAL-PRODUCTION-DEPLOY-01`
TYPE: Real production host deployment via approved SSH operator access.
AUTHORIZATION: Explicit product-owner authorization for production
deployment of the already-approved Task-07 implementation.
EXECUTED_ON: `srv-api` (operador@192.168.1.237 — canonical target per
AGENTS.md), repo `~/projetos/delpi-central`, prod compose
`docker-compose.yml --env-file infra/.env`, gunicorn runtime.

## 1. Canonical reanchor

- Local HEAD == origin/main == `78e7b4d7ef` (concurrent engineering LMP
  commits atop `df2df3c9c4`; zero delia-api drift).
- Server pre-pull SHA: `1f34403767` (predates Task 07 lineage).
- `git merge-base --is-ancestor 6fc0d7cb98 HEAD` → confirmed: the
  release artifact includes the Task-07 engine-selection implementation
  and doc-199 evidence.
- Working tree on server: clean before pull (no pending uncommitted
  production changes).

## 2. Production host verification

- `hostname` = `srv-api`, user `operador`, SSH key auth — matches the
  canonical AGENTS.md operator target. Not inferred from container
  names.
- Live stack: 92 `delpi-*` containers; `delpi-delia-api` was Up 8h
  healthy on the pre-deploy image before this task touched it.

## 3. Pre-deploy state (captured for rollback)

| item | value |
|---|---|
| previous code SHA | `1f34403767` |
| previous image | `infra-delia-api` `sha256:9947eac96f471f55b9ea4de5c67675b962261ded9d07c047e8f4e02de3fad1c8` (retained on host) |
| engine selector | absent (predates feature) |
| model | `moonshotai/kimi-k3` via `https://openrouter.ai/api/v1` (`DELIA_ENV=production`) |

## 4. Deployment sequence (canonical runbook)

```text
git pull --ff-only                    → 1f34403767 → 78e7b4d7ef
DELIA_ORCHESTRATION_ENGINE=langgraph  → appended to infra/.env (line 378)
./infra/scripts/up-prod-sequential.sh --build delia-api
```

- Only `delia-api` rebuilt/recreated. All other services untouched —
  verified by post-deploy container ages (api-delpi Up 8h, core,
  keycloak, portal, gateway unchanged).
- No database reset, no migrations, no domain-data writes, no
  Keycloak/Core/Portal changes, no MCP provider changes.
- `DEPLOY_STARTED_AT`≈23:10 -0300 · `DEPLOY_COMPLETED_AT`≈23:11 -0300.

## 5. Post-deploy verification (D1–D10)

| gate | evidence |
|---|---|
| D1 process | gunicorn worker booted, `env=production` |
| D2 health | `State.Health=healthy`; `/health` 200 |
| D3 engine | startup log `delia_orchestration_engine selected=langgraph surface=configured` + env `DELIA_ORCHESTRATION_ENGINE=langgraph` |
| D4 deps | `pip list` in deployed image: langgraph 1.2.16, langgraph-checkpoint 4.3.1, langgraph-prebuilt 1.1.1, langgraph-sdk 0.4.10, pydantic 2.14.1 |
| D5 model | `DELIA_LLM_MODEL=moonshotai/kimi-k3`, OpenRouter base URL — production model preserved; local Ollama override NOT carried |
| D6 contracts | authenticated turns return the existing response shape (content, epistemic_class, grounding_status, provenance, observability) |
| D7 security | admission stage ran on both turns; no AuthZ/policy/PREPARE/ACT/candidate-binding path touched; no identity mutation performed |
| D8 observability | `recovery_opportunity` projection + full per-stage `calls[]` + provenance present in live responses |
| D9 errors | 0 critical/traceback/unhandled entries in post-deploy logs |
| D10 single engine | `governed_attempts=1` per turn; no dual execution |

Deployed image digest:
`sha256:8931066ee0e7a49728c578c5da8826b9eafbb4e876d62c0363cb23fbf90f27c6`
(`infra-delia-api:latest`, code `78e7b4d7ef`).

## 6. Bounded authenticated production smoke (≤2 READ turns)

Identity: `user` (product-owner-provided credential, password grant via
gateway, `aud=[delpi-central, account]`). No Keycloak admin API, no
password reset, no RBAC mutation — the previously flagged drift was
NOT repeated.

| # | question | HTTP | outcome | grounding | calls | in/out tok | latency | stages reach |
|---|---|---|---|---|---|---|---|---|
| S1 | `Qual e a descricao do produto de codigo 10080092?` | 200 | OBSERVATION | **GROUNDED** | 7 | 10429/1676 | 32.0s | admission→group→capability→native_assessment→arguments→candidate_arguments→goal_evidence_relevance |
| S2 | `Me de dois exemplos de terminal bala` | 200 | OBSERVATION | **GROUNDED** | 7 | 10446/3331 | 40.1s | admission→group→capability→native_assessment→arguments→select_candidate→candidate_arguments |

- S1: real owner record returned — `10080092 TERM. BALA 0,50-2,27MM2
  ESTANHADO CARRETEL S/ISOLACAO` (category group 1008) via DAVI
  `search_products`/`execute_delpi_information` over MCP; provenance
  complete (correlation_id `54bad670-…`, source api-delpi).
- S2: `read_governed_technical_knowledge` owner call executed with
  complete provenance; owner returned an empty collection — honest
  typed outcome, no fabrication (consistent with the known
  lexical-search residual recorded in doc 172).
- `recovery_opportunity` counters all zero on both turns — the live
  reuse window did not materialize (consistent with Task 05/06
  findings; counters now flowing on real production turns).
- Token source: provider-reported usage in `observability.tokens`.
- BUSINESS_OUTCOME=VERIFIED for S1 (known authoritative record, exact
  match); S2 VERIFIED as truthful fail-closed-empty, not a
  fabrication.

## 7. Rollback readiness

- `DELIA_ORCHESTRATION_ENGINE=delia` in `infra/.env` + recreate =
  Engine A composition (selector tested locally and in-container).
- Previous image `sha256:9947eac9…` retained on host — revert = env +
  retag/rebuild via the same script.
- No schema migrations involved; no material action is replayed by
  rollback (configuration restart only).
- Healthy service was not interrupted to re-test rollback (already
  proven locally in Task 07).

## 8. Residuals / drift

- EXECUTION_DRIFT=none on production host. `infra/.env` received one
  additive config key (canonical per-host config surface; not
  versioned code) — disclosed.
- AUTH deviation: product-owner provided `user` credential for the
  smoke instead of `devin-smoke-r4` (whose stored credential was
  rotated); no identity writes performed.
- UNRESOLVED: production eligibility frequency of the reuse path —
  counters now emit on real turns; cross-turn aggregation remains a
  separately authorized step.
- PRODUCTION_VERDICT=PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED on
  srv-api; B1 selected, Engine A rollback retained.
