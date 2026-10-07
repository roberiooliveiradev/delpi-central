# tv-dashboard-render-worker

Bounded **execution host** that paints the shared presentation stage
(`@delpi/tv-dashboard-presentation` → `DesignViewportStage` + `NativeSlideView`,
the same mount used by editor preview and the TV kiosk) in headless Chromium
and returns a browser-rasterized `canonical_stage` PNG.

It exists so VISTA visual verification can obtain real pixels **without the
editor or any MFE open**. It is not a renderer of record and not a screenshot
service — it is a render-only shell around the shared package.

## Ownership boundary

```text
tv-dashboard-api  = domain authority (payload, revision, artifact lifecycle)
render-worker     = execution host  (paint → PNG bytes, nothing else)
```

The worker holds no domain state, performs no mutation, and runs no AuthZ.
`tv-dashboard-api` pushes the canonical TV-parity payload, receives the PNG,
re-validates the revision (fail-closed race discard) and stores the artifact
via `SlidePreviewRenderService`.

## Contract (`POST /render`)

Request — allowed fields only, anything else is `422 FORBIDDEN_FIELD`:

```json
{
  "playlistId": "…",          // resource id
  "slideId": "…",             // resource id inside the payload's slides[]
  "revision": 5,              // expected authoritative revision
  "viewport": { "width": 1920, "height": 1080 },   // optional hint
  "presentation": { "playlist": {…}, "slides": […], "presentationMeta": { "revision": 5 } }
}
```

**Payload identity binding** (fail-closed, `422`):
`presentation.playlist.id` must equal `playlistId`; `slides[]` must contain
`slideId`; `presentationMeta.revision` must equal `revision`. The canonical
payload's `playlist.viewportWidth/Height` is the authoritative paint size —
`viewport` is only a fallback hint.

Forbidden by design: `url`, `html`, `script`, `selector`, `cookies`,
`headers`, `waitFor`, arbitrary navigation — there is no way to turn this
into a generic screenshotter.

Auth: `Authorization: Bearer $TV_RENDER_WORKER_SERVICE_TOKEN`
(timing-safe compare). **Dedicated secret — intentionally NOT
`API_DELPI_INTERNAL_SERVICE_TOKEN`** or any other platform credential; the
same dedicated value is provisioned on the API (caller) and the worker
(verifier). New secret to provision at deploy time.

Response: `200 image/png` (bytes) or typed JSON error:
`UNAUTHORIZED`, `FORBIDDEN_FIELD`, `PAYLOAD_TOO_LARGE`,
`PAYLOAD_IDENTITY_MISMATCH`, `PAYLOAD_REVISION_MISMATCH`,
`RENDER_BUSY` (429), `RENDER_TIMEOUT` (504),
`UNSUPPORTED_EXTERNAL_CONTENT` (422), `SLIDE_NOT_IN_PAYLOAD`,
`RENDER_FAILED`.

## Bounds

| Bound | Value | Env |
|---|---|---|
| Request body | 32 MiB | fixed |
| Concurrency | 2 renders | `RENDER_WORKER_CONCURRENCY` |
| Per-render timeout | 30 s (queue wait included) | `RENDER_WORKER_TIMEOUT_MS` |
| Viewport edge | 16–8192 px | fixed |
| Memory | 2 GiB (compose `deploy.limits`) | `RENDER_WORKER_MEMORY_LIMIT` |

Browser isolation: one shared Chromium process, fresh incognito context per
render. A `context.route("**/*")` allowlist permits only (a) this worker's
loopback render page and (b) canonical media paths on the internal
`tv-dashboard-api` origin — everything else is aborted (`blockedbyclient`).
External/iframe slides are refused with `UNSUPPORTED_EXTERNAL_CONTENT`.

## Endpoints

- `GET /healthz` → `{ status, uptimeSec, browser }` (browser readiness)
- `POST /render` → S2S only (see contract)
- `GET /render-page/*` → bundled render shell; consumed by the worker's own
  Chromium on loopback. Still served on the container port but unreachable
  externally (no gateway route) and useless without `/render`.

## Env

| Var | Default | Purpose |
|---|---|---|
| `RENDER_WORKER_PORT` | `8100` | listen port |
| `TV_RENDER_WORKER_SERVICE_TOKEN` | — | required; S2S bearer |
| `TV_DASHBOARD_API_INTERNAL_URL` | `http://tv-dashboard-api:8000` | media URL target |
| `TV_DASHBOARD_API_ROOT_PATH` | `/apps/tv-dashboard-api` | media URL prefix |
| `RENDER_WORKER_CONCURRENCY` | `2` | max parallel renders |
| `RENDER_WORKER_TIMEOUT_MS` | `30000` | per-render bound |

Caller side (tv-dashboard-api): `TV_RENDER_WORKER_URL`,
`TV_RENDER_WORKER_SERVICE_TOKEN` (same dedicated value),
`TV_RENDER_WORKER_TIMEOUT_SECONDS`, `TV_RENDER_WORKER_TRIGGER_ON_CONTEXT`
(lazy fill on `get_playlist_context?include_preview=true`). A concurrent
reader on a render-in-flight key gets `rendered.status = "pending"` /
`failureCode = RENDER_PENDING` — not `unavailable`; a later request reads the
completed artifact.

## Local

```bash
npm install
npm run build         # vite render-page + tsc server
npm test              # contract/server unit tests (no browser needed)
npm start             # node dist/server.js (needs chromium + system libs)
```

Dev loop without build: `npm run dev` (tsx) — but the render page must be
built first (`npm run build:page`), it is served from `dist/render-page/`.

In Docker the base image is `mcr.microsoft.com/playwright:v1.62.1-noble`
(chromium + system deps). Outside Docker, `npx playwright install --with-deps
chromium` or equivalent system libraries are required.
