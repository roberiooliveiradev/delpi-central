import { describe, expect, it } from "vitest";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  columnForSelectedSeries,
  linkedChartSeriesForSource,
  seriesForColumn,
} from "./dataPrepareCrossHighlight";

describe("dataPrepareCrossHighlight", () => {
  const blocks = [
    {
      id: "src-1",
      type: "data_source",
      frame: { x: 0, y: 0, w: 1, h: 1 },
      dataBinding: { operationId: "op" },
    },
    {
      id: "chart-1",
      type: "chart_view",
      frame: { x: 0, y: 0, w: 1, h: 1 },
      dataSourceId: "src-1",
      chartProjection: {
        categoryField: "periodo",
        series: [
          { field: "oee_filial_01", label: "SC", color: "#111" },
          { field: "oee_filial_02", label: "ES", color: "#222" },
        ],
      },
    },
  ] as ComunicadoBlock[];

  it("lista séries ligadas à fonte", () => {
    const linked = linkedChartSeriesForSource(blocks, "src-1");
    expect(linked).toHaveLength(2);
    expect(seriesForColumn(linked, "oee_filial_01")?.seriesIndex).toBe(0);
    expect(columnForSelectedSeries(linked, "chart-1", 1)).toBe("oee_filial_02");
  });

  it("ignora fontes sem vínculo", () => {
    expect(linkedChartSeriesForSource(blocks, "other")).toEqual([]);
  });
});
