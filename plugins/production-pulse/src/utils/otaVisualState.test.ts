import { describe, expect, it } from "vitest";

import { resolveOtaVisualState } from "./otaVisualState";

describe("resolveOtaVisualState wake taxonomy", () => {
  it("shows offline awaiting when device is offline", () => {
    const visual = resolveOtaVisualState({
      status: "authorized",
      deviceOnline: false,
      wakeStatus: "accepted",
    });
    expect(visual.label).toMatch(/offline/i);
    expect(visual.phase).toBe("authorized");
  });

  it("shows wake pending while avisando", () => {
    const visual = resolveOtaVisualState({
      status: "authorized",
      wakeStatus: "pending",
      deviceOnline: true,
    });
    expect(visual.phase).toBe("wake_pending");
    expect(visual.label).toMatch(/Avisando/i);
  });

  it("shows wake accepted as avisado aguardando consulta", () => {
    const visual = resolveOtaVisualState({
      status: "authorized",
      wakeStatus: "accepted",
      deviceOnline: true,
    });
    expect(visual.phase).toBe("wake_accepted");
    expect(visual.label).toMatch(/Avisado|consulta/i);
  });

  it("shows wake failed as pull fallback", () => {
    const visual = resolveOtaVisualState({
      status: "authorized",
      wakeStatus: "failed",
      deviceOnline: true,
    });
    expect(visual.phase).toBe("wake_failed");
    expect(visual.label).toMatch(/Não avisou|pull/i);
  });

  it("keeps downloading independent of wake", () => {
    const visual = resolveOtaVisualState({
      status: "downloading",
      wakeStatus: "failed",
      progressPercent: 40,
      deviceOnline: true,
    });
    expect(visual.phase).toBe("downloading");
    expect(visual.progressPercent).toBe(40);
  });
});
