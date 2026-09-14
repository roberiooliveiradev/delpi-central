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

OAuth client candidate ``chatgpt-tv-dashboard`` is **TARGET / MANUAL_CONFIGURATION_REQUIRED**
(Keycloak + GPT Builder). This package prepares the HTTP surface; it does not
claim the client already exists or that Builder is configured.

## PREPARE vs ACT

- Suggest / preview = PREPARE (``persisted=false``). Preview returns ``planDigest``;
  it never exposes ``httpCommands`` on the public GPT DTO.
- Commit = ACT via shared ``TvPresentationWriteService`` (same boundary as UI CRUD).
  No HTTP loopback against ``/playlists/**``.

## OCC / catalog / digest / idempotency

- ``expectedRevision`` must match persisted revision (409 ``REVISION_CONFLICT``).
- ``catalogVersion`` must match current authority (409 ``CATALOG_VERSION_STALE``).
- ``planDigest`` binds actor + target + ops + catalogVersion + baseRevision
  (409 ``PLAN_MISMATCH``).
- ``Idempotency-Key`` required on commit; same key+fingerprint replays outcome;
  same key+different fingerprint → 409 ``IDEMPOTENCY_CONFLICT``.
  Store: ``tv_dashboard.gpt_actions_idempotency_keys`` (24h retention on get).

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
