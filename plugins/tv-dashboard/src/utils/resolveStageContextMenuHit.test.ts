import { describe, expect, it } from "vitest";

import { resolveStageContextMenuHit } from "./resolveStageContextMenuHit";

describe("resolveStageContextMenuHit", () => {
  it("prioriza blockId explícito", () => {
    expect(
      resolveStageContextMenuHit({
        blockId: "icon-1",
        eventTarget: document.body,
      }),
    ).toEqual({ type: "block", blockId: "icon-1" });
  });

  it("resolve ancestral data-block-id (handles / SVG)", () => {
    const wrap = document.createElement("div");
    wrap.setAttribute("data-block-id", "icon-2");
    const svg = document.createElement("div");
    wrap.appendChild(svg);
    document.body.appendChild(wrap);
    expect(resolveStageContextMenuHit({ eventTarget: svg })).toEqual({
      type: "block",
      blockId: "icon-2",
    });
    wrap.remove();
  });

  it("fundo sem bloco → empty", () => {
    expect(resolveStageContextMenuHit({ eventTarget: document.body })).toEqual({
      type: "empty",
    });
  });
});
