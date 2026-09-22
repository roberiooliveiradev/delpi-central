import { describe, expect, it } from "vitest";

import { buildTvDashboardHostContext } from "./hostSurfaceContext";

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

  it("preserva fontes, seleção visual e conflito de draft do host", () => {
    const ctx = buildTvDashboardHostContext({
      playlistId: "pl-1",
      slideId: "sl-1",
      selectedDataSourceId: "ds-1",
      selectedVisualId: "viz-1",
      dataSources: [
        {
          id: "ds-1",
          operationId: "get_overall_equipment_effectiveness_pct",
          label: "OEE",
        },
        { id: "", operationId: "invalid", label: "inválida" },
      ],
      hasLocalDraft: true,
    });

    expect(ctx.selectedDataSourceId).toBe("ds-1");
    expect(ctx.selectedVisualId).toBe("viz-1");
    expect(ctx.dataSources).toEqual([
      {
        id: "ds-1",
        operationId: "get_overall_equipment_effectiveness_pct",
        label: "OEE",
      },
    ]);
    expect(ctx.hasLocalDraft).toBe(true);
  });
});
