"""TV Dashboard — Custom GPT Actions (OAuth façade).

Owner: ``tv-dashboard-api``. Custom GPT is an external consumer, not a second
catalog or writer. Canonical capability contract remains ``TvCopilotPatchV1``
(``tv_copilot_content.json`` + Copilot services).

## Surface

Gateway form:

```text
https://{host}/apps/tv-dashboard-api/gpt-actions/v1
```

Eight imported Actions (``openapi.json`` is import-only, not in schema paths):

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

- Suggest / preview = PREPARE (``persisted=false``). Preview returns ``planDigest``;
  it never exposes ``httpCommands`` on the public GPT DTO.
- Commit = ACT via shared ``TvPresentationWriteService`` (same boundary as UI CRUD).
  No HTTP loopback against ``/playlists/**``.

## OCC / catalog / digest / idempotency

- ``expectedRevision`` is required for existing playlist (422 if missing) and must match
  persisted revision (409 ``REVISION_CONFLICT``).
- ``catalogVersion`` must match current authority (409 ``CATALOG_VERSION_STALE``).
- ``planDigest`` binds actor + target + **typed ops** + catalogVersion + baseRevision
  (409 ``PLAN_MISMATCH``). Preview returns the same typed ``ops`` used to compute the digest.
- ``Idempotency-Key`` required on commit; atomic acquire (UNIQUE + status) before first write.
  Same key+fingerprint completed → replay; different fingerprint → 409 ``IDEMPOTENCY_CONFLICT``;
  in-progress → 409 ``IDEMPOTENCY_IN_PROGRESS`` (retryable). PARTIAL outcomes are completed
  into the idempotency record and replayed without re-executing writes.
  Known deterministic pre-write rejections (e.g. invalid ``playlistId`` UUID) complete the
  reservation with a stable error outcome so replay never returns ``IDEMPOTENCY_IN_PROGRESS``.
  Store: ``tv_dashboard.gpt_actions_idempotency_keys`` (V016 table + V017 ``status`` column).

## Migrations (operational chain)

Do **not** treat V017 as standalone. On each environment:

1. Run the canonical TV Dashboard migration mechanism (`migrations_runner` / container startup path).
2. Verify **V016** applied (creates ``gpt_actions_idempotency_keys``).
3. Verify **V017** applied **after** V016 (adds ``status`` for atomic acquire).

This package documents the chain only; it does not apply migrations to remote environments.

- ``expectedRevision`` is **required** when ``target.playlistId`` exists. Omit only for
  ``create_playlist`` without a pre-existing playlist. Missing → 422 ``INVALID_CHANGE``.

``RATE_LIMITED`` (429) is **not implemented** in this V1 — no rate limiter was added.

## Confirmation / postcondition

- Confirmation policy derives from the Copilot catalog (``confirm`` for deletes).
- Successful ACT returns ``status=VERIFIED``, ``persisted=true``, ``verified=true``
  after authoritative read-back. Failure to verify → ``OUTCOME_NOT_VERIFIED``.
- Multi-op batches are ordered stop-on-first-failure (no false VERIFIED on PARTIAL).

## Limits (V1)

- Local editor draft is unknown: ``localDraftCoordination=unavailable_external``.
- No binary media upload; keep ``assetId`` model.
- Free M / DAX / SQL generation is forbidden; typed Copilot transforms only.
- Legacy ``POST /data/copilot/apply-patch`` remains a non-persisting planner.

## Sync artifact

```bash
PYTHONPATH=.:../shared python3 scripts/sync_gpt_actions_openapi.py
```

Writes ``docs/gpt-actions/openapi-gpt-actions.json`` from the canonical builder.
