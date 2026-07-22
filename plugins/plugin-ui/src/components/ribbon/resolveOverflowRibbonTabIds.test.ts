import { describe, expect, it } from "vitest";

import {
  resolveOverflowRibbonTabIds,
  type RibbonTabSize,
} from "./resolveOverflowRibbonTabIds";

function tabs(widths: Array<[string, number]>): RibbonTabSize[] {
  return widths.map(([id, width], order) => ({ id, width, order }));
}

describe("resolveOverflowRibbonTabIds", () => {
  it("não esconde quando tudo cabe", () => {
    const list = tabs([
      ["a", 80],
      ["b", 80],
      ["c", 80],
    ]);
    expect([...resolveOverflowRibbonTabIds(list, 300, { overflowControlWidth: 40 })]).toEqual([]);
  });

  it("esconde da direita para a esquerda e reserva o botão Mais", () => {
    const list = tabs([
      ["a", 100],
      ["b", 100],
      ["c", 100],
    ]);
    /* full 300; com Mais: a+b+Mais = 100+100+40 = 240 */
    const one = resolveOverflowRibbonTabIds(list, 250, { overflowControlWidth: 40 });
    expect([...one]).toEqual(["c"]);

    const two = resolveOverflowRibbonTabIds(list, 180, { overflowControlWidth: 40 });
    expect([...two].sort()).toEqual(["b", "c"]);
  });

  it("mantém pelo menos uma aba visível", () => {
    const list = tabs([
      ["a", 120],
      ["b", 120],
    ]);
    const overflow = resolveOverflowRibbonTabIds(list, 50, { overflowControlWidth: 40 });
    expect(overflow.size).toBe(1);
    expect(overflow.has("b")).toBe(true);
    expect(overflow.has("a")).toBe(false);
  });

  it("promove a aba ativa se cairia no overflow", () => {
    const list = tabs([
      ["a", 100],
      ["b", 100],
      ["c", 100],
    ]);
    const overflow = resolveOverflowRibbonTabIds(list, 250, {
      overflowControlWidth: 40,
      activeId: "c",
    });
    expect(overflow.has("c")).toBe(false);
    expect([...overflow]).toEqual(["b"]);
  });

  it("respeita gap entre abas", () => {
    const list = tabs([
      ["a", 100],
      ["b", 100],
      ["c", 100],
    ]);
    /* a+b+gap+Mais = 100+100+8+40 = 248 → cabe em 260 com só c oculto */
    const overflow = resolveOverflowRibbonTabIds(list, 260, {
      overflowControlWidth: 40,
      gap: 8,
    });
    expect([...overflow]).toEqual(["c"]);
    /* em 250: 248 não cabe (espera Mais após gap) → esconde b também */
    const tighter = resolveOverflowRibbonTabIds(list, 250, {
      overflowControlWidth: 40,
      gap: 8,
    });
    expect([...tighter].sort()).toEqual(["b", "c"]);
  });
});
