import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveSelectedDataContext } from "./selectedDataContext";

function source(id: string, operationId = "op.a"): ComunicadoBlock {
  return {
    id,
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: { operationId, params: {} },
  } as ComunicadoBlock;
}

function chart(id: string, dataSourceId?: string): ComunicadoBlock {
  return {
    id,
    type: "chart_view",
    frame: { x: 0, y: 0, w: 20, h: 20 },
    chartType: "bar",
    dataSourceId,
  } as ComunicadoBlock;
}

describe("resolveSelectedDataContext", () => {
  it("retorna none sem seleção de dados", () => {
    const shape = {
      id: "s1",
      type: "shape",
      frame: { x: 0, y: 0, w: 5, h: 5 },
      shape: "rect",
    } as ComunicadoBlock;
    expect(resolveSelectedDataContext([shape], ["s1"]).kind).toBe("none");
  });

  it("single com visual ligado à fonte", () => {
    const blocks = [source("src1"), chart("c1", "src1")];
    const ctx = resolveSelectedDataContext(blocks, ["c1"]);
    expect(ctx.kind).toBe("single");
    expect(ctx.bindingTarget?.id).toBe("src1");
    expect(ctx.primary?.id).toBe("c1");
  });

  it("homogeneous quando vários visuais usam a mesma fonte", () => {
    const blocks = [source("src1"), chart("c1", "src1"), chart("c2", "src1")];
    const ctx = resolveSelectedDataContext(blocks, ["c1", "c2"]);
    expect(ctx.kind).toBe("homogeneous");
    expect(ctx.bindingTarget?.id).toBe("src1");
  });

  it("mixed quando fontes diferem", () => {
    const blocks = [source("src1"), source("src2"), chart("c1", "src1"), chart("c2", "src2")];
    const ctx = resolveSelectedDataContext(blocks, ["c1", "c2"]);
    expect(ctx.kind).toBe("mixed");
    expect(ctx.bindingTarget).toBeNull();
    expect(ctx.message).toMatch(/diferentes/i);
  });
});
