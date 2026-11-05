# 290 — DÉLIA · Review P1: VISTA read e DAVI single-entity corrigidos; analyze residual do owner

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-P1-VISTA-PROTOCOL-DAVI-COVERAGE-AND-REAL-EVAL-01`  
**BASE_HEAD:** `8ea4c07552ae9d4450c2898c6bfe1593a2e64b6b`  
**REVIEWED_SHA:** `545775a821f488d7a2614d8451ec2be930001f97`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for bounded DÉLIA adapter/evidence renderer fixes; `P0=PASS_REPORTED`, `P1=PARTIAL`; production `NOT_AUTHORIZED`.

## Independent source findings

- Exact commit changes `delia-api/app/application/specialist_interop/specialist_interop.py`, `delia-api/app/application/capability_provision/generic_evidence_renderer.py`, two tests, doc288 and execution ledger. No new planner/parser/adapter, `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND`.
- The MCP interoperability adapter adds `UNKNOWN_ENTITY`, `UNKNOWN_ACTION`, `UNKNOWN_OPERATION` to `_OWNER_ARG_VALIDATION_CODES`; behavior still requires owner-declared `recoverable=true`. Test suite adds three positive recoverable error mappings and a `recoverable=false` terminal case. Scope is translation of known owner error taxonomy, not granting authority. Avoid treating arbitrary tool metadata as permission.
- Renderer `_resolver_entities` recognizes bounded nested Mapping with owner identity keys `code/product_code/component_code/item_code/material_code/codigo`, after collection scan and excluding `_is_capability_descriptor`. Six new tests cover detail shape `data.product`, another identity key, collection priority, metadata without code, shape without identity and descriptor exclusion.
- **Security/generalization residual:** generic `code` may appear on **owner error/envelope mappings** (`{"code":"UNKNOWN_ENTITY","recoverable":true,"isError":true}`); current test suite does not show that such structures are excluded from business-entity extraction. Verify `_resolver_entities` and its callers only see successful business payloads or add a targeted RED negative test against an error-shaped payload; fix minimally only if risk realized. Do not create a new evidence engine.
- Docs correct prior `enum/const` overstatement to `enum` and ledger records results. Full backend suite exit 0 is executor-reported; this review independently verified source diff but did not execute tests or reproduce MCP calls.
- Runtime outcomes reported: product 50220013 grounded at ~32s, existing product 99999999 grounded at ~60s after coverage fix, VISTA playlists `read(entity=playlist,action=list)` grounded at ~48–57s, owner-confirmed negative control 00000000 non-grounded at ~68s. HTTP200 and authentic MCP execution are executor-reported.
- **VISTA analyze residual:** the report attributes failed `vista.analyze` to an owner-side schema gap: field `analysis` declared as free string without enumerated supported values. The model attempts an unrecognized value, owner rejects non-recoverably; DÉLIA falls back to VISTA read and honestly declares limitations. Before changing owner contract, verify real accepted values, implementation, schema consumers/versioning and contract security. `vista.read` success does not establish `vista.analyze` business success. No DÉLIA provider-name branches or fabricated enum options.
- P0 endpoint remains functional as reported; exact prod provider/profile and release approvals absent; production remains blocked. Residual RQ24/RQ28 beyond owner analyze and hardening remain partial as recorded by executor.

## Next bounded owner task

**TASK_ID:** `DELIA-C3-P1-VISTA-ANALYZE-OWNER-CONTRACT-AND-REAL-READ-EVAL-01`.

1. Reanchor HEAD/status, project instructions, canonical 16→50→17→49→51→52→21→20→25, architecture/product/spec, ledger/docs 256/288–290. Identify owner `tv-dashboard-api` and its native contract, capability metadata projection, consumers, actual function implementation and authorized values for `analysis`; prove `EXISTING_EQUIVALENT`/`REUSE_DECISION`.
2. If owner truly accepts bounded fixed values, publish those **from owner implementation** through existing MCP schema (enum or native equivalent), preserving backward compatibility. If values are extensible, provide owner-authoritative discoverability instead of inventing allowlist at DÉLIA. Reject unsupported action values according to existing typed recoverable/error contracts; do not broaden authorization. Confirm proper error categorization and no excessive/raw diagnostic logging.
3. Add RED→GREEN owner and DÉLIA contract-consumer tests. Preserve `read` functionality, auth and evidence. Verify direct owner `analyze` with a real authorized dataset and complete DÉLIA client answer after model-selected `vista.analyze`, not fallback `vista.read`. Report actual owner operation selected, schema, grounded refs, HTTP response and timeout.
4. Add a small adversarial `_resolver_entities` test ensuring typed error payloads with `code` are never promoted to business evidence. Fix only if proven; avoid duplicate engines or owner-specific per-ID branches.
5. Independently verify baseline 50220013, 99999999, VISTA read, negative/clarification, full owner/DELIA regressions and security. Remove any replaced legacy, fix consumers, residual search; docs and ledger after actual outcomes, push. No production deploy.

**STOP:** if owner schema contract change conflicts with frozen authority or is not backward compatible, classify `ARCHITECTURE_DECISION_REQUIRED`; if no real authorized dataset, `INCONCLUSIVE` rather than a fabricated PASS.

**Review summary:** P1 improvement accepted, separate residual VISTA analyze belongs first at owner contract; DÉLIA evidence renderer requires negative error-shaped fixture confirmation.
