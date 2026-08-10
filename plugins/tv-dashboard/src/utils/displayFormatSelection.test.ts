import { describe, expect, it } from "vitest";

import {
  applyDisplayFormatSpecToBlock,
  resolveCurrentDisplayFormatSpec,
  resolveDisplayFormatTarget,
} from "./displayFormatSelection";

describe("displayFormatSelection", () => {
  it("mapa seleção → slot: eixo X vs valores", () => {
    const chart = {
      id: "c1",
      type: "chart_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartOptions: { valueFormat: "auto" as const, categoryLabelFormat: "raw" as const },
    };
    expect(
      resolveDisplayFormatTarget({
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      }),
    ).toBe("chartCategory");
    expect(
      resolveDisplayFormatTarget({
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "y" },
      }),
    ).toBe("chartValue");
    expect(resolveDisplayFormatTarget({ selected: chart })).toBe("chartValue");
  });

  it("leitura: spec ganha do enum; gravação escreve spec + espelho", () => {
    const chart = {
      id: "c1",
      type: "chart_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartOptions: {
        valueFormat: "auto" as const,
        categoryLabelFormat: "raw" as const,
        displayCategoryFormat: {
          category: "date" as const,
          presetId: "date-short",
          pattern: "dd/mm/yyyy",
        },
      },
    };
    expect(
      resolveCurrentDisplayFormatSpec({
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      }).presetId,
    ).toBe("date-short");

    const patch = applyDisplayFormatSpecToBlock(
      { selected: { ...chart, chartOptions: { categoryLabelFormat: "raw" } } },
      { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
    );
    expect(patch).toMatchObject({
      chartOptions: {
        displayValueFormat: expect.objectContaining({ category: "date" }),
        valueFormat: "auto",
      },
    });

    const catPatch = applyDisplayFormatSpecToBlock(
      {
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      },
      { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
    );
    expect(catPatch).toMatchObject({
      chartOptions: {
        displayCategoryFormat: expect.objectContaining({ presetId: "date-short" }),
        categoryLabelFormat: "day",
      },
    });
  });

  it("com eixo X focado, % grava nos valores (não na categoria)", () => {
    const chart = {
      id: "c1",
      type: "chart_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartOptions: {
        valueFormat: "auto" as const,
        categoryLabelFormat: "day" as const,
        displayCategoryFormat: {
          category: "date" as const,
          presetId: "date-short",
          pattern: "dd/mm/yyyy",
        },
      },
    };
    const patch = applyDisplayFormatSpecToBlock(
      {
        selected: chart,
        selectedChartPart: { kind: "axis", axis: "x" },
      },
      { category: "percent", presetId: "percent", decimalPlaces: 1 },
    );
    expect(patch).toMatchObject({
      chartOptions: {
        displayValueFormat: expect.objectContaining({ category: "percent" }),
        valueFormat: "percent",
        categoryLabelFormat: "day",
      },
    });
  });

  it("tabela: grava spec + espelho legado", () => {
    const table = {
      id: "t1",
      type: "table_view" as const,
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tableOptions: { valueFormat: "auto" as const },
    };
    const patch = applyDisplayFormatSpecToBlock(
      { selected: table },
      { category: "currency", presetId: "currency-brl", currency: "BRL", decimalPlaces: 2 },
    );
    expect(patch).toMatchObject({
      tableOptions: {
        displayValueFormat: expect.objectContaining({ category: "currency" }),
        valueFormat: "currency",
      },
    });
  });
});
