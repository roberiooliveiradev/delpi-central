import { describe, expect, it } from "vitest";

import {
  DELIA_AUDIO_PRODUCT_LIMITS,
  DELIA_AUDIO_PRODUCT_MAX_BYTES,
  DELIA_AUDIO_PRODUCT_MAX_DURATION_MS,
  DELIA_DICTATION_STT_DISCLOSURE,
  DELIA_LOCAL_CAPTURE_DISCLOSURE,
  resolveAudioCaptureLimits,
} from "./audioCaptureTestAdmission";

describe("audio capture product limits (VD-F05)", () => {
  it("exposes the product-approved 300 s capture bound", () => {
    expect(DELIA_AUDIO_PRODUCT_LIMITS).toEqual({
      maxDurationMs: DELIA_AUDIO_PRODUCT_MAX_DURATION_MS,
      maxBytes: DELIA_AUDIO_PRODUCT_MAX_BYTES,
    });
    expect(DELIA_AUDIO_PRODUCT_MAX_DURATION_MS).toBe(300_000);
    expect(DELIA_AUDIO_PRODUCT_MAX_BYTES).toBe(8_388_608);
  });

  it("requires no dedicated audio permission — availability is app-access scoped", () => {
    // The module must not consume permissions, JWT claims, URLs or
    // flags: admission to the app (delia.access) is decided upstream.
    expect(Object.keys(DELIA_AUDIO_PRODUCT_LIMITS)).toEqual([
      "maxDurationMs",
      "maxBytes",
    ]);
  });
});

describe("resolveAudioCaptureLimits — min(product, contract)", () => {
  it("falls back to product limits when no contract status exists", () => {
    expect(resolveAudioCaptureLimits(null)).toEqual(DELIA_AUDIO_PRODUCT_LIMITS);
  });

  it("falls back to product limits when the contract publishes nulls", () => {
    expect(
      resolveAudioCaptureLimits({
        maxDurationMs: null,
        maxAudioBytes: null,
      }),
    ).toEqual(DELIA_AUDIO_PRODUCT_LIMITS);
  });

  it("clamps to the contract when the backend admits less", () => {
    expect(
      resolveAudioCaptureLimits({
        maxDurationMs: 120_000,
        maxAudioBytes: 1_048_576,
      }),
    ).toEqual({ maxDurationMs: 120_000, maxBytes: 1_048_576 });
  });

  it("keeps product limits when the contract admits more", () => {
    expect(
      resolveAudioCaptureLimits({
        maxDurationMs: 600_000,
        maxAudioBytes: 20_000_000,
      }),
    ).toEqual(DELIA_AUDIO_PRODUCT_LIMITS);
  });

  it("mixes each axis independently", () => {
    expect(
      resolveAudioCaptureLimits({
        maxDurationMs: 120_000,
        maxAudioBytes: 20_000_000,
      }),
    ).toEqual({ maxDurationMs: 120_000, maxBytes: 8_388_608 });
  });
});

describe("contextual disclosures (VD-F04)", () => {
  it("declares honest contextual disclosures, not a global banner", () => {
    // The permanent audio/dictation header banner was removed; the
    // purpose copy now lives contextually inside the capture surface.
    expect(DELIA_DICTATION_STT_DISCLOSURE).toContain("transcrição");
    expect(DELIA_DICTATION_STT_DISCLOSURE).toContain("Revise");
    expect(DELIA_LOCAL_CAPTURE_DISCLOSURE).toContain("navegador");
    expect(DELIA_LOCAL_CAPTURE_DISCLOSURE).not.toContain("enviada");
  });
});
