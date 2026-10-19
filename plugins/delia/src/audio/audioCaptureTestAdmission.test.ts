import { describe, expect, it } from "vitest";

import {
  DELIA_AUDIO_TEST_BANNER,
  DELIA_AUDIO_TEST_LIMITS,
  DELIA_AUDIO_TEST_MAX_BYTES,
  DELIA_AUDIO_TEST_MAX_DURATION_MS,
} from "./audioCaptureTestAdmission";

describe("audio capture bounded test availability", () => {
  it("exposes the Product Master bounded test limits", () => {
    expect(DELIA_AUDIO_TEST_LIMITS).toEqual({
      maxDurationMs: DELIA_AUDIO_TEST_MAX_DURATION_MS,
      maxBytes: DELIA_AUDIO_TEST_MAX_BYTES,
    });
    expect(DELIA_AUDIO_TEST_MAX_DURATION_MS).toBe(60_000);
    expect(DELIA_AUDIO_TEST_MAX_BYTES).toBe(256_000);
  });

  it("requires no dedicated audio permission — availability is app-access scoped", () => {
    // The module must not consume permissions, JWT claims, URLs or
    // flags: admission to the app (delia.access) is decided upstream.
    expect(Object.keys(DELIA_AUDIO_TEST_LIMITS)).toEqual([
      "maxDurationMs",
      "maxBytes",
    ]);
  });

  it("declares a bounded, honest test notice", () => {
    expect(DELIA_AUDIO_TEST_BANNER).toContain("teste");
    expect(DELIA_AUDIO_TEST_BANNER).toContain("não pode ser enviado");
  });
});
