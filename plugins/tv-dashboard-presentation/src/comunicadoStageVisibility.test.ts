import { describe, expect, it } from "vitest";

import {
  filterStageSelectableIds,
  isBlockHiddenOnStage,
  isBlockSelectableOnStage,
  listViewsLinkedToDataSource,
  resolveBlockStageHideReason,
  resolveStageSelectionTargetId,
} from "./comunicadoStageVisibility";
import type { ComunicadoBlock } from "./comunicadoTypes";

describe("comunicadoStageVisibility", () => {
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

  const tableBlock: ComunicadoBlock = {
    id: "table-1",
    type: "table_view",
    tablePreset: "grid",
    dataSourceId: "src-1",
    frame: { x: 10, y: 10, w: 40, h: 40 },
  };

  const freeSource: ComunicadoBlock = {
    id: "src-free",
    type: "data_source",
    frame: { x: 5, y: 5, w: 10, h: 10 },
    dataBinding: { operationId: "get_otd", params: {} },
  };

  it("oculta fonte vinculada e mantém fonte livre selecionável", () => {
    const blocks = [sourceBlock, chartBlock, freeSource];
    expect(isBlockHiddenOnStage(sourceBlock, blocks)).toBe(true);
    expect(isBlockSelectableOnStage(sourceBlock, blocks)).toBe(false);
    expect(isBlockHiddenOnStage(freeSource, blocks)).toBe(false);
    expect(isBlockSelectableOnStage(chartBlock, blocks)).toBe(true);
  });

  it("filtra IDs ocultos da seleção/marquee", () => {
    const blocks = [sourceBlock, chartBlock, freeSource];
    expect(filterStageSelectableIds(["src-1", "chart-1", "src-free"], blocks)).toEqual([
      "chart-1",
      "src-free",
    ]);
  });

  it("lista visuais ligados e redireciona seleção da fonte oculta", () => {
    const blocks = [sourceBlock, chartBlock, tableBlock];
    expect(listViewsLinkedToDataSource("src-1", blocks).map((b) => b.id)).toEqual([
      "chart-1",
      "table-1",
    ]);
    expect(resolveStageSelectionTargetId("src-1", blocks)).toBe("chart-1");
    expect(resolveStageSelectionTargetId("chart-1", blocks)).toBe("chart-1");
  });

  it("oculta bloco com hidden=true do usuário", () => {
    const block: ComunicadoBlock = {
      id: "text-1",
      type: "text",
      content: "A",
      frame: { x: 0, y: 0, w: 10, h: 10 },
      hidden: true,
    };
    expect(resolveBlockStageHideReason(block, [block])).toBe("user_hidden");
    expect(isBlockHiddenOnStage(block, [block])).toBe(true);
  });
});
