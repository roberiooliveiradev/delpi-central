import { describe, expect, it } from "vitest";

import { applyStagePanScrollDelta } from "./stagePan";

describe("applyStagePanScrollDelta", () => {
  it("arrastar para a direita revela conteúdo à esquerda (scrollLeft diminui)", () => {
    expect(applyStagePanScrollDelta({ scrollLeft: 40, scrollTop: 10 }, 12, -4)).toEqual({
      scrollLeft: 28,
      scrollTop: 14,
    });
  });
});
