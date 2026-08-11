import { describe, expect, it } from "vitest";
import { createBlock } from "@delpi/tv-dashboard-presentation";

import { reorderLayerIds } from "./comunicadoLayerOrder";

function layered(id: string, z: number) {
  const block = createBlock("text", id);
  block.id = id;
  block.style = { ...block.style, zIndex: z };
  return block;
}

describe("reorderLayerIds", () => {
  const blocks = [layered("back", 1), layered("mid", 2), layered("front", 3)];

  it("before (acima na lista z-desc) coloca o movido na frente do alvo", () => {
    const next = reorderLayerIds(blocks, ["back"], "mid", "before");
    expect(next.map((block) => block.id)).toEqual(["mid", "back", "front"]);
    expect(next.find((block) => block.id === "back")?.style?.zIndex).toBeGreaterThan(
      next.find((block) => block.id === "mid")?.style?.zIndex ?? 0,
    );
  });

  it("after (abaixo na lista) deixa o movido atrás do alvo", () => {
    const next = reorderLayerIds(blocks, ["front"], "mid", "after");
    expect(next.map((block) => block.id)).toEqual(["back", "front", "mid"]);
    expect(next.find((block) => block.id === "front")?.style?.zIndex).toBeLessThan(
      next.find((block) => block.id === "mid")?.style?.zIndex ?? 99,
    );
  });
});
