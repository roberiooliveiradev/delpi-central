import { describe, expect, it } from "vitest";

import {
  isCompositeContentPart,
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
        contentPart: true,
      }),
    ).toBe("drag-block");
  });

  it("bloco selecionado + parte de conteúdo seleciona a parte (Excel-like)", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: false,
        partAllowsMove: false,
        contentPart: true,
      }),
    ).toBe("select-part");
  });

  it("moldura com bloco selecionado ainda arrasta o bloco", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: false,
        partAllowsMove: true,
        contentPart: false,
      }),
    ).toBe("drag-block");
  });

  it("mesma parte já selecionada e móvel arrasta a parte", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: true,
        partAllowsMove: true,
        contentPart: true,
      }),
    ).toBe("part-move");
  });

  it("parte de conteúdo já selecionada e não móvel fica em select-part", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: true,
        partAllowsMove: false,
        contentPart: true,
      }),
    ).toBe("select-part");
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

  it("subitens (control, title, value, series) usam chrome da parte", () => {
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "control" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "title" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "series" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "card" })).toBe(true);
    expect(isCompositeContentPart("chart_view", { kind: "series" })).toBe(true);
    expect(isCompositeContentPart("chart_view", { kind: "chartArea" })).toBe(false);
  });

  it("sem parte = chrome global", () => {
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", null)).toBe(false);
    expect(isMolduraPartSelection("input", null)).toBe(false);
  });
});
