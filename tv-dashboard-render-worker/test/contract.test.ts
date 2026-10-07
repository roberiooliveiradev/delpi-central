import { describe, expect, it } from "vitest";
import {
  RENDER_REQUEST_MAX_BYTES,
  validateRenderRequest,
} from "../src/contract.js";

const VALID = {
  playlistId: "3f6b1f9e-4a11-4f7a-9d2c-7d44a3a1b001",
  slideId: "9b1c2d3e-4f5a-4b6c-8d7e-9f0a1b2c3d4e",
  revision: 7,
  viewport: { width: 1920, height: 1080 },
  presentation: {
    playlist: { id: "3f6b1f9e-4a11-4f7a-9d2c-7d44a3a1b001" },
    presentationMeta: { revision: 7 },
    slides: [{ id: "9b1c2d3e-4f5a-4b6c-8d7e-9f0a1b2c3d4e" }],
  },
};

describe("validateRenderRequest", () => {
  it("accepts a bounded semantic request", () => {
    const res = validateRenderRequest(VALID);
    expect(res.ok).toBe(true);
    if (res.ok) {
      expect(res.value.revision).toBe(7);
      expect(res.value.viewport).toEqual({ width: 1920, height: 1080 });
    }
  });

  it.each(["url", "html", "javascript", "script", "selector", "cookie", "cookies", "headers", "waitFor", "path", "file", "navigation"])(
    "rejects forbidden field %s",
    (field) => {
      const res = validateRenderRequest({ ...VALID, [field]: "https://evil.test" });
      expect(res.ok).toBe(false);
      if (!res.ok) expect(res.error.code).toBe("FORBIDDEN_FIELD");
    },
  );

  it("rejects unknown extra fields", () => {
    const res = validateRenderRequest({ ...VALID, arbitrary: true });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.code).toBe("FORBIDDEN_FIELD");
  });

  it("rejects non-object body", () => {
    expect(validateRenderRequest("x").ok).toBe(false);
    expect(validateRenderRequest(null).ok).toBe(false);
    expect(validateRenderRequest([]).ok).toBe(false);
  });

  it("rejects invalid resource ids", () => {
    expect(validateRenderRequest({ ...VALID, playlistId: "../etc" }).ok).toBe(false);
    expect(validateRenderRequest({ ...VALID, slideId: "" }).ok).toBe(false);
    expect(
      validateRenderRequest({ ...VALID, slideId: "a".repeat(65) }).ok,
    ).toBe(false);
  });

  it("rejects non-integer / negative revision", () => {
    expect(validateRenderRequest({ ...VALID, revision: -1 }).ok).toBe(false);
    expect(validateRenderRequest({ ...VALID, revision: 1.5 }).ok).toBe(false);
    expect(validateRenderRequest({ ...VALID, revision: "7" }).ok).toBe(false);
  });

  it("rejects out-of-bounds viewport", () => {
    expect(
      validateRenderRequest({ ...VALID, viewport: { width: 4, height: 1080 } }).ok,
    ).toBe(false);
    expect(
      validateRenderRequest({ ...VALID, viewport: { width: 1920, height: 99999 } }).ok,
    ).toBe(false);
    expect(
      validateRenderRequest({ ...VALID, viewport: { width: 1920, height: 1080, scale: 9 } }).ok,
    ).toBe(false);
  });

  it("rejects missing presentation payload", () => {
    const { presentation: _drop, ...rest } = VALID;
    expect(validateRenderRequest(rest).ok).toBe(false);
  });

  it("rejects a payload bound to a different playlist", () => {
    const res = validateRenderRequest({
      ...VALID,
      presentation: {
        ...VALID.presentation,
        playlist: { id: "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb" },
      },
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.code).toBe("PAYLOAD_IDENTITY_MISMATCH");
  });

  it("rejects when the requested slide is not in the payload", () => {
    const res = validateRenderRequest({
      ...VALID,
      presentation: {
        ...VALID.presentation,
        slides: [{ id: "11111111-2222-3333-4444-555555555555" }],
      },
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.code).toBe("SLIDE_NOT_IN_PAYLOAD");
  });

  it("rejects a payload stamped for a different revision", () => {
    const res = validateRenderRequest({
      ...VALID,
      presentation: {
        ...VALID.presentation,
        presentationMeta: { revision: 6 },
      },
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.code).toBe("PAYLOAD_REVISION_MISMATCH");
  });

  it("allows viewport omitted (defaults to design size)", () => {
    const { viewport: _drop, ...rest } = VALID;
    const res = validateRenderRequest(rest);
    expect(res.ok).toBe(true);
    if (res.ok) expect(res.value.viewport).toBeNull();
  });

  it("exports a sane body cap", () => {
    expect(RENDER_REQUEST_MAX_BYTES).toBeGreaterThan(1024 * 1024);
    expect(RENDER_REQUEST_MAX_BYTES).toBeLessThanOrEqual(64 * 1024 * 1024);
  });
});
