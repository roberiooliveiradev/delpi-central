import { describe, expect, it } from "vitest";

import {
  isMolduraPartSelection,
  resolveCompositePartPointerAction,
  shouldUsePartChromeInsteadOfBlock,
} from "./compositePartSelection";

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

describe("isMolduraPartSelection / shouldUsePartChromeInsteadOfBlock", () => {
  it("moldura do filtro, gráfico e tabela usam chrome global", () => {
    expect(isMolduraPartSelection("input", { kind: "frame" })).toBe(true);
    expect(isMolduraPartSelection("chart_view", { kind: "chartArea" })).toBe(true);
    expect(isMolduraPartSelection("table_view", { kind: "frame" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "chartArea" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "frame" })).toBe(false);
  });

  it("subitens (control, title, value) e card KPI usam chrome da parte", () => {
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "control" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "title" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "card" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "value" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("table_view", { kind: "header" })).toBe(true);
  });

  it("sem parte = chrome global", () => {
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", null)).toBe(false);
    expect(isMolduraPartSelection("input", null)).toBe(false);
  });
});
