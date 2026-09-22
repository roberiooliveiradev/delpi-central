"""TV Dashboard — Custom GPT Actions (OAuth façade).

Owner: ``tv-dashboard-api``. Custom GPT is an external consumer, not a second
catalog or writer. Canonical capability contract remains ``TvPresentationPatchV1``
(``tv_copilot_content.json`` + Copilot services).

## Surface

Gateway form:

```text
https://{host}/apps/tv-dashboard-api/gpt-actions/v1
```

Eight imported Actions under **GOVERNED_PREPARE_COMMIT_V2**
(``openapi.json`` is import-only, not in schema paths):

| operationId | Method | Path | Permission |
|---|---|---|---|
| gpt_get_catalog | GET | /catalog | TV_WRITE |
| gpt_list_playlists | GET | /playlists | TV_READ + owner/share segregation |
| gpt_get_playlist_context | GET | /playlists/{id} | TV_READ + resource read |
| gpt_search_data_routes | GET | /data-routes | TV_READ |
| gpt_preview_data_block | POST | /data-preview | TV_READ (+ resource read) |
| gpt_suggest_change | POST | /changes/suggest | TV_WRITE |
| gpt_preview_change | POST | /changes/preview | TV_WRITE (+ resource edit) |
| gpt_commit_change | POST | /changes/commit | TV_WRITE (+ resource edit) |

``gpt_commit_change`` is consequential (``x-openai-isConsequential``).
Canonical matrix: [`../integrations/vista-capability-matrix.md`](../integrations/vista-capability-matrix.md).

## Auth

- AuthN: Keycloak OAuth / Bearer JWT (same middleware as the product API).
- Platform RBAC: existing Core permissions (``tv-dashboard.read`` / ``.write``).
- Resource AuthZ: ``PlaylistAccessService`` (viewer cannot commit; editor ≠ owner).
- Only ``GET /gpt-actions/v1/openapi.json`` is public (exact path).
- No API Key authority for writes. No OpenAI email identity. No GPT-local RBAC matrix.

OAuth client ``chatgpt-tv-dashboard`` is a **TEMPORARY_BRIDGE_CLIENT**
(``MANUAL_CONFIGURATION_REQUIRED`` in Keycloak + GPT Builder). Go-live checklist:
``docs/gpt-actions/gpt-builder-go-live.md``. Specialist persona **VISTA**:
``docs/gpt-actions/specialist-instructions.md`` + Knowledge
``docs/gpt-actions/vista-display-playbooks.md``. This package owns the HTTP façade;
it does not auto-provision the client. Durable target remains Plugin + MCP
(Custom GPT bridge is temporary).

## PREPARE vs ACT

- Suggest = NL planner (optional; does **not** mint a proposal). Skip when the
  user intent is already a typed op (e.g. create slide/playlist).
- Preview = PREPARE. Returns opaque ``proposal_handle``; typed ops visible for
  explanation; never exposes ``httpCommands`` on the public GPT DTO.
- **Additive single-shot** (``confirmationPolicy=direct``): call
  ``gpt_preview_change`` with ``commit_now=true`` + ``confirmation.confirmed=true``
  + ``Idempotency-Key`` (header) or body ``idempotency_key``. Server PREPARE+COMMIT
  in one request → ``status=VERIFIED``. Compound lots (playlist+slide+block) are
  PlanCompiler-ordered; do not split in chat.
- **Destructive** (``confirmationPolicy=confirm``): preview without ``commit_now``
  (``commit_now`` is ignored if set) → one conversational confirm →
  ``gpt_commit_change`` with the **exact** opaque handle. Invented aliases
  (``latest``, ``current``, …) → ``PROPOSAL_NOT_FOUND``.
- Standalone commit = ACT via shared ``TvPresentationWriteService``. Input is
  **only** ``proposal_handle`` + ``confirmation`` (+ idempotency). No client
  ``ops``/``target``/``planDigest`` authority. No HTTP loopback against ``/playlists/**``.

## OCC / catalog / proposal / idempotency

- Proposal binds actor + target + typed ops + catalogVersion + baseRevision
  (server-side store; HMAC-opaque handle). Wrong actor → ``AUTHZ_DENIED``.
  Expired → ``PROPOSAL_EXPIRED``. Consumed/stale revision → ``PROPOSAL_CHANGED``.
- ``catalogVersion`` on the stored proposal must match current authority
  (409 ``CATALOG_VERSION_STALE``).
- ``Idempotency-Key`` required on commit; atomic acquire (UNIQUE + status) before first write.
  Same key+fingerprint completed → replay; different fingerprint → 409 ``IDEMPOTENCY_CONFLICT``;
  in-progress → 409 ``IDEMPOTENCY_IN_PROGRESS`` (retryable). PARTIAL outcomes are completed
  into the idempotency record and replayed without re-executing writes.
  Known deterministic pre-write rejections (e.g. invalid ``playlistId`` UUID) complete the
  reservation with a stable error outcome so replay never returns ``IDEMPOTENCY_IN_PROGRESS``.
  Store: ``tv_dashboard.gpt_actions_idempotency_keys`` (V016 table + V017 ``status`` column).
- Proposal store: in-process → **ACCEPT_WITH_RESIDUAL** (single replica). Review if workers/replicas > 1.

## Migrations (operational chain)

Do **not** treat V017 as standalone. On each environment:

1. Run the canonical TV Dashboard migration mechanism (`migrations_runner` / container startup path).
2. Verify **V016** applied (creates ``gpt_actions_idempotency_keys``).
3. Verify **V017** applied **after** V016 (adds ``status`` for atomic acquire).

This package documents the chain only; it does not apply migrations to remote environments.

``RATE_LIMITED`` (429) is **not implemented** in this V1 — no rate limiter was added.

## Confirmation / postcondition

- Confirmation policy derives from the Copilot catalog (``confirm`` for deletes).
- Commit always requires ``confirmation.confirmed=true`` (or boolean ``true``).
  Conversational OK is not AuthZ.
- Successful ACT returns ``status=VERIFIED``, ``persisted=true``, ``verified=true``
  after authoritative read-back. Failure to verify → ``OUTCOME_NOT_VERIFIED``.
- Multi-op batches are ordered stop-on-first-failure (no false VERIFIED on PARTIAL).

## Limits (V1)

- Local editor draft is unknown: ``localDraftCoordination=unavailable_external``.
- No binary media upload; keep ``assetId`` model.
- Free M / DAX / SQL generation is forbidden; typed Copilot transforms only.
- Legacy ``POST /data/copilot/*`` returns **410 Gone** (use VISTA gpt-actions).
- No generic entity CRUD Actions (``search_records`` / ``prepare_record_change``) — not VISTA's domain shape.

## Sync artifact

```bash
PYTHONPATH=.:../shared python3 scripts/sync_gpt_actions_openapi.py
```

Writes ``docs/gpt-actions/openapi-gpt-actions.json`` from the canonical builder.

## Nested operation schemas

Complex Copilot op shapes (``patch``, ``items``, ``steps``, ``block``, ``params``,
``fieldLabels``) are owned by ``tv_copilot_content.json`` ``operations.*.inputSchema``.
The GPT OpenAPI ``ops.items.oneOf`` is a projection of that catalog — not a second
authority (used on **preview/suggest**, not on commit).

Intentional free-form **request** objects (editor-native data-preview blobs) must
set ``x-delpi-gpt-opaque-object: true`` plus a non-empty description. Response
``error.details`` is the same class of diagnostic bag.

After any schema change: reimport the public OpenAPI in GPT Builder and start a
**new** conversation. Stale GPT versions are not acceptance evidence.

## Intent / compound planning boundary

VISTA understands the user goal and **orchestrates existing** semantic capabilities.
It does not become a second catalog, writer, or RBAC matrix.

| Layer | Owns |
|---|---|
| VISTA (Instructions + Knowledge) | Intent routing, desired-outcome reasoning, conversation UX |
| ``tv_copilot_content.json`` / TvCopilot | Supported operations and input schemas |
| GPT façade (8 Actions) | Transport: catalog, reads, suggest, preview, commit |
| ``TvPresentationWriteService`` | Material persistence path (same as UI) |
| Core + ``PlaylistAccessService`` | Platform RBAC + resource AuthZ |
| Keycloak | AuthN only |

Do **not** add a ninth Action merely for chaining. Compound execution, when
justified by the Abstraction Gate, evolves **behind** suggest / preview / commit.

**PROVEN:** typed catalog ops; PREPARE ``persisted=false``; commit is the only
public writer; ordered multi-op ACT with stop-on-first-failure; commit tracks
``created`` playlist/slide; authoritative ``VERIFIED`` / ``PARTIAL`` /
``OUTCOME_NOT_VERIFIED``; ``add_blank_slide`` is a blank native slide; background
is ``patch_native_config``; nested schema hardening is the GPT contract.

**CURRENT LIMITATION (PROVEN):** preview is not fully dependency-aware for every
create-then-modify combination (blank-slide preview has no authoritative id).

**TARGET / PLANNED:** Intent Frame as reasoning vocabulary (not persisted
authority); desired-state-first planning as formal contract; automatic compound
plans for utterances such as “crie um slide com fundo verde”; preview-time
resource binding / synthetic in-memory state; one confirmation for an unchanged
compound plan; optional richer atomic create (OPTION A) vs compound plan
(OPTION B). Neither option is implemented by this documentation.

No generic workflow DSL. No arbitrary HTTP. No free SQL/M/DAX.
