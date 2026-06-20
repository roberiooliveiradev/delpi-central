import { describe, expect, it } from "vitest";

import { resolveResponseModeEffectNotice } from "./responseModeEffectNotice";

describe("resolveResponseModeEffectNotice", () => {
  it("returns notice from intelligence.pipeline", () => {
    const notice = resolveResponseModeEffectNotice({
      intelligence: {
        pipeline: {
          responseModeEffect: "llm_synthesis",
          responseModeEffectNotice:
            "Texto gerado pelo modelo com base nos dados consultados.",
        },
      },
    });

    expect(notice).toBe("Texto gerado pelo modelo com base nos dados consultados.");
  });

  it("returns null when pipeline notice is absent", () => {
    expect(resolveResponseModeEffectNotice(null)).toBeNull();
    expect(resolveResponseModeEffectNotice({ intelligence: { pipeline: {} } })).toBeNull();
  });
});
