import { describe, expect, it } from "vitest";

import {
  DELIA_AUDIO_QA_MAX_BYTES,
  DELIA_AUDIO_QA_MAX_DURATION_MS,
  isAudioQaBundleAllowed,
  resolveAudioQaAdmission,
} from "./audioCaptureQaAdmission";

const devEnv = { DEV: true } as const;
const prodEnv = { DEV: false } as const;
const qaBuiltEnv = { DEV: false, VITE_DELIA_AUDIO_QA: "1" } as const;

describe("isAudioQaBundleAllowed", () => {
  it("admits dev bundles", () => {
    expect(isAudioQaBundleAllowed(devEnv)).toBe(true);
  });

  it("admits bundles built with VITE_DELIA_AUDIO_QA=1", () => {
    expect(isAudioQaBundleAllowed(qaBuiltEnv)).toBe(true);
  });

  it("rejects production bundles", () => {
    expect(isAudioQaBundleAllowed(prodEnv)).toBe(false);
  });
});

describe("resolveAudioQaAdmission", () => {
  it("returns null in production even with the query param", () => {
    expect(
      resolveAudioQaAdmission("?delia-audio-qa=1", prodEnv),
    ).toBeNull();
  });

  it("returns null without the explicit param even in dev", () => {
    expect(resolveAudioQaAdmission("", devEnv)).toBeNull();
    expect(resolveAudioQaAdmission("?other=1", devEnv)).toBeNull();
  });

  it("returns null for param values other than 1", () => {
    expect(
      resolveAudioQaAdmission("?delia-audio-qa=true", devEnv),
    ).toBeNull();
    expect(
      resolveAudioQaAdmission("?delia-audio-qa=yes", devEnv),
    ).toBeNull();
  });

  it("admits QA limits in a dev bundle with the explicit param", () => {
    expect(
      resolveAudioQaAdmission("?delia-audio-qa=1", devEnv),
    ).toEqual({
      maxDurationMs: DELIA_AUDIO_QA_MAX_DURATION_MS,
      maxBytes: DELIA_AUDIO_QA_MAX_BYTES,
    });
  });

  it("admits QA limits in a flagged QA build", () => {
    expect(
      resolveAudioQaAdmission(
        "/apps/delia?delia-audio-qa=1",
        qaBuiltEnv,
      ),
    ).toEqual({
      maxDurationMs: DELIA_AUDIO_QA_MAX_DURATION_MS,
      maxBytes: DELIA_AUDIO_QA_MAX_BYTES,
    });
  });

  it("QA limits are declared test fixtures, not production policy", () => {
    expect(DELIA_AUDIO_QA_MAX_DURATION_MS).toBe(60_000);
    expect(DELIA_AUDIO_QA_MAX_BYTES).toBe(256_000);
  });
});
