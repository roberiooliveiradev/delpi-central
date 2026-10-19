import { describe, expect, it } from "vitest";

import {
  DELIA_AUDIO_TEST_BANNER,
  DELIA_AUDIO_TEST_MAX_BYTES,
  DELIA_AUDIO_TEST_MAX_DURATION_MS,
  DELIA_AUDIO_TEST_PERMISSION,
  resolveAudioTestAdmission,
} from "./audioCaptureTestAdmission";

describe("audio capture production-test admission", () => {
  it("admits when the Core-resolved permission is present", () => {
    const admission = resolveAudioTestAdmission([
      "delia.access",
      DELIA_AUDIO_TEST_PERMISSION,
    ]);
    expect(admission).toEqual({
      maxDurationMs: DELIA_AUDIO_TEST_MAX_DURATION_MS,
      maxBytes: DELIA_AUDIO_TEST_MAX_BYTES,
    });
  });

  it("fails closed without the permission", () => {
    expect(resolveAudioTestAdmission(["delia.access"])).toBeNull();
    expect(resolveAudioTestAdmission([])).toBeNull();
  });

  it("fails closed when the projection is absent or null", () => {
    expect(resolveAudioTestAdmission(undefined)).toBeNull();
    expect(resolveAudioTestAdmission(null)).toBeNull();
  });

  it("requires an exact permission code — no prefix/suffix match", () => {
    expect(
      resolveAudioTestAdmission([`${DELIA_AUDIO_TEST_PERMISSION}.extra`]),
    ).toBeNull();
    expect(
      resolveAudioTestAdmission([`x.${DELIA_AUDIO_TEST_PERMISSION}`]),
    ).toBeNull();
    expect(resolveAudioTestAdmission(["delia.audio-capture"])).toBeNull();
  });

  it("declares a bounded, honest test notice", () => {
    expect(DELIA_AUDIO_TEST_BANNER).toContain("teste");
    expect(DELIA_AUDIO_TEST_BANNER).toContain("não pode ser enviado");
  });
});
