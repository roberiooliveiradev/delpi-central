import { describe, expect, it } from "vitest";

import {
  getLinkedDataSourceIds,
  resolvePreferredDataSourceId,
  shouldHideDataSourceOnStage,
} from "./comunicadoDataArchitecture";
import type { ComunicadoBlock } from "./comunicadoTypes";

describe("comunicadoDataArchitecture", () => {
  const sourceBlock: ComunicadoBlock = {
    id: "src-1",
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: { operationId: "get_oee", params: {} },
  };

  const chartBlock: ComunicadoBlock = {
    id: "chart-1",
    type: "chart_view",
    chartType: "line",
    dataSourceId: "src-1",
    frame: { x: 0, y: 0, w: 50, h: 30 },
  };

  it("detecta fontes vinculadas", () => {
    expect(getLinkedDataSourceIds([sourceBlock, chartBlock])).toEqual(new Set(["src-1"]));
  });

  it("oculta fonte no palco quando vinculada", () => {
    expect(shouldHideDataSourceOnStage("src-1", [sourceBlock, chartBlock])).toBe(true);
    expect(shouldHideDataSourceOnStage("src-1", [sourceBlock])).toBe(false);
  });

  it("resolve fonte preferida ao inserir visual", () => {
    expect(resolvePreferredDataSourceId([sourceBlock], "src-1")).toBe("src-1");
    expect(resolvePreferredDataSourceId([sourceBlock], null)).toBe("src-1");
    expect(
      resolvePreferredDataSourceId(
        [
          sourceBlock,
          { ...sourceBlock, id: "src-2" },
        ],
        null,
      ),
    ).toBeUndefined();
  });
});
