import { describe, expect, it } from "vitest";

import {
  resolveCollapsedRibbonGroupIds,
  stabilizeCollapsedRibbonGroupIds,
  sumRibbonGroupsWidth,
  type RibbonGroupSize,
} from "./resolveCollapsedRibbonGroupIds";

function groups(widths: Array<[string, number, number]>): RibbonGroupSize[] {
  return widths.map(([id, expandedWidth, collapsedWidth], order) => ({
    id,
    expandedWidth,
    collapsedWidth,
    order,
  }));
}

describe("resolveCollapsedRibbonGroupIds", () => {
  it("não colapsa quando tudo cabe", () => {
    const list = groups([
      ["a", 100, 56],
      ["b", 100, 56],
      ["c", 100, 56],
    ]);
    // 300 + 2*8 = 316
    expect([...resolveCollapsedRibbonGroupIds(list, 400, 8)]).toEqual([]);
  });

  it("colapsa da direita para a esquerda", () => {
    const list = groups([
      ["a", 120, 56],
      ["b", 120, 56],
      ["c", 120, 56],
    ]);
    // full 360+16=376; collapse c → 120+120+56+16=312; collapse b,c → 120+56+56+16=248
    const one = resolveCollapsedRibbonGroupIds(list, 330, 8);
    expect([...one]).toEqual(["c"]);

    const two = resolveCollapsedRibbonGroupIds(list, 260, 8);
    expect([...two].sort()).toEqual(["b", "c"]);
  });

  it("sumRibbonGroupsWidth respeita gap e modo", () => {
    const list = groups([
      ["a", 100, 50],
      ["b", 100, 50],
    ]);
    expect(sumRibbonGroupsWidth(list, new Set(), 10)).toBe(210);
    expect(sumRibbonGroupsWidth(list, new Set(["b"]), 10)).toBe(160);
  });
});

describe("stabilizeCollapsedRibbonGroupIds", () => {
  it("mantém colapso na fronteira (histerese) em vez de expandir↔colapsar", () => {
    const list = groups([
      ["a", 400, 56],
      ["b", 400, 56],
      ["c", 400, 56],
    ]);
    // Tudo expandido: 1200+16=1216. Com C colapsado: 400+400+56+16=872.
    const available = 1216;
    const previous = new Set(["c"]);
    // Ideal puro reexpandiria (cabe exatamente), mas histerese de 24 exige folga.
    const stable = stabilizeCollapsedRibbonGroupIds(list, available, previous, 8, 24);
    expect([...stable]).toEqual(["c"]);

    // Com folga clara, reexpande.
    const roomy = stabilizeCollapsedRibbonGroupIds(list, available + 24, previous, 8, 24);
    expect([...roomy]).toEqual([]);
  });

  it("ainda colapsa mais quando a largura aperta", () => {
    const list = groups([
      ["a", 400, 56],
      ["b", 400, 56],
      ["c", 400, 56],
    ]);
    const previous = new Set(["c"]);
    // Com B+C colapsados: 400+56+56+16=528 — cabe em 600; A permanece expandido.
    const next = stabilizeCollapsedRibbonGroupIds(list, 600, previous, 8, 24);
    expect([...next].sort()).toEqual(["b", "c"]);
  });

  it("simula oscilação de medida na fronteira sem flip-flop", () => {
    const tight = groups([
      ["a", 401, 56],
      ["b", 401, 56],
      ["c", 401, 56],
    ]);
    const loose = groups([
      ["a", 399, 56],
      ["b", 399, 56],
      ["c", 399, 56],
    ]);
    const available = 1216; // exatamente 3*400 + 16
    let collapsed = stabilizeCollapsedRibbonGroupIds(tight, available, new Set(), 8, 24);
    expect([...collapsed].sort()).toEqual(["c"]);

    for (let i = 0; i < 20; i += 1) {
      const measures = i % 2 === 0 ? loose : tight;
      collapsed = stabilizeCollapsedRibbonGroupIds(measures, available, collapsed, 8, 24);
    }
    expect([...collapsed].sort()).toEqual(["c"]);
  });
});
