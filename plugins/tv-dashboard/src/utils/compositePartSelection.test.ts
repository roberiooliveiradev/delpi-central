import { describe, expect, it } from "vitest";

import { resolveCompositePartPointerAction } from "./compositePartSelection";

describe("resolveCompositePartPointerAction", () => {
  it("primeiro clique (bloco não selecionado) arrasta o bloco", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: false,
        samePartSelected: false,
        partAllowsMove: true,
      }),
    ).toBe("drag-block");
  });

  it("bloco selecionado sem parte arrasta o bloco (não entra na parte)", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: false,
        partAllowsMove: true,
      }),
    ).toBe("drag-block");
  });

  it("mesma parte já selecionada e móvel arrasta a parte", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: true,
        partAllowsMove: true,
      }),
    ).toBe("part-move");
  });

  it("parte selecionada mas não móvel destravar para o bloco", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: true,
        partAllowsMove: false,
      }),
    ).toBe("drag-block");
  });
});
