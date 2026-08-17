import { describe, expect, it, vi } from "vitest";

import {
  applyTvCopilotPreviewSideEffects,
  planTvCopilotSideEffects,
} from "./tvCopilotSideEffects";

describe("planTvCopilotSideEffects", () => {
  it("usa sideEffectHints do BFF sem inspecionar o nome da op", () => {
    const plan = planTvCopilotSideEffects({
      nativeConfig: { version: 4, blocks: [{ id: "kpi-1", type: "kpi_view" }] },
      sideEffectHints: ["replaceNativeConfig"],
      sideEffects: {},
    });
    expect(plan.replaceNativeConfig).toBe(true);
    expect(plan.refreshFilmstrip).toBe(false);
    expect(plan.nativeConfig).toEqual({
      version: 4,
      blocks: [{ id: "kpi-1", type: "kpi_view" }],
    });
  });

  it("resolve removeBlockIds a partir de sideEffects + hint", () => {
    const plan = planTvCopilotSideEffects({
      sideEffectHints: ["replaceNativeConfig", "removeBlockIds"],
      nativeConfig: { version: 4, blocks: [] },
      sideEffects: { removedBlockIds: ["kpi-1"] },
    });
    expect(plan.removeBlockIds).toEqual(["kpi-1"]);
    expect(plan.replaceNativeConfig).toBe(true);
  });

  it("infere refreshFilmstrip de slides legados sem hints", () => {
    const plan = planTvCopilotSideEffects({
      sideEffects: {
        slides: [{ id: "new-slide", title: "Novo" }],
      },
    });
    expect(plan.refreshFilmstrip).toBe(true);
    expect(plan.replaceNativeConfig).toBe(false);
  });
});

describe("applyTvCopilotPreviewSideEffects", () => {
  it("aplica replaceNativeConfig e não chama remove quando config veio no envelope", () => {
    const replaceNativeConfig = vi.fn(() => true);
    const removeBlockIds = vi.fn(() => true);
    const refreshFilmstrip = vi.fn(() => false);

    const result = applyTvCopilotPreviewSideEffects(
      {
        sideEffectHints: ["replaceNativeConfig", "removeBlockIds"],
        nativeConfig: { version: 4, blocks: [{ id: "a", type: "text" }] },
        sideEffects: { removedBlockIds: ["gone"] },
      },
      { replaceNativeConfig, removeBlockIds, refreshFilmstrip },
    );

    expect(result.appliedReplace).toBe(true);
    expect(result.appliedRemove).toBe(false);
    expect(replaceNativeConfig).toHaveBeenCalledTimes(1);
    expect(removeBlockIds).not.toHaveBeenCalled();
  });

  it("remove blocos locais quando só há hint removeBlockIds", () => {
    const replaceNativeConfig = vi.fn(() => false);
    const removeBlockIds = vi.fn(() => true);
    const refreshFilmstrip = vi.fn(() => false);

    const result = applyTvCopilotPreviewSideEffects(
      {
        sideEffectHints: ["removeBlockIds"],
        sideEffects: { removedBlockIds: ["b1", "b2"] },
      },
      { replaceNativeConfig, removeBlockIds, refreshFilmstrip },
    );

    expect(result.appliedRemove).toBe(true);
    expect(removeBlockIds).toHaveBeenCalledWith(["b1", "b2"]);
  });
});
