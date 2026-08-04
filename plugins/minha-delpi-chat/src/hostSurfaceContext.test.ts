import { describe, expect, it, beforeEach, vi } from "vitest";

import {
  buildTvDashboardHostContext,
  notifyHostOfTvCopilotToolCalls,
} from "./hostSurfaceContext";

describe("buildTvDashboardHostContext", () => {
  it("envia playlist, slide e seleção com resumo de foco", () => {
    const ctx = buildTvDashboardHostContext({
      playlistId: "pl-1",
      slideId: "sl-1",
      selectedBlockIds: ["b1", "b2", "b1"],
      selectedBlockTypes: ["kpi_view", "text"],
    });
    expect(ctx).toEqual({
      surface: "tv-dashboard",
      playlistId: "pl-1",
      slideId: "sl-1",
      selectedBlockIds: ["b1", "b2"],
      selectedBlockTypes: ["kpi_view", "text"],
      focusBlockId: "b1",
      focusBlockType: "kpi_view",
    });
  });

  it("omite seleção vazia", () => {
    const ctx = buildTvDashboardHostContext({
      playlistId: "pl-1",
      slideId: null,
      selectedBlockIds: [],
    });
    expect(ctx.selectedBlockIds).toBeUndefined();
    expect(ctx.focusBlockId).toBeUndefined();
  });

  it("inclui operationId e dataSourceId quando informados", () => {
    const ctx = buildTvDashboardHostContext({
      playlistId: "pl-1",
      slideId: "sl-1",
      operationId: "get_overall_equipment_effectiveness_pct",
      dataSourceId: "ds-1",
      presetKey: "production_oee_overview",
    });
    expect(ctx.operationId).toBe("get_overall_equipment_effectiveness_pct");
    expect(ctx.dataSourceId).toBe("ds-1");
    expect(ctx.presetKey).toBe("production_oee_overview");
  });
});

describe("notifyHostOfTvCopilotToolCalls", () => {
  beforeEach(() => {
    (globalThis as { window?: unknown }).window = {
      __DELPI_TV_COPILOT_HOST__: undefined,
    };
  });

  it("repassa sideEffectHints e nativeConfig no preview (sem if por op)", () => {
    const onPreviewPatch = vi.fn();
    (globalThis as { window: { __DELPI_TV_COPILOT_HOST__: unknown } }).window =
      {
        __DELPI_TV_COPILOT_HOST__: { onPreviewPatch },
      };

    notifyHostOfTvCopilotToolCalls([
      {
        name: "tv_dashboard_copilot",
        arguments: { mode: "preview", ops: [{ op: "upsert_block" }] },
        metadata: {
          ok: true,
          data: {
            nativeConfig: { version: 4, blocks: [{ id: "a", type: "text" }] },
            sideEffects: { removedBlockIds: [] },
            sideEffectHints: ["replaceNativeConfig"],
            diff: { addedBlockIds: ["a"] },
          },
        },
      },
    ]);

    expect(onPreviewPatch).toHaveBeenCalledTimes(1);
    expect(onPreviewPatch.mock.calls[0][0]).toMatchObject({
      nativeConfig: { version: 4, blocks: [{ id: "a", type: "text" }] },
      sideEffectHints: ["replaceNativeConfig"],
      ops: [{ op: "upsert_block" }],
    });
  });

  it("repassa sideEffectHints no apply", () => {
    const onApplyPatchResult = vi.fn();
    (globalThis as { window: { __DELPI_TV_COPILOT_HOST__: unknown } }).window =
      {
        __DELPI_TV_COPILOT_HOST__: { onApplyPatchResult },
      };

    notifyHostOfTvCopilotToolCalls([
      {
        name: "tv_dashboard_copilot",
        arguments: { mode: "apply" },
        metadata: {
          ok: true,
          data: {
            persisted: true,
            target: { playlistId: "pl", slideId: "sl" },
            sideEffectHints: ["refreshFilmstrip"],
          },
        },
      },
    ]);

    expect(onApplyPatchResult).toHaveBeenCalledWith(
      expect.objectContaining({
        ok: true,
        persisted: true,
        sideEffectHints: ["refreshFilmstrip"],
        target: { playlistId: "pl", slideId: "sl" },
      }),
    );
  });
});
