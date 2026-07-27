import { describe, expect, it } from "vitest";

import {
  isCompositeContentPart,
  isMolduraPartSelection,
  resolveCompositePartPointerAction,
  shouldAttachCompositePartInteraction,
  shouldUsePartChromeInsteadOfBlock,
  toggleCompositePartSelection,
} from "./compositePartSelection";

describe("shouldAttachCompositePartInteraction", () => {
  it("sempre liga handlers no editor (fluxo composto unificado)", () => {
    expect(shouldAttachCompositePartInteraction("chart_view")).toBe(true);
    expect(shouldAttachCompositePartInteraction("kpi_view")).toBe(true);
    expect(shouldAttachCompositePartInteraction("table_view")).toBe(true);
  });
});

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
  it("molduras usam chrome global do bloco (pai ativo)", () => {
    expect(isMolduraPartSelection("kpi_view", { kind: "card" })).toBe(true);
    expect(isMolduraPartSelection("input", { kind: "frame" })).toBe(true);
    expect(isMolduraPartSelection("chart_view", { kind: "chartArea" })).toBe(true);
    expect(isMolduraPartSelection("table_view", { kind: "frame" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "chartArea" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "frame" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "card" })).toBe(false);
  });

  it("subitens (filhos) desativam chrome do pai — complexo ≡ agrupado", () => {
    expect(isCompositeContentPart("input", { kind: "control" })).toBe(true);
    expect(isCompositeContentPart("chart_view", { kind: "title" })).toBe(true);
    expect(isCompositeContentPart("kpi_view", { kind: "value" })).toBe(true);
    expect(isCompositeContentPart("kpi_view", { kind: "card" })).toBe(false);
    expect(shouldUsePartChromeInsteadOfBlock("input", { kind: "control" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", { kind: "title" })).toBe(true);
    expect(shouldUsePartChromeInsteadOfBlock("kpi_view", { kind: "value" })).toBe(true);
  });

  it("sem parte = chrome global", () => {
    expect(shouldUsePartChromeInsteadOfBlock("chart_view", null)).toBe(false);
    expect(isMolduraPartSelection("input", null)).toBe(false);
  });
});

describe("toggleCompositePartSelection", () => {
  const equal = (a: { kind: string }, b: { kind: string }) => a.kind === b.kind;

  it("sem additive substitui", () => {
    expect(
      toggleCompositePartSelection({
        blockType: "kpi_view",
        current: [{ kind: "title" }],
        next: { kind: "value" },
        equal,
      }),
    ).toEqual([{ kind: "value" }]);
  });

  it("additive alterna filhos de conteúdo", () => {
    expect(
      toggleCompositePartSelection({
        blockType: "kpi_view",
        current: [{ kind: "title" }],
        next: { kind: "value" },
        equal,
        additive: true,
      }),
    ).toEqual([{ kind: "title" }, { kind: "value" }]);
    expect(
      toggleCompositePartSelection({
        blockType: "kpi_view",
        current: [{ kind: "title" }, { kind: "value" }],
        next: { kind: "title" },
        equal,
        additive: true,
      }),
    ).toEqual([{ kind: "value" }]);
  });

  it("moldura ignora additive e volta ao pai", () => {
    expect(
      toggleCompositePartSelection({
        blockType: "kpi_view",
        current: [{ kind: "title" }, { kind: "value" }],
        next: { kind: "card" },
        equal,
        additive: true,
      }),
    ).toEqual([{ kind: "card" }]);
  });
});
