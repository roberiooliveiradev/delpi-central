# 209 — Controlled production deploy of orchestration instruction v28 (srv-api)

Task: `DELIA-C3-ORCHESTRATION-V28-CONTROLLED-PRODUCTION-DEPLOY-01`
Date: 2026-10-29 · Executor: Cursor/Devin · Host: `srv-api` (`operador@192.168.1.237`)

## 1. Reanchor

- `HEAD = origin/main = 5144a3258333d079664380a4111f33998b77e1c9` (matches LAST_OBSERVED_MAIN).
- `f2da73f121` (Task 16 consolidation) and `71d11ef468` (Task 17, v28) confirmed ancestors of main.
- Working tree carried unrelated controllership-finance/CLARA modifications from a concurrent workstream — preserved, never staged.
- Production repo `/home/operador/projetos/delpi-central` already at `5144a32583`, clean status — git side pre-synced by a prior workstream pull.

## 2. Release diff (isolated)

Between the prod delia-api image bake SHA (`e9c405cee9`, doc-207 deploy) and HEAD, the **only** commits touching `delia-api/` are `f2da73f121` and `71d11ef468`. The image build context copies `delia-api/` + `shared/`; `shared/delpi_auth` (the only shared package delia-api imports) had zero non-Task-17 changes — `delpi_character_profiles`/avatar additions in `shared/` are inert bytes for this service. No `requirements.txt` drift.

Release scope therefore = `delia-api` image rebuild only.

## 3. Production inventory / drift classification

| Service | Prod state before deploy | Classification |
|---|---|---|
| `delia-api` | image `c87dc40a7bb1` (built 12:09 UTC), runtime **instruction v26** | `INSTRUCTION_DRIFT` + `CODE_DRIFT` (loader version list) |
| `api-delpi` | image rebuilt 19:13 UTC by concurrent workstream; enriched DAVI description verified live at `server.py:235` | `NO_DRIFT` (T16 content already active) |
| `transformometro-api` | image rebuilt 19:14 UTC; enriched TÉO timeline description verified live (`server.py:615`, `capability_descriptors.py:625`) | `NO_DRIFT` |
| All others | — | `NO_DRIFT` / out of scope |

Runtime evidence was gathered inside the running containers (loaded JSON + source grep), not from Git history or image timestamps.

## 4. Gates / rollback preparation

- `CANONICAL_REANCHOR=PASS`, `RELEASE_DIFF=PASS` (single-service scope), `OWNER_CONTRACTS=PASS` (no contract change in the release), `INSTRUCTION_RESOURCE=PASS` (v28 accepted by loader, 4 canonical statuses, fail-closed, `owner_vocabulary_discovery` resolver class — all proven by Task 17 tests), `LANGGRAPH_B1_CONFORMANCE=PASS`, `ENGINE_A_COMPATIBILITY=PASS` (rollback path = env selector, untouched), `MODEL_CONTRACT=PASS` (`DELIA_LLM_MODEL=moonshotai/kimi-k3`, OpenRouter base URL, all sampling/timeout vars unchanged — env not modified by the deploy), `SECURITY=PASS`, `PREPARE_ACT=PASS` (no ACT surface touched).
- Rollback prepared before mutation: prior image `c87dc40a7bb1` (v26 baked) tagged `infra-delia-api:rollback-v26-task18`; second prior image `e0ef09851204` also retained on host. Rollback = retag `infra-delia-api` to rollback image + `up -d --no-deps`, or rebuild at `e9c405cee9` via the same runbook. No DB migration, no Keycloak change, no secret rotation involved.

## 5. Deploy

- Method: SSH `operador@192.168.1.237`, official runbook `./infra/scripts/up-prod-sequential.sh --fase api --build delia-api` — scoped to the single drifting service; no `--pull` needed (repo already at HEAD); no other service rebuilt or recreated by this run.
- Result: new image `sha256:c043368e862312ee25b80b21fb7d0f1fb984c4b2d0517c76aa2ee723c136cff9` (built 19:16:45 UTC), container recreated, `healthy` in <60s.

## 6. Runtime verification (inside the running container)

| Check | Evidence |
|---|---|
| `RESOURCE_VERSION` | **28** |
| `native_assessment` fingerprint | `sha256:a7696bb6344ccc24` — **byte-identical to HEAD** resource |
| `owner_vocabulary_discovery` resolver class | present in loaded instruction |
| `DELIA_ORCHESTRATION_ENGINE` | `langgraph` (B1 active) |
| Model | `moonshotai/kimi-k3` via `openrouter` OpenRouter — **unchanged** |
| CRI | `cri_instruction_resource`/`cri_presentation_resource` loaded at boot (`root_composer` INFO); `delia_orchestration_engine selected=langgraph`, `delia_response_intelligence effective=cri` |
| AuthZ gate | unauthenticated `POST /apps/delia-api/interaction/turns` → **HTTP 401** |

## 7. Bounded authenticated smoke — NOT EXECUTED

The sanctioned smoke identity for prod (`user`, João Silva) uses a product-owner-provided credential that is not stored anywhere reachable in this session; `devin-smoke-r4`'s stored credential was rotated (doc 200); `devin-smoke-g16` had its grants revoked and KC account disabled after its smoke (doc 114). The user was asked and chose **Pular smoke**. Executing with an unauthorized identity or creating/resetting credentials without explicit authorization was not permitted by the task.

Consequence: `AUTHENTICATED_SMOKE=NOT_EXECUTED`; Business Outcome on the production model could not be measured in this task; AC11/AC13 not satisfied. All deploy verification that does not require a subject token was completed (§6).

## 8. Residuals / drift

- `EXECUTION_DRIFT`: none on the release itself — single-service scoped rebuild at a SHA containing only accepted Task 16/17 service changes. Concurrent workstreams advanced `shared/` and other services; their code rides inside the new image but is unreachable from delia-api (only `delpi_auth` imported) — disclosed, not silently included.
- `delpi-external-data-scheduler` was `unhealthy` before and after — pre-existing, unrelated to this release.
- WSL crashed once during the task (local tooling only; no production impact).
- Container env printing exposed the production `DELIA_LLM_API_KEY` value in executor output — pre-existing config surface, noted for hygiene; not repeated in artifacts.
- `UNRESOLVED`: production-measured native_assessment foreign-rate under `kimi-k3` remains unmeasured until a sanctioned smoke identity is available; `vista_prepare`/`teo_latest` model-bound anchors from doc 208 are unaffected by this deploy decision.
- `ROLLBACK_EXECUTED=NO`; `ROLLBACK_AVAILABLE=YES` (tagged image + runbook path).

## 9. Verdict

`PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED` for the release artifact: v28 instruction active, fingerprint proven, engine/model/governance preserved, auth gate intact, rollback armed. Authenticated Business Outcome deferred to the next session with a sanctioned smoke identity.
