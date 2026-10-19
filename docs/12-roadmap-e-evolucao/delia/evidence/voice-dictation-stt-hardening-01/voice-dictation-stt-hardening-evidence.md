# VD-F03 Bounded Hardening — Evidence

**TASK_ID:** `DELIA-VD-F03-STT-BOUNDED-HARDENING-01`
**DATE:** 2026-10-19
**BASE_HEAD:** `6cfb4ea7c3` (origin/main; implementation base `9a8b05063d` is ancestor)
**SCOPE:** single bounded cycle — GET /dictation/status AuthZ, log
privacy, model admission verification, dictation regression. No new
features, no provider/architecture changes.

## 1. Corrections applied

| # | Item | Action | Evidence |
|---|------|--------|----------|
| 1 | `GET /dictation/status` lacked explicit `delia.access` check | Reused the canonical `has_delia_access()` helper (owner: `app.application.interaction.handle_interactive_turn`) against the same Core-resolved `g.platform_access` used by the POST use case. `403 forbidden` for authenticated-without-access; `401` preserved by middleware; `200`/`available` semantics unchanged | `dictation_routes.py`; tests `test_status_requires_authentication`, `test_status_forbidden_without_delia_access`, `test_status_reports_unavailable_without_config`, `test_status_reports_available_with_handler_and_limits` |
| 2 | `logger.exception(...)` on unexpected errors could leak exception messages carrying provider payload/transcript/request material | `logger.error` with `exc_type` + `request_id` only — no traceback, no `str(exc)`. Typed `DictationError` path unchanged (metadata-only). Legitimate observability retained (code + exception type + correlation) | `dictation_routes.py`; test `test_internal_error_never_logs_audio_token_or_transcript` — sentinel audio (raw + base64), token and transcript embedded in the raised exception AND in the posted payload; zero sentinels in captured log stream while `internal_error`/`RuntimeError` remain |
| 3 | STT model admission | Verified: `_wire_dictation_handler` activates the adapter only when `DELIA_STT_PROVIDER=openai_compatible_audio` AND base_url AND model AND api_key all present — else `None` → `available=false` (fail closed). No hardcoded model in adapter (`stt provider configuration missing {name}` on empty), no silent fallback to `DELIA_LLM_MODEL`, secrets backend-only (env → Settings → adapter; never serialized). Contract `dictation-transcription-contract-v1.md` §2.1 updated for the status AuthZ | `root_composer.py:300`, `settings.py:144-161`, live container env |
| 4 | Distributed rate limit | Platform has no distributed limiter: `core-api` `rate_limit`/`integration_rate_limit` are in-process dict-based; no Redis-backed mechanism. Per task constraint (no new infra), per-user window limiter remains in-process | `DISTRIBUTED_RATE_LIMIT=RESIDUAL` (as documented in contract §3) |

## 2. Tests executed (this task, not prior evidence)

| Gate | Result |
|------|--------|
| Backend dictation contract tests | **PASS 25/25** (22 prior + 3 new: status 401, status 403, log-privacy sentinels) |
| Backend full suite | **PASS** (pytest exit 0, whole `tests/` — no regressions) |
| Frontend targeted (DeliaComposer + dictationClient + audio admission) | **PASS 56/56** (`vitest run src/ui/DeliaComposer.test.tsx src/api`) |
| Frontend code | unchanged — no defect proven |

## 3. Live smoke (authorized local stack, rebuilt `delpi-delia-api`)

| Check | Result |
|-------|--------|
| `GET /dictation/status` unauthenticated | **401** |
| `GET /dictation/status` authorized (`e2e-delia`, `delia.access`) | **200** `{available:true, contract_version:"1", language:"pt-BR", max_audio_bytes:4194304, max_duration_ms:120000}` |
| `POST /dictation/transcriptions` real pt-BR webm via provider | **200** real transcript returned (pt-BR production-vocabulary phrase) |
| Container logs after live calls | metadata only (`transcription_id`, `mime`, `bytes`, `duration_ms`, `request_id`, `status`); zero audio/base64/transcript/Authorization content — verified by grep |

## 4. Residuals (unchanged from VD-F03 evidence)

- `DISTRIBUTED_RATE_LIMIT=RESIDUAL` — in-process per user/replica.
- `MODEL_APPROVAL=TO_VERIFY` — `google/gemini-2.5-flash` proven on the
  approved OpenRouter family path; formal operational approval of the
  specific model for production is a deployment-gate decision.
- Human microphone QA, WER/CER corpus, independent review: pending.
- Deploy production: rebuild `delia-api` (+`plugin-ui`/`delia` if not
  already rebuilt) and `DELIA_STT_*` in host `.env`.
