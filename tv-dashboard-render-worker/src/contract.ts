/**
 * Bounded render request contract — semantic TV resource only.
 *
 * Allowed: playlistId, slideId, revision, viewport, presentation (canonical
 * TV-parity payload pushed by tv-dashboard-api).
 *
 * Anything else is rejected. There is deliberately no url/html/script/
 * selector/cookie/headers field — this is not a screenshot service.
 */

export const RENDER_REQUEST_MAX_BYTES = 32 * 1024 * 1024;
export const VIEWPORT_MIN_EDGE = 16;
export const VIEWPORT_MAX_EDGE = 8192;

const ALLOWED_KEYS = new Set([
  "playlistId",
  "slideId",
  "revision",
  "viewport",
  "presentation",
]);

const RESOURCE_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;

export type RenderViewport = { width: number; height: number };

export type RenderRequest = {
  playlistId: string;
  slideId: string;
  revision: number;
  viewport: RenderViewport | null;
  presentation: Record<string, unknown>;
};

export type ContractError = { code: string; message: string };

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validateRenderRequest(
  body: unknown,
): { ok: true; value: RenderRequest } | { ok: false; error: ContractError } {
  if (!isPlainObject(body)) {
    return { ok: false, error: { code: "INVALID_REQUEST", message: "body must be an object" } };
  }
  for (const key of Object.keys(body)) {
    if (!ALLOWED_KEYS.has(key)) {
      return {
        ok: false,
        error: { code: "FORBIDDEN_FIELD", message: `field '${key}' is not allowed` },
      };
    }
  }
  const playlistId = String(body.playlistId ?? "");
  const slideId = String(body.slideId ?? "");
  if (!RESOURCE_ID.test(playlistId) || !RESOURCE_ID.test(slideId)) {
    return {
      ok: false,
      error: { code: "INVALID_REQUEST", message: "playlistId/slideId must be resource ids" },
    };
  }
  const revision = body.revision;
  if (typeof revision !== "number" || !Number.isInteger(revision) || revision < 0 || revision > 1_000_000_000) {
    return {
      ok: false,
      error: { code: "INVALID_REQUEST", message: "revision must be a bounded integer" },
    };
  }
  let viewport: RenderViewport | null = null;
  if (body.viewport !== undefined && body.viewport !== null) {
    if (!isPlainObject(body.viewport)) {
      return { ok: false, error: { code: "INVALID_REQUEST", message: "viewport must be an object" } };
    }
    for (const key of Object.keys(body.viewport)) {
      if (key !== "width" && key !== "height") {
        return {
          ok: false,
          error: { code: "FORBIDDEN_FIELD", message: `viewport field '${key}' is not allowed` },
        };
      }
    }
    const width = Number(body.viewport.width);
    const height = Number(body.viewport.height);
    if (
      !Number.isInteger(width) ||
      !Number.isInteger(height) ||
      width < VIEWPORT_MIN_EDGE ||
      height < VIEWPORT_MIN_EDGE ||
      width > VIEWPORT_MAX_EDGE ||
      height > VIEWPORT_MAX_EDGE
    ) {
      return {
        ok: false,
        error: { code: "INVALID_REQUEST", message: "viewport edges out of bounds" },
      };
    }
    viewport = { width, height };
  }
  if (!isPlainObject(body.presentation)) {
    return {
      ok: false,
      error: { code: "INVALID_REQUEST", message: "presentation must be the canonical payload object" },
    };
  }
  // Payload identity binding: the pushed payload must belong to the requested
  // resources — the worker never paints an unrelated payload under different
  // resource ids.
  const playlist = body.presentation.playlist;
  if (!isPlainObject(playlist) || playlist.id !== playlistId) {
    return {
      ok: false,
      error: {
        code: "PAYLOAD_IDENTITY_MISMATCH",
        message: "presentation.playlist.id does not match playlistId",
      },
    };
  }
  const slides = body.presentation.slides;
  if (
    !Array.isArray(slides) ||
    !slides.some((s) => isPlainObject(s) && s.id === slideId)
  ) {
    return {
      ok: false,
      error: {
        code: "SLIDE_NOT_IN_PAYLOAD",
        message: "requested slideId is not part of the pushed presentation",
      },
    };
  }
  const meta = body.presentation.presentationMeta;
  const payloadRevision = isPlainObject(meta) ? meta.revision : undefined;
  if (payloadRevision !== revision) {
    return {
      ok: false,
      error: {
        code: "PAYLOAD_REVISION_MISMATCH",
        message: "presentation.presentationMeta.revision does not match revision",
      },
    };
  }
  return {
    ok: true,
    value: {
      playlistId,
      slideId,
      revision,
      viewport,
      presentation: body.presentation,
    },
  };
}
