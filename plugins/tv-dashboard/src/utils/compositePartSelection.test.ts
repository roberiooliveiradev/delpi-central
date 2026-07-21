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

  it("bloco selecionado + clique em conteúdo ainda arrasta o bloco (modo comum)", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: false,
        partAllowsMove: false,
        contentPart: true,
      }),
    ).toBe("drag-block");
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

  it("parte já selecionada e não móvel permanece no bloco (sem select-part no clique)", () => {
    expect(
      resolveCompositePartPointerAction({
        blockSelected: true,
        samePartSelected: true,
        partAllowsMove: false,
        contentPart: true,
      }),
    ).toBe("drag-block");
  });
});

describe("isMolduraPartSelection / shouldUsePartChromeInsteadOfBlock", () => {
  it("molduras (KPI card, filtro, gráfico, tabela) usam chrome global do bloco", () => {
    expect(isMolduraPartSelection("kpi_view", { kind: "card" })).toBe(true);
    expect(isMolduraPartSelection("input", { kind: "frame" })).toBe(true);
    expect(isMolduraPartSelection("chart_view", { kind: "chartArea" })).toBe(true);
    expect(isMolduraPartSelection("table_view", { kind: "frame" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "chartArea" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "frame" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "card" })).toBe(false);
  });

  it("subitens são conteúdo; chrome de palco permanece no bloco (como formas)", () => {
    expect(isCompositeContentPart("input", { kind: "control" })).toBe(true);
    expect(isCompositeContentPart("chart_view", { kind: "title" })).toBe(true);
    expect(isCompositeContentPart("chart_view", { kind: "series" })).toBe(true);
    expect(isCompositeContentPart("kpi_view", { kind: "value" })).toBe(true);
    expect(isCompositeContentPart("kpi_view", { kind: "card" })).toBe(false);
    expect(isCompositeContentPart("chart_view", { kind: "chartArea" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "control" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "title" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "value" })).toBe(false);
  });

  it("sem parte = chrome global", () => {
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", null)).toBe(false);
    expect(isMolduraPartSelection("input", null)).toBe(false);
  });
});
