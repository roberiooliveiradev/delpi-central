import { describe, expect, it } from "vitest";

import {
  duplicateBlocksWithDataPolicy,
  needsDataSourceDuplicateChoice,
} from "./duplicateBlocksWithDataPolicy";
import type { ComunicadoBlock } from "./comunicadoTypes";

const sourceBlock = (id: string): ComunicadoBlock =>
  ({
    id,
    type: "data_source",
    frame: { x: 10, y: 10, w: 20, h: 10 },
    dataBinding: { operationId: "get_oee", params: { dateRangePreset: "this_month" } },
  }) as ComunicadoBlock;

const chartView = (id: string, dataSourceId: string): ComunicadoBlock =>
  ({
    id,
    type: "chart_view",
    chartType: "bar",
    dataSourceId,
    frame: { x: 30, y: 10, w: 40, h: 30 },
  }) as ComunicadoBlock;

describe("duplicateBlocksWithDataPolicy", () => {
  it("needsDataSourceDuplicateChoice detecta visual com fonte", () => {
    expect(needsDataSourceDuplicateChoice([chartView("c1", "src-1")])).toBe(true);
    expect(needsDataSourceDuplicateChoice([{ id: "t1", type: "text", content: "x", frame: { x: 0, y: 0, w: 10, h: 10 } }])).toBe(
      false,
    );
  });

  it("share_source mantém dataSourceId original", () => {
    const existing = [sourceBlock("src-1")];
    const result = duplicateBlocksWithDataPolicy(existing, [chartView("c1", "src-1")], "share_source");
    const copy = result.blocks.find((block) => block.id === result.pastedIds[0]);
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).toBe("src-1");
    expect(result.blocks.filter((block) => block.type === "data_source")).toHaveLength(1);
  });

  it("clone_source duplica fonte externa e remapeia visual", () => {
    const existing = [sourceBlock("src-1")];
    const result = duplicateBlocksWithDataPolicy(existing, [chartView("c1", "src-1")], "clone_source");
    const sources = result.blocks.filter((block) => block.type === "data_source");
    expect(sources).toHaveLength(2);
    const copy = result.blocks.find((block) => block.id === result.pastedIds[0]);
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).not.toBe("src-1");
    expect(copy && "dataSourceId" in copy ? copy.dataSourceId : null).toBe(sources[1]?.id);
  });

  it("duplica grupo com novo groupId (não entra no grupo da origem)", () => {
    const a = {
      id: "a",
      type: "text" as const,
      content: "A",
      frame: { x: 10, y: 10, w: 20, h: 10 },
      groupId: "grp_orig",
    };
    const b = {
      id: "b",
      type: "text" as const,
      content: "B",
      frame: { x: 40, y: 10, w: 20, h: 10 },
      groupId: "grp_orig",
    };
    const result = duplicateBlocksWithDataPolicy([a, b], [a, b], "share_source");
    const pasted = result.blocks.filter((block) => result.pastedIds.includes(block.id));
    expect(pasted).toHaveLength(2);
    expect(pasted[0]?.groupId).toBeTruthy();
    expect(pasted[0]?.groupId).not.toBe("grp_orig");
    expect(pasted[1]?.groupId).toBe(pasted[0]?.groupId);
    expect(result.blocks.find((block) => block.id === "a")?.groupId).toBe("grp_orig");
  });
});
